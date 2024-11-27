import os
import openai  # Import OpenAI library
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

# Set up the OpenAI client
openai.api_key = OPENAI_API_KEY

# Set up the OpenAI client
openai.api_key = OPENAI_API_KEY

# Start streaming the response from OpenAI and log each chunk
try:
    stream = openai.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": "Write a haiku about recursion in programming."}],
        stream=True,
    )

    print("OpenAI Streaming Response:")

    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            chunk_text = chunk.choices[0].delta.content
            print(chunk_text, end="", flush=True)

            # Log each chunk with Maxim using a unique event ID
            trace.event(str(uuid4()), "OpenAI Stream Chunk", {"chunk": chunk_text})

finally:
    # Clean up the logger session
    trace.end()
    logger.cleanup()