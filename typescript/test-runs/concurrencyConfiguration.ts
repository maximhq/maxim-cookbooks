import { createDataStructure, Data, Maxim } from "@maximai/maxim-js";
import "dotenv/config";
import { generateResponse } from "./utils/openai-helper.js";

// Validate required environment variables
const requiredEnvVars = {
  MAXIM_API_KEY: process.env.MAXIM_API_KEY,
  MAXIM_WORKSPACE_ID: process.env.MAXIM_WORKSPACE_ID,
  MAXIM_WORKFLOW_ID: process.env.MAXIM_WORKFLOW_ID,
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
const MAXIM_WORKFLOW_ID = requiredEnvVars.MAXIM_WORKFLOW_ID!;
const MAXIM_DATASET_ID = requiredEnvVars.MAXIM_DATASET_ID!;

// Initialize Maxim SDK
const maxim = new Maxim({ apiKey: MAXIM_API_KEY });

const dataStructure = createDataStructure({
  Input: "INPUT",
  "Expected Output": "EXPECTED_OUTPUT",
  Context: "CONTEXT_TO_EVALUATE",
});

console.log("🚀 Concurrency Configuration Examples");
console.log("=====================================\n");

// Example 1: Sequential processing (concurrency = 1)
console.log("📌 Example 1: Sequential Processing (Concurrency = 1)");
console.log("Best for: Rate-limited APIs, debugging, careful processing\n");

const sequentialResult = await maxim
  .createTestRun(`Sequential Processing - ${new Date().toISOString()}`, MAXIM_WORKSPACE_ID)
  .withDataStructure(dataStructure)
  .withData(MAXIM_DATASET_ID)
  .withWorkflowId(MAXIM_WORKFLOW_ID)
  .withEvaluators("Faithfulness", "Semantic Similarity")
  .withConcurrency(1) // Process one at a time
  .run();

console.log(`✅ Sequential completed. Failed: ${sequentialResult.failedEntryIndices.length}`);
console.log(`🔗 Results: ${sequentialResult.testRunResult.link}\n`);

// Example 2: Moderate concurrency (concurrency = 3)
console.log("📌 Example 2: Moderate Concurrency (Concurrency = 3)");
console.log("Best for: Balanced performance and safety, production workloads\n");

const moderateResult = await maxim
  .createTestRun(`Moderate Concurrency - ${new Date().toISOString()}`, MAXIM_WORKSPACE_ID)
  .withDataStructure(dataStructure)
  .withData(MAXIM_DATASET_ID)
  .withWorkflowId(MAXIM_WORKFLOW_ID)
  .withEvaluators("Faithfulness", "Semantic Similarity")
  .withConcurrency(3) // Process 3 in parallel
  .run();

console.log(`✅ Moderate concurrency completed. Failed: ${moderateResult.failedEntryIndices.length}`);
console.log(`🔗 Results: ${moderateResult.testRunResult.link}\n`);

// Example 3: Local workflow with high concurrency
console.log("📌 Example 3: Local Workflow with High Concurrency (Concurrency = 5)");
console.log("Best for: Local processing, robust APIs, maximum speed\n");

async function intelligentProcessor(data: Data<typeof dataStructure>) {
  const startTime = Date.now();
  const processingId = Math.random().toString(36).substr(2, 6);

  console.log(`[${processingId}] Processing: ${data.Input.substring(0, 30)}...`);

  try {
    // Handle context - convert array to string if needed
    const contextString = Array.isArray(data.Context) ? data.Context.join("\n") : data.Context;

    const aiResponse = await generateResponse(
      data.Input,
      contextString,
      "You are a helpful assistant providing concise, accurate responses."
    );

    const endTime = Date.now();
    console.log(`[${processingId}] Completed in ${endTime - startTime}ms`);

    return {
      data: aiResponse.response,
      retrievedContextToEvaluate: data.Context,
      meta: {
        ...aiResponse.usage,
        cost: aiResponse.cost,
        processingId,
        modelUsed: "gpt-3.5-turbo",
        processingTime: endTime - startTime,
      },
    };
  } catch (error) {
    console.error(`[${processingId}] Failed: ${error}`);
    throw error;
  }
}

const highConcurrencyResult = await maxim
  .createTestRun(`High Concurrency Local - ${new Date().toISOString()}`, MAXIM_WORKSPACE_ID)
  .withDataStructure(dataStructure)
  .withData(MAXIM_DATASET_ID)
  .yieldsOutput(intelligentProcessor)
  .withEvaluators("Faithfulness", "Semantic Similarity")
  .withConcurrency(5) // High parallel processing
  .run();

console.log(`✅ High concurrency completed. Failed: ${highConcurrencyResult.failedEntryIndices.length}`);
console.log(`🔗 Results: ${highConcurrencyResult.testRunResult.link}\n`);

// Summary and best practices
console.log("📋 Concurrency Best Practices");
console.log("=====================================");
console.log("• Concurrency 1:     Sequential - safest for rate-limited APIs");
console.log("• Concurrency 2-3:   Moderate - good balance of speed and safety");
console.log("• Concurrency 4-5:   High - fastest, check API rate limits");
console.log("• Concurrency 6+:    Very high - use only with robust APIs");
console.log("\n💡 Tips:");
console.log("• Start with moderate concurrency (2-3) and adjust based on results");
console.log("• Higher concurrency = faster completion but more API load");
console.log("• Monitor for rate limit errors and reduce concurrency if needed");
console.log("• Local workflows can typically handle higher concurrency than hosted APIs");

await maxim.cleanup();
