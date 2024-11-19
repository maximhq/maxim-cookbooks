import os
from uuid import uuid4
from langchain_anthropic import ChatAnthropic
from maxim.maxim import Logger, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig

# Retrieve API keys from environment variables
MAXIM_API_KEY = os.getenv("MAXIM_API_KEY")
LOG_REPOSITORY_ID = "cm34ngxje000589znzbrupw12" # ENTER YOUR OWN LOG REPOSITORY
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not MAXIM_API_KEY or not LOG_REPOSITORY_ID or not ANTHROPIC_API_KEY:
    raise EnvironmentError("API keys are not set in the environment variables.")

# Set up Maxim logger configuration
logger_config = LoggerConfig(id=LOG_REPOSITORY_ID)
logger = Logger(config=logger_config, api_key=MAXIM_API_KEY, base_url="https://app.getmaxim.ai")

# Set up a unique session for logging
session_id = str(uuid4())
session_config = SessionConfig(id=session_id)
session = logger.session(session_config)

# Initialize the LangChain client for Claude (ChatAnthropic)
MODEL_NAME = "claude-3-sonnet-20240229"  # Example of a Claude model version
llm = ChatAnthropic(model=MODEL_NAME, api_key=ANTHROPIC_API_KEY)

# Prepare the question to send to the model
question = "When did Mauritius gain independence?"

# Prepare the messages for the model
messages = [
    ("system", "You are a helpful assistant."),
    ("human", question)
]

# Function to get the response from Claude and log it to Maxim
def get_Claude_response(messages):
    # Create a unique trace ID and start the trace
    trace_id = str(uuid4())
    trace_config = TraceConfig(id=trace_id)
    trace = session.trace(trace_config)
    
    # Make the API call to Claude using LangChain's `ChatAnthropic`
    response = llm.invoke(messages)
    
    # Extract the response text from the 'content' field
    response_text = response.content  # Use the 'content' field directly
    
    # Log the response to Maxim
    trace.event(str(uuid4()), "Claude's Response", {"response_text": response_text})
    trace.end()  # End the trace after logging the response
    
    return response_text

# Get the completion from Claude and log the response
completion = get_Claude_response(messages)

# Print the response
print(completion)
