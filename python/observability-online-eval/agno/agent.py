import os
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.google.gemini import Gemini
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.yfinance import YFinanceTools

from maxim import Maxim
from maxim.logger.agno import instrument_agno

# Load environment variables from .env file
load_dotenv()

instrument_agno(Maxim().logger())

# Web Search Agent: Fetches financial information from the web
web_search_agent = Agent(
    name="Web Agent",
    role="Search the web for information",
    model=Gemini(id="gemini-2.0-flash-001"),
    tools=[GoogleSearchTools()],
    instructions="Always include sources",
    show_tool_calls=True,
    markdown=True,
)


finance_agent = Agent(
    name="Finance Agent",
    role="Get financial data",
    model=Gemini(id="gemini-2.0-flash-001"),
    tools=[YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True)],
    instructions="Use tables to display data",
    markdown=True,
)

# Aggregate both agents into a multi-agent system
multi_ai_agent = Agent(
    team=[web_search_agent, finance_agent],
    model=Gemini(id="gemini-2.0-flash-001"),
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
        # DEBUG: Print system prompt
        print("---------------------------------")
        print("DEBUG: multi_ai_agent.instructions =", getattr(multi_ai_agent, "instructions", None))
        # DEBUG: Print tool calls (tools for each agent)
        for idx, agent in enumerate([web_search_agent, finance_agent], 1):
            print("---------------------------------")
            print(f"DEBUG: Agent {idx} tools:", getattr(agent, "tools", None))
        print("---------------------------------")
        print("DEBUG: multi_ai_agent.tools =", getattr(multi_ai_agent, "tools", None))
        # DEBUG: Print model and its attributes before running
        model = getattr(multi_ai_agent, "model", None)
        print("DEBUG: multi_ai_agent.model =", model)
        if model:
            print("---------------------------------")
            print("DEBUG: model.__dict__ =", getattr(model, "__dict__", {}))
            print("DEBUG: model.model_settings =", getattr(model, "model_settings", None))
            print("DEBUG: model.kwargs =", getattr(model, "kwargs", None))
            print("DEBUG: model.id =", getattr(model, "id", None))
            print("DEBUG: model.provider =", getattr(model, "provider", None))
        response = multi_ai_agent.run(
            f"Conversation so far:\n{conversation}\n\nRespond to the latest user message."
        )
        agent_reply = getattr(response, "content", response)
        print("---------------------------------")
        print("Agent:", agent_reply)
        messages.append({"role": "agent", "content": str(agent_reply)})
