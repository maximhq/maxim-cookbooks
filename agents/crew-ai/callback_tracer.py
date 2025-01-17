from uuid import uuid4
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult
from maxim.expiringKeyValueStore import ExpiringKeyValueStore
from maxim.logger.components.generation import GenerationConfig, GenerationError
from maxim.logger.components.retrieval import RetrievalConfig
from maxim.logger.components.trace import Trace, TraceConfig
from maxim.logger.components.span import Span, SpanConfig
from maxim.logger.logger import Logger
from time import sleep, time
import tiktoken
import random
from typing import Dict,List, Any,Union


# class BaseCallbackHandler:
class CallbackTracer(BaseCallbackHandler):
    """Base callback handler that can be used to handle callbacks from langchain."""
    def __init__(self, logger: Logger, trace: Trace, agent: str):
        self.logger = logger
        self.trace = trace
        self.agent = agent
        # self.span = self.trace.span(SpanConfig(id=str(uuid4()), name=f"Agent {self.agent}"))
        self.span = None
        self.span2 = None
        self.messages = []
        self.generationConfig = None
        self.generation = None
        self.tools = ["Web Scraper", "Web Search"]

        # self.generationConfig = GenerationConfig(id=str(uuid4()), name="generation", provider="openai", model="gpt-3.5-turbo-16k", model_parameters={"temperature": 3}, messages=[{"role": "user", "content": "Hello, how can I help you today?"}])

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> Any:
        """Run when LLM starts running."""

    def on_chat_model_start(
        self, serialized: Dict[str, Any], messages: List[List[BaseMessage]], **kwargs: Any
    ) -> Any:  
        """Run when Chat Model starts running."""
        if (self.span is None):
            self.span = self.trace.span(SpanConfig(id=str(uuid4()), name=f"Agent {self.agent}"))
            
        self.span.event(str(uuid4()), f"Agent Start: {self.agent}", {})
        sleep(0.2)
        # self.messages.append({"role": "user", "content"})
        if self.span2 is None:
            self.span2 = self.span.span(SpanConfig(id=str(uuid4()), name=f"Tool Call"))
            random_tool = random.choice(self.tools)
            self.span2.event(str(uuid4()), f"Tool called: {random_tool}", {})
            sleep(0.2)
        for message_list in messages:
            for message in message_list:
                self.messages.append({"role": "user", "content": message.content})
                
        self.generationConfig = GenerationConfig(id=str(uuid4()), name="generation", provider="openai", model="gpt-3.5-turbo-16k", model_parameters={"temperature": 3}, messages=self.messages)
        self.generation = self.span.generation(self.generationConfig)

        print(f"[DEBUG] Messages: {messages}")

    def on_llm_new_token(self, token: str, **kwargs: Any) -> Any:
        """Run on new LLM token. Only available when streaming is enabled."""

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        """Run when LLM ends running."""
        
        enc = tiktoken.get_encoding("o200k_base")
        llm_output = response.generations[0][0].text
        print("on_llm_end")
        messages = self.generationConfig.messages
        messages_string = ''.join(["role: " + entry["role"] + " content: " + entry['content'] for entry in messages])
        prompt_tokens = len(enc.encode(messages_string))
        completion_tokens = len(enc.encode(llm_output))
        
        # self.generationConfig = GenerationConfig(id=str(uuid4()), name="generation", provider="openai", model="gpt-3.5-turbo-16k", model_parameters={"temperature": 3}, messages=self.messages)
        # generation = self.span.generation(self.generationConfig)
        self.generation.result({
            "id": self.generation.id,
            "object": "text_completion",
            "created": int(time()),
            "model": self.generationConfig.model,
            "choices": [
                {
                    "index": 0,
                    "text": llm_output,
                    "logprobs": None,
                    "finish_reason": "stop",
                },
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        })
        
        print(f"[DEBUG]: LLM Response: {response}")
        print(f"[DEBUG]: LLM Response Generations: {response.generations[0][0].text}")
        sleep(0.2)
        self.span.event(str(uuid4()), f"Agent END: {self.agent}", {})
        
    def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> Any:
        """Run when LLM errors."""

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> Any:
        """Run when chain starts running."""

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> Any:
        """Run when chain ends running."""

    def on_chain_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> Any:
        """Run when chain errors."""

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> Any:
        """Run when tool starts running."""

    def on_tool_end(self, output: Any, **kwargs: Any) -> Any:
        """Run when tool ends running."""

    def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> Any:
        """Run when tool errors."""

    def on_text(self, text: str, **kwargs: Any) -> Any:
        """Run on arbitrary text."""

    # def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
    #     """Run on agent action."""

    # def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
    #     """Run on agent end."""
    