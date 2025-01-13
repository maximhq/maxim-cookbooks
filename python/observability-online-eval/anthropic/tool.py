import os
import base64
import anthropic
import httpx
from maxim.maxim import Logger, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig
from maxim.logger.components.generation import GenerationConfig
from uuid import uuid4
from time import time

# Define the model name
MODEL_NAME = "claude-3-5-sonnet-20241022"

# Set up Maxim logger configuration
logger_config = LoggerConfig(id=LOG_REPOSITORY_ID)
logger = Logger(config=logger_config, api_key=MAXIM_API_KEY, base_url="https://app.getmaxim.ai")

# Set up a unique session and trace for each script run
session_id = str(uuid4())
session_config = SessionConfig(id=session_id)
session = logger.session(session_config)

trace_id = str(uuid4())
trace_config = TraceConfig(id=trace_id)
trace = session.trace(trace_config)

# Fetch the PDF and encode it in base64
pdf_url = "https://assets.anthropic.com/m/1cd9d098ac3e6467/original/Claude-3-Model-Card-October-Addendum.pdf"
pdf_data = base64.standard_b64encode(httpx.get(pdf_url).content).decode("utf-8")

# Create an instance of the Anthropic client
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Set up generation tracking
generation_id = str(uuid4())
user_query = "Which model has the highest human preference win rates across each use-case?"
generation_config = GenerationConfig(
    id=generation_id, 
    name="generation", 
    provider="anthropic", 
    model="claude-3-5-sonnet",
    messages=[{"role": "user", "content": user_query}]  # Just include the query text
)
generation = trace.generation(generation_config)

# Send the request to Claude with the PDF and user query
message = client.beta.messages.create(
    model="claude-3-5-sonnet-20241022",
    betas=["pdfs-2024-09-25"],
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data
                    }
                },
                {
                    "type": "text",
                    "text": user_query
                }
            ]
        }
    ],
)

# Extract the text content from the response
response_text = message.content[0].text if isinstance(message.content, list) else message.content.text

# Log the generation result
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
        "total_tokens": message.usage.input_tokens + message.usage.output_tokens,
    },
})
generation.end()

# Print Claude's response
print("Claude's Response:")
print(response_text)

# Clean up the logger session at the end
trace.end()
logger.cleanup()