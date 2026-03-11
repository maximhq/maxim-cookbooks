"""
Terminal chat interface for the Coding Agent.

Usage:
    python cli.py
"""

import sys
import threading
import time
from uuid import uuid4

import dotenv

from coding_agent.agent import CodingAgent, SessionState
from coding_agent.ai import AI
from coding_agent.observability import CodingAgentObservability

dotenv.load_dotenv()


def main():
    obs = CodingAgentObservability()
    ai = AI(obs=obs)
    agent = CodingAgent(ai, obs)

    session_id = uuid4().hex
    session = SessionState(session_id=session_id)

    print("Coding Agent (type 'quit' to exit)")
    print(f"Session: {session_id}")
    print("-" * 40)

    try:
        while True:
            try:
                message = input("\nYou: ").strip()
            except EOFError:
                break

            if not message:
                continue
            if message.lower() in ("quit", "exit"):
                break

            trace_id = uuid4().hex
            trace = obs.start_trace(
                trace_id=trace_id,
                name="Chat Turn",
                input_text=message,
                session_id=session_id,
                tags={"session_id": session_id},
            )

            # Show a live timer while the agent works
            stop_spinner = threading.Event()

            def spinner(stop_event=stop_spinner):
                start = time.time()
                while not stop_event.is_set():
                    elapsed = time.time() - start
                    print(f"\r  Generating... {elapsed:.0f}s", end="", flush=True)
                    stop_event.wait(1)
                elapsed = time.time() - start
                print(f"\r  Done in {elapsed:.0f}s      ")

            t = threading.Thread(target=spinner, daemon=True)
            t.start()

            output_text = "ERROR: turn failed before completion"
            try:
                result = agent.chat(message, session, trace)
                output_text = result.files.to_display()
                obs.attach_evaluators(trace, message, output_text)
            finally:
                stop_spinner.set()
                t.join()
                try:
                    obs.end_trace(trace, output_text)
                except Exception as trace_error:
                    # Preserve the original turn exception when trace finalization fails.
                    if sys.exc_info()[0] is None:
                        raise
                    print(f"\nWarning: failed to end trace: {trace_error}")

            print(f"\n[{result.mode}] {result.summary}")
            print(f"\nFiles ({len(result.files)}):")
            for filename in result.files:
                print(f"  - {filename}")
    except KeyboardInterrupt:
        print()
    finally:
        obs.cleanup()
        print("Goodbye!")


if __name__ == "__main__":
    main()
