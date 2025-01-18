import os

import pandas as pd
import weaviate
import weaviate.classes as wvc
from tqdm import tqdm
from weaviate.collections.classes.config import (Configure, VectorDistances,
                                                 VectorIndexConfigDynamic,
                                                 VectorizerConfig)

import dotenv

dotenv.load_dotenv()

openai_key = os.environ.get("OPENAI_API_KEY", "")
weaviate_url = os.environ.get("WEAVIATE_URL", "")
weaviate_key = os.environ.get("WEAVIATE_API_KEY", "")


# Setting up client
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=weaviate.auth.AuthApiKey(api_key=weaviate_key),
    headers={
        "X-OpenAI-Api-Key": openai_key,  # Replace with your OpenAI key
    },
)

# Load and prepare dataset
df = pd.read_csv(
    "movie_data.csv",
    usecols=[
        "id",
        "Name",
        "PosterLink",
        "Genres",
        "Actors",
        "Director",
        "Description",
        "DatePublished",
        "Keywords",
    ],
    parse_dates=["DatePublished"],
    on_bad_lines="skip",
    low_memory=False,
    skip_blank_lines=True,
    verbose=True,
)
df["year"] = df["DatePublished"].dt.year.fillna(0).astype(int)
df.drop(["DatePublished"], axis=1, inplace=True)
df = df[df.year > 1970]

# Plot dataset
plots = pd.read_csv("wiki_movie_plots_deduped.csv")
plots = plots[plots["Release Year"] > 1970]
plots = plots[plots.duplicated(subset=["Title", "Release Year", "Plot"]) == False]
plots = plots[plots.duplicated(subset=["Title", "Release Year"]) == False]
plots = plots[["Title", "Plot", "Release Year"]]

plots.columns = ["Name", "Plot", "year"]

# Merge
df = df.merge(plots, on=["Name", "year"], how="left").fillna("")
df.reset_index(drop=True, inplace=True)

collection_name = "Awesome_moviate_movies"

# Checking if Movies schema already exists, then delete it
if client.collections.exists(collection_name):
    client.collections.delete(collection_name)

# Create collection with proper configuration
collection = client.collections.create(
    name=collection_name,
    description="A collection of movies since 1970.",
    vectorizer_config=Configure.Vectorizer.text2vec_openai(
        model="text-embedding-3-small",
        model_version="3",
        type_="text",        
        vectorize_collection_name=False
    ),
    vector_index_config=Configure.VectorIndex.hnsw(
        distance_metric=VectorDistances.COSINE
    ),
    properties=[
        wvc.config.Property(
            name="movie_id",
            data_type=wvc.config.DataType.NUMBER,
            description="The id of the movie",
            skip_vectorization=True
        ),
        wvc.config.Property(
            name="title",
            data_type=wvc.config.DataType.TEXT,
            description="The name of the movie",
            skip_vectorization=True
        ),
        wvc.config.Property(
            name="year",
            data_type=wvc.config.DataType.NUMBER,
            description="The year in which movie was published",
            skip_vectorization=True
        ),
        wvc.config.Property(
            name="poster_link",
            data_type=wvc.config.DataType.TEXT,
            description="The poster link of the movie",
            skip_vectorization=True
        ),
        wvc.config.Property(
            name="genres",
            data_type=wvc.config.DataType.TEXT,
            description="The genres of the movie",
            skip_vectorization=True
        ),
        wvc.config.Property(
            name="actors",
            data_type=wvc.config.DataType.TEXT,
            description="The actors of the movie",
            skip_vectorization=True
        ),
        wvc.config.Property(
            name="director",
            data_type=wvc.config.DataType.TEXT,
            description="Director of the movie",
            skip_vectorization=True
        ),
        wvc.config.Property(
            name="description",
            data_type=wvc.config.DataType.TEXT,
            description="overview of the movie"
        ),
        wvc.config.Property(
            name="Plot",
            data_type=wvc.config.DataType.TEXT,
            description="Plot of the movie from Wikipedia"
        ),
        wvc.config.Property(
            name="keywords",
            data_type=wvc.config.DataType.TEXT,
            description="main keywords of the movie"
        )
    ]
)

data_rows = []
# Importing the data
for i in tqdm(range(len(df))):
    item = df.iloc[i]

    movie_object = {
        "movie_id": float(item["id"]),
        "title": str(item["Name"]).lower(),
        "year": int(item["year"]),
        "poster_link": str(item["PosterLink"]),
        "genres": str(item["Genres"]),
        "actors": str(item["Actors"]).lower(),
        "director": str(item["Director"]).lower(),
        "description": str(item["Description"]),
        "plot": str(item["Plot"]),
        "keywords": str(item["Keywords"]),
    }
    data_rows.append(movie_object)

try:
    with collection.batch.dynamic() as batch:
        for data_row in data_rows:
            batch.add_object(
                properties=data_row,
            )            
        batch.flush()
except BaseException as error:
    print("Import Failed at: ", i)
    print("An exception occurred: {}".format(error))
    # Stop the import on error    


client.close()
