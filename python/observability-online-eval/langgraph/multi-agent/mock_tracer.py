import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from langchain.callbacks.base import BaseCallbackHandler


@dataclass
class Container:
    type: str
    id: str
    name: Optional[str] = None
    parent: Optional[str] = None


class MockTracer(BaseCallbackHandler):
    def __init__(self) -> None:
        super().__init__()
        self.parent_span = str(uuid4())
        self.containers: Dict[str, Container] = {}

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        tags = tags or []
        if "langsmith:hidden" in tags:
            return
        print("on_chain_start", run_id, parent_run_id, kwargs.get("name", None))
        self.containers[str(run_id)] = Container(
            type="span",
            id=str(run_id),
            name=kwargs.get("name", None),
            parent=str(parent_run_id) if parent_run_id else None,
        )

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        return super().on_llm_start(
            serialized,
            prompts,
            run_id=run_id,
            parent_run_id=parent_run_id,
            tags=tags,
            metadata=metadata,
            **kwargs
        )

    def on_chat_model_start(
        self,
        serialized,
        messages,
        *,
        run_id,
        parent_run_id=None,
        tags=None,
        metadata=None,
        **kwargs
    ):
        print("on_chat_model_start", run_id, parent_run_id)
        print("adding generation to", self.containers[str(parent_run_id)])

    def on_llm_error(self, error, *, run_id, parent_run_id=None, **kwargs):
        pass

    def on_llm_end(self, response, *, run_id, parent_run_id=None, **kwargs):
        print("on_llm_end", run_id, parent_run_id)

    def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        **kwargs: Any
    ) -> Any:
        if "langsmith:hidden" in tags:
            return
        print("on_chain_end", run_id, parent_run_id, kwargs.get("name", None))

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        inputs: Optional[dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        print("on_tool_start", str(run_id), str(parent_run_id))
        print("adding tool to", self.containers[str(parent_run_id)])

    def on_tool_end(self, output: Any, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> Any:
        print("on_tool_end", str(run_id), str(parent_run_id))