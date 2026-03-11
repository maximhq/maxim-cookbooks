"""
FastAPI application for the Coding Agent cookbook.

Provides a single /chat endpoint that accepts user messages, auto-detects
the appropriate mode (generate/improve/debug), and returns generated code
with full Maxim observability and evaluation.
"""

from collections import OrderedDict
from uuid import uuid4

import dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from coding_agent.agent import CodingAgent, SessionState
from coding_agent.ai import AI
from coding_agent.files import FilesDict
from coding_agent.observability import CodingAgentObservability

dotenv.load_dotenv()

app = FastAPI(title="Coding Agent")

MAX_SESSIONS = 50


# ── Request / Response Models ────────────────────────────────────────


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    mode: str
    files: dict[str, str]
    summary: str
    trace_id: str


# ── Global State ─────────────────────────────────────────────────────

sessions: OrderedDict[str, SessionState] = OrderedDict()

obs = CodingAgentObservability()
ai = AI(obs=obs)
agent = CodingAgent(ai, obs)


# ── Endpoints ────────────────────────────────────────────────────────


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Handle a chat turn: detect mode, generate/improve/debug, evaluate."""
    session = _get_or_create_session(request.session_id)
    trace_id = uuid4().hex

    # Start trace
    trace = obs.start_trace(
        trace_id=trace_id,
        name="Chat Turn",
        input_text=request.message,
        session_id=request.session_id,
        tags={"session_id": request.session_id},
    )

    output_text = "ERROR: turn failed before completion"
    try:
        # Run agent
        result = agent.chat(request.message, session, trace)

        # Format output for evaluators (all files concatenated)
        output_text = result.files.to_display()

        # Attach evaluators
        obs.attach_evaluators(trace, request.message, output_text)
    except Exception as exc:
        output_text = f"ERROR: {exc}"
        raise
    finally:
        # End trace even when agent/evaluator flow fails.
        obs.end_trace(trace, output_text)

    return ChatResponse(
        session_id=request.session_id,
        mode=result.mode,
        files=dict(result.files),
        summary=result.summary,
        trace_id=trace_id,
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/session/{session_id}")
def get_session(session_id: str):
    """Retrieve session state (files and history)."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {
        "session_id": session_id,
        "files": dict(session.files),
        "history": session.history,
    }


@app.on_event("shutdown")
def shutdown():
    obs.cleanup()


# ── Helpers ──────────────────────────────────────────────────────────


def _get_or_create_session(session_id: str) -> SessionState:
    """Get existing session or create a new one, evicting oldest if at capacity."""
    if session_id not in sessions:
        if len(sessions) >= MAX_SESSIONS:
            sessions.popitem(last=False)  # evict oldest
        sessions[session_id] = SessionState(session_id=session_id)
    return sessions[session_id]
