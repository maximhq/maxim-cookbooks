import {
    createCustomCombinedEvaluatorsFor,
    createDataStructure,
    Maxim,
} from "@maximai/maxim-js";
import "dotenv/config";

let apiKey: string, workspaceId: string, workflowId: string, datasetId: string;
if (!process.env.MAXIM_API_KEY)
    throw new Error("Missing MAXIM_API_KEY environment variable");
if (!process.env.MAXIM_WORKSPACE_ID)
    throw new Error("Missing MAXIM_WORKSPACE_ID environment variable");
if (!process.env.MAXIM_WORKFLOW_ID)
    throw new Error("Missing MAXIM_WORKFLOW_ID environment variable");
if (!process.env.MAXIM_DATASET_ID)
    throw new Error("Missing MAXIM_DATASET_ID environment variable");
apiKey = process.env.MAXIM_API_KEY;
workspaceId = process.env.MAXIM_WORKSPACE_ID;
workflowId = process.env.MAXIM_WORKFLOW_ID;
datasetId = process.env.MAXIM_DATASET_ID;

const maxim = new Maxim({ apiKey });

const dataStructure = createDataStructure({
    Input: "INPUT",
    "Expected Output": "EXPECTED_OUTPUT",
    Context: "VARIABLE",
});

const customCombinedProcessingEvaluator = createCustomCombinedEvaluatorsFor(
    "minimum-sentence-evaluator",
    "specialCharactersCounter",
).build<typeof dataStructure>(
    async (result, data) => {
        const response = await mockLLMEvaluationCall(result.output, data.Context);
        return {
            "minimum-sentence-evaluator": {
                score: response.missingSentenceResult.score,
                reasoning: response.missingSentenceResult.reasoning,
            },
            specialCharactersCounter: {
                score: response.specialCharactersCount,
            },
        };
    },
    {
        "minimum-sentence-evaluator": {
            onEachEntry: {
                scoreShouldBe: "=",
                value: true,
            },
            forTestrunOverall: {
                overallShouldBe: ">=",
                value: 80,
                for: "percentageOfPassedResults",
            },
        },
        specialCharactersCounter: {
            onEachEntry: {
                scoreShouldBe: ">=",
                value: 3,
            },
            forTestrunOverall: {
                overallShouldBe: ">=",
                value: 4,
                for: "average",
            },
        },
    },
);

const result = await maxim
    .createTestRun(`sdk test run on ${Date.now()}`, workspaceId)
    .withDataStructure(dataStructure)
    .withData(datasetId)
    .withWorkflowId(workflowId)
    .withEvaluators("Faithfulness", customCombinedProcessingEvaluator)
    .run();

console.log("\n\n========Test run results========");
console.log("\nFailed values: ", result.failedEntryIndices);
console.log("\nTest run link: ", result.testRunResult.link);
console.log("\nFinal result: ", result.testRunResult.result[0]);

await maxim.cleanup();

async function mockLLMEvaluationCall(output: string, context?: string | string[]) {
    await new Promise((resolve) => setTimeout(resolve, 1000));

    const specialCharactersCountInOutput =
        output.match(/[!@#$%^&*(),.?":{}|<>]/g)?.length ?? 0;

    if (context) {
        const score = output.split(".").length > 3;
        return {
            missingSentenceResult: {
                score,
                reasoning: score
                    ? "Considering context is present, the output is more than 3 sentences!"
                    : "Context is present, but the output is less than 3 sentences.",
            },
            specialCharactersCount: specialCharactersCountInOutput,
        };
    } else {
        const score = output.split(".").length > 1;
        return {
            missingSentenceResult: {
                score,
                reasoning: score
                    ? "Considering context is not present, the output is more than 1 sentence!"
                    : "The output is less than 1 sentence.",
            },
            specialCharactersCount: specialCharactersCountInOutput,
        };
    }
}
