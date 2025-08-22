from sqlalchemy import (
    Column,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    insert,
    inspect,
    text,
)
from maxim import Maxim
from maxim.logger.smolagents import instrument_smolagents
import os
from smolagents import OpenAIServerModel
from smolagents import CodeAgent


engine = create_engine("sqlite:///:memory:")
metadata_obj = MetaData()

# create receipts SQL table
table_name = "receipts"
receipts = Table(
    table_name,
    metadata_obj,
    Column("receipt_id", Integer, primary_key=True),
    Column("customer_name", String(16), primary_key=True),
    Column("price", Float),
    Column("tip", Float),
)
metadata_obj.create_all(engine)

rows = [
    {"receipt_id": 1, "customer_name": "Alan Payne", "price": 12.06, "tip": 1.20},
    {"receipt_id": 2, "customer_name": "Alex Mason", "price": 23.86, "tip": 0.24},
    {"receipt_id": 3, "customer_name": "Woodrow Wilson", "price": 53.43, "tip": 5.43},
    {"receipt_id": 4, "customer_name": "Margaret James", "price": 21.11, "tip": 1.00},
]
for row in rows:
    stmt = insert(receipts).values(**row)
    with engine.begin() as connection:
        connection.execute(stmt)

inspector = inspect(engine)
columns_info = [(col["name"], col["type"]) for col in inspector.get_columns("receipts")]

table_description = "Columns:\n" + "\n".join([f"  - {name}: {col_type}" for name, col_type in columns_info])
print(table_description)

from smolagents import tool
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

instrument_smolagents(Maxim().logger())


@tool
def sql_engine(query: str) -> str:
    """
    Allows you to perform SQL queries on the table. Returns a string representation of the result.
    The table is named 'receipts'. Its description is as follows:
        Columns:
        - receipt_id: INTEGER
        - customer_name: VARCHAR(16)
        - price: FLOAT
        - tip: FLOAT

    Args:
        query: The query to perform. This should be correct SQL.
    """
    output = ""
    with engine.connect() as con:
        rows = con.execute(text(query))
        for row in rows:
            output += "\n" + str(row)
    return output


try:
    # Preferred (per docs/examples)
    from smolagents import InferenceClientModel as HFModel
except Exception:  # pragma: no cover - fallback for older/newer versions
    from smolagents import HfApiModel as HFModel  # type: ignore

from smolagents import CodeAgent


agent = CodeAgent(
    tools=[sql_engine],
    model=OpenAIServerModel(
        model_id="gpt-4o-mini",               # or "gpt-4o"
        api_key=os.environ["OPENAI_API_KEY"], # uses .env via load_dotenv()
        api_base="https://api.openai.com/v1", # optional, default works
    ),
)

print(
    agent.run("Can you give me the name of the client who got the most expensive receipt?")
)

