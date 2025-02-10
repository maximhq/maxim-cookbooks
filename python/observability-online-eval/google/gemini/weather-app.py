import os
from uuid import uuid4
import dotenv
from flask import Flask, request
from flask.json import jsonify
from google import genai
from maxim import Maxim, Config, LoggerConfig
from maxim.logger import TraceConfig
from maxim.logger.gemini import MaximGeminiClient

dotenv.load_dotenv()

maxim_api_key = os.getenv("MAXIM_API_KEY")
maxim_repo_id = os.getenv("MAXIM_REPO_ID")
if maxim_api_key is None or maxim_repo_id is None:
    raise ValueError("Please configure Maxim API key and repo id")

logger = Maxim(Config(api_key=maxim_api_key)).logger(LoggerConfig(id=maxim_repo_id))


app = Flask(__name__)
client = MaximGeminiClient(
    client=genai.Client(api_key=os.getenv("GEMINI_API_KEY")), logger=logger
)


def get_current_weather(location: str) -> str:
    """Get the current whether in a given location.

    Args:
        location: required, The city and state, e.g. San Franciso, CA
        unit: celsius or fahrenheit
    """
    print(f"Called with: {location=}")
    return "23C"


@app.post("/ask2")
def ask_weather_second():
    """
    Process a weather-related query using Gemini 2.0 Flash model.

    Endpoint expects a POST request with JSON body containing a 'query' field.
    Creates a trace for logging and passes the query to Gemini model with weather tools.

    Here we pass external trace to log this generation

    Returns:
        JSON containing 'data' field with generated response text
        400 error if request/JSON is invalid
    """
    if request is None or request.json is None:
        return jsonify({"data": "Invalid query"}), 400
    trace = logger.trace(TraceConfig(id=str(uuid4())))
    query = request.json["query"]
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=query,
        config={
            "tools": [get_current_weather],
            "system_instruction": "You are a helpful assisatant",
            "temperature": 0.8,
        },
        trace_id=trace.id,
    )
    trace.end()
    return jsonify({"data": response.text})


@app.post("/ask")
def ask_weather():
    """
    Process a weather-related query using Gemini 2.0 Flash model.

    Endpoint expects a POST request with JSON body containing a 'query' field.
    Creates a trace for logging and passes the query to Gemini model with weather tools.

    Here we ask MaximGeminiClient to create the trace

    Returns:
        JSON containing 'data' field with generated response text
        400 error if request/JSON is invalid
    """
    if request is None or request.json is None:
        return jsonify({"data": "Invalid query"}), 400
    query = request.json["query"]
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=query,
        config={
            "tools": [get_current_weather],
            "system_instruction": "You are a helpful assisatant",
            "temperature": 0.8,
        },
    )
    return jsonify({"data": response.text})


app.run(port=8000)
