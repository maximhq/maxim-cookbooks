import {
    createDataStructure,
    Data,
    LocalEvaluationResult,
    Maxim,
    TestRunLogger,
    YieldedOutput,
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

class CustomLogger implements TestRunLogger<typeof dataStructure> {
    error(message: string) {
        console.error("[ERROR]", message);
    }
    info(message: string) {
        console.info("[INFO]", message);
    }
    processed(
        message: string,
        data: {
            datasetEntry: Data<typeof dataStructure>;
            output?: YieldedOutput;
            evaluationResults?: LocalEvaluationResult[];
        },
    ) {
        console.log("[PROCESSED]", message);
        // OR
        // console.log("[ENTRY]", data.datasetEntry);
        // console.log("[OUTPUT]", data.output);
        // console.log("\n=====EVALUATION RESULTS=====\n", data.evaluationResults);
    }
}

const result = await maxim
    .createTestRun(`sdk test run on ${Date.now()}`, workspaceId)
    .withDataStructure(dataStructure)
    .withData(datasetId)
    .withWorkflowId(workflowId)
    .withEvaluators("Faithfulness", "Semantic Similarity")
    .withLogger(new CustomLogger())
    // OR
    // .withLogger({
    //     info(message) {
    //         console.info('[INFO] ', message);
    //     },
    //     error(message) {
    //         console.error('[ERROR] ', message);
    //     },
    //     processed(message, data) {
    //         console.info('[PROCESSED] ', message);
    //         // OR
    //         // console.log("[ENTRY]", data.datasetEntry);
    //         // console.log("[OUTPUT]", data.output);
    //         // console.log("\n=====EVALUATION RESULTS=====\n", data.evaluationResults);
    //     },
    // })
    .run();

console.log("\n\n========Test run results========");
console.log("\nFailed values: ", result.failedEntryIndices);
console.log("\nTest run link: ", result.testRunResult.link);
console.log("\nFinal result: ", result.testRunResult.result[0]);

await maxim.cleanup();
