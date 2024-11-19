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
    "stream": True,
    "temperature": 0
}

# Function to stream the response from Grok and log it
def stream_grok_response(data):
    # Create a unique trace ID and start the trace
    trace_id = str(uuid4())
    trace_config = TraceConfig(id=trace_id)
    trace = session.trace(trace_config)
    
    # Start streaming from the Grok API
    with requests.post(grok_url, headers=headers, json=data, stream=True) as response:
        if response.status_code == 200:
            # Process each chunk as it arrives
            for chunk in response.iter_lines(decode_unicode=True):
                if chunk:
                    chunk_data = chunk.strip()
                    trace.event(str(uuid4()), "Grok Streamed Chunk", {"chunk_content": chunk_data})
                    print(chunk_data)  # Optionally print the chunk content
                    
            # End the trace after streaming is complete
            trace.end()
        else:
            # If the request fails, log the error
            trace.event(str(uuid4()), "Error", {"error": response.text})
            trace.end()
            print(f"Error: {response.status_code}")

# Stream the response and log it
stream_grok_response(data)
