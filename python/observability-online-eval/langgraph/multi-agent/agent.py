import os
import re
import subprocess
from operator import itemgetter
from typing import (
    Callable,
    List,
    Literal,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    cast,
)

from dotenv.main import load_dotenv
from flask import Flask, jsonify, request
from IPython.display import Image, display
from langchain.chains import create_sql_query_chain
from langchain.tools import tool
from langchain_chroma import Chroma
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities import SQLDatabase
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel, LanguageModelLike
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import (
    Runnable,
    RunnableBinding,
    RunnableConfig,
    RunnableLambda,
    RunnablePassthrough,
)
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph._api.deprecation import deprecated_parameter
from langgraph.errors import ErrorCode, create_error_message
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.graph import CompiledGraph
from langgraph.graph.message import add_messages
from langgraph.managed import IsLastStep, RemainingSteps
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.prebuilt.tool_node import ToolNode, tools_condition
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer, Command
from langgraph.utils.runnable import RunnableCallable
from maxim import Config, Maxim
from maxim.decorators import current_span, current_trace, span, trace
from maxim.decorators.langchain import langchain_callback, langgraph_agent
from maxim.logger import LoggerConfig
from maxim.logger.components.generation import Generation, GenerationConfig
from maxim.logger.components.span import Span, SpanConfig
from maxim.logger.components.toolCall import ToolCall, ToolCallConfig
from maxim.logger.components.trace import Trace
from mock_tracer import MockTracer
from pydantic import BaseModel
from typing_extensions import Annotated, TypedDict

load_dotenv()


os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.environ.get("LANGCHAIN_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = "langgraph_multi_agent_blog"
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "")
os.environ["TAVILY_API_KEY"] = os.environ.get("TAVILY_API_KEY", "")


maxim_api_key = os.environ.get("MAXIM_API_KEY", "")
maxim_base_url = os.environ.get("MAXIM_BASE_URL", "")
maxim_repo_id = os.environ.get("MAXIM_LOG_REPO_ID", "")
logger = Maxim(
    Config(api_key=maxim_api_key, debug=True, base_url=maxim_base_url)
).logger(LoggerConfig(id=maxim_repo_id))

llm = ChatOpenAI(model_name="gpt-4o")

web_search_tool = TavilySearchResults(max_results=2)


def load_documents(folder_path: str) -> List[Document]:
    documents = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if filename.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif filename.endswith(".docx"):
            loader = Docx2txtLoader(file_path)
        else:
            # print(f"Unsupported file type: {filename}")
            
            continue
        documents.extend(loader.load())
    return documents


def vector_store() -> Chroma:
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    # Check if the database already exists
    if os.path.exists("./chroma_db"):
        # print("Loading existing vector store from './chroma_db'")
        vectorstore = Chroma(
            collection_name="my_collection",
            embedding_function=embedding_function,
            persist_directory="./chroma_db",
        )
    else:
        # print("Creating new vector store...")
        folder_path = os.path.join(os.path.dirname(__file__), "content", "docs")
        documents = load_documents(folder_path)
        # print(f"Loaded {len(documents)} documents from the folder.")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, length_function=len
        )

        splits = text_splitter.split_documents(documents)
        # print(f"Split the documents into {len(splits)} chunks.")

        vectorstore = Chroma.from_documents(
            collection_name="my_collection",
            documents=splits,
            embedding=embedding_function,
            persist_directory="./chroma_db",
        )
        # print("Vector store created and persisted to './chroma_db'")

    return vectorstore


vectorstore = vector_store()

retriever = vectorstore.as_retriever(search_kwargs={"k": 2})


class RagToolSchema(BaseModel):
    question: str


@tool(args_schema=RagToolSchema)
def retriever_tool(question):
    """Tool to Retrieve Semantically Similar documents to answer User Questions related to FutureSmart AI"""
    # print("INSIDE RETRIEVER NODE")
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
    retriever_results = retriever.invoke(question)
    return "\n\n".join(doc.page_content for doc in retriever_results)


if not os.path.exists("Chinook.db"):
    # print("Downloading Chinook database...")
    subprocess.run(
        [
            "wget",
            "https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite",
        ]
    )
    subprocess.run(["mv", "Chinook_Sqlite.sqlite", "Chinook.db"])
else:
    # print("Chinook database already exists")
    pass


db = SQLDatabase.from_uri("sqlite:///Chinook.db")


def clean_sql_query(text: str) -> str:
    """
    Clean SQL query by removing code block syntax, various SQL tags, backticks,
    prefixes, and unnecessary whitespace while preserving the core SQL query.

    Args:
        text (str): Raw SQL query text that may contain code blocks, tags, and backticks

    Returns:
        str: Cleaned SQL query
    """
    # Step 1: Remove code block syntax and any SQL-related tags
    # This handles variations like ```sql, ```SQL, ```SQLQuery, etc.
    block_pattern = r"```(?:sql|SQL|SQLQuery|mysql|postgresql)?\s*(.*?)\s*```"
    text = re.sub(block_pattern, r"\1", text, flags=re.DOTALL)

    # Step 2: Handle "SQLQuery:" prefix and similar variations
    # This will match patterns like "SQLQuery:", "SQL Query:", "MySQL:", etc.
    prefix_pattern = r"^(?:SQL\s*Query|SQLQuery|MySQL|PostgreSQL|SQL)\s*:\s*"
    text = re.sub(prefix_pattern, "", text, flags=re.IGNORECASE)

    # Step 3: Extract the first SQL statement if there's random text after it
    # Look for a complete SQL statement ending with semicolon
    sql_statement_pattern = r"(SELECT.*?;)"
    sql_match = re.search(sql_statement_pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if sql_match:
        text = sql_match.group(1)

    # Step 4: Remove backticks around identifiers
    text = re.sub(r"`([^`]*)`", r"\1", text)

    # Step 5: Normalize whitespace
    # Replace multiple spaces with single space
    text = re.sub(r"\s+", " ", text)

    # Step 6: Preserve newlines for main SQL keywords to maintain readability
    keywords = [
        "SELECT",
        "FROM",
        "WHERE",
        "GROUP BY",
        "HAVING",
        "ORDER BY",
        "LIMIT",
        "JOIN",
        "LEFT JOIN",
        "RIGHT JOIN",
        "INNER JOIN",
        "OUTER JOIN",
        "UNION",
        "VALUES",
        "INSERT",
        "UPDATE",
        "DELETE",
    ]

    # Case-insensitive replacement for keywords
    pattern = "|".join(r"\b{}\b".format(k) for k in keywords)
    text = re.sub(f"({pattern})", r"\n\1", text, flags=re.IGNORECASE)

    # Step 7: Final cleanup
    # Remove leading/trailing whitespace and extra newlines
    text = text.strip()
    text = re.sub(r"\n\s*\n", "\n", text)

    return text


class SQLToolSchema(BaseModel):
    question: str


@tool(args_schema=SQLToolSchema)
def nl2sql_tool(question):
    """Tool to Generate and Execute SQL Query to answer User Questions related to chinook DB"""
    # print("INSIDE NL2SQL TOOL")
    execute_query = QuerySQLDataBaseTool(db=db)
    write_query = create_sql_query_chain(llm, db)

    chain = RunnablePassthrough.assign(
        query=write_query | RunnableLambda(clean_sql_query)
    ).assign(result=itemgetter("query") | execute_query)

    response = chain.invoke({"question": question})
    return response["result"]


members = ["web_researcher", "rag", "nl2sql"]
# Our supervisor is an LLM node. It just picks the next agent to process
# and decides when the work is completed
options = members + ["FINISH"]

system_prompt = (
    "You are a supervisor tasked with managing a conversation between the"
    f" following workers: {members}. Given the following user request,"
    " respond with the worker to act next. Each worker will perform a"
    " task and respond with their results and status. When finished,"
    " respond with FINISH."
)


class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal["web_researcher", "rag", "nl2sql", "FINISH"]


def supervisor_node(
    state: MessagesState,
) -> Command[Literal["web_researcher", "rag", "nl2sql", "__end__"]]:
    messages = [
        {"role": "system", "content": system_prompt},
    ] + state["messages"]
    response = llm.with_structured_output(Router).invoke(messages)
    goto = response["next"]
    # print(f"Next Worker: {goto}")
    if goto == "FINISH":
        goto = END

    return Command(goto=goto)


class AgentState(TypedDict):
    """The state of the agent."""

    messages: Annotated[Sequence[BaseMessage], add_messages]


def create_agent(llm, tools):
    llm_with_tools = llm.bind_tools(tools)

    def chatbot(state: AgentState):
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("agent", chatbot)

    tool_node = ToolNode(tools=tools)
    graph_builder.add_node("tools", tool_node)

    graph_builder.add_conditional_edges(
        "agent",
        tools_condition,
    )
    # Any time a tool is called, we return to the chatbot to decide the next step
    graph_builder.add_edge("tools", "agent")
    graph_builder.set_entry_point("agent")
    graph = graph_builder.compile()
    return graph


websearch_agent = create_agent(llm, [web_search_tool])

# try:
#     print(websearch_agent.get_graph().draw_mermaid_png())
# except Exception:
#     pass


def web_research_node(state: MessagesState) -> Command[Literal["supervisor"]]:
    result = websearch_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=result["messages"][-1].content, name="web_researcher"
                )
            ]
        },
        goto="supervisor",
    )


rag_agent = create_agent(llm, [retriever_tool])


def rag_node(state: MessagesState) -> Command[Literal["supervisor"]]:
    result = rag_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="rag")
            ]
        },
        goto="supervisor",
    )


nl2sql_agent = create_agent(llm, [nl2sql_tool])


def nl2sql_node(state: MessagesState) -> Command[Literal["supervisor"]]:
    result = nl2sql_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="nl2sql")
            ]
        },
        goto="supervisor",
    )


builder = StateGraph(MessagesState)
builder.add_edge(START, "supervisor")
builder.add_node("supervisor", supervisor_node)
builder.add_node("web_researcher", web_research_node)
builder.add_node("rag", rag_node)
builder.add_node("nl2sql", nl2sql_node)
graph = builder.compile()


@langgraph_agent(name="multi-agent-work")
def ask_agent(user_message: str):
    config = {"callbacks": [langchain_callback()]}
    repsonse = ""
    for s in graph.stream(
        input={
            "messages": [("user", user_message)],
        },
        config=config,
        subgraphs=True,
    ):
        response = str(s)
    return response

flask_app = Flask(__name__)


@flask_app.post("/chat")
@trace(logger=logger, name="movie-search-v1")
def chat():
    query = request.json["query"]
    response = ask_agent(query)
    current_trace().set_output(response)
    return jsonify({"result": response})


flask_app.run(port=8000)

# from langfuse.callback import CallbackHandler
# langfuse_handler = CallbackHandler()
