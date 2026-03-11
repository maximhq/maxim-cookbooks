"""
OpenAI SDK wrapper with context compaction support.
"""

from typing import TYPE_CHECKING, Any
from uuid import uuid4

from openai import OpenAI

if TYPE_CHECKING:
    from coding_agent.observability import CodingAgentObservability


class AI:
    """Thin wrapper around OpenAI chat completions."""

    # Rough token limit before compaction kicks in
    COMPACTION_THRESHOLD = 80_000
    CHARS_PER_TOKEN = 4

    def __init__(
        self,
        model: str = "gpt-4.1",
        temperature: float = 0.1,
        obs: "CodingAgentObservability" = None,
    ):
        self.client = OpenAI()
        self.model = model
        self.temperature = temperature
        self.obs = obs

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        history: list[dict] = None,
        parent: Any = None,
        generation_name: str = None,
    ) -> tuple[str, dict]:
        """Single LLM call. Returns (response_text, usage_dict).

        usage_dict contains prompt_tokens, completion_tokens, total_tokens.
        """
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        messages = self._maybe_compact(messages)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
        response_text = response.choices[0].message.content

        if self.obs and parent is not None and generation_name:
            self.obs.log_generation(
                parent,
                gen_id=uuid4().hex,
                name=generation_name,
                model=self.model,
                messages=messages,
                response_text=response_text,
                usage=usage,
                model_parameters={"temperature": self.temperature},
            )

        return response_text, usage

    def _maybe_compact(self, messages: list[dict]) -> list[dict]:
        """Compact messages if context exceeds the threshold.

        Uses a simple summarization approach: keeps system + last few messages
        and summarizes the middle via an LLM call.
        """
        total_chars = sum(len(m.get("content", "")) for m in messages)
        estimated_tokens = total_chars // self.CHARS_PER_TOKEN

        if estimated_tokens <= self.COMPACTION_THRESHOLD:
            return messages

        # Keep system message and last 4 messages, summarize the rest
        system = messages[0]
        middle = messages[1:-4]
        recent = messages[-4:]

        if not middle:
            return messages

        middle_text = "\n".join(
            f"{m['role']}: {m.get('content', '')}" for m in middle
        )
        try:
            summary_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Summarize the following conversation concisely, preserving key decisions and code context:",
                    },
                    {"role": "user", "content": middle_text},
                ],
                temperature=0.0,
                max_tokens=2000,
            )
            summary = summary_response.choices[0].message.content or ""
        except Exception:
            return [system, *recent]

        return [
            system,
            {"role": "assistant", "content": f"[Conversation summary]: {summary}"},
            *recent,
        ]
