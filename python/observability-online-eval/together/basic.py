import os
from uuid import uuid4
from time import time
from together import Together
from maxim.maxim import Logger, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig
from maxim.logger.components.generation import GenerationConfig, GenerationError

# Environment setup
MAXIM_API_KEY = os.getenv("MAXIM_API_KEY")
LOG_REPOSITORY_ID = os.getenv("LOG_REPOSITORY_ID")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
MODEL_NAME = "meta-llama/Meta-Llama-3.2-8B"

if not all([MAXIM_API_KEY, LOG_REPOSITORY_ID, TOGETHER_API_KEY]):
    raise EnvironmentError("API keys and Log Repository ID are not set in the environment variables.")

# Maxim logger setup
logger_config = LoggerConfig(id=LOG_REPOSITORY_ID)
logger = Logger(config=logger_config, api_key=MAXIM_API_KEY, base_url="https://app.getmaxim.ai")
session_id = str(uuid4())
session_config = SessionConfig(id=session_id)
session = logger.session(session_config)
trace_id = str(uuid4())
trace_config = TraceConfig(id=trace_id)
trace = session.trace(trace_config)

# Together AI client setup
client = Together(api_key=TOGETHER_API_KEY)

def get_together_response(messages):
    generation_id = str(uuid4())
    generation_config = GenerationConfig(
        id=generation_id,
        name="generation",
        provider="together",
        model=MODEL_NAME,
        messages=messages
    )
    generation = trace.generation(generation_config)
    
    try:
        # Get response from Together AI
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages
        )
        
        response_text = response.choices[0].message.content
        
        # Log the generation result
        generation.result({
            "id": generation_id,
            "object": "chat.completion",
            "created": int(time()),
            "model": MODEL_NAME,
            "choices": [
                {
                    "index": 0,
                    "text": response_text,
                    "logprobs": None,
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": getattr(response, 'usage', {}).get('prompt_tokens', 0),
                "completion_tokens": getattr(response, 'usage', {}).get('completion_tokens', 0),
                "total_tokens": getattr(response, 'usage', {}).get('total_tokens', 0),
            }
        })
        
        return response_text
        
    except Exception as e:
        generation.error(GenerationError(str(e)))
        raise
        
    finally:
        generation.end()

try:
    # Example query
    messages = [{"role": "user", "content": "What are some fun things to do in New York?"}]
    
    # Get and log response
    completion = get_together_response(messages)
    
    # Print result
    print("\nTogether AI Response:")
    print(completion)
    
finally:
    # Cleanup
    trace.end()
    logger.cleanup()
