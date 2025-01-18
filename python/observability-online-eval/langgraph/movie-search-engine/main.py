import json
import logging
import os
from functools import lru_cache
from typing import Annotated, List, Literal, Sequence, Tuple, TypedDict, Union
from uuid import uuid4
import asyncio
import dotenv
import weaviate
from flask import Flask, jsonify, request
from langchain.tools.retriever import create_retriever_tool
from langchain_anthropic import ChatAnthropic
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_weaviate import WeaviateVectorStore
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode

from maxim import Config, Maxim
from maxim.decorators import current_trace, span, trace, current_span
from maxim.logger.components.span import Span, SpanConfig
from maxim.logger.components.trace import Trace
from maxim.decorators.langchain import langchain_callback, langgraph_agent
from maxim.logger import LoggerConfig


logging.basicConfig(level=logging.INFO)

dotenv.load_dotenv()

# Environment variables
weaviate_url = os.environ.get("WEAVIATE_URL", "")
weaviate_key = os.environ.get("WEAVIATE_API_KEY", "")
openai_key = os.environ.get("OPENAI_API_KEY", "")
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
tavily_api_key = os.environ.get("TAVILY_API_KEY", "")

maxim_api_key = os.environ.get("MAXIM_API_KEY", "")
maxim_base_url = os.environ.get("MAXIM_BASE_URL", "")
maxim_repo_id = os.environ.get("MAXIM_LOG_REPO_ID", "")

logger = Maxim(Config(api_key=maxim_api_key, debug=True, base_url=maxim_base_url)).logger(
    LoggerConfig(id=maxim_repo_id)
)

# Initialize Weaviate client
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=weaviate.auth.AuthApiKey(api_key=weaviate_key),
    skip_init_checks=True
)

# Initialize vector store and retriever
vector_store = WeaviateVectorStore(
    client=client,
    index_name="Awesome_moviate_movies",
    text_key="title",
    embedding=OpenAIEmbeddings(api_key=openai_key,model="text-embedding-3-small"),
    attributes=[
        "title",
        "description",
        "Plot",
        "keywords",
        "genres",
        "actors",
        "director",
    ],
)
retriever = vector_store.as_retriever()

# Create tools
retriever_tool = create_retriever_tool(
    retriever,
    "search_movies",
    "Search for information about movies in the database.",
)

tavily_tool = TavilySearchResults(max_results=3, tavily_api_key=tavily_api_key)

tools = [retriever_tool, tavily_tool]


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    retriever_tried: bool


@lru_cache(maxsize=4)
def get_model(model_name: str):
    if model_name == "openai":
        model = ChatOpenAI(temperature=0, model_name="gpt-4", api_key=openai_key)
    elif model_name == "anthropic":
        model = ChatAnthropic(
            temperature=0,
            model_name="claude-3-sonnet-20240229",
            api_key=anthropic_api_key,
        )
    else:
        raise ValueError(f"Unsupported model type: {model_name}")

    model = model.bind_tools(tools)
    return model


def should_continue(state: AgentState) -> str:
    """Determine the next step in the workflow."""
    messages = state["messages"]
    retriever_tried = state.get("retriever_tried", False)

    if not retriever_tried:
        # First try the movie database retriever
        return "retrieve"

    last_message = messages[-1]
    # Check if we need to use Tavily search
    if last_message.tool_calls is not None and isinstance(last_message.tool_calls, list) and len(last_message.tool_calls) > 0 and  last_message.tool_calls[0] is not None:
        return "search"

    # If we've already tried both or found an answer, end
    return "end"


def call_model(state: AgentState, config: dict) -> dict:
    """Call the LLM with the current state."""
    messages = state["messages"]
    model_name = config.get("configurable", {}).get("model_name", "openai")
    model = get_model(model_name)

    # Add system prompt
    system_prompt = """You are a helpful movie information assistant. You have search_movie and tavily search tools.
    Priorotise database search but if you need to do a general search, use tavily search. Make sure your answer is valid irrespective of the search.    
    Always provide clear, concise answers."""

    # Prepare messages
    formatted_messages = [{"role": "system", "content": system_prompt}] + messages

    response = model.invoke(formatted_messages)
    return {"messages": [response]}


def run_retriever(state: AgentState) -> dict:
    """Execute the movie database retrieval."""
    messages = state["messages"]
    last_message = messages[-1]
    tool_call_id = last_message.tool_calls[0]["id"]
    try:
        
        results = retriever_tool.invoke(
            input=str(last_message.tool_calls[0]["args"]["query"])
        )
        if not results:
            return {
                "messages": [
                    ToolMessage(
                        tool_call_id=tool_call_id,
                        content="No relevant information found in the movie database. Let's try a general search."
                    )
                ],
                "retriever_tried": True,
            }
        return {
            "messages": [ToolMessage(tool_call_id=tool_call_id,content=f"Found in movie database: {results}")],
            "retriever_tried": True,
        }
    except Exception as e:
        logging.error(f"Retriever error: {e}")
        return {
            "messages": [
                ToolMessage(
                    tool_call_id=tool_call_id,
                    content="Error accessing movie database. Let's try a general search."
                )
            ],
            "retriever_tried": True,
        }


def run_search(state: AgentState) -> dict:
    """Execute the Tavily search."""
    messages = state["messages"]
    last_message = messages[-1]
    tool_call_id = last_message.tool_calls[0]["id"]
    try:
        results = tavily_tool.invoke(input= str(last_message.tool_calls[0]["args"]["query"]))
        return {
            "messages": [ToolMessage(tool_call_id=tool_call_id,content=f"Found from general search: {results}")]
        }
    except Exception as e:
        logging.error(f"Tavily search error: {e}")
        return {
            "messages": [
                ToolMessage(tool_call_id=tool_call_id,content="Sorry, I couldn't find any relevant information.")
            ]
        }


# Create the workflow graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", call_model)
workflow.add_node("retrieve", run_retriever)
workflow.add_node("search", run_search)

# Set entry point
workflow.set_entry_point("agent")

# Add edges with conditions
workflow.add_conditional_edges(
    "agent", should_continue, {"retrieve": "retrieve", "search": "search", "end": END}
)

# Add return edges to agent
workflow.add_edge("retrieve", "agent")
workflow.add_edge("search", "agent")

# Compile the workflow
app = workflow.compile()
# Flask application
flask_app = Flask(__name__)
trace_id = str(uuid4())

# @span(name="retieve")
# def retriever_span(k,v)->None:
#     print("Here in Retrieve")
#     current_span().event(str(uuid4()), f"{k}",{})

# @span(name="search")
# def search_span(k,v)->None:
#     print("Here in Search")
#     current_span().event(str(uuid4()), f"{k}",{})

# @span(logger=logger,trace_id=trace_id,name="agent")
# def agent_span(k,v)->None:
#     print("Here in Agent")
#     current_span().event(str(uuid4()), f"{k}",{})
def serialize_tool_call(tool_call):
    """Helper function to serialize tool calls"""
    if tool_call is None:
        return None
    
    return {
        "content": tool_call.content,
        "type": "tool_call",
        **({"id": tool_call.id} if hasattr(tool_call, "id") else {}),
        **({"tool_call_id": tool_call.tool_call_id} if hasattr(tool_call, "tool_call_id") else {})
    }

def serialize_message(message):
    """Helper function to serialize AIMessage objects"""
    if message is None:
        return None
    
    return {
        "content": message.content,
        "type": message.type,
        # Only include other fields if they exist and are not None
        **({"additional_kwargs": message.additional_kwargs} if hasattr(message, "additional_kwargs") else {}),
        **({"tool_calls": message.tool_calls} if hasattr(message, "tool_calls") else {}),
        **({"id": message.id} if hasattr(message, "id") else {})
    }

@langgraph_agent(name="movie-agent-v1")
async def ask_agent(trace:Trace,initial_state:dict,query: str) -> str:
    config = {"callbacks": [langchain_callback()]}
    async for event in app.astream(input=initial_state, config=config):
        print('*'*50)
        print(event)
        print('*'*50)
        for k, v in event.items():
            # if k == "retrieve":
                # retriever_span(k,v)
                # message_dict = serialize_tool_call(v['messages'][0])
                # serialized_event = json.dumps(message_dict)
                # print(f"serialized retrieve tool call {serialized_event}")
                # span = trace.span(SpanConfig(id=str(uuid4()), name=f"retrieve"))
                # span.event(str(uuid4()), f"{k}",{k:serialized_event})
            # if k == "search":
                # search_span(k,v)
                # span = trace.span(SpanConfig(id=str(uuid4()), name=f"search-{str(uuid4())}"))
            if k == "agent":
                # agent_span(k,v)
                message_dict = serialize_message(v['messages'][0])
                serialized_event = json.dumps(message_dict)
                print(f"serialized event {serialized_event}")
                span = trace.span(SpanConfig(id=str(uuid4()), name=f"agent"))
                span.event(str(uuid4()), f"{k}",{k:serialized_event})
                response = str(v["messages"][0].content)
    return response

@flask_app.post("/chat")
@trace(logger=logger, name="movie-search-v1")
async def chat():
    try:
        query = request.json["query"]
        initial_state = {
            "messages": query,
            "retriever_tried": False,
        }
        trace = current_trace()
        response = await ask_agent(trace,initial_state,query)
        trace.set_input(query)
        trace.set_output(str(response))
        trace.attach_evaluators(evaluators=['Bias','Output Relevance','isMoviePresent'])
        trace.with_variables(for_evaluators=['Bias','Output Relevance','isMoviePresent'],variables={'input':query,'output':response,"expectedOutput":""})

        return jsonify({"result": response})
    except Exception as e:
        logging.error(f"Chat endpoint error: {e}")
        return jsonify({"error": str(e)}), 500

print(app.get_graph().draw_mermaid())

if __name__ == "__main__":
    flask_app.run(port=8000,debug=True)
