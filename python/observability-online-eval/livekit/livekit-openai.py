import os
import uuid

import dotenv
from livekit import agents
from livekit import api as livekit_api
from livekit.agents import Agent, AgentSession
from livekit.api.room_service import CreateRoomRequest
from livekit.plugins import openai
from maxim import Maxim
from maxim.logger.livekit import instrument_livekit

dotenv.load_dotenv()

logger = Maxim().logger()
instrument_livekit(logger)



class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant.")

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
            empty_timeout=300,        # keep the room alive 5m after empty
            max_participants=10,      # adjust as needed
        )
        await lkapi.room.create_room(req)               # :contentReference[oaicite:0]{index=0}
    finally:
        await lkapi.aclose()

    # 3) start your agent session in that real room
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(voice="coral"),
    )
    await session.start(room=room_name, agent=Assistant())
    await ctx.connect()
    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )

if __name__ == "__main__":
    opts = agents.WorkerOptions(entrypoint_fnc=entrypoint)
    agents.cli.run_app(opts)
