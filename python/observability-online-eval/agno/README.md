# Agno Agent

## Setup and Usage (with uv)

1. **Create a virtual environment:**

```bash
uv venv
```

2. **Activate the virtual environment:**

- On macOS/Linux:
  ```bash
  source .venv/bin/activate
  ```
- On Windows:
  ```cmd
  .venv\Scripts\activate
  ```

3. **Install dependencies (including local maxim-py):**

```bash
uv pip install --no-cache-dir .
```

4. **Run the agent:**

```bash
python agent.py
```

---

- Make sure you have [uv](https://github.com/astral-sh/uv) installed. You can install it with:
  ```bash
  curl -Ls https://astral.sh/uv/install.sh | sh
  ```
- The local maxim-py package must be present at the correct relative path (as configured in `pyproject.toml`).