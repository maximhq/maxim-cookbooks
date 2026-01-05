import os

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    AgentServer,
    JobContext,
    RunContext,
    cli,
    metrics,
)
from livekit.agents.llm import FallbackAdapter as FallbackLLMAdapter
from livekit.agents.llm import function_tool
from livekit.agents.stt import FallbackAdapter as FallbackSTTAdapter
from livekit.agents.telemetry import set_tracer_provider
from livekit.agents.tts import FallbackAdapter as FallbackTTSAdapter
from livekit.agents.voice import MetricsCollectedEvent
from livekit.plugins import openai, silero, google
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.util.types import AttributeValue

load_dotenv()

api_key = os.getenv("MAXIM_API_KEY")
repo_id = os.getenv("MAXIM_LOG_REPO_ID")


def setup_maxim_otel(
    metadata: dict[str, AttributeValue] | None = None,
) -> TracerProvider:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    trace_provider = TracerProvider()
    trace_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint="https://api.getmaxim.ai/v1/otel",
                headers={
                    "x-maxim-repo-id": repo_id or "",
                    "x-maxim-api-key": api_key or "",
                },
            )
        )
    )
    set_tracer_provider(trace_provider, metadata=metadata)
    return trace_provider


@function_tool
async def lookup_weather(context: RunContext, location: str) -> str:
    """Called when the user asks for weather related information.

    Args:
        location: The location they are asking for
    """

    return "sunny with a temperature of 70 degrees."


class Kelly(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="Your name is Kelly.",
            llm=FallbackLLMAdapter(
                llm=[
                    openai.LLM(model="gpt-4.1"),
                    google.LLM(model="gemini-2.5-flash-preview-05-20"),
                ]
            ),
            stt=FallbackSTTAdapter(
                stt=[openai.STT(model="gpt-4o-transcribe"), openai.STT(model="gpt-4o-mini-transcribe")]
            ),
            tts=FallbackTTSAdapter(
                tts=[
                    openai.TTS(model="tts-1"),
                    openai.TTS(model="gpt-4o-mini-tts"),
                ]
            ),
            turn_detection=MultilingualModel(),
            tools=[lookup_weather],
        )

    async def on_enter(self):
        self.session.generate_reply()

    @function_tool
    async def transfer_to_alloy(self) -> Agent:
        """Transfer the call to Alloy."""
        return Alloy()


class Alloy(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="Your name is Alloy.",
            llm=openai.realtime.RealtimeModel(voice="alloy"),
            tools=[lookup_weather],
        )

    async def on_enter(self):
        self.session.generate_reply()

    @function_tool
    async def transfer_to_kelly(self) -> Agent:
        """Transfer the call to Kelly."""

        return Kelly()


server = AgentServer()

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    trace_provider = setup_maxim_otel(
        # metadata will be set as attributes on all spans created by the tracer
        metadata={
            "session.id": ctx.room.name,
        }
    )

    # (optional) add a shutdown callback to flush the trace before process exit
    async def flush_trace():
        trace_provider.force_flush()

    ctx.add_shutdown_callback(flush_trace)

    session = AgentSession(vad=silero.VAD.load())

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)

    await session.start(agent=Kelly(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(server)
