import os
import uuid

import dotenv
from livekit import agents
from livekit import api as livekit_api
from livekit.agents import Agent, AgentSession
from livekit.api.room_service import CreateRoomRequest
from livekit.plugins import google
from maxim import Maxim
from maxim.logger.livekit import instrument_livekit

dotenv.load_dotenv(override=True)

logger = Maxim({"base_url":"https://app.beta.getmaxim.ai", "debug":True}).logger()

def on_event(event:str, data:dict):
    print(f"##################Event: {event}, Data: {data}")

instrument_livekit(logger, on_event)

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
        room = await lkapi.room.create_room(req)               # :contentReference[oaicite:0]{index=0}
        print(f"Room created: {room}")
        session = AgentSession(
            llm=google.beta.realtime.RealtimeModel(model="gemini-2.0-flash-exp", voice="Puck"),
            
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
