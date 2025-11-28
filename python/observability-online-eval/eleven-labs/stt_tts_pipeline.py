"""Example agent using ElevenLabs STT-TTS pipeline with Maxim tracing."""

import os
from uuid import uuid4

from dotenv import load_dotenv
from elevenlabs.play import play
from elevenlabs.client import ElevenLabs
from elevenlabs.core import RequestOptions

from maxim import Maxim
from maxim.logger.components.trace import TraceConfigDict
from maxim.logger.elevenlabs import instrument_elevenlabs

load_dotenv()

# Configuration
ELEVENLABS_API_KEY = os.getenv("EL_API_KEY")

if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY environment variable is not set")

# Initialize Maxim logger
# This automatically picks up MAXIM_API_KEY and MAXIM_LOG_REPO_ID from environment variables
logger = Maxim().logger()

# Instrument ElevenLabs STT/TTS methods
instrument_elevenlabs(logger)

# Initialize ElevenLabs client
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)


def mock_llm(transcript: str) -> str:
    """
    Mock LLM that generates a response based on the user's transcript.
    In a real scenario, this would call an actual LLM API.
    """
    # Simple mock responses based on transcript content
    transcript_lower = transcript.lower()

    if "hello" in transcript_lower or "hi" in transcript_lower:
        return "Hello! How can I help you today?"
    elif "weather" in transcript_lower:
        return "I'm sorry, I don't have access to weather information right now."
    elif "time" in transcript_lower:
        return "I don't have access to the current time, but I'm here to help with other questions!"
    elif "goodbye" in transcript_lower or "bye" in transcript_lower:
        return "Goodbye! Have a great day!"
    else:
        return f"I heard you say: {transcript}. How can I assist you further?"


def stt_tts_pipeline_agent():
    """
    A simple agent that demonstrates the STT-LLM-TTS pipeline with unified tracing.

    Flow:
    1. User provides audio input (speech)
    2. STT converts audio to text (transcript) - instrumented, sets trace input
    3. Mock LLM processes the transcript and generates a response
    4. TTS converts LLM response text to audio - instrumented, sets trace output
    5. Audio is returned as output

    Both STT and TTS operations are traced under a single trace via instrumentation.
    The trace input is the user's speech transcript, and the output is the LLM response text.
    Both user speech and assistant speech audio files are attached to the trace.
    """

    # Create a shared trace ID for the entire pipeline
    trace_id = str(uuid4())

    trace = logger.trace(
        TraceConfigDict(
            id=trace_id,
            name="STT-TTS Pipeline Agent",
            tags={"provider": "elevenlabs", "operation": "pipeline"},
        )
    )

    # Create request options with trace_id header for both STT and TTS
    request_options = RequestOptions(
        additional_headers={
            "x-maxim-trace-id": trace_id
        }
    )

    print("=== STT-TTS Pipeline Agent ===")
    print(f"Trace ID: {trace_id}")

    audio_file_path = os.path.join(
        os.path.dirname(__file__),
        "files",
        "sample_audio.wav"
    )

    # Check if sample file exists, otherwise create a dummy scenario
    if os.path.exists(audio_file_path):
        print(f"Processing audio file: {audio_file_path}")

        # Convert speech to text
        # This will add to the existing trace (trace_id from request_options)
        # - Input: audio attachment (speech)
        # - Output: transcript text
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.speech_to_text.convert(
                file=audio_file,
                model_id="scribe_v1",
                request_options=request_options
            )

        # Extract transcript text from the result object
        transcript_text = ""
        if isinstance(transcript, str):
            transcript_text = transcript
        elif hasattr(transcript, "text"):
            transcript_text = transcript.text
        elif isinstance(transcript, dict) and "text" in transcript:
            transcript_text = transcript["text"]
        else:
            transcript_text = str(transcript)

        print(f"Transcript: {transcript_text}")

        # Mock LLM processing
        print("\n=== Mock LLM Processing ===")
        response_text = mock_llm(transcript_text)
        print(f"LLM Response: {response_text}")

        # Text-to-Speech
        print("\n=== Text-to-Speech ===")

        # Convert LLM response text to speech
        # This will also add to the same trace (trace_id from request_options)
        # - Input: LLM response text (already set as trace output above)
        # - Output: audio attachment (assistant speech)
        audio_output = client.text_to_speech.convert(
            text=response_text,
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
            request_options=request_options
        )

        play(audio_output)
    else:
        print(f"Sample audio file not found at {audio_file_path}")
        print("Creating a simple STT-LLM-TTS example instead...")

        # Create a dummy transcript for testing
        dummy_transcript = "Hello, how are you?"
        print(f"Using dummy transcript: {dummy_transcript}")

        # Set trace input to the transcript
        trace.set_input(dummy_transcript)

        # Mock LLM processing
        print("\n=== Mock LLM Processing ===")
        response_text = mock_llm(dummy_transcript)
        print(f"LLM Response: {response_text}")

        # Text-to-Speech
        print("\n=== Text-to-Speech ===")

        audio_output = client.text_to_speech.convert(
            text=response_text,
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
            request_options=request_options
        )

    trace.end()

    print("\n=== Pipeline Complete ===")
    print("Check your Maxim dashboard to see the unified trace with:")
    print("- Input: User speech transcript (set by STT instrumentation)")
    print("- Output: LLM response text (set by TTS instrumentation)")
    print("- Input attachment: User speech audio file (added by STT instrumentation)")
    print("- Output attachment: Assistant speech audio file (added by TTS instrumentation)")
    print(f"- Trace ID: {trace_id}")


if __name__ == "__main__":
    try:
        stt_tts_pipeline_agent()
    finally:
        logger.cleanup()

