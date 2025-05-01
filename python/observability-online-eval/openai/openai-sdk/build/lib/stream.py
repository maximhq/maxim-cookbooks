import os
from time import time
from uuid import uuid4

import openai
from maxim.logger.components.generation import GenerationConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig
from maxim.maxim import Logger, LoggerConfig

# Retrieve API keys from environment variables
MAXIM_API_KEY = os.getenv("MAXIM_API_KEY")
LOG_REPOSITORY_ID = os.getenv("MAXIM_LOG_REPO_ID")
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

# Initialize generation configuration
generation_id = str(uuid4())
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Write a haiku about recursion in programming."},
]

generation_config = GenerationConfig(
    id=generation_id,
    name="generation",
    provider="openai",
    model=MODEL_NAME,
    messages=messages
)
generation = trace.generation(generation_config)

try:
    # Create a chat completion request
    response = openai.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
    )
    
    # Extract response text and usage
    response_text = response.choices[0].message.content
    usage = response.usage

    # Log the generation result with tokens
    generation.result({
        "id": generation_id,
        "object": "chat.completion",
        "created": int(time()),
        "model": MODEL_NAME,
        "choices": [
            {
                "index": 0,
                "text": response_text,
                "logprobs": None,
                "finish_reason": response.choices[0].finish_reason,
            },
        ],
        "usage": {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
        },
    })

    # Print the response
    print("OpenAI's Response:")
    print(response_text)
    print("\nToken Usage:")
    print(f"Prompt tokens: {usage.prompt_tokens}")
    print(f"Completion tokens: {usage.completion_tokens}")
    print(f"Total tokens: {usage.total_tokens}")

    generation.end()

finally:
    # Clean up the logger session
    trace.end()
    logger.cleanup()
