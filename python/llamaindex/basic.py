import os
from llama_index.llms.openai import OpenAI
from maxim.maxim import Logger, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig
from uuid import uuid4

# Retrieve API keys from environment variables
MAXIM_API_KEY = os.getenv("MAXIM_API_KEY")
LOG_REPOSITORY_ID = os.getenv("LOG_REPOSITORY_ID")
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

# Initialize the LlamaIndex OpenAI client
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
llm = OpenAI(model=MODEL_NAME)

try:
    # Define the prompt and interact with the model using LlamaIndex
    prompt = "Write a haiku about recursion in programming."
    
    # Set up generation logging
    generation_id = str(uuid4())
    generation_config = GenerationConfig(
        id=generation_id,
        name="generation",
        provider="openai",
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}]
    )
    generation = trace.generation(generation_config)
    
    response = llm.complete(prompt)  # Directly get the text response
    response_text = str(response)

    # Log the generation result
    generation.result({
        "id": generation_id,
        "object": "text_completion",
        "created": int(time()),
        "model": MODEL_NAME,
        "choices": [
            {
                "index": 0,
                "text": response_text,
                "logprobs": None,
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    })

    # Log the response with Maxim
    trace.event(str(uuid4()), "LlamaIndex Response", {"response_text": response_text})

    # Print the response
    print("LlamaIndex's Response:")
    print(response_text)

finally:
    # Clean up the logger session
    trace.end()
    logger.cleanup()