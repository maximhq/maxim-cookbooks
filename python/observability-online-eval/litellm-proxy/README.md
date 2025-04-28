# Using Maxim for tracing all traffic from LiteLLM

## Docker setup

1. Copy `maxim_proxy_tracer.py` to your image
2. Add `maxim-py>=3.4.16` to the requirements.txt or pyproject.toml
3. Update config.yml

```yml
...
litellm_settings:
  callbacks: maxim_proxy_tracer.litellm_handler
```

4. Add following keys to .env or environment variables

```
MAXIM_API_KEY=
MAXIM_LOG_REPO_ID=
```
