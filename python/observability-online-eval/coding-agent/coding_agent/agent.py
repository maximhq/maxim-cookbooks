"""
CodingAgent — multi-turn coding agent with auto mode detection.

Supports three modes:
  - generate: Build code from scratch
  - improve: Modify existing code via diffs
  - debug: Execute code, detect errors, and auto-fix in a loop

Adapted from gpt-engineer's simple_agent + steps, simplified for cookbook clarity.
"""

import os
from dataclasses import dataclass, field
from uuid import uuid4

from coding_agent.ai import AI
from coding_agent.execution import ExecutionEnvironment, ExecutionResult
from coding_agent.files import FilesDict, apply_diffs, parse_chat_to_files, parse_diffs
from coding_agent.observability import CodingAgentObservability


@dataclass
class ChatResult:
    mode: str  # "generate" | "improve" | "debug"
    files: FilesDict
    summary: str


@dataclass
class SessionState:
    session_id: str
    history: list[dict] = field(default_factory=list)
    files: FilesDict = field(default_factory=FilesDict)


class CodingAgent:
    """Multi-turn coding agent with Maxim observability."""

    MAX_DEBUG_ATTEMPTS = 5

    def __init__(self, ai: AI, obs: CodingAgentObservability):
        self.ai = ai
        self.obs = obs
        self.prompts = self._load_prompts()

    def chat(self, message: str, session: SessionState, trace) -> ChatResult:
        """Handle a single chat turn: detect mode, execute, summarize."""
        # 1. Detect mode
        mode = self._detect_mode(message, session, trace)

        # 2. Execute mode
        if mode == "generate":
            files = self._generate(message, session, trace)
        elif mode == "improve":
            files = self._improve(message, session, trace)
        else:
            files = self._debug(message, session, trace)

        # 3. Generate summary
        summary = self._generate_summary(message, files, mode, trace)

        # 4. Update session state
        session.history.append({"role": "user", "content": message})
        session.history.append({"role": "assistant", "content": summary})
        session.files = files

        return ChatResult(mode=mode, files=files, summary=summary)

    # ── Mode Detection ──────────────────────────────────────────────

    def _detect_mode(self, message: str, session: SessionState, trace) -> str:
        """Detect whether to generate, improve, or debug."""
        span = self.obs.start_span(trace, uuid4().hex, "Mode Detection")
        try:
            # No existing files → always generate
            if not session.files:
                return "generate"

            # Use LLM to classify
            system_prompt = self.prompts["mode_selection"]
            user_msg = (
                f"User message: {message}\n\n"
                f"Project has {len(session.files)} existing file(s): "
                f"{', '.join(session.files.keys())}"
            )

            response, _ = self.ai.chat(
                system_prompt,
                user_msg,
                parent=span,
                generation_name="mode_selection",
            )

            mode = response.strip().lower()
            if mode not in ("generate", "improve", "debug"):
                mode = "improve"  # safe default
            return mode
        finally:
            self.obs.end_span(span)

    # ── Generate ─────────────────────────────────────────────────────

    def _generate(self, message: str, session: SessionState, trace) -> FilesDict:
        """Generate code from scratch."""
        span = self.obs.start_span(trace, uuid4().hex, "Code Generation")
        try:
            # Build system prompt: roadmap + generate (with file_format inlined) + philosophy
            file_format = self.prompts["file_format"]
            generate_prompt = self.prompts["generate"].replace("FILE_FORMAT", file_format)
            system_prompt = (
                f"{self.prompts['roadmap']}\n\n{generate_prompt}\n\n{self.prompts['philosophy']}"
            )

            response, _ = self.ai.chat(
                system_prompt,
                message,
                session.history,
                parent=span,
                generation_name="gen_code",
            )
            files = parse_chat_to_files(response)
        finally:
            self.obs.end_span(span)

        # Generate entrypoint (run.sh)
        ent_span = self.obs.start_span(trace, uuid4().hex, "Entrypoint Generation")
        try:
            ent_system = self.prompts["entrypoint"]
            ent_user = (
                f"Information about the codebase:\n\n{files.to_context()}\n\n"
                "Write a run.sh that runs this code."
            )
            ent_response, _ = self.ai.chat(
                ent_system,
                ent_user,
                parent=ent_span,
                generation_name="gen_entrypoint",
            )

            # Parse the entrypoint response for a run.sh code block
            entrypoint_files = parse_chat_to_files(ent_response)
            if "run.sh" in entrypoint_files:
                files["run.sh"] = entrypoint_files["run.sh"]
            elif entrypoint_files:
                # Use whatever file was returned
                for name, content in entrypoint_files.items():
                    files[name] = content
        finally:
            self.obs.end_span(ent_span)
        return files

    # ── Improve ──────────────────────────────────────────────────────

    def _improve(self, message: str, session: SessionState, trace) -> FilesDict:
        """Improve existing code via diffs."""
        span = self.obs.start_span(trace, uuid4().hex, "Code Improvement")
        try:
            # Build system prompt: roadmap + improve (with file_format_diff inlined) + philosophy
            file_format_diff = self.prompts["file_format_diff"]
            improve_prompt = self.prompts["improve"].replace(
                "FILE_FORMAT", file_format_diff
            )
            system_prompt = (
                f"{self.prompts['roadmap']}\n\n{improve_prompt}\n\n{self.prompts['philosophy']}"
            )

            files_context = session.files.to_context()
            user_msg = f"{message}\n\nExisting code:\n{files_context}"
            response, _ = self.ai.chat(
                system_prompt,
                user_msg,
                session.history,
                parent=span,
                generation_name="improve_code",
            )

            # Parse and apply diffs
            diffs = parse_diffs(response)
            if diffs:
                return apply_diffs(diffs, session.files)

            # Fallback: try parsing as full files
            parsed = parse_chat_to_files(response)
            updated = FilesDict(session.files.copy())
            updated.update(parsed)
            return updated
        finally:
            self.obs.end_span(span)

    # ── Debug ────────────────────────────────────────────────────────

    def _debug(self, message: str, session: SessionState, trace) -> FilesDict:
        """Execute code, detect errors, and auto-fix in a loop."""
        span = self.obs.start_span(trace, uuid4().hex, "Debug Loop")
        files = FilesDict(session.files.copy())
        env = ExecutionEnvironment()

        try:
            for attempt in range(self.MAX_DEBUG_ATTEMPTS):
                # Write files and execute
                env.write_files(files)
                exec_span = self.obs.start_span(
                    span, uuid4().hex, f"Execution Attempt {attempt + 1}"
                )
                try:
                    result = env.execute()
                    self.obs.log_event(
                        exec_span,
                        uuid4().hex,
                        "execution_result",
                        metadata={
                            "success": result.success,
                            "return_code": result.return_code,
                            "stderr": result.stderr[:500],
                            "stdout": result.stdout[:500],
                        },
                    )
                finally:
                    self.obs.end_span(exec_span)

                if result.success:
                    break

                # Fix: use improve logic with error context
                fix_span = self.obs.start_span(
                    span, uuid4().hex, f"Code Fix {attempt + 1}"
                )
                try:
                    file_format_fix = self.prompts["file_format_fix"]
                    system_prompt = (
                        f"{self.prompts['roadmap']}\n\n{file_format_fix}\n\n"
                        f"{self.prompts['philosophy']}"
                    )
                    fix_user = (
                        f"Original request: {message}\n\n"
                        f"Current code:\n{files.to_context()}\n\n"
                        f"Error output:\nstdout: {result.stdout}\nstderr: {result.stderr}\n\n"
                        f"Please fix the errors in the code."
                    )

                    fix_response, _ = self.ai.chat(
                        system_prompt,
                        fix_user,
                        parent=fix_span,
                        generation_name="fix_code",
                    )

                    # Parse fixed files (full file format, not diffs)
                    fixed = parse_chat_to_files(fix_response)
                    if fixed:
                        files.update(fixed)
                finally:
                    self.obs.end_span(fix_span)
        finally:
            env.cleanup()
            self.obs.end_span(span)
        return files

    # ── Summary ──────────────────────────────────────────────────────

    def _generate_summary(
        self, message: str, files: FilesDict, mode: str, trace
    ) -> str:
        """Generate a short summary of what was done."""
        span = self.obs.start_span(trace, uuid4().hex, "Summary Generation")
        try:
            system_prompt = (
                "You are a coding assistant. Summarize what was done in 2-3 sentences. "
                "Be specific about files created or modified."
            )
            user_msg = (
                f"Mode: {mode}\n"
                f"User request: {message}\n"
                f"Files: {', '.join(files.keys())}"
            )

            response, _ = self.ai.chat(
                system_prompt,
                user_msg,
                parent=span,
                generation_name="generate_summary",
            )
            return response
        finally:
            self.obs.end_span(span)

    # ── Prompt Loading ───────────────────────────────────────────────

    def _load_prompts(self) -> dict[str, str]:
        """Load all .md prompt files from the prompts/ directory.

        Keys are the stem (e.g. "generate"), values are the file contents.
        """
        prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
        prompts = {}
        for filename in os.listdir(prompts_dir):
            if not filename.endswith(".md"):
                continue
            filepath = os.path.join(prompts_dir, filename)
            if os.path.isfile(filepath):
                with open(filepath) as f:
                    # Strip the .md extension for the key
                    prompts[filename.removesuffix(".md")] = f.read()
        return prompts
