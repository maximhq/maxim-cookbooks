"""
Context Summarization with Realtime API (SDK Version)

Build an end-to-end voice bot that listens to your mic, speaks back in real time
and summarises long conversations so quality never drops.

This version uses the OpenAI SDK directly (like tool_calling.py) instead of raw websockets.

Prerequisites:
- Python >= 3.10
- OpenAI API key (set OPENAI_API_KEY environment variable)
- Maxim API key (set MAXIM_API_KEY environment variable)
- Maxim base URL (set MAXIM_BASE_URL environment variable)
- Mic + speakers (grant OS permission if prompted)
"""

# Standard library imports
# Third-party imports
import asyncio
import base64
import json
import os
import random
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal

import simpleaudio  # speaker playback
import sounddevice as sd  # microphone capture
from dotenv import load_dotenv

# OpenAI SDK imports
from openai import OpenAI

from maxim import Maxim
from maxim.logger.openai import MaximOpenAIClient

load_dotenv()


# --------------------------------------------------------------------------- #
# Tool Definitions                                                            #
# --------------------------------------------------------------------------- #

TOOLS = [
    {
        "type": "function",
        "name": "get_weather",
        "description": "Get the current weather for a specific location. Use this when the user asks about weather conditions.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and country, e.g. 'Paris, France' or 'New York, USA'",
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit preference",
                },
            },
            "required": ["location"],
        },
    },
    {
        "type": "function",
        "name": "get_current_time",
        "description": "Get the current date and time. Use this when the user asks what time it is or what the date is.",
        "parameters": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "The timezone, e.g. 'UTC', 'America/New_York', 'Europe/Paris'. Defaults to local time if not specified.",
                },
            },
            "required": [],
        },
    },
    {
        "type": "function",
        "name": "set_reminder",
        "description": "Set a reminder for the user. Use this when the user wants to be reminded about something.",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The reminder message",
                },
                "time": {
                    "type": "string",
                    "description": "When to remind, e.g. 'in 5 minutes', 'at 3pm', 'tomorrow morning'",
                },
            },
            "required": ["message", "time"],
        },
    },
]


def execute_tool(name: str, arguments: Dict[str, Any]) -> str:
    """Execute a tool and return the result as a string."""
    if name == "get_weather":
        # Simulated weather data
        location = arguments.get("location", "Unknown")
        unit = arguments.get("unit", "celsius")

        # Generate mock weather data
        conditions = ["sunny", "partly cloudy", "cloudy", "rainy", "stormy"]
        condition = random.choice(conditions)
        temp_c = random.randint(5, 35)
        temp = temp_c if unit == "celsius" else int(temp_c * 9 / 5 + 32)
        unit_symbol = "°C" if unit == "celsius" else "°F"
        humidity = random.randint(30, 90)

        return json.dumps(
            {
                "location": location,
                "temperature": f"{temp}{unit_symbol}",
                "condition": condition,
                "humidity": f"{humidity}%",
                "wind": f"{random.randint(5, 30)} km/h",
            }
        )

    elif name == "get_current_time":
        timezone = arguments.get("timezone", "local")
        now = datetime.now()

        return json.dumps(
            {
                "date": now.strftime("%A, %B %d, %Y"),
                "time": now.strftime("%I:%M %p"),
                "timezone": timezone if timezone != "local" else "Local Time",
                "unix_timestamp": int(now.timestamp()),
            }
        )

    elif name == "set_reminder":
        message = arguments.get("message", "")
        time = arguments.get("time", "")

        # In a real app, you'd actually schedule the reminder
        # Here we just acknowledge it
        return json.dumps(
            {
                "status": "success",
                "message": f"Reminder set: '{message}' for {time}",
                "id": f"reminder_{random.randint(1000, 9999)}",
            }
        )

    else:
        return json.dumps({"error": f"Unknown tool: {name}"})


# Set your API keys safely
openaiapikey = os.getenv("OPENAI_API_KEY", None)
if not openaiapikey:
    raise ValueError("OPENAI_API_KEY not found – please set env var.")

baseURL = os.getenv("MAXIM_BASE_URL")

# Audio/config knobs
SAMPLE_RATE_HZ = 24_000  # Required by pcm16
CHUNK_DURATION_MS = 40  # chunk size for audio capture
BYTES_PER_SAMPLE = 2  # pcm16 = 2 bytes/sample
SUMMARY_TRIGGER = 2_000  # Summarise when context >= this
KEEP_LAST_TURNS = 2  # Keep these turns verbatim
SUMMARY_MODEL = "gpt-4o-mini"  # Cheaper, fast summariser


@dataclass
class Turn:
    """One utterance in the dialogue (user **or** assistant)."""

    role: Literal["user", "assistant"]
    item_id: str  # Server‑assigned identifier
    text: str | None = None  # Filled once transcript is ready


@dataclass
class ConversationState:
    """All mutable data the session needs — nothing more, nothing less."""

    history: List[Turn] = field(default_factory=list)  # Ordered log
    waiting: dict[str, asyncio.Future] = field(
        default_factory=dict
    )  # Pending transcript fetches
    summary_count: int = 0

    latest_tokens: int = 0  # Window size after last reply
    summarising: bool = False  # Guard so we don't run two summaries at once


def print_history(state) -> None:
    """Pretty-print the running transcript so far."""
    print("—— Conversation so far ———————————————")
    for turn in state.history:
        text_preview = (turn.text or "").strip().replace("\n", " ")
        print(f"[{turn.role:<9}] {text_preview}  ({turn.item_id})")
    print("——————————————————————————————————————————")


async def mic_to_queue(pcm_queue: asyncio.Queue[bytes]) -> None:
    """
    Capture raw PCM‑16 microphone audio and push ~CHUNK_DURATION_MS chunks
    to *pcm_queue* until the surrounding task is cancelled.

    Parameters
    ----------
    pcm_queue : asyncio.Queue[bytes]
        Destination queue for PCM‑16 frames (little‑endian int16).
    """
    blocksize = int(SAMPLE_RATE_HZ * CHUNK_DURATION_MS / 1000)

    def _callback(indata, _frames, _time, status):
        if status:  # XRuns, device changes, etc.
            print("⚠️", status, file=sys.stderr)
        try:
            pcm_queue.put_nowait(bytes(indata))  # 1‑shot enqueue
        except asyncio.QueueFull:
            # Drop frame if upstream (WebSocket) can't keep up.
            pass

    # RawInputStream is synchronous; wrap in context manager to auto‑close.
    with sd.RawInputStream(
        samplerate=SAMPLE_RATE_HZ,
        blocksize=blocksize,
        dtype="int16",
        channels=1,
        callback=_callback,
    ):
        try:
            # Keep coroutine alive until cancelled by caller.
            await asyncio.Event().wait()
        finally:
            print("⏹️  Mic stream closed.")


# Helper function to encode audio chunks in base64
def b64(blob):
    return base64.b64encode(blob).decode()


async def queue_to_connection(pcm_queue: asyncio.Queue[bytes], connection):
    """Read audio chunks from queue and send to connection."""
    try:
        while (chunk := await pcm_queue.get()) is not None:
            await connection.input_audio_buffer.append(audio=b64(chunk))
    except Exception as e:
        print(f"Connection closed – stopping uploader: {e}")


async def run_summary_llm(text: str, client: OpenAI) -> str:
    """Call a lightweight model to summarise `text`."""
    resp = await asyncio.to_thread(
        lambda: client.chat.completions.create(
            model=SUMMARY_MODEL,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "Summarise in French the following conversation "
                    "in one concise paragraph so it can be used as "
                    "context for future dialogue.",
                },
                {"role": "user", "content": text},
            ],
        )
    )
    return resp.choices[0].message.content.strip()


async def summarise_and_prune(connection, state, client: OpenAI):
    """Summarise old turns, delete them server‑side, and prepend a single summary
    turn locally + remotely."""
    state.summarising = True
    print(
        f"⚠️  Token window ≈{state.latest_tokens} ≥ {SUMMARY_TRIGGER}. Summarising…",
    )
    old_turns, recent_turns = (
        state.history[:-KEEP_LAST_TURNS],
        state.history[-KEEP_LAST_TURNS:],
    )
    convo_text = "\n".join(f"{t.role}: {t.text}" for t in old_turns if t.text)

    if not convo_text:
        print("Nothing to summarise (transcripts still pending).")
        state.summarising = False
        return

    summary_text = await run_summary_llm(convo_text, client) if convo_text else ""
    state.summary_count += 1
    summary_id = f"sum_{state.summary_count:03d}"
    state.history[:] = [Turn("assistant", summary_id, summary_text)] + recent_turns

    print_history(state)

    # Create summary on server
    await connection.conversation.item.create(
        item={
            "id": summary_id,
            "type": "message",
            "role": "system",
            "content": [{"type": "input_text", "text": summary_text}],
        },
        previous_item_id="root",
    )

    # Delete old items
    for turn in old_turns:
        await connection.conversation.item.delete(item_id=turn.item_id)

    print(f"✅ Summary inserted ({summary_id})")

    state.summarising = False


async def fetch_full_item(
    connection, item_id: str, state: ConversationState, attempts: int = 1
):
    """
    Ask the server for a full conversation item; retry up to 5× if the
    transcript field is still null.  Resolve the waiting future when done.
    """
    # If there is already a pending fetch, just await it
    if item_id in state.waiting:
        return await state.waiting[item_id]

    fut = asyncio.get_running_loop().create_future()
    state.waiting[item_id] = fut

    # Request the item - this sends the request and returns immediately
    # The actual item will come through as a conversation.item.retrieved event
    await connection.conversation.item.retrieve(item_id=item_id)

    # Wait for the event to resolve the future (with timeout)
    try:
        item = await asyncio.wait_for(fut, timeout=2.0)
    except asyncio.TimeoutError:
        # If timeout, retry
        state.waiting.pop(item_id, None)
        if attempts < 5:
            await asyncio.sleep(0.4 * attempts)
            return await fetch_full_item(connection, item_id, state, attempts + 1)
        return None

    # If transcript still missing retry (max 5×)
    content = item.get("content", [{}])
    transcript = content[0].get("transcript") if content else None
    if attempts < 5 and not transcript:
        state.waiting.pop(item_id, None)
        await asyncio.sleep(0.4 * attempts)
        return await fetch_full_item(connection, item_id, state, attempts + 1)

    # Done – remove the marker
    state.waiting.pop(item_id, None)
    return item


# --------------------------------------------------------------------------- #
# Realtime session                                                          #
# --------------------------------------------------------------------------- #
async def realtime_session(
    model="gpt-realtime",
    voice="shimmer",
    enable_playback=True,
):
    """
    Main coroutine: connects to the Realtime endpoint, spawns helper tasks,
    and processes incoming events using the OpenAI SDK.
    """
    state = ConversationState()  # Reset state for each run

    pcm_queue: asyncio.Queue[bytes] = asyncio.Queue()
    assistant_audio: List[bytes] = []

    # Create logger and client
    logger = Maxim({"base_url": baseURL}).logger()
    openai_client = OpenAI(api_key=openaiapikey)
    client = MaximOpenAIClient(openai_client, logger=logger).aio

    async with client.realtime.connect(
        model=model,
        extra_headers={
            "maxim-session-name": "Context Summarization with Realtime API SDK",
            "maxim-session-tags": {
                "env": "staging",
                "feature": "context_summarization_with_realtime_api_sdk",
            },
        },
    ) as connection:
        # ------------------------------------------------------------------- #
        # Configure session: voice, modalities, audio formats, transcription  #
        # ------------------------------------------------------------------- #
        await connection.session.update(
            session={
                "model": model,
                "type": "realtime",
                "output_modalities": ["audio"],
                "tracing": "auto",
                "tools": TOOLS,
                "tool_choice": "auto",
                "audio": {
                    "input": {
                        "transcription": {
                            "language": "en",
                            "model": "gpt-4o-transcribe",
                        },
                        "format": {"rate": SAMPLE_RATE_HZ, "type": "audio/pcm"},
                    }
                },
            },
        )
        print("session.created ✅")
        print(f"🔧 Tools available: {[t['name'] for t in TOOLS]}")

        # ------------------------------------------------------------------- #
        # Launch background tasks: mic capture → queue → connection            #
        # ------------------------------------------------------------------- #
        mic_task = asyncio.create_task(mic_to_queue(pcm_queue))
        upl_task = asyncio.create_task(queue_to_connection(pcm_queue, connection))

        print("🎙️ Speak now (Ctrl‑C to quit)…")

        try:
            # ------------------------------------------------------------------- #
            # Main event loop: process incoming events from the connection         #
            # ------------------------------------------------------------------- #
            async for event in connection:
                etype = event.type

                # --------------------------------------------------------------- #
                # User just spoke ⇢ conversation.item.created (role = user)        #
                # --------------------------------------------------------------- #
                if etype == "conversation.item.created":
                    item = event.item
                    if item.role == "user":
                        text = None
                        if item.content:
                            # Extract transcript from content
                            content_item = item.content[0] if item.content else None
                            if content_item:
                                # Handle both dict and object access patterns
                                if isinstance(content_item, dict):
                                    text = content_item.get("transcript")
                                elif hasattr(content_item, "transcript"):
                                    text = content_item.transcript
                                elif hasattr(content_item, "get"):
                                    text = content_item.get("transcript")

                        state.history.append(Turn("user", item.id, text))

                        # If transcript not yet available, fetch it later
                        if text is None:
                            asyncio.create_task(
                                fetch_full_item(connection, item.id, state)
                            )

                # --------------------------------------------------------------- #
                # Transcript fetched ⇢ conversation.item.retrieved                 #
                # --------------------------------------------------------------- #
                elif etype == "conversation.item.retrieved":
                    item = event.item

                    # Extract transcript from content
                    transcript = None
                    if item.content:
                        content_item = item.content[0] if item.content else None
                        if content_item:
                            # Handle both dict and object access patterns
                            if isinstance(content_item, dict):
                                transcript = content_item.get("transcript")
                            elif hasattr(content_item, "transcript"):
                                transcript = content_item.transcript
                            elif hasattr(content_item, "get"):
                                transcript = content_item.get("transcript")

                    # Fill missing transcript in history
                    for t in state.history:
                        if t.item_id == item.id:
                            t.text = transcript
                            break

                    # Resolve the future if one exists
                    item_id = item.id
                    if item_id in state.waiting:
                        # Convert item to dict-like structure matching original format
                        # This matches what fetch_full_item expects
                        item_dict = {
                            "id": item.id,
                            "content": [{"transcript": transcript}]
                            if transcript
                            else [],
                        }
                        state.waiting[item_id].set_result(item_dict)
                        state.waiting.pop(item_id, None)

                # --------------------------------------------------------------- #
                # Assistant audio arrives in deltas                               #
                # --------------------------------------------------------------- #
                elif etype == "response.output_audio.delta":
                    assistant_audio.append(base64.b64decode(event.delta))

                # --------------------------------------------------------------- #
                # Function call completed - execute tool and send result          #
                # --------------------------------------------------------------- #
                elif etype == "response.function_call_arguments.done":
                    call_id = event.call_id
                    function_name = event.name
                    arguments_str = event.arguments

                    print(f"🔧 Tool call: {function_name}({arguments_str})")

                    # Parse arguments and execute the tool
                    try:
                        arguments = json.loads(arguments_str) if arguments_str else {}
                    except json.JSONDecodeError:
                        arguments = {}

                    result = execute_tool(function_name, arguments)
                    print(f"   → Result: {result}")

                    # Send the function call output back to the conversation
                    await connection.conversation.item.create(
                        item={
                            "type": "function_call_output",
                            "call_id": call_id,
                            "output": result,
                        }
                    )

                    # Trigger a new response to continue the conversation
                    await connection.response.create()

                # --------------------------------------------------------------- #
                # Assistant reply finished ⇢ response.done                        #
                # --------------------------------------------------------------- #
                elif etype == "response.done":
                    response = event.response

                    # Extract assistant messages and tokens
                    if response.output:
                        for output_item in response.output:
                            if (
                                output_item.type == "message"
                                and output_item.role == "assistant"
                            ):
                                content_item = (
                                    output_item.content[0]
                                    if output_item.content
                                    else None
                                )
                                txt = None
                                if content_item:
                                    # Handle both dict and object access patterns
                                    if isinstance(content_item, dict):
                                        txt = content_item.get("transcript")
                                    elif hasattr(content_item, "transcript"):
                                        txt = content_item.transcript
                                    elif hasattr(content_item, "get"):
                                        txt = content_item.get("transcript")

                                if txt:
                                    state.history.append(
                                        Turn("assistant", output_item.id, txt)
                                    )

                    # Extract token usage
                    if response.usage:
                        state.latest_tokens = response.usage.total_tokens

                    print(
                        f"—— response.done  (window ≈{state.latest_tokens} tokens) ——"
                    )
                    print_history(state)

                    # Fetch any still‑missing user transcripts
                    for turn in state.history:
                        if (
                            turn.role == "user"
                            and turn.text is None
                            and turn.item_id not in state.waiting
                        ):
                            asyncio.create_task(
                                fetch_full_item(connection, turn.item_id, state)
                            )

                    # Playback collected audio once reply completes
                    if enable_playback and assistant_audio:
                        simpleaudio.play_buffer(
                            b"".join(assistant_audio),
                            1,
                            BYTES_PER_SAMPLE,
                            SAMPLE_RATE_HZ,
                        )
                        assistant_audio.clear()

                    # Summarise if context too large – fire in background so we don't block dialogue
                    if (
                        state.latest_tokens >= SUMMARY_TRIGGER
                        and len(state.history) > KEEP_LAST_TURNS
                        and not state.summarising
                    ):
                        asyncio.create_task(
                            summarise_and_prune(connection, state, openai_client)
                        )

        except KeyboardInterrupt:
            print("\nStopping…")
        finally:
            mic_task.cancel()
            await pcm_queue.put(None)
            await upl_task


def main():
    """Run the realtime session."""
    asyncio.run(realtime_session())


if __name__ == "__main__":
    main()
