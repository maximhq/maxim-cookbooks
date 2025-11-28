#!/usr/bin/env python
# coding: utf-8
"""
Voice Agent using OpenAI Agents SDK with Maxim Logging

This demonstrates how to build a voice assistant using OpenAI's Agents SDK
with Maxim tracing for observability.

The assistant includes:
- Triage Agent: Routes queries to appropriate specialized agents
- Search Agent: Performs web search for real-time information
- Knowledge Agent: Searches product knowledge base
- Account Agent: Provides account information via function calling
"""

import os

import dotenv
import numpy as np
import sounddevice as sd
from agents import Agent, Runner, add_trace_processor, function_tool, set_default_openai_key
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from agents.voice import AudioInput, SingleAgentVoiceWorkflow, TTSModelSettings, VoicePipeline, VoicePipelineConfig

# Optional: Import WebSearchTool if available
try:
    from agents import WebSearchTool
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False
    WebSearchTool = None
    print("⚠️ WebSearchTool not available")

from maxim import Maxim, Config
from maxim.logger.openai.agents import MaximOpenAIAgentsTracingProcessor

dotenv.load_dotenv()

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAXIM_API_KEY = os.getenv("MAXIM_API_KEY")
MAXIM_LOG_REPO_ID = os.getenv("MAXIM_LOG_REPO_ID")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Set OpenAI API key for agents
set_default_openai_key(OPENAI_API_KEY)

# Initialize Maxim logger
# Maxim SDK automatically picks up MAXIM_API_KEY and MAXIM_LOG_REPO_ID from env variables
logger = Maxim(Config()).logger()

# Add Maxim trace processor to automatically trace all agent interactions
add_trace_processor(MaximOpenAIAgentsTracingProcessor(logger))
print("✅ Maxim logging enabled for Agents SDK")


# ============================================================================
# Tools
# ============================================================================

@function_tool
def get_account_info(user_id: str) -> dict:
    """Return account info for a given user ID."""
    return {
        "user_id": user_id,
        "name": "Bugs Bunny",
        "account_balance": "£72.50",
        "membership_status": "Gold Executive"
    }


# ============================================================================
# Agents
# ============================================================================

# Voice-optimized system prompt
VOICE_SYSTEM_PROMPT = """
[Output Structure]

Your output will be delivered in an audio voice response, please ensure that every response meets these guidelines:

1. Use a friendly, human tone that will sound natural when spoken aloud.
2. Keep responses short and segmented—ideally one to two concise sentences per step.
3. Avoid technical jargon; use plain language so that instructions are easy to understand.
4. Provide only essential details so as not to overwhelm the listener.
"""

# Search Agent
search_agent = Agent(
    name="SearchAgent",
    instructions=VOICE_SYSTEM_PROMPT + (
        "You immediately provide an input to the WebSearchTool to find up-to-date information on the user's query."
    ),
    tools=[WebSearchTool()] if WEB_SEARCH_AVAILABLE else [],
)

# Knowledge Agent
# Note: Requires vector store ID - replace with your actual vector store ID
# knowledge_agent = Agent(
#     name="KnowledgeAgent",
#     instructions=VOICE_SYSTEM_PROMPT + (
#         "You answer user questions on our product portfolio with concise, helpful responses using the FileSearchTool."
#     ),
#     tools=[FileSearchTool(
#         max_num_results=3,
#         vector_store_ids=["YOUR_VECTOR_STORE_ID"],
#     )],
# )

# Account Agent
account_agent = Agent(
    name="AccountAgent",
    instructions=VOICE_SYSTEM_PROMPT + (
        "You provide account information based on a user ID using the get_account_info tool."
    ),
    tools=[get_account_info],
)

# Triage Agent
triage_agent = Agent(
    name="VoiceAssistant",
    instructions=prompt_with_handoff_instructions("""
You are the virtual assistant for Acme Shop. Welcome the user and ask how you can help.

Based on the user's intent, route to:
- AccountAgent for account-related queries
- SearchAgent for anything requiring real-time web search
"""),
    handoffs=[account_agent, search_agent],
)


# ============================================================================
# Voice Pipeline Configuration
# ============================================================================

# Custom TTS model settings for natural voice output
custom_tts_settings = TTSModelSettings(
    instructions=(
        "Personality: upbeat, friendly, persuasive guide. "
        "Tone: Friendly, clear, and reassuring, creating a calm atmosphere and making the listener feel confident and comfortable. "
        "Pronunciation: Clear, articulate, and steady, ensuring each instruction is easily understood while maintaining a natural, conversational flow. "
        "Tempo: Speak at a moderate, natural pace - not too fast, not too slow. Use strategic pauses between sentences and after important points. Include brief pauses before and after questions to allow the listener to process the information. "
        "Emotion: Warm and supportive, conveying empathy and care, ensuring the listener feels guided and safe throughout the journey."
    )
)

voice_pipeline_config = VoicePipelineConfig(tts_settings=custom_tts_settings)


# ============================================================================
# Voice Assistant with Maxim Logging
# ============================================================================

async def voice_assistant_with_maxim():
    """Run voice assistant with Maxim tracing (automatic via trace processor)."""
    # Use a standard sample rate for better quality and compatibility
    # 16000 Hz is commonly used for speech recognition and provides good quality
    # 24000 Hz is also good and matches OpenAI's TTS output rate
    SAMPLE_RATE = 16000  # Standard sample rate for speech
    
    print("🎤 Voice Assistant Ready!")
    print("Press Enter to speak your query (or type 'exit' to quit)")
    print(f"📊 Audio settings: {SAMPLE_RATE} Hz, mono, 16-bit")
    print("-" * 60)
    
    while True:
        # Check for input to either provide voice or exit
        cmd = input("\nPress Enter to speak (or type 'exit' to quit): ")
        
        if cmd.lower() == "exit":
            print("👋 Exiting...")
            break
        
        try:
            print("🎤 Listening...")
            recorded_chunks = []
            
            # Start streaming from microphone with fixed sample rate for better quality
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype='int16',
                blocksize=4096,  # Larger block size for better quality
                callback=lambda indata, frames, time, status: recorded_chunks.append(indata.copy())
            ):
                input()  # Wait for Enter key
            
            # Concatenate chunks into single buffer
            recording = np.concatenate(recorded_chunks, axis=0)
            
            # Ensure recording is in the correct format (flatten if needed)
            if recording.ndim > 1:
                recording = recording.flatten()
            
            # Create audio input
            audio_input = AudioInput(buffer=recording)
            
            # Create pipeline
            pipeline = VoicePipeline(
                workflow=SingleAgentVoiceWorkflow(triage_agent),
                config=voice_pipeline_config
            )
            
            # Run the pipeline
            # Maxim tracing is automatic via MaximOpenAIAgentsTracingProcessor
            print("🤔 Processing...")
            result = await pipeline.run(audio_input)
            
            # Transfer the streamed result into chunks of audio
            response_chunks = []
            transcript_parts = []
            
            async for event in result.stream():
                if event.type == "voice_stream_event_audio":
                    response_chunks.append(event.data)
                elif event.type == "voice_stream_event_text":
                    # Capture transcript for display
                    if hasattr(event, 'text'):
                        transcript_parts.append(event.text)
            
            response_audio = np.concatenate(response_chunks, axis=0)
            transcript = " ".join(transcript_parts) if transcript_parts else "Audio response generated"
            
            # Play response
            # Ensure response audio is in correct format
            if response_audio.ndim > 1:
                response_audio = response_audio.flatten()
            
            print("🔊 Assistant is responding...")
            # Use the same sample rate for playback as recording
            sd.play(response_audio, samplerate=SAMPLE_RATE)
            sd.wait()
            
            print(f"✅ Response: {transcript[:100]}..." if len(transcript) > 100 else f"✅ Response: {transcript}")
            print("📊 Interaction automatically traced to Maxim")
            
        except KeyboardInterrupt:
            print("\n👋 Interrupted by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Cleanup
    try:
        logger.cleanup()
    except Exception as e:
        print(f"⚠️ Logger cleanup error: {e}")


# ============================================================================
# Text-based Testing (for development)
# ============================================================================

async def test_agents_text():
    """Test agents with text input (for development/debugging)."""
    examples = [
        "What's my ACME account balance? My user ID is 1234567890",  # Account Agent test
        "What's trending in duck hunting gear right now?",  # Search Agent test
    ]
    
    try:
        for query in examples:
            print(f"\n👤 User: {query}")
            # Maxim tracing is automatic via MaximOpenAIAgentsTracingProcessor
            result = await Runner.run(triage_agent, query)
            print(f"🤖 Assistant: {result.final_output}")
            print("📊 Interaction automatically traced to Maxim")
            print("-" * 60)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        try:
            logger.cleanup()
        except Exception as e:
            print(f"⚠️ Logger cleanup error: {e}")


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Main entry point."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("🧪 Running text-based agent tests...")
        await test_agents_text()
    else:
        print("🎤 Starting voice assistant...")
        await voice_assistant_with_maxim()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

