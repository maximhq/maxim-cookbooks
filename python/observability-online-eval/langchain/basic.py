import os
from uuid import uuid4
from langchain_anthropic import ChatAnthropic
from maxim.maxim import Logger, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig


# Retrieve API keys from environment variables
MAXIM_API_KEY = os.getenv("MAXIM_API_KEY")
LOG_REPOSITORY_ID = os.getenv("LOG_REPOSITORY_ID")  # ENTER YOUR OWN LOG REPOSITORY
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Set up Maxim logger configuration
logger_config = LoggerConfig(id=LOG_REPOSITORY_ID)
logger = Logger(
    config=logger_config, api_key=MAXIM_API_KEY, base_url="https://app.getmaxim.ai"
)

# Set up a unique session and trace for the application
session_id = str(uuid4())
session_config = SessionConfig(id=session_id)
session = logger.session(session_config)

trace_id = str(uuid4())
trace_config = TraceConfig(id=trace_id)
trace = session.trace(trace_config)

# Initialize the LangChain client for Claude
MODEL_NAME = "claude-3-sonnet-20240229"
llm = ChatAnthropic(model=MODEL_NAME, api_key=ANTHROPIC_API_KEY)

# Prepare the question and messages
user_input = "When did Mauritius gain independence?"
system_message = "You are a helpful assistant."

# Set up generation configuration
generation_id = str(uuid4())
generation_config = GenerationConfig(
    id=generation_id,
    name="generation",
    provider="anthropic",
    model=MODEL_NAME,
    messages=[
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_input},
    ],
)
generation = trace.generation(generation_config)

try:
    # Make the API call to Claude using LangChain
    messages = [("system", system_message), ("human", user_input)]
    response = llm.invoke(messages)
    response_text = response.content

    # Log the response with Maxim
    generation.result(
        {
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
                "prompt_tokens": 0,  # LangChain might not provide token counts
                "completion_tokens": 0,
                "total_tokens": 0,
            },
        }
    )

    # Print the response
    print(response_text)

except Exception as e:
    error_message = f"Error occurred: {str(e)}"
    print(error_message)
    generation.error(GenerationError(error_message))

finally:
    # End the generation and clean up
    generation.end()
    trace.end()
    logger.cleanup()
