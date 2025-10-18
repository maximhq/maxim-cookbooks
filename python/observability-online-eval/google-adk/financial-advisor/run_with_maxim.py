#!/usr/bin/env python3
"""
Minimal conversational agent using Google ADK Financial Advisor with Maxim tracing.

Usage:
    python3 run_with_maxim.py

Note: Maxim is automatically instrumented via instrument_google_adk() in __init__.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from financial_advisor import root_agent
from google.adk.runners import InMemoryRunner
from google.genai.types import Part, UserContent


async def interactive_session():
    """Run interactive conversation with the financial advisor."""
    print("\n" + "=" * 80)
    print("Financial Advisor - Conversational Agent")
    print("=" * 80)
    
    # Create runner - Maxim plugin auto-injected
    runner = InMemoryRunner(agent=root_agent)
    
    session = await runner.session_service.create_session(
        app_name=runner.app_name,
        user_id="user"
    )
    
    print("\nType your message (or 'exit' to quit)")
    print("=" * 80 + "\n")
    
    try:
        while True:
            try:
                user_input = input("You: ").strip()
            except EOFError:
                break
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit']:
                break
            
            # Send message to agent
            content = UserContent(parts=[Part(text=user_input)])
            print("\nAgent: ", end="", flush=True)
            
            try:
                async for event in runner.run_async(
                    user_id=session.user_id,
                    session_id=session.id,
                    new_message=content,
                ):
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                print(part.text, end="", flush=True)
            except Exception as e:
                print(f"\n\n❌ Error: {e}")
                continue
            
            print("\n")
    
    except KeyboardInterrupt:
        pass
    
    finally:
        # End Maxim session
        from maxim.logger.google_adk.client import end_maxim_session
        end_maxim_session()
        print("\n" + "=" * 80)
        print("View traces at: https://app.getmaxim.ai")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(interactive_session())
