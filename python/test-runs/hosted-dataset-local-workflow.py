from dotenv import dotenv_values
from maxim import Maxim, Config
from maxim.models import ManualData, YieldedOutput

config = dotenv_values()

API_KEY: str = config.get("MAXIM_API_KEY") or ""
WORKSPACE_ID: str = config.get("MAXIM_WORKSPACE_ID") or ""
WORKFLOW_ID: str = config.get("MAXIM_WORKFLOW_ID") or ""
DATASET_ID: str = config.get("MAXIM_DATASET_ID") or ""
PROMPT_VERSION_ID: str = config.get("MAXIM_PROMPT_VERSION_ID") or ""
MAXIM_UNKNOWN_WORKFLOW_ID: str = config.get("MAXIM_UNKNOWN_WORKFLOW_ID") or ""
MAXIM_INVALID_WORKFLOW_ID: str = config.get("MAXIM_INVALID_WORKFLOW_ID") or ""

maxim = Maxim(config=Config(api_key=API_KEY))


def run(data: ManualData):
    """
    This will contain you local workflow.
    For this cookbook, we are sending hardcoded test as output
    YieldedOutput type also supports metadata like
        - meta
            - cost
            - token usage etc.
    You can also pass context as retrieved_context_to_evaluate
    """
    print(f"processing => {data.get("Input")}")
    return YieldedOutput(data="test")

maxim.create_test_run(
    name="Local workflow test run from SDK", in_workspace_id=WORKSPACE_ID
).with_concurrency(2).with_data(DATASET_ID).yields_output(run).with_evaluators(
    "Bias", "Clarity"
).run()
