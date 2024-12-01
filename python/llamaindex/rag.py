import os
from time import time
from dotenv import dotenv_values
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, ServiceContext
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.llms.openai import OpenAI
from maxim.maxim import Logger, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig
from maxim.logger.components.generation import GenerationConfig, GenerationError
from uuid import uuid4

# Environment setup
MAXIM_API_KEY = os.getenv("MAXIM_API_KEY")
LOG_REPOSITORY_ID = os.getenv("LOG_REPOSITORY_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-4o-mini"

# Maxim logger setup
logger_config = LoggerConfig(id=LOG_REPOSITORY_ID)
logger = Logger(config=logger_config, api_key=MAXIM_API_KEY, base_url="https://app.getmaxim.ai")

session_id = str(uuid4())
session_config = SessionConfig(id=session_id)
session = logger.session(session_config)

trace_id = str(uuid4())
trace_config = TraceConfig(id=trace_id)
trace = session.trace(trace_config)

# Initialize components
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
llm = OpenAI(model=MODEL_NAME)
documents = SimpleDirectoryReader("../maxim-cookbooks/").load_data()

# Setup RAG components
node_parser = SimpleNodeParser.from_defaults(chunk_size=512)
nodes = node_parser.get_nodes_from_documents(documents=documents)
vector_index = VectorStoreIndex(nodes)
query_engine = vector_index.as_query_engine(similarity_top_k=2)

try:
    # Set up generation logging
    generation_id = str(uuid4())
    query = "What is the total amount of collected comprehensive trailer videos?"
    
    generation_config = GenerationConfig(
        id=generation_id,
        name="generation",
        provider="openai",
        model=MODEL_NAME,
        messages=[{"role": "user", "content": query}]
    )
    generation = trace.generation(generation_config)
    
    try:
        # Get response from query engine
        response_vector = query_engine.query(query)
        response_text = str(response_vector.response)
        
        # Log retrieved nodes/context
        trace.event(str(uuid4()), "Retrieved Contexts", {
            "source_nodes": [str(node) for node in response_vector.source_nodes]
        })
        
        # Log the generation result
        generation.result({
            "id": generation_id,
            "object": "text_completion",
            "created": int(time()),
            "model": MODEL_NAME,
            "choices": [
                {
                    "index": 0,
                    "text": response_text,
                    "logprobs": None,
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
        })
        
        # Print the response
        print("RAG Query Response:")
        print(response_text)
        
    except Exception as e:
        generation.error(GenerationError(str(e)))
        raise
        
    finally:
        generation.end()

finally:
    # Cleanup
    trace.end()
    logger.cleanup()
