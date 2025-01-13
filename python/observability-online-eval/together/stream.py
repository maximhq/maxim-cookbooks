import os
from time import time
from uuid import uuid4
from together import Together
from maxim.maxim import Logger, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig
from maxim.logger.components.generation import GenerationConfig, GenerationError

# Environment setup
MAXIM_API_KEY = os.getenv("MAXIM_API_KEY")
LOG_REPOSITORY_ID = os.getenv("LOG_REPOSITORY_ID")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
MODEL_NAME = "meta-llama/Meta-Llama-3.2-8B"

if not all([MAXIM_API_KEY, LOG_REPOSITORY_ID, TOGETHER_API_KEY]):
    raise EnvironmentError("API keys and Log Repository ID are not set in the environment variables.")

# Maxim logger setup
logger_config = LoggerConfig(id=LOG_REPOSITORY_ID)
logger = Logger(config=logger_config, api_key=MAXIM_API_KEY, base_url="https://app.getmaxim.ai")
session_id = str(uuid4())
session_config = SessionConfig(id=session_id)
session = logger.session(session_config)
trace_id = str(uuid4())
trace_config = TraceConfig(id=trace_id)
trace = session.trace(trace_config)

# Together AI client setup
client = Together(api_key=TOGETHER_API_KEY)

# Define the message
messages = [{"role": "user", "content": "What are some fun things to do in New York?"}]
generation_id = str(uuid4())

# Initialize the generation
generation_config = GenerationConfig(
    id=generation_id,
    name="generation",
    provider="together",
    model=MODEL_NAME,
    messages=messages
)
generation = trace.generation(generation_config)

# Variable to store streamed chunks
response_chunks = []

try:
    print("Together AI Response (streaming):")
    
    # Stream the response
    stream = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        stream=True
    )
    
    # Process each chunk
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            chunk_text = chunk.choices[0].delta.content
            response_chunks.append(chunk_text)
            print(chunk_text, end="", flush=True)
    
    # Combine all chunks into final response
    final_response = "".join(response_chunks)
    
    # Log the generation result
    generation.result({
        "id": generation_id,
        "object": "chat.completion",
        "created": int(time()),
        "model": MODEL_NAME,
        "choices": [
            {
                "index": 0,
                "text": final_response,
                "logprobs": None,
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 0,  # Set to 0 for streaming
            "completion_tokens": 0,  # Set to 0 for streaming
            "total_tokens": 0,  # Set to 0 for streaming
        }
    })
    generation.end()

finally:
    # Cleanup
    trace.end()
    logger.cleanup()
