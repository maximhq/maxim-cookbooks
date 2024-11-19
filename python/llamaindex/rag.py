import os
from dotenv import dotenv_values
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, ServiceContext
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.llms.openai import OpenAI
from maxim.maxim import Logger, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig
from uuid import uuid4

# Retrieve API keys from environment variables
MAXIM_API_KEY = os.getenv("MAXIM_API_KEY")
LOG_REPOSITORY_ID = os.getenv("LOG_REPOSITORY_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Define the OpenAI model
MODEL_NAME = "gpt-4o-mini"

# Set up Maxim logger configuration
logger_config = LoggerConfig(id=LOG_REPOSITORY_ID)
logger = Logger(config=logger_config, api_key=MAXIM_API_KEY, base_url="https://app.getmaxim.ai")

# Set up a unique session and trace for the application
session_id = str(uuid4())
session_config = SessionConfig(id=session_id)
session = logger.session(session_config)

trace_id = str(uuid4())
trace_config = TraceConfig(id=trace_id)
trace = session.trace(trace_config)

# Initialize the LlamaIndex OpenAI client
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
llm = OpenAI(model=MODEL_NAME)
documents = SimpleDirectoryReader("../maxim-cookbooks/").load_data()

# Define the LLM and other components
llm = OpenAI(model="gpt-3.5-turbo")
node_parser = SimpleNodeParser.from_defaults(chunk_size=512)
nodes = node_parser.get_nodes_from_documents(documents=documents)
vector_index = VectorStoreIndex(nodes)
query_engine = vector_index.as_query_engine(similarity_top_k=2)

# Perform the query and retrieve the response
response_vector = query_engine.query("What is the total amount of collected comprehensive trailer videos?")

# Extract the response
response_text = response_vector.response

# Log the response with Maxim
try:
    # Log the response text to Maxim
    trace.event(str(uuid4()), "RAG Query Response", {"response_text": response_text})
    
    # Print the response to the console
    print("RAG Query Response:")
    print(response_text)

finally:
    # Clean up the logger session
    trace.end()
    logger.cleanup()