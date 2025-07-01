import logging
import os
import uuid

import dotenv
from livekit import agents
from livekit import api as livekit_api
from livekit.agents import Agent, AgentSession, function_tool
from livekit.api.room_service import CreateRoomRequest
from livekit.plugins import openai
from maxim import Maxim
from maxim.logger.livekit import instrument_livekit
from tavily import TavilyClient

dotenv.load_dotenv(override=True)
logging.basicConfig(level=logging.DEBUG)

logger = Maxim().logger()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


def on_event(event: str, data: dict):
    if event == "maxim.session.started":
        session_id = data["session_id"]
        logger.session({"id": session_id, "name": "custom session name"})
    elif event == "maxim.trace.started":
        trace_id = data["trace_id"]
        trace = data["trace"]
        logging.debug(f"Trace started - ID: {trace_id}", extra={"trace": trace})
    elif event == "maxim.trace.ended":
        trace_id = data["trace_id"]
        trace = data["trace"]
        logging.debug(f"Trace ended - ID: {trace_id}", extra={"trace": trace})


instrument_livekit(logger, on_event)


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a helpful voice AI assistant. You can search the web using the web_search tool."
        )

    @function_tool()
    async def web_search(self, query: str) -> str:
        """
        Performs a web search for the given query.
        """
        if not TAVILY_API_KEY:
            return "Tavily API key is not set. Please set the TAVILY_API_KEY environment variable."

        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        try:
            response = tavily_client.search(query=query, search_depth="basic")
            if response.get("answer"):
                return response["answer"]
            return str(response.get("results", "No results found."))
        except Exception as e:
            return f"An error occurred during web search: {e}"


async def entrypoint(ctx: agents.JobContext):
    # 1) pick a room name
    room_name = os.getenv("LIVEKIT_ROOM_NAME") or f"assistant-room-{uuid.uuid4().hex}"

    # 2) provision the room via the server API
    lkapi = livekit_api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET"),
    )
    try:
        req = CreateRoomRequest(
            name=room_name,
            empty_timeout=300,  # keep the room alive 5m after empty
            max_participants=10,  # adjust as needed
        )
        room = await lkapi.room.create_room(
            req
        )  # :contentReference[oaicite:0]{index=0}
        print(f"Room created: {room}")
        session = AgentSession(
            llm=openai.realtime.RealtimeModel(voice="coral"),
        )
        await session.start(room=room, agent=Assistant())
        await ctx.connect()
        await session.generate_reply(
            instructions="Greet the user and offer your assistance."
        )
    finally:
        await lkapi.aclose()


if __name__ == "__main__":
    opts = agents.WorkerOptions(entrypoint_fnc=entrypoint)
    agents.cli.run_app(opts)
