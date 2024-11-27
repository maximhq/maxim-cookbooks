import os
from uuid import uuid4
from langchain_community.tools import DuckDuckGoSearchRun
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

# Initialize the DuckDuckGo search tool
search = DuckDuckGoSearchRun()

# Function to search and get the latest info
def get_latest_info(query):
    search_results = search.invoke(query)
    return search_results

# Function to stream the response from Claude and log it to Maxim
def stream_Claude_response(question):
    # Perform DuckDuckGo search first
    search_results = get_latest_info(question)

    # Prepare the messages for Claude, including the search results
    messages = [
        ("system", "You are a helpful assistant."),
        ("human", f"Here's the latest info: {search_results}. Now, {question}")
    ]
    
    # Create a unique trace ID and start the trace
    trace_id = str(uuid4())
    trace_config = TraceConfig(id=trace_id)
    trace = session.trace(trace_config)
    
    # Make the API call to Claude using LangChain's `ChatAnthropic`
    response = model.invoke(messages)
    
    # Extract the response text from the 'content' field
    response_text = response.content  # Use the 'content' field directly
    
    # Log the response to Maxim
    trace.event(str(uuid4()), "Claude's Response", {"response_text": response_text})
    trace.end()  # End the trace after logging the response
    
    return response_text

# Define the question for the model
question = "What is Obama's first name?"

# Get the completion from Claude and log the response
completion = stream_Claude_response(question)

# Output the final full response
print(completion)
