import { Maxim } from "@maximai/maxim-js";
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

const result = await maxim
    .createTestRun(`sdk test run on ${Date.now()}`, workspaceId)
    .withData(datasetId)
    .withWorkflowId(workflowId)
    .withEvaluators("Human_Evaluator_on_Platform")
    .withHumanEvaluationConfig({
        emails: ["test@acmecorp.com"],
        instructions:
            "Please go through and evaluate only the entries that are related to customer service.",
    })
    .run();

console.log("\n\n========Test run results========");
console.log("\nFailed values: ", result.failedEntryIndices);
console.log("\nTest run link: ", result.testRunResult.link);
console.log("\nFinal result: ", result.testRunResult.result[0]);

await maxim.cleanup();
