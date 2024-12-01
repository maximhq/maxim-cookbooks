import os
from time import time
from uuid import uuid4
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.llms.openai import OpenAI
from maxim.maxim import Logger, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig
from maxim.logger.components.generation import GenerationConfig

# Retrieve API keys from environment variables
MAXIM_API_KEY = os.getenv("MAXIM_API_KEY")
LOG_REPOSITORY_ID = os.getenv("LOG_REPOSITORY_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Define the model name
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

# Initialize components and RAG setup
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
llm = OpenAI(model=MODEL_NAME)
documents = SimpleDirectoryReader("../maxim-cookbooks/").load_data()
node_parser = SimpleNodeParser.from_defaults(chunk_size=512)
nodes = node_parser.get_nodes_from_documents(documents=documents)
vector_index = VectorStoreIndex(nodes)
query_engine = vector_index.as_query_engine(similarity_top_k=2, streaming=True)

# Define the query
query = "What is the total amount of collected comprehensive trailer videos?"
generation_id = str(uuid4())

# Initialize the generation
generation_config = GenerationConfig(
    id=generation_id,
    name="generation",
    provider="openai",
    model=MODEL_NAME,
    messages=[{"role": "user", "content": query}]
)
generation = trace.generation(generation_config)

# Variable to store streamed chunks
response_chunks = []

try:
    print("RAG Query Response (streaming):")

    # Stream the response
    response_stream = query_engine.query(query)
    for chunk in response_stream.response_gen:
        # Collect streamed chunks
        chunk_text = str(chunk)
        response_chunks.append(chunk_text)

        # Print the streamed text chunk
        print(chunk_text, end="", flush=True)

    # Combine all chunks into the final response text
    final_response = "".join(response_chunks)

    # Log the response with Maxim
    generation.result({
        "id": generation_id,
        "object": "text_completion",
        "created": int(time()),
        "model": MODEL_NAME,
        "choices": [
            {
                "index": 0,
                "text": final_response,
                "logprobs": None,
                "finish_reason": "stop",
            },
        ],
        "usage": {
            "prompt_tokens": 0,  # Set to 0 for streaming
            "completion_tokens": 0,  # Set to 0 for streaming
            "total_tokens": 0,  # Set to 0 for streaming
        },
    })
    generation.end()

finally:
    # Clean up the logger session
    trace.end()
    logger.cleanup()
