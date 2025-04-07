# Maxim Cookbooks

Maxim Cookbooks is a collection of example projects demonstrating how to integrate [**Maxim**](https://www.getmaxim.ai/) for AI agent **observability**, **auto-evaluation**, **prompt management**, **simulation**, and **test run workflows** across a variety of popular frameworks and SDKs.

Maxim is an end-to-end AI evaluation and observability platform that empowers modern AI teams to ship agents with quality, reliability, and speed.

## 🔧 What’s in this Repository?

This repository provides ready-to-run **code samples**, **notebooks**, and **configuration files** to help you quickly understand how to:

- Integrate **observability and tracing** in agents.
- Perform **automated evaluations** on agent outputs.
- Manage and **retrieve prompts** via Maxim APIs.
- **Simulate** agent behavior with pre-defined workflows.
- Run **offline and hosted test runs** for evaluation and regression tracking.

## 👇Directory Structure

```jsx
maxim-cookbooks/
├── .github/                 # GitHub action workflows
├── .vscode/                # Editor configuration
├── go/
│   └── observability-online-eval/
│       ├── azure/
│       ├── bedrock/
│       └── openai/
├── java/                   # (WIP or initial structure)
├── python/
│   ├── observability-online-eval/
│   ├── prompt-management/
│   ├── simulation/
│   └── test-runs/
├── typescript/
│   ├── langchain/
│   ├── langgraph/customer-support/
│   ├── llamaindex/
│   └── test-runs/
├── README.md

```

## 🧩 Some Use Case Examples

### 1. Observability in Agents

### Crew AI Agent with Maxim

Add observability to a [Crew AI agent](https://github.com/maximhq/maxim-cookbooks/blob/main/python/observability-online-eval/crew-ai/cooking-agent/agent.py):

```python
from maxim import Config, Maxim
from maxim import logger
from maxim.logger import LoggerConfig
from maxim.maxim import LoggerConfig
from maxim.logger.langchain import MaximLangchainTracer

maxim_api_key = os.environ.get("MAXIM_API_KEY", "")
maxim_base_url = os.environ.get("MAXIM_BASE_URL", "")
maxim_repo_id = os.environ.get("MAXIM_LOG_REPO_ID", "")

logger = Maxim(
    Config(api_key=maxim_api_key, debug=True, base_url=maxim_base_url)
).logger(LoggerConfig(id=maxim_repo_id))

callback = MaximLangchainTracer(logger=logger,metadata=None)

... your agent implementation

```

### React-based Agent with Maxim

### ⚡ React-style Agent with Maxim Observability

Want to track every step of a Reasoning Loop (Thought → Action → Observation → Answer)? Here’s a minimal version using Maxim SDK:

```jsx
from maxim.maxim import Maxim, Config, LoggerConfig
from maxim.logger.components.session import SessionConfig
from maxim.logger.components.trace import TraceConfig
from maxim.logger.components.span import SpanConfig
import os, re
from uuid import uuid4

# Setup Maxim
maxim = Maxim(Config(apiKey=os.environ["MAXIM_API_KEY"]))
logger = maxim.logger(LoggerConfig(id=os.environ["MAXIM_LOG_REPO"]))
session = logger.session(SessionConfig(id=uuid4().hex))
trace = session.trace(TraceConfig(id=uuid4().hex))

# Simple tools
def wikipedia(query): return f"Fetched wiki for: {query}"
def calculate(expr): return eval(expr)

# Reasoning loop
query = "What is 4 * (Saturn's ring count)?"
agent_thoughts = [
    ("Thought", "I should look up how many rings Saturn has."),
    ("Action", "wikipedia: Saturn rings"),
    ("Observation", "Saturn has 7 main ring groups."),
    ("Thought", "Now I can calculate 4 * 7."),
    ("Action", "calculate: 4 * 7"),
    ("Observation", "28"),
    ("Answer", "28")
]

for i, (step, content) in enumerate(agent_thoughts, 1):
    span = trace.span(SpanConfig(id=uuid4().hex, name=f"{step} {i}"))
    span.event(str(uuid4()), f"{step}: {content}", {})
    if step == "Action":
        if "wikipedia" in content:
            span.event(str(uuid4()), "Tool Used: Wikipedia", {})
        elif "calculate" in content:
            span.event(str(uuid4()), "Tool Used: Calculator", {})

print("✔ Logged agent's entire reasoning trace to Maxim.")

```

This example tracks:

- Every agent step (`Thought`, `Action`, `Observation`, `Answer`)
- Tool usage events
- Full trace within a Maxim session

📎 See the full version [here](https://github.com/maximhq/maxim-cookbooks/blob/main/python/observability-online-eval/re-ACT-agent/python-agent.ipynb)

---

### 2. Prompt Management with Maxim

### Retrieve and Run Prompts

Use Maxim to retrieve prompts dynamically and execute agents with those prompts:

📎 [View notebook](https://github.com/maximhq/maxim-cookbooks/blob/main/python/prompt-management/retrieve_prompt_and_run.ipynb)

```python
api_key = os.environ["MAXIM_API_KEY"]
prompt_id = os.environ["PROMPT_ID"]

from maxim import Config, Maxim

# setting up maxim
config = Config(api_key=api_key, prompt_management=True)

from maxim.models import QueryBuilder

env = "prod"
tenantId = "123"
def getPrompt():    
    print(f"Getting prompt for env {env}")
    rule = (
        QueryBuilder()
        .and_()
        .deployment_var("Environment", env)        
        .deployment_var("TenantID", tenantId, False)   
        .build()
    )
    return maxim.get_prompt(prompt_id, rule=rule)

```

### Proxy Prompts using Bifrost

Enable proxy-based prompt execution using Maxim’s Bifrost integration:

📎 [Proxy prompts example](https://github.com/maximhq/maxim-cookbooks/blob/main/python/prompt-management/proxy_prompts_via_maxim.ipynb)

---

### 3. Simulation Workflow

Use simulation workflows to model agent behavior in multi-turn settings or to evaluate multiple edge cases in one go:

📎 [Simulation example](https://github.com/maximhq/maxim-cookbooks/blob/main/python/simulation/simulation-workflow.md)

Supports:

- Custom `.ipynb` or `.py` simulation flows
- Integrated eval metrics logging
- Scenario coverage and variations

---

### 4. Test Runs

Maxim makes it easy to set up **test runs** using datasets, prompt versions, and workflows—either hosted or fully local. Below are simplified and categorized examples you can run directly with the SDK.

Basic Hosted Test Run

Run a test using:

- Hosted prompt version
- Uploaded dataset
- Built-in evaluators like Bias, Clarity, etc.

```python
from dotenv import dotenv_values
from maxim import Config, Maxim

config = dotenv_values()
maxim = Maxim(config=Config(api_key=config["MAXIM_API_KEY"]))

maxim.create_test_run(
    name="Hosted test run",
    in_workspace_id=config["MAXIM_WORKSPACE_ID"]
).with_concurrency(2).with_data(
    config["MAXIM_DATASET_ID"]
).with_prompt_version_id(
    config["MAXIM_PROMPT_VERSION_ID"]
).with_evaluators(
    "Bias", "Clarity"
).run()
```

Local Workflow Test Run

Run a test where the **workflow is defined in code** using `yields_output`.

```python

from maxim.models import ManualData, YieldedOutput

def run(data: ManualData):
    # Your custom inference logic here
    return YieldedOutput(data="test response")

maxim.create_test_run(
    name="Local workflow run",
    in_workspace_id=config["MAXIM_WORKSPACE_ID"]
).with_concurrency(2).with_data(
    config["MAXIM_DATASET_ID"]
).yields_output(
    run
).with_evaluators(
    "Bias", "Clarity"
).run()

```

### 🧪 Test Run Types Supported

| Type | Description |
| --- | --- |
| **Hosted Prompt Version** | Use a versioned prompt deployed via Maxim |
| **Local Workflow** | Define inference logic in Python, pass via SDK |
| **Local Dataset** | Inline datasets for ad-hoc testing |
| **Hosted Dataset** | Use Maxim dashboard to manage your test datasets |

### Notebooks & Examples

| Notebook | Use Case |
| --- | --- |
| [`basic-with-prompt-version.ipynb`](https://www.notion.so/maximai/python/test-runs/basic-with-prompt-version.ipynb) | Hosted Prompt + Dataset Run |
| `local-evaluators.ipynb` | SDK workflow test |
| `local-dataset-local-workflow.ipynb` | Local workflow + inline dataset |

## 🔗 Resources

| Resource | Link |
| --- | --- |
| Maxim Platform | [getmaxim.ai](https://www.getmaxim.ai/) |
| Maxim Docs | https://www.getmaxim.ai/docs |
| Maxim SDK (Python) | https://pypi.org/project/maxim-py/ |
| GitHub Organization | [github.com/maximhq](https://github.com/maximhq) |
| Community & Support | Join Slack |

## 🤝 Contribute

We welcome your PRs to:

- Add new agent framework integrations (LangGraph, Claude, etc.)
- Expand test coverage
- Improve observability examples
- Add tutorials for enterprise usage
