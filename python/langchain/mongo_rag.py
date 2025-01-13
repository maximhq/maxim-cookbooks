import json
import logging
import os
from math import log
from flask import Flask, jsonify, request
from langchain.chat_models.openai import ChatOpenAI
from langchain.tools import tool
from langchain_openai import OpenAIEmbeddings

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from maxim import Config, Maxim
from maxim.decorators import current_retrieval, current_trace, retrieval, trace
from maxim.decorators.langchain import langchain_callback, langchain_llm_call
from maxim.logger import LoggerConfig

maxim_api_key = os.environ.get("MAXIM_API_KEY", "")
log_repo_id = os.environ.get("LOG_REPO_ID", "")
openai_key = os.environ.get("OPENAI_API_KEY", "")
mongo_uri = os.environ.get("MONGO_URI", "")

logging.basicConfig(level=logging.INFO)

maxim = Maxim(
    config=Config(
        api_key=maxim_api_key, debug=True, base_url="https://app.getmaxim.ai"
    )
)

logger = maxim.logger(LoggerConfig(id=log_repo_id))
llm = ChatOpenAI(api_key=openai_key, model="gpt-4o-mini")
client = MongoClient(mongo_uri, server_api=ServerApi('1'))

embeddings = OpenAIEmbeddings(
    model="text-embedding-ada-002",
    openai_api_key=openai_key
)

app = Flask(__name__)

@retrieval(name="mongo-retrieval")
def retrieve_docs(query: str):
    db= client["sample_mflix"]
    collection = db["embedded_movies"]
    query_vector= embeddings.embed_query(query)

    response = collection.aggregate([
        {
            '$vectorSearch': {
                "index": "idx_plot_embedding",
                "path": "plot_embedding",
                "queryVector": query_vector,
                "numCandidates": 50,
                "limit": 10
            }
        }
    ])
    docs = [
        {
            "Title": item.get('title', 'N/A'),
            "Plot": item.get('plot', 'N/A'),
            "Year": item.get('year', 'N/A')
        }
        for item in response
    ]
    return docs


@langchain_llm_call(name="llm-call")
def execute(query: str):
    context = retrieve_docs(query)
    messages = [
        (
            "system",
            f"You are a smart movie recommendation expert. A question will be asked to you along with relevant information. "
            f"Your task is to recommend the just title of the movie using this context: {json.dumps(context)}"
            f"Respond in proper markdown format",
        ),
        ("human", query),
    ]
    result = llm.invoke(messages, config={"callbacks": [langchain_callback()]})
    return result.content


@app.post("/chat")
@trace(logger=logger, name="movie-chat-v1")
def handler():
    print(current_trace().id)
    query = request.json["query"]
    result = execute(query)
    return jsonify({"result": result})

app.run(port=8000)