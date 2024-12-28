import logging
import os
from functools import lru_cache
from typing import Annotated, List, Literal, Sequence, Tuple, TypedDict, Union
from uuid import uuid4

from flask import Flask, jsonify, request
from langchain import hub
from langchain_anthropic import Anthropic, ChatAnthropic
from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchTool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode, create_react_agent
from maxim import Config, Maxim
from maxim.decorators import current_trace, span, trace
from maxim.decorators.langchain import langchain_callback, langgraph_agent
from maxim.logger import LoggerConfig
from pydantic.type_adapter import R

logging.basicConfig(level=logging.INFO)

openAIKey = os.environ.get("OPENAI_API_KEY", None)
anthropicApiKey = os.environ.get("ANTHROPIC_API_KEY", None)
apiKey = os.environ.get("MAXIM_API_KEY", None)
baseUrl = os.environ.get("MAXIM_BASE_URL", None)
repoId = os.environ.get("LOG_REPO_ID", None)
tavilyApiKey = os.environ.get("TAVILY_API_KEY", None)


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


tools = [TavilySearchResults(max_results=1, tavily_api_key=tavilyApiKey)]


@lru_cache(maxsize=4)
def _get_model(model_name: str):
    if model_name == "openai":
        model = ChatOpenAI(temperature=0, model_name="gpt-4o", api_key=openAIKey)
    elif model_name == "anthropic":
        model = ChatAnthropic(
            temperature=0,
            model_name="claude-3-sonnet-20240229",
            api_key=anthropicApiKey,
        )
    else:
        raise ValueError(f"Unsupported model type: {model_name}")

    model = model.bind_tools(tools)
    return model


# Define the function that determines whether to continue or not
def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    # If there are no tool calls, then we finish
    if not last_message.tool_calls:
        return "end"
    # Otherwise if there is, we continue
    else:
        return "continue"


system_prompt = """Be a helpful assistant"""


# Define the function that calls the model
def call_model(state, config):
    messages = state["messages"]
    messages = [{"role": "system", "content": system_prompt}] + messages
    model_name = config.get("configurable", {}).get("model_name", "anthropic")
    model = _get_model(model_name)
    response = model.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


# Define the function to execute tools
tool_node = ToolNode(tools)


# Define the config
class GraphConfig(TypedDict):
    model_name: Literal["anthropic", "openai"]


# Define a new graph
workflow = StateGraph(AgentState, config_schema=GraphConfig)

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("action", tool_node)

# Set the entrypoint as `agent`
# This means that this node is the first one called
workflow.set_entry_point("agent")

# We now add a conditional edge
workflow.add_conditional_edges(
    # First, we define the start node. We use `agent`.
    # This means these are the edges taken after the `agent` node is called.
    "agent",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
    # Finally we pass in a mapping.
    # The keys are strings, and the values are other nodes.
    # END is a special node marking that the graph should finish.
    # What will happen is we will call `should_continue`, and then the output of that
    # will be matched against the keys in this mapping.
    # Based on which one it matches, that node will then be called.
    {
        # If `tools`, then we call the tool node.
        "continue": "action",
        # Otherwise we finish.
        "end": END,
    },
)

# We now add a normal edge from `tools` to `agent`.
# This means that after `tools` is called, `agent` node is called next.
workflow.add_edge("action", "agent")

logger = Maxim(Config(api_key=apiKey, debug=True)).logger(
    LoggerConfig(id=repoId)
)

# Finally, we compile it!
# This compiles it into a LangChain Runnable,
# meaning you can use it as you would any other runnable
app = workflow.compile()
flask_app = Flask(__name__)


@span(name="another_method")
def another_method(query:str)->str:
    return query

@langgraph_agent(name="agent-v1")
async def ask_agent(query: str) -> str:
    config = {"recursion_limit": 50, "callbacks": [langchain_callback()]}
    async for event in app.astream(input={"messages": [query]}, config=config):
        for k, v in event.items():
            if k == "agent":
                response = str(v["messages"][0].content)
    return response


@flask_app.post("/chat")
@trace(logger=logger, name="chat-v1-handler")
async def handle():
    resp = await ask_agent(request.json["query"])
    current_trace().set_output(str(resp))
    await another_method(str(resp))
    return jsonify({"result": resp})


flask_app.run(port=8000)
