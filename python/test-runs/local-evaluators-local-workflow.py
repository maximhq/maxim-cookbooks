from typing import Dict
from dotenv import dotenv_values
from maxim import Config, Maxim
from maxim.evaluators import BaseEvaluator
from maxim.models import (
    LocalEvaluatorResultParameter,
    LocalEvaluatorReturn,
    ManualData,
    PassFailCriteria,
    YieldedOutput
)
from maxim.models.evaluator import (
    PassFailCriteriaForTestrunOverall,
    PassFailCriteriaOnEachEntry,
)

config = dotenv_values()

API_KEY: str = config.get("MAXIM_API_KEY") or ""
WORKSPACE_ID: str = config.get("MAXIM_WORKSPACE_ID") or ""
WORKFLOW_ID: str = config.get("MAXIM_WORKFLOW_ID") or ""
DATASET_ID: str = config.get("MAXIM_DATASET_ID") or ""
PROMPT_VERSION_ID: str = config.get("MAXIM_PROMPT_VERSION_ID") or ""
MAXIM_UNKNOWN_WORKFLOW_ID: str = config.get("MAXIM_UNKNOWN_WORKFLOW_ID") or ""
MAXIM_INVALID_WORKFLOW_ID: str = config.get("MAXIM_INVALID_WORKFLOW_ID") or ""

maxim = Maxim(
    config=Config(
        api_key=API_KEY,
    )
)

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

class MyCustomEvaluator(BaseEvaluator):
    """
    Custom evaluator class that extends BaseEvaluator to perform custom evaluations.
    """

    def evaluate(
        self, result: LocalEvaluatorResultParameter, data: ManualData
    ) -> Dict[str, LocalEvaluatorReturn]:
        """
        You are supposed to override this function and run evaluations
        Args:
            result (LocalEvaluatorResultParameter): The result parameter containing evaluation data
            data (ManualData): The manual data to evaluate against
        Returns:
            Dict[str, LocalEvaluatorReturn]: Dictionary mapping evaluation names to score results.
        """
        return {
            "Evaluation 1": LocalEvaluatorReturn(score=1),
            "Evaluation 2": LocalEvaluatorReturn(score=False, reasoning="Just chillll"),
        }


maxim.create_test_run(name="Local workflow test run from SDK", in_workspace_id=WORKSPACE_ID).with_data(
    DATASET_ID
).with_concurrency(2).with_evaluators(
    "Bias",
    MyCustomEvaluator(
        pass_fail_criteria={
            "Evaluation 1": PassFailCriteria(
                for_testrun_overall_pass_if=PassFailCriteriaForTestrunOverall(
                    ">", 3, "average"
                ),
                on_each_entry_pass_if=PassFailCriteriaOnEachEntry(">", 1),
            ),
            "Evaluation 2": PassFailCriteria(
                for_testrun_overall_pass_if=PassFailCriteriaForTestrunOverall(
                    overall_should_be="!=", value=2, for_result="average"
                ),
                on_each_entry_pass_if=PassFailCriteriaOnEachEntry("=", True),
            ),
        }
    ),
).yields_output(run).run()
