import json
import logging
import os
from math import log

import weaviate
from flask import Flask, jsonify, request
from langchain.chat_models.openai import ChatOpenAI
from langchain.tools import tool
from langchain_community.vectorstores import Weaviate
from maxim import Config, Maxim
from maxim.decorators import (current_retrieval, current_trace,
                              langchain_callback, langchain_llm_call,
                              retrieval, trace)
from maxim.logger import LoggerConfig

maxim_api_key = os.environ.get("MAXIM_API_KEY", "")
log_repo_id = os.environ.get("LOG_REPO_ID", "")
openai_key = os.environ.get("OPENAI_API_KEY", "")
weaviate_url = os.environ.get("WEAVIATE_URL", "")
weaviate_key = os.environ.get("WEAVIATE_API_KEY", "")

logging.basicConfig(level=logging.INFO)

maxim = Maxim(
    config=Config(
        api_key=maxim_api_key, debug=True, base_url="https://app.beta.getmaxim.ai"
    )
)
logger = maxim.logger(LoggerConfig(id=log_repo_id))
llm = ChatOpenAI(api_key=openai_key, model="gpt-4o-mini")
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=weaviate.auth.AuthApiKey(api_key=weaviate_key),
    headers={
        "X-OpenAI-Api-Key": openai_key,
    },
)

app = Flask(__name__)


@retrieval(name="weaviate-call")
def retrieve_docs(query: str):
    current_retrieval().input(query)
    collection = client.collections.get("Awesome_moviate_movies")
    response = collection.query.near_text(query=query, limit=3)
    docs = [
        {
            "title": item.properties["title"],
            "year": item.properties["year"],
            "description": item.properties["description"],
            "genres": item.properties["genres"],
            "actors": item.properties["actors"],
            "director": item.properties["director"],
        }
        for item in response.objects
    ]
    return docs


@langchain_llm_call(name="llm-call")
def execute(query: str):    
    context = retrieve_docs(query)
    messages = [
        (
            "system",
            f"You answer questions about movies. Use provided list of movies to refine the response.\n\n List of movies: {json.dumps(context)}\n Respond in proper markdown format",
        ),
        ("human", query),
    ]
    result = llm.invoke(messages, config={"callbacks": [langchain_callback()]})
    return result.content


@app.post("/api/v1/chat")
@trace(logger=logger, name="movie-chat-v1")
def handler():
    print(current_trace().id)
    query = request.json["query"]
    result = execute(query)
    return jsonify({"result": result})


app.run(port=8000)
client.close()
