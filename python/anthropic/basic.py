import os
from anthropic import Anthropic  # Import required constants
from maxim.maxim import Logger, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig
from uuid import uuid4

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

# Call Claude and log the response
try:
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": "What was the capital of France in 1800s?"}]
    )
    # Extract the plain text from the response
    if isinstance(message.content, list):
        response_text = " ".join(block.text for block in message.content)
    else:
        response_text = message.content.text

    # Log the response with Maxim
    trace.event(str(uuid4()), "Claude's Response", {"response_text": response_text})

    # Print the response
    print("Claude's Response:")
    print(response_text)

finally:
    # Clean up the logger session
    trace.end()
    logger.cleanup()