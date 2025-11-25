# ElevenLabs STT-TTS Integration with Maxim SDK

This cookbook demonstrates how to integrate Maxim SDK tracing with ElevenLabs Speech-to-Text (STT) and Text-to-Speech (TTS) operations to create a unified trace for voice-based AI applications.

## Overview

The integration enables you to:
- Trace STT operations (speech → text)
- Trace TTS operations (text → speech)
- Link both operations under a single trace
- Attach audio files (input and output) to traces
- Monitor the complete voice pipeline in Maxim dashboard

## Prerequisites

- Python 3.9+
- ElevenLabs API key
- Maxim API credentials

## Installation

1. Install dependencies:
```bash
uv sync
```

2. Create a `.env` file in this directory:
```bash
# ElevenLabs Configuration
EL_API_KEY=your-elevenlabs-api-key

# Maxim Configuration
MAXIM_API_KEY=your-maxim-api-key
MAXIM_LOG_REPO_ID=your-maxim-log-repo-id
```

## Usage

### Basic Pipeline

The `stt_tts_pipeline.py` script demonstrates a complete STT-LLM-TTS pipeline:

```python
from maxim import Maxim
from maxim.logger.elevenlabs import instrument_elevenlabs
from elevenlabs.client import ElevenLabs

# Initialize Maxim logger
# This automatically picks up MAXIM_API_KEY and MAXIM_LOG_REPO_ID from environment variables
logger = Maxim().logger()

# Instrument ElevenLabs (one-line integration)
instrument_elevenlabs(logger)

# Initialize ElevenLabs client
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
```

### Running the Example

```bash
python stt_tts_pipeline.py
```

## How It Works

1. **STT Operation**: Converts audio input to text
   - Automatically creates/updates trace with input audio attachment
   - Sets trace input to the transcript text

2. **LLM Processing**: Processes the transcript (mock in example)
   - Can be replaced with any LLM API call

3. **TTS Operation**: Converts LLM response to audio
   - Automatically adds to the same trace
   - Sets trace output to the response text
   - Attaches output audio file to trace

### Trace Structure

The instrumentation creates a unified trace containing:
- **Input**: User speech transcript
- **Output**: LLM response text
- **Input Attachment**: Original audio file (user speech)
- **Output Attachment**: Generated audio file (assistant speech)
- **Metadata**: Model IDs, voice IDs, timestamps, etc.

## Configuration

### STT Configuration

```python
transcript = client.speech_to_text.convert(
    file=audio_file,
    model_id="scribe_v1",  # ElevenLabs STT model
    request_options=request_options  # Include trace_id header
)
```

### TTS Configuration

```python
audio_output = client.text_to_speech.convert(
    text=response_text,
    voice_id="JBFqnCBsd6RMkjVDRZzb",  # Voice ID
    model_id="eleven_multilingual_v2",  # TTS model
    output_format="mp3_44100_128",
    request_options=request_options  # Include trace_id header
)
```

## Trace Linking

To link STT and TTS operations under a single trace:

1. Create a trace with a unique ID:
```python
from uuid import uuid4
trace_id = str(uuid4())
trace = logger.trace(TraceConfigDict(id=trace_id, name="STT-TTS Pipeline"))
```

2. Pass the trace ID in request options:
```python
from elevenlabs.core import RequestOptions

request_options = RequestOptions(
    additional_headers={"x-maxim-trace-id": trace_id}
)
```

3. Use the same `request_options` for both STT and TTS calls

## Sample Audio File

Place a sample audio file (`.wav` format) in the `files/` directory named `sample_audio.wav` to test with real audio input. If the file is not found, the script will use a dummy transcript for demonstration.

## Maxim Dashboard

After running the pipeline, check your Maxim dashboard to see:
- Complete trace with STT and TTS operations
- Input/output text
- Audio file attachments
- Performance metrics
- Model and voice configurations

## Requirements

- `maxim-py>=3.13.6` (includes ElevenLabs instrumentation support)
- `elevenlabs>=1.0.0`
- `python-dotenv>=1.0.1`

## License

Copyright 2025 Maxim AI

