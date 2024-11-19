import os
import base64
import anthropic
import httpx
from maxim.maxim import Logger, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig
from uuid import uuid4

# Retrieve API keys from environment variables
MAXIM_API_KEY = os.getenv("MAXIM_API_KEY")
LOG_REPOSITORY_ID = os.getenv("LOG_REPOSITORY_ID")  # Ensure to set this in the environment
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

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
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)  # Replace with your actual key

# Set up the streaming request to Claude
try:
    print("Claude's Response (streaming):")

    # Stream the response from Claude
    with client.messages.stream(
        model="claude-3-5-sonnet-20241022",
        betas=["pdfs-2024-09-25"],  # Specify the beta feature for PDFs
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
                            "data": pdf_data  # Attach the base64-encoded PDF
                        }
                    },
                    {
                        "type": "text",
                        "text": "Which model has the highest human preference win rates across each use-case?"  # User prompt
                    }
                ]
            }
        ]
    ) as stream:
        for text in stream.text_stream:
            # Print the streamed text chunk
            print(text, end="", flush=True)

            # Log each streamed chunk with a unique event ID
            trace.event(str(uuid4()), "Claude's Stream Chunk", {"chunk": text})

finally:
    # Clean up the logger session at the end
    trace.end()
    logger.cleanup()
