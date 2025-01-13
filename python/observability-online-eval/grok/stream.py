import os
import requests
from maxim.maxim import Logger, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig
from maxim.logger.components.generation import GenerationConfig
from uuid import uuid4
from time import time

# Retrieve API keys from environment variables
MAXIM_API_KEY = os.getenv("MAXIM_API_KEY")
LOG_REPOSITORY_ID = os.getenv("LOG_REPOSITORY_ID")
XAI_API_KEY = os.getenv("XAI_API_KEY")

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

# Define the Grok API URL and headers
grok_url = "https://api.x.ai/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {XAI_API_KEY}",
}

# Define the user input
user_input = "What is the answer to life and universe?"
generation_id = str(uuid4())

# Initialize the generation
generation_config = GenerationConfig(
    id=generation_id,
    name="generation",
    provider="xai",
    model="grok-beta",
    messages=[{"role": "user", "content": user_input}]
)
generation = trace.generation(generation_config)

# Prepare the request data
data = {
    "messages": [
        {"role": "system", "content": "You are Grok, a chatbot inspired by the Hitchhikers Guide to the Galaxy."},
        {"role": "user", "content": user_input}
    ],
    "model": "grok-beta",
    "stream": True,
    "temperature": 0
}

# Variable to store streamed chunks
response_chunks = []

try:
    print("Grok's Response (streaming):")
    
    # Make the streaming request
    response = requests.post(grok_url, headers=headers, json=data, stream=True)
    
    if response.status_code == 200:
        for line in response.iter_lines():
            if line:
                # Parse the SSE data
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    json_str = line[6:]  # Remove 'data: ' prefix
                    if json_str != '[DONE]':
                        chunk_data = json.loads(json_str)
                        if chunk_data['choices'][0].get('delta', {}).get('content'):
                            chunk_text = chunk_data['choices'][0]['delta']['content']
                            response_chunks.append(chunk_text)
                            print(chunk_text, end="", flush=True)

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

