import os
from dotenv import load_dotenv
from agno.agent import Agent
# from agno.models.google.gemini import Gemini
from agno.models.openai import OpenAIChat
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.yfinance import YFinanceTools
from maxim import Maxim
from maxim.logger.agno import instrument_agno

# Load environment variables from .env file
load_dotenv()

instrument_agno(Maxim(
    {
        "debug": True
    }
).logger())

# Web Search Agent: Fetches financial information from the web
web_search_agent = Agent(
    name="Web Agent",
    role="Search the web for information",
    # model=Gemini(id="gemini-2.0-flash-001"),
    model=OpenAIChat(id="gpt-4o"),
    tools=[GoogleSearchTools()],
    instructions="Always include sources",
    show_tool_calls=True,
    markdown=True,
)


finance_agent = Agent(
    name="Finance Agent",
    role="Get financial data",
    # model=Gemini(id="gemini-2.0-flash-001"),
    model=OpenAIChat(id="gpt-4o"),
    tools=[YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True)],
    instructions="Use tables to display data",
    markdown=True,
)

# Aggregate both agents into a multi-agent system
multi_ai_agent = Agent(
    team=[web_search_agent, finance_agent],
    # model=Gemini(id="gemini-2.0-flash-001"),
    model=OpenAIChat(id="gpt-4o"),
    instructions="You are a helpful financial assistant. Answer user questions about stocks, companies, and financial data.",
    show_tool_calls=True,
    markdown=True
)

if __name__ == "__main__":
    print("Welcome to the Financial Conversational Agent! Type 'exit' to quit.")
    messages = []
    while True:
        print("********************************")
        user_input = input("You: ")
        if user_input.strip().lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        messages.append({"role": "user", "content": user_input})
        conversation = "\n".join([
            ("User: " + m["content"]) if m["role"] == "user" else ("Agent: " + m["content"]) for m in messages
        ])
        response = multi_ai_agent.run(
            f"Conversation so far:\n{conversation}\n\nRespond to the latest user message."
        )
        agent_reply = getattr(response, "content", response)
        print("---------------------------------")
        print("Agent:", agent_reply)
        messages.append({"role": "agent", "content": str(agent_reply)})

        # Print the full response object for debugging
        print("Full response object:", response)