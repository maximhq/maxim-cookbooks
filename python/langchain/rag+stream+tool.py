import os
from uuid import uuid4
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.tools import DuckDuckGoSearchRun
from maxim.maxim import Logger, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig

# Retrieve API keys and Log Repository ID from environment variables
MAXIM_API_KEY = os.getenv("MAXIM_API_KEY")
LOG_REPOSITORY_ID = os.getenv("LOG_REPOSITORY_ID") # Your Log Repository ID
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not MAXIM_API_KEY or not LOG_REPOSITORY_ID or not OPENAI_API_KEY:
    raise EnvironmentError("API keys and Log Repository ID are not set in the environment variables.")

# Set up Maxim logger configuration
logger_config = LoggerConfig(id=LOG_REPOSITORY_ID)
logger = Logger(config=logger_config, api_key=MAXIM_API_KEY, base_url="https://app.getmaxim.ai")

# Set up a unique session for logging
session_id = str(uuid4())
session_config = SessionConfig(id=session_id)
session = logger.session(session_config)

# Initialize the LangChain OpenAI model for inference (with streaming)
model = ChatOpenAI(model="gpt-4", api_key=OPENAI_API_KEY)

# Initialize the DuckDuckGo search tool
search = DuckDuckGoSearchRun()

# Function to read PDF content
def read_pdf(pdf_path):
    import fitz  # PyMuPDF for reading PDF
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

# Function to log retrieval with Maxim using traces
def log_retrieval(query, docs, trace):
    # Log the query and the documents retrieved
    trace.event(str(uuid4()), "Retrieval Query", {"query": query})
    trace.event(str(uuid4()), "Retrieved Documents", {"docs": [doc.page_content for doc in docs]})

# Function to format documents for input into the model
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# Function to perform RAG retrieval for the first query
def retrieve_and_generate(query):
    # Start a unique trace for this operation
    trace_id = str(uuid4())
    trace_config = TraceConfig(id=trace_id)
    trace = session.trace(trace_config)

    # Retrieve relevant documents from the PDF
    retrieved_docs = retriever.get_relevant_documents(query)

    # Log the retrieval in Maxim
    log_retrieval(query, retrieved_docs, trace)

    # Format the retrieved documents and prepare the prompt for OpenAI
    formatted_docs = format_docs(retrieved_docs)
    messages = [
        ("system", "You are a helpful assistant."),
        ("human", f"Here's the latest info from the document: {formatted_docs}. Now, {query}")
    ]
    
    # Get response from OpenAI model (ChatGPT)
    response = model.invoke(messages)
    response_text = response.content
    
    # Log the response to Maxim
    trace.event(str(uuid4()), "OpenAI Response", {"response_text": response_text})
    
    # End the trace after logging both retrieval and response
    trace.end()

    return response_text

# Function to perform a DuckDuckGo search using the model's response and get more context
def perform_duckduckgo_search(response_text):
    # Use the OpenAI model's response to perform a DuckDuckGo search
    search_results = search.invoke(response_text)
    return search_results

# Function to perform the second RAG query using DuckDuckGo results as context
def retrieve_and_generate_with_search(query, search_results):
    # Start a unique trace for this operation (we'll use the same trace ID from the first query)
    trace_id = str(uuid4())  # Use the same trace if you want the same trace ID for the whole session
    trace_config = TraceConfig(id=trace_id)
    trace = session.trace(trace_config)

    # Retrieve relevant documents from the PDF for the second query
    retrieved_docs = retriever.get_relevant_documents(query)

    # Log the retrieval in Maxim
    log_retrieval(query, retrieved_docs, trace)

    # Combine the DuckDuckGo search results with the retrieved documents
    search_context = "\n\n".join(search_results)
    formatted_docs = format_docs(retrieved_docs) + "\n\n" + search_context
    messages = [
        ("system", "You are a helpful assistant."),
        ("human", f"Here's additional information from the search: {search_context}. Also, here is some relevant info from the document: {formatted_docs}. Now, {query}")
    ]
    
    # Get response from OpenAI model (ChatGPT)
    response = model.invoke(messages)
    response_text = response.content
    
    # Log the response to Maxim
    trace.event(str(uuid4()), "OpenAI Response with Search", {"response_text": response_text})
    
    # End the trace after logging both retrieval and response
    trace.end()

    return response_text

# Example query
query = "What is the total amount of collected comprehensive trailer videos?"

# Run the first RAG query
first_response = retrieve_and_generate(query)

# Log the first response
print("First Response:", first_response)

# Perform DuckDuckGo search based on the first response
search_results = perform_duckduckgo_search(first_response)

# Log the search results
print("DuckDuckGo Search Results:", search_results)

# Run the second RAG query using the search results for further context
second_response = retrieve_and_generate_with_search("Based on the previous information, tell me more about the trailer videos.", search_results)

# Log the second response
print("Second Response:", second_response)
