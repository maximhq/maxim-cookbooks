import os
from anthropic import Anthropic  # Import required constants
from maxim.maxim import Logger, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig
from uuid import uuid4
from maxim.logger.components.generation import GenerationConfig, GenerationError
from time import time 

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

user_input ="What was the capital of France in 1800s?"
generation_id =str(uuid4())
generation_config = GenerationConfig(id=generation_id, name="generation", provider="anthropic", model="claude-3-5-sonnet", messages=[{"role":"user", "content": user_input}])
generation= trace.generation(generation_config)

# Call Claude and log the response
try:
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": user_input}]
    )
    # Extract the plain text from the response
    if isinstance(message.content, list):
        response_text = " ".join(block.text for block in message.content)
    else:
        response_text = message.content.text

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
                    "prompt_tokens": message.usage.input_tokens,
                    "completion_tokens": message.usage.output_tokens,
                    "total_tokens": message.usage.input_tokens+message.usage.output_tokens,
                },
            })
    generation.end()
    # Print the response
    print(message)
    print(response_text)

finally:
    # Clean up the logger session
    trace.end()
    logger.cleanup()