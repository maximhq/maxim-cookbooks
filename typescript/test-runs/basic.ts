import { Maxim } from "@maximai/maxim-js";
import "dotenv/config";

// Validate required environment variables
const requiredEnvVars = {
  MAXIM_API_KEY: process.env.MAXIM_API_KEY,
  MAXIM_WORKSPACE_ID: process.env.MAXIM_WORKSPACE_ID,
  MAXIM_WORKFLOW_ID: process.env.MAXIM_WORKFLOW_ID,
  MAXIM_DATASET_ID: process.env.MAXIM_DATASET_ID,
};

for (const [key, value] of Object.entries(requiredEnvVars)) {
  if (!value) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
}

// Now we can safely assert these are strings since we validated above
const MAXIM_API_KEY = requiredEnvVars.MAXIM_API_KEY!;
const MAXIM_WORKSPACE_ID = requiredEnvVars.MAXIM_WORKSPACE_ID!;
const MAXIM_WORKFLOW_ID = requiredEnvVars.MAXIM_WORKFLOW_ID!;
const MAXIM_DATASET_ID = requiredEnvVars.MAXIM_DATASET_ID!;

// Initialize Maxim SDK
const maxim = new Maxim({ apiKey: MAXIM_API_KEY });

// Run a basic test using hosted workflow and dataset
const result = await maxim
  .createTestRun(`Basic Test Run - ${new Date().toISOString()}`, MAXIM_WORKSPACE_ID)
  .withData(MAXIM_DATASET_ID) // Use hosted dataset
  .withWorkflowId(MAXIM_WORKFLOW_ID) // Use hosted workflow
  .withEvaluators("Faithfulness", "Semantic Similarity") // Built-in evaluators
  .run();

// Display results
console.log("\n🔬 Basic Test Run Results");
console.log("=====================================");
console.log(`❌ Failed entries: ${result.failedEntryIndices.length > 0 ? result.failedEntryIndices.join(", ") : "None"}`);
console.log(`🔗 View results: ${result.testRunResult.link}`);
console.log(`📊 Summary: ${JSON.stringify(result.testRunResult.result[0], null, 2)}`);

await maxim.cleanup();
