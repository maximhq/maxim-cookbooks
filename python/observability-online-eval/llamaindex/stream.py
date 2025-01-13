import os
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

# Define the prompt
prompt = "Write a one liner about programming."
generation_id = str(uuid4())

# Initialize the generation
generation_config = GenerationConfig(
    id=generation_id,
    name="generation",
    provider="openai",
    model=MODEL_NAME,
    messages=[{"role": "user", "content": prompt}]
)
generation = trace.generation(generation_config)

# Variable to store streamed chunks
response_chunks = []

try:
    print("LlamaIndex's Response (streaming):")
    response_stream = llm.stream_complete(prompt)

    # Collect and print streamed chunks
    for chunk in response_stream:
        chunk_text = chunk.delta
        response_chunks.append(chunk_text)
        print(chunk_text, end="", flush=True)

    # Combine all chunks into final response
    final_response = "".join(response_chunks)

    # Log the complete response with Maxim
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
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    })
    generation.end()

finally:
    # Clean up the logger session
    trace.end()
    logger.cleanup()