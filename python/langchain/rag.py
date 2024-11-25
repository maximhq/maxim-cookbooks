import os
from uuid import uuid4
import fitz  # PyMuPDF for reading PDF
from langchain import hub
from langchain_openai import OpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
from maxim.maxim import Logger, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig

# Retrieve API keys and Log Repository ID from environment variables
MAXIM_API_KEY = os.getenv("MAXIM_API_KEY")
LOG_REPOSITORY_ID = "your-log-id"
OPENAI_API_KEY = "your-openai-api-key"

if not MAXIM_API_KEY or not LOG_REPOSITORY_ID or not OPENAI_API_KEY:
    raise EnvironmentError("API keys and Log Repository ID are not set in the environment variables.")

# Set up Maxim logger configuration
logger_config = LoggerConfig(id=LOG_REPOSITORY_ID)
logger = Logger(config=logger_config, api_key=MAXIM_API_KEY, base_url="https://app.getmaxim.ai")

# Set up a unique session for logging
session_id = str(uuid4())
session_config = SessionConfig(id=session_id)
session = logger.session(session_config)

# Function to read PDF content
def read_pdf(pdf_path):
    doc = fitz.open(pdf_path)  # Open the PDF
    text = ""
    for page in doc:
        text += page.get_text()  # Extract text from each page
    return text

# Read the PDF content
pdf_path = "test.pdf"  # Replace with your PDF path
pdf_content = read_pdf(pdf_path)

# Split the content into chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_text(pdf_content)

# Convert each chunk into a Document object
documents = [Document(page_content=split) for split in splits]

# Initialize Chroma vector store and OpenAI embeddings
vectorstore = Chroma.from_documents(documents=documents, embedding=OpenAIEmbeddings(api_key=OPENAI_API_KEY))

# Set up the retriever
retriever = vectorstore.as_retriever()

# Initialize the LangChain OpenAI model for inference
openai_llm = OpenAI(api_key=OPENAI_API_KEY)

# Function to log retrieval with Maxim using traces
def log_retrieval(query, docs):
    # Create a unique trace ID and start the trace
    trace_id = str(uuid4())
    trace_config = TraceConfig(id=trace_id)
    trace = session.trace(trace_config)
    
    # Log the query and the documents retrieved
    trace.event(str(uuid4()), "Retrieval Query", {"query": query})
    trace.event(str(uuid4()), "Retrieved Documents", {"docs": [doc.page_content for doc in docs]})
    
    # End the trace after logging the events
    trace.end()

# Function to format documents for input into the model
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# Define the RAG chain with retrieval and OpenAI model
def run_rag_inference(query):
    # Perform the retrieval using get_relevant_documents
    retrieved_docs = retriever.get_relevant_documents(query)

    # Log the retrieval in Maxim
    log_retrieval(query, retrieved_docs)

    # Format the retrieved documents and prepare the prompt
    formatted_docs = format_docs(retrieved_docs)
    messages = [
        ("system", "You are a helpful assistant."),
        ("human", f"Here's the latest info: {formatted_docs}. Now, {query}")
    ]
    
    # Generate the response using OpenAI model
    response = openai_llm.invoke(messages)
    
    # Parse and return the response
    return response

# Example query
query = "What is the total amount of collected comprehensive trailer videos?"

# Run the RAG inference and log the process
response = run_rag_inference(query)

# Print the final response
print(response)
