import os
import requests
from uuid import uuid4
from maxim.maxim import Logger, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig

# Retrieve API keys and Log Repository ID from environment variables
MAXIM_API_KEY = os.getenv("MAXIM_API_KEY")
LOG_REPOSITORY_ID = os.getenv("LOG_REPOSITORY_ID")  # Your Log Repository ID
XAI_API_KEY = os.getenv("XAI_API_KEY")  # Your Grok API Key

if not MAXIM_API_KEY or not LOG_REPOSITORY_ID or not XAI_API_KEY:
    raise EnvironmentError("API keys and Log Repository ID are not set in the environment variables.")

# Set up Maxim logger configuration
logger_config = LoggerConfig(id=LOG_REPOSITORY_ID)
logger = Logger(config=logger_config, api_key=MAXIM_API_KEY, base_url="https://app.getmaxim.ai")

# Set up a unique session for logging
session_id = str(uuid4())
session_config = SessionConfig(id=session_id)
session = logger.session(session_config)

# Define the Grok API URL and the message payload
grok_url = "https://api.x.ai/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {XAI_API_KEY}",
}

data = {
    "messages": [
        {"role": "system", "content": "You are Grok, a chatbot inspired by the Hitchhikers Guide to the Galaxy."},
        {"role": "user", "content": "What is the answer to life and universe?"}
    ],
    "model": "grok-beta",
    "stream": False,
    "temperature": 0
}

# Function to make the request and log the response
def get_grok_response(data):
    # Create a unique trace ID and start the trace
    trace_id = str(uuid4())
    trace_config = TraceConfig(id=trace_id)
    trace = session.trace(trace_config)
    
    # Make the API call to Grok
    response = requests.post(grok_url, headers=headers, json=data)
    
    if response.status_code == 200:
        # Extract the response text (assuming it's in the "choices" key)
        response_text = response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
        
        # Log the response to Maxim
        trace.event(str(uuid4()), "Grok Response", {"response_text": response_text})
        trace.end()  # End the trace after logging the response

        return response_text
    else:
        # If the request fails, log the error
        trace.event(str(uuid4()), "Error", {"error": response.text})
        trace.end()
        return f"Error: {response.status_code}"

# Get the completion from Grok and log the response
completion = get_grok_response(data)

# Print the response
print(completion)
