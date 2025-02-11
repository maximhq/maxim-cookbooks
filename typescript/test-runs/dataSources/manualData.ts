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
    .withData([
        {
            Input: "Summarize the patient's condition",
            "Expected Output":
                "The patient has mild hypertension and requires daily monitoring",
            Context:
                "Blood pressure readings: 140/90, 138/88, 142/92. Patient reports occasional headaches.",
        },
        {
            Input: "What's the weather forecast?",
            "Expected Output": "Expect rain in the morning with afternoon clearing",
            Context:
                "Current conditions: Low pressure system, 85% humidity, temp dropping from 75°F to 65°F",
        },
        {
            Input: "Should we proceed with the campaign?",
            "Expected Output":
                "Yes, but adjust the budget allocation to focus on social media",
            Context:
                "Previous campaign metrics: Email open rate 2%, social media engagement 15%, PPC conversion 3%",
        },
    ])
    .withWorkflowId(workflowId)
    .withEvaluators("Faithfulness", "Semantic Similarity")
    .run();

console.log("\n\n========Test run results========");
console.log("\nFailed values: ", result.failedEntryIndices);
console.log("\nTest run link: ", result.testRunResult.link);
console.log("\nFinal result: ", result.testRunResult.result[0]);

await maxim.cleanup();
