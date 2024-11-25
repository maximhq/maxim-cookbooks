import os
from uuid import uuid4
from together import Together
from maxim.maxim import Logger, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig

# Retrieve API keys and Log Repository ID from environment variables
MAXIM_API_KEY = os.getenv("MAXIM_API_KEY")
LOG_REPOSITORY_ID = os.getenv("LOG_REPOSITORY_ID")  # Your Log Repository ID
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")  # Your Together API Key

if not MAXIM_API_KEY or not LOG_REPOSITORY_ID or not TOGETHER_API_KEY:
    raise EnvironmentError("API keys and Log Repository ID are not set in the environment variables.")

# Set up Maxim logger configuration
logger_config = LoggerConfig(id=LOG_REPOSITORY_ID)
logger = Logger(config=logger_config, api_key=MAXIM_API_KEY, base_url="https://app.getmaxim.ai")

# Set up a unique session for logging
session_id = str(uuid4())
session_config = SessionConfig(id=session_id)
session = logger.session(session_config)

# Initialize the Together AI client
client = Together(api_key=TOGETHER_API_KEY)

# Define the message for the model
messages = [{"role": "user", "content": "What are some fun things to do in New York?"}]

# Function to send request to Together AI and log the response
def get_together_response(messages):
    # Create a unique trace ID and start the trace
    trace_id = str(uuid4())
    trace_config = TraceConfig(id=trace_id)
    trace = session.trace(trace_config)

    # Send the request to the Together API
    response = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3-8B-Instruct-Turbo",
        messages=messages
    )

    # Extract the response content
    response_text = response.choices[0].message.content

    # Log the response to Maxim
    trace.event(str(uuid4()), "Together AI Response", {"response_text": response_text})
    trace.end()  # End the trace after logging the response

    return response_text

# Get the response from Together AI and log the output
completion = get_together_response(messages)

# Output the final response
print(completion)
