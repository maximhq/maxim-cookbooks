"""
Maxim observability wrapper — tracing, spans, generations, and evaluator wiring.

Uses the Maxim Python SDK to create structured traces for every agent interaction
and attach 5 coding-specific evaluators to each trace.
"""

from time import time

from maxim import Maxim


class CodingAgentObservability:
    """Wraps Maxim SDK for trace/span/generation logging and evaluator attachment."""

    EVALUATOR_NAMES = [
        "Code Completeness",
        "Code Language Selection",
        "Code Correctness",
        "Code Safety",
        "Code Readability",
    ]

    def __init__(self):
        self.maxim = Maxim()
        self.logger = self.maxim.logger()

    def start_trace(
        self,
        trace_id: str,
        name: str,
        input_text: str,
        session_id: str = None,
        tags: dict = None,
    ) -> object:
        """Start a new trace."""
        config = {
            "id": trace_id,
            "name": name,
            "tags": tags or {},
            "input": input_text,
        }
        if session_id:
            config["session_id"] = session_id
        return self.logger.trace(config)

    def start_span(
        self, parent, span_id: str, name: str, tags: dict = None
    ) -> object:
        """Start a span under a trace or another span."""
        return parent.span({"id": span_id, "name": name, "tags": tags or {}})

    def log_generation(
        self,
        parent,
        gen_id: str,
        name: str,
        model: str,
        messages: list[dict],
        response_text: str,
        usage: dict,
        model_parameters: dict = None,
    ) -> None:
        """Log an LLM call as a generation under a trace or span."""
        generation = parent.generation({
            "id": gen_id,
            "provider": "openai",
            "model": model,
            "model_parameters": model_parameters or {},
            "messages": [
                {
                    "role": m["role"],
                    "content": m.get("content", ""),
                }
                for m in messages
            ],
            "name": name,
        })
        generation.result({
            "id": gen_id,
            "object": "chat.completion",
            "created": int(time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "content": response_text,
                        "role": "assistant",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": usage,
        })

    def attach_evaluators(
        self, trace, input_text: str, output_text: str
    ) -> None:
        """Attach all 5 coding agent evaluators to the trace."""
        trace.evaluate().with_evaluators(
            *self.EVALUATOR_NAMES
        ).with_variables({
            "input": input_text,
            "output": output_text,
        })

    def log_event(
        self,
        parent,
        event_id: str,
        name: str,
        tags: dict = None,
        metadata: dict = None,
    ) -> None:
        """Log an event on a trace or span."""
        parent.event(event_id, name, tags=tags, metadata=metadata)

    def end_span(self, span) -> None:
        """End a span."""
        span.end()

    def end_trace(self, trace, output_text: str) -> None:
        """Set output and end a trace."""
        output_method = getattr(trace, "output", None)
        if callable(output_method):
            output_method(output_text)
        else:
            set_output_method = getattr(trace, "set_output", None)
            if callable(set_output_method):
                set_output_method(output_text)
        trace.end()

    def cleanup(self) -> None:
        """Flush pending logs and clean up resources."""
        self.logger.flush()
        self.maxim.cleanup()
