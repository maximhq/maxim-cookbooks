import os
from anthropic import Anthropic  # Import required constants
from maxim.maxim import Logger, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig
from maxim.logger.components.generation import GenerationConfig
from uuid import uuid4
from time import time

# Retrieve API keys from environment variables
MAXIM_API_KEY = os.getenv("MAXIM_API_KEY")
LOG_REPOSITORY_ID = os.getenv("LOG_REPOSITORY_ID")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Define the model name
MODEL_NAME = "claude-3-5-sonnet-20241022"

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

# Set up the Anthropic client
client = Anthropic(api_key=ANTHROPIC_API_KEY)

# Define the user input
user_input = "What was the capital of France in 1800s?"
generation_id = str(uuid4())

# Initialize the generation
generation_config = GenerationConfig(
    id=generation_id,
    name="generation",
    provider="anthropic",
    model=MODEL_NAME,
    messages=[{"role": "user", "content": user_input}]
)
generation = trace.generation(generation_config)

# Variable to store streamed chunks
response_chunks = []

try:
    print("Claude's Response (streaming):")

    # Stream the response from Claude
    with client.messages.stream(
        max_tokens=1024,
        messages=[{"role": "user", "content": user_input}],
        model=MODEL_NAME,
    ) as stream:
        for text_chunk in stream.text_stream:
            # Collect streamed chunks
            response_chunks.append(text_chunk)

            # Print the streamed text chunk
            print(text_chunk, end="", flush=True)

    # Combine all chunks into the final response text
    final_response = "".join(response_chunks)

    # Log the response with Maxim
    generation.result({
        "id": generation_id,
        "object": "text_completion",
        "created": int(time()),
        "model": generation_config.model,
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
