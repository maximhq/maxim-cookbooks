from dotenv import dotenv_values
from maxim import Config, Maxim

config = dotenv_values()

API_KEY: str = config.get("MAXIM_API_KEY") or ""
WORKSPACE_ID: str = config.get("MAXIM_WORKSPACE_ID") or ""
WORKFLOW_ID: str = config.get("MAXIM_WORKFLOW_ID") or ""
DATASET_ID: str = config.get("MAXIM_DATASET_ID") or ""
PROMPT_VERSION_ID: str = config.get("MAXIM_PROMPT_VERSION_ID") or ""

maxim = Maxim(config=Config(api_key=API_KEY))

maxim.create_test_run(
    name="Basic test run from code", in_workspace_id=WORKSPACE_ID
).with_concurrency(2).with_data(DATASET_ID).with_prompt_version_id(
    PROMPT_VERSION_ID
).with_evaluators(
    "Bias", "Clarity"
).run()
