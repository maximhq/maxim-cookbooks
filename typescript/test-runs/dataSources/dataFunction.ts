import { createDataStructure, Maxim } from "@maximai/maxim-js";
import "dotenv/config";

let apiKey: string, workspaceId: string, workflowId: string;
if (!process.env.MAXIM_API_KEY)
    throw new Error("Missing MAXIM_API_KEY environment variable");
if (!process.env.MAXIM_WORKSPACE_ID)
    throw new Error("Missing MAXIM_WORKSPACE_ID environment variable");
if (!process.env.MAXIM_WORKFLOW_ID)
    throw new Error("Missing MAXIM_WORKFLOW_ID environment variable");
apiKey = process.env.MAXIM_API_KEY;
workspaceId = process.env.MAXIM_WORKSPACE_ID;
workflowId = process.env.MAXIM_WORKFLOW_ID;

const maxim = new Maxim({ apiKey });

const dataStructure = createDataStructure({
    Input: "INPUT",
    "Expected Output": "EXPECTED_OUTPUT",
    Context: "VARIABLE",
});

const result = await maxim
    .createTestRun(`sdk test run on ${Date.now()}`, workspaceId)
    .withDataStructure(dataStructure)
    // OR
    // .withDataStructure({
    //     Input: "INPUT",
    //     "Expected Output": "EXPECTED_OUTPUT",
    //     Context: "VARIABLE",
    // })
    .withData((page) => {
        // this is just a mock, you can replace it with your own API call / logic that can use paging to fetch data
        const PAGE_SIZE = 5;
        if (page < 3) {
            return Array.from({ length: PAGE_SIZE }, (_, i) => i).map((i) => ({
                Input: `Input ${page * PAGE_SIZE + i}`,
                "Expected Output": `Expected Output ${page * PAGE_SIZE + i}`,
                Context: `Context ${page * PAGE_SIZE + i}`,
            }));
        }
        // returning null will be treated as the end of the data
        return null;
    })
    .withWorkflowId(workflowId)
    .withEvaluators("Faithfulness", "Semantic Similarity")
    .run();

console.log("\n\n========Test run results========");
console.log("\nFailed values: ", result.failedEntryIndices);
console.log("\nTest run link: ", result.testRunResult.link);
console.log("\nFinal result: ", result.testRunResult.result[0]);

await maxim.cleanup();
