import { createDataStructure, Data, Maxim } from "@maximai/maxim-js";
import "dotenv/config";
import { generateResponse } from "./utils/openai-helper.js";

// Validate required environment variables
const requiredEnvVars = {
  MAXIM_API_KEY: process.env.MAXIM_API_KEY,
  MAXIM_WORKSPACE_ID: process.env.MAXIM_WORKSPACE_ID,
  MAXIM_DATASET_ID: process.env.MAXIM_DATASET_ID,
  OPENAI_API_KEY: process.env.OPENAI_API_KEY,
};

for (const [key, value] of Object.entries(requiredEnvVars)) {
  if (!value) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
}

const MAXIM_API_KEY = requiredEnvVars.MAXIM_API_KEY!;
const MAXIM_WORKSPACE_ID = requiredEnvVars.MAXIM_WORKSPACE_ID!;
const MAXIM_DATASET_ID = requiredEnvVars.MAXIM_DATASET_ID!;

// Initialize Maxim SDK
const maxim = new Maxim({ apiKey: MAXIM_API_KEY });

// Define data structure matching your hosted dataset
const dataStructure = createDataStructure({
  Input: "INPUT",
  "Expected Output": "EXPECTED_OUTPUT",
  Context: "CONTEXT_TO_EVALUATE",
});

// Local workflow using OpenAI for intelligent processing
async function intelligentLocalWorkflow(data: Data<typeof dataStructure>) {
  const startTime = Date.now();
  const processingId = Math.random().toString(36).substr(2, 6);

  console.log(`[${processingId}] Processing: ${data.Input.substring(0, 50)}...`);

  try {
    // Handle context - convert array to string if needed
    const contextString = Array.isArray(data.Context) ? data.Context.join("\n") : data.Context;

    // Generate intelligent response using OpenAI
    const aiResponse = await generateResponse(
      data.Input,
      contextString,
      "You are a helpful AI assistant that provides accurate, well-structured responses based on the given context."
    );

    const endTime = Date.now();
    console.log(`[${processingId}] Completed in ${endTime - startTime}ms`);

    return {
      data: aiResponse.response,
      retrievedContextToEvaluate: data.Context,
      meta: {
        processingId,
        usage: aiResponse.usage,
        cost: aiResponse.cost,
        performance: {
          processingTime: endTime - startTime,
          efficiency: aiResponse.usage.latency < 2000 ? "fast" : "normal",
        },
        modelUsed: "gpt-3.5-turbo",
        workflowType: "local-intelligent",
        timestamp: new Date().toISOString(),
      },
    };
  } catch (error) {
    console.error(`[${processingId}] Failed: ${error}`);
    throw new Error(`Local workflow processing failed: ${error}`);
  }
}

console.log("🏠 Hosted Dataset + Local Workflow Example");
console.log("==========================================\n");
console.log("This example demonstrates using a hosted dataset with custom local processing logic.");
console.log("Benefits: Centralized data management + flexible custom processing\n");

// Run test with hosted dataset and local workflow
const result = await maxim
  .createTestRun(`Hosted Dataset + Local Workflow - ${new Date().toISOString()}`, MAXIM_WORKSPACE_ID)
  .withDataStructure(dataStructure)
  .withData(MAXIM_DATASET_ID) // Use hosted dataset
  .yieldsOutput(intelligentLocalWorkflow) // Custom local processing
  .withEvaluators("Bias", "Clarity")
  .withConcurrency(2) // Moderate concurrency for API calls
  .run();

// Display results
console.log("📊 Test Results");
console.log("=====================================");
console.log(`❌ Failed entries: ${result.failedEntryIndices.length > 0 ? result.failedEntryIndices.join(", ") : "None"}`);
console.log(`🔗 View results: ${result.testRunResult.link}`);
console.log(`📈 Summary: ${JSON.stringify(result.testRunResult.result[0], null, 2)}`);

console.log("\n💡 Hosted Dataset + Local Workflow Benefits:");
console.log("• Use centrally managed datasets with version control");
console.log("• Apply custom processing logic and business rules");
console.log("• Control model selection and parameters");
console.log("• Track detailed processing metadata");
console.log("• Test custom AI workflows before deployment");
console.log("• Maintain consistency across team testing");

await maxim.cleanup();
