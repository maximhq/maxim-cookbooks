import os
from anthropic import Anthropic # Import required constants
from maxim.maxim import Logger, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig
from uuid import uuid4

# Retrieve API keys from environment variables
MAXIM_API_KEY = os.getenv("MAXIM_API_KEY")
LOG_REPOSITORY_ID = os.getenv("LOG_REPOSITORY_ID")  # Ensure to set this in the environment
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

# Call Claude and stream the response
try:
    print("Claude's Response (streaming):")

    # Stream the response from Claude
    with client.messages.stream(
        max_tokens=1024,
        messages=[{"role": "user", "content": "What was the capital of France in 1800s?"}],
        model="claude-3-5-sonnet-20241022",
    ) as stream:
        for text in stream.text_stream:
            # Print the streamed text chunk
            print(text, end="", flush=True)

            # Log each streamed chunk with a unique event ID
            trace.event(str(uuid4()), "Claude's Stream Chunk", {"chunk": text})

finally:
    # Clean up the logger session
    trace.end()
    logger.cleanup()