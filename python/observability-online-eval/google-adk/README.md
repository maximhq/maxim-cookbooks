# Google ADK Financial Advisor with Maxim Instrumentation

Multi-agent system for financial analysis built with Google's Agent Development Kit (ADK) and instrumented with Maxim.

## Environment Setup

Create a `.env` file in the `financial-advisor` directory:

```bash
# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_API_KEY=your-google-api-key
GOOGLE_GENAI_USE_VERTEXAI=False

# Maxim
MAXIM_API_KEY=your-maxim-api-key
MAXIM_LOG_REPO_ID=your-log-repository-id
```

## Run Commands

```bash
cd financial-advisor
uv sync
adk run financial_advisor
```

## Additional Commands

```bash
# Web UI
adk web

# Tests
uv run pytest tests

# Evaluations
uv run pytest eval
```

