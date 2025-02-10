import os
from uuid import uuid4
from langchain_anthropic import ChatAnthropic
from maxim.maxim import Logger, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig

# Retrieve API keys and Log Repository ID from environment variables
MAXIM_API_KEY = os.getenv("MAXIM_API_KEY")
LOG_REPOSITORY_ID = os.getenv("LOG_REPOSITORY_ID")  # Your Log Repository ID
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not MAXIM_API_KEY or not LOG_REPOSITORY_ID or not ANTHROPIC_API_KEY:
    raise EnvironmentError("API keys and Log Repository ID are not set in the environment variables.")

# Set up Maxim logger configuration
logger_config = LoggerConfig(id=LOG_REPOSITORY_ID)
logger = Logger(config=logger_config, api_key=MAXIM_API_KEY, base_url="https://app.getmaxim.ai")

# Set up a unique session for logging
session_id = str(uuid4())
session_config = SessionConfig(id=session_id)
session = logger.session(session_config)

# Initialize the LangChain client for Claude (ChatAnthropic)
model = ChatAnthropic(model="claude-3-5-sonnet-20240620", api_key=ANTHROPIC_API_KEY)

# Define the question for the model
question = "What color is the sky?"

# Function to stream the response from Claude and log it to Maxim
def stream_Claude_response(question):
    # Create a unique trace ID and start the trace
    trace_id = str(uuid4())
    trace_config = TraceConfig(id=trace_id)
    trace = session.trace(trace_config)
    
    # Start streaming from the model
    chunks = []
    for chunk in model.stream(question):
        chunks.append(chunk)
        
        # Log the chunk content to Maxim
        trace.event(str(uuid4()), "Claude Streamed Response", {"chunk_content": chunk.content})
    
    # End the trace after streaming is complete
    trace.end()

    # Combine all chunks to form the complete response
    full_response = ''.join([chunk.content for chunk in chunks])
    return full_response

# Stream the response and log it
completion = stream_Claude_response(question)

# Output the final full response
print(completion)
