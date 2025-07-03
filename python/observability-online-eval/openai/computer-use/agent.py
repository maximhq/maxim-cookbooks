import os
from typing import Literal, List

from dotenv import load_dotenv
from langchain_core.messages import AnyMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from langgraph_cua import create_cua
from langgraph_cua.types import CUAState
from maxim.decorators.langchain import langchain_callback, langgraph_agent
from maxim.decorators import trace, current_trace
from maxim import Maxim


load_dotenv()

# Initialize Maxim logger for observability
logger = Maxim({"api_key": os.getenv("MAXIM_API_KEY")}).logger({"id": os.getenv("MAXIM_LOG_REPO_ID")})

# Create the base CUA graph
cua_graph = create_cua()


class ResearchState(CUAState):
    """State class for the research agent workflow, extending the CUA state.
    This state tracks whether to use the computer for research or respond directly."""
    route: Literal["respond", "computer_use_agent"]


def process_input(state: ResearchState):
    """
    Analyzes the user's latest message and determines whether to route to the
    computer use agent for research or generate a direct response.
    """
    system_message = {
        "role": "system",
        "content": (
            "You're an advanced AI assistant tasked with routing the user's query to the appropriate node."
            "Your options are: computer use or respond. You should pick computer use if the user's request requires "
            "using a computer (e.g. looking up information online, checking websites, or doing research), "
            "and pick respond for ANY other inputs."
        ),
    }

    class RoutingToolSchema(BaseModel):
        """Route the user's request to the appropriate node."""
        route: Literal["respond", "computer_use_agent"] = Field(
            ...,
            description="The node to route to, either 'computer_use_agent' for any input which might require using a computer to assist the user, or 'respond' for any other input",
        )

    model = ChatOpenAI(model="gpt-4o", temperature=0)
    model_with_tools = model.with_structured_output(RoutingToolSchema)

    user_messages = state.get("messages", [])
    if not user_messages:
        return {"route": "respond"}  # Default to respond if no messages

    messages = [system_message, {"role": "user", "content": user_messages[-1].content}]
    response = model_with_tools.invoke(messages)
    return {"route": response.route}


def respond(state: ResearchState):
    """
    Generates a general response to the user based on the entire conversation history.
    """
    def format_messages(messages: List[AnyMessage]) -> str:
        """Formats a list of messages into a single string with type and content."""
        return "\n".join([f"{message.type}: {message.content}" for message in messages])

    system_message = {
        "role": "system",
        "content": (
            "You're an advanced AI assistant tasked with responding to the user's input. "
            "You're provided with the full conversation between the user and the AI assistant. "
            "This conversation may include messages from a computer use agent that has performed research, "
            "along with general user inputs and AI responses.\n\n"
            "Given all of this, please RESPOND to the user. If there is nothing to respond to, "
            "you may return something like 'Let me know what information you'd like me to research for you.'"
        ),
    }
    human_message = {
        "role": "user",
        "content": "Here are all of the messages in the conversation:\n\n"
        + format_messages(state.get("messages")),
    }

    model = ChatOpenAI(model="gpt-4o", temperature=0)
    response = model.invoke([system_message, human_message])

    return {"response": response}


def route_after_processing_input(state: ResearchState):
    """Conditional router that returns the route determined by process_input."""
    return state.get("route")


workflow = StateGraph(ResearchState)
workflow.add_node("process_input", process_input)
workflow.add_node("respond", respond)
workflow.add_node("computer_use_agent", cua_graph)

workflow.add_edge(START, "process_input")
workflow.add_conditional_edges("process_input", route_after_processing_input)
workflow.add_edge("respond", END)
workflow.add_edge("computer_use_agent", END)

graph = workflow.compile()
graph.name = "Research Agent"


@langgraph_agent(name="research-agent-v1")
async def ask_agent(messages):
    config = {"recursion_limit": 100, "callbacks": [langchain_callback()]}
    stream = graph.astream({"messages": messages}, subgraphs=True, stream_mode="updates", config=config)
    last_update = None
    async for update in stream:
        if "computer_use_agent" in update[1]:
            last_update = update[1]["computer_use_agent"].get("messages", {})
    return last_update


@trace(logger=logger, name="research-agent-v1")
async def handle(messages) -> str:
    response = await ask_agent(messages)
    if isinstance(response, str):
        current_trace().set_output(response)
    return response


async def main():
    """Run the research agent workflow with automatic tracing."""
    messages = [
        {
            "role": "system",
            "content": (
                "You're an advanced AI computer use assistant. The browser you are using "
                "is already initialized, and visiting google.com."
            ),
        },
        {
            "role": "user",
            "content": "find today's top 1 song on billboard's charts.",
        },
    ]

    await handle(messages)
    print("\nCheck your Maxim dashboard to see the full trace of this research interaction!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
