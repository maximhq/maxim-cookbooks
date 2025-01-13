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

# Set up Maxim logger configuration
logger_config = LoggerConfig(id=LOG_REPOSITORY_ID)
logger = Logger(config=logger_config, api_key=MAXIM_API_KEY, base_url="https://app.getmaxim.ai")

# Set up a unique session for logging
session_id = str(uuid4())
session_config = SessionConfig(id=session_id)
session = logger.session(session_config)

# Initialize the LangChain client for Claude
MODEL_NAME = "claude-3-sonnet-20240229"
model = ChatAnthropic(model=MODEL_NAME, api_key=ANTHROPIC_API_KEY)

# Initialize the DuckDuckGo search tool
search = DuckDuckGoSearchRun()

def get_latest_info(query):
    search_results = search.invoke(query)
    return search_results

def stream_Claude_response(question):
    try:
        # Create a unique trace
        trace_id = str(uuid4())
        trace_config = TraceConfig(id=trace_id)
        trace = session.trace(trace_config)

        # Perform DuckDuckGo search
        search_results = get_latest_info(question)

        # Set up system message and combined prompt
        system_message = "You are a helpful assistant."
        combined_prompt = f"Here's the latest info: {search_results}. Now, {question}"

        # Create generation configuration
        generation_id = str(uuid4())
        generation_config = GenerationConfig(
            id=generation_id,
            name="generation",
            provider="anthropic",
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": combined_prompt}
            ]
        )
        generation = trace.generation(generation_config)

        # Make the API call to Claude
        messages = [
            ("system", system_message),
            ("human", combined_prompt)
        ]
        response = model.invoke(messages)
        response_text = response.content

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
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
        })

        return response_text

    except Exception as e:
        error_message = f"Error occurred: {str(e)}"
        print(error_message)
        if 'generation' in locals():
            generation.error(GenerationError(error_message))
        raise
    finally:
        if 'generation' in locals():
            generation.end()
        if 'trace' in locals():
            trace.end()

def main():
    try:
        # Define the question for the model
        question = "What is Obama's first name?"

        # Get the completion from Claude and log the response
        completion = stream_Claude_response(question)

        # Output the final full response
        print("Final Response:", completion)

    except Exception as e:
        print(f"Main execution error: {str(e)}")

    finally:
        # Cleanup the logger
        logger.cleanup()

if __name__ == "__main__":
    main()
