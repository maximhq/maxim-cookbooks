FROM python:3.14-slim@sha256:c845af9399020c7e562969a13689e929074a10fd057acd1b1fad06a2fb068e97

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy configuration files first to leverage Docker cache
COPY requirements.txt config.yml ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY maxim_proxy_tracer.py ./

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application with config
CMD ["litellm", "--port", "8000", "--config", "config.yml"]
