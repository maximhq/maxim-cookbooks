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

# Define a custom tool or function to process input
def custom_respond(input_text):
    """
    Custom function to process input, generate a response using LlamaIndex,
    and return the processed result.
    """
    print(f"Processing input: {input_text}")
    
    # Generate response using the LlamaIndex query engine
    response = query_engine.query(input_text)
    response_text = response.response  # Extracting the text from the response
    
    return str(response_text)  # Return as string to ensure compatibility

try:
    # Define the input prompt for the custom tool
    prompt = "What is the total amount of collected comprehensive trailer videos?"
    
    # Use the custom tool to generate the response
    response_text = custom_respond(prompt)

    # Log the response with Maxim
    trace.event(str(uuid4()), "Tool Response", {"response_text": response_text})

    # Print the response
    print("Custom Tool Response:")
    print(response_text)

finally:
    # Clean up the logger session
    trace.end()
    logger.cleanup()