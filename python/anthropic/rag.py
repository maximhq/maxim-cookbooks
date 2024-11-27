import os
import base64
import anthropic
import base64
import httpx
from maxim.maxim import Logger, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig
from uuid import uuid4

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

# Send the request to Claude with the PDF and a user query
message = client.beta.messages.create(
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
    ],
)

# Extract the text content from the BetaTextBlock (response object)
response_text = message.content[0].text if isinstance(message.content, list) else message.content.text

# Log the response with Maxim
trace.event(str(uuid4()), "Claude's Response", {"response_text": response_text})

# Print Claude's response
print("Claude's Response:")
print(response_text)

# Clean up the logger session at the end
trace.end()
logger.cleanup()