import os
import requests
from uuid import uuid4
from time import time
from maxim.maxim import Logger, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig
from maxim.logger.components.generation import GenerationConfig, GenerationError

# Retrieve API keys and Log Repository ID from environment variables
MAXIM_API_KEY = os.getenv("MAXIM_API_KEY")
LOG_REPOSITORY_ID = os.getenv("LOG_REPOSITORY_ID")
XAI_API_KEY = os.getenv("XAI_API_KEY")

if not MAXIM_API_KEY or not LOG_REPOSITORY_ID or not XAI_API_KEY:
    raise EnvironmentError("API keys and Log Repository ID are not set in the environment variables.")

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

user_input = "What is the answer to life and universe?"
data = {
    "messages": [
        {"role": "system", "content": "You are Grok, a chatbot inspired by the Hitchhikers Guide to the Galaxy."},
        {"role": "user", "content": user_input}
    ],
    "model": "grok-beta",
    "stream": False,
    "temperature": 0
}

# Set up generation configuration
generation_id = str(uuid4())
generation_config = GenerationConfig(
    id=generation_id,
    name="generation",
    provider="xai",
    model="grok-beta",
    messages=[{"role": "user", "content": user_input}]
)
generation = trace.generation(generation_config)

try:
    # Make the API call to Grok
    response = requests.post(grok_url, headers=headers, json=data)
    
    if response.status_code == 200:
        response_json = response.json()
        response_text = response_json['choices'][0]['message']['content']
        
        # Log the response with Maxim
        generation.result({
            "id": generation_id,
            "object": "text_completion",
            "created": int(time()),
            "model": generation_config.model,
            "choices": [
                {
                    "index": 0,
                    "text": response_text,
                    "logprobs": None,
                    "finish_reason": "stop",
                },
            ],
            "usage": {
                "prompt_tokens": response_json.get('usage', {}).get('prompt_tokens', 0),
                "completion_tokens": response_json.get('usage', {}).get('completion_tokens', 0),
                "total_tokens": response_json.get('usage', {}).get('total_tokens', 0),
            },
        })
        
        # Print the response
        print(response_text)

except Exception as e:
    generation.error(GenerationError(str(e)))
    print(f"Error occurred: {str(e)}")

finally:
    # End the generation logging
    generation.end()
    # Clean up the trace and logger session
    trace.end()
    logger.cleanup()

