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

# Call OpenAI API and log the response
try:
    # Create a chat completion request
    response = openai.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Write a haiku about recursion in programming."},
        ],
    )
    # Correctly extract the plain text from the response
    response_text = response.choices[0].message.content

    # Log the response with Maxim
    trace.event(str(uuid4()), "OpenAI's Response", {"response_text": response_text})

    # Print the response
    print("OpenAI's Response:")
    print(response_text)

finally:
    # Clean up the logger session
    trace.end()
    logger.cleanup()
