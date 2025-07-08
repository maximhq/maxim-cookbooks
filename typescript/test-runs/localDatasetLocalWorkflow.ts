import { createDataStructure, Data, Maxim } from "@maximai/maxim-js";
import "dotenv/config";
import { generateResponse } from "./utils/openai-helper.js";

// Validate required environment variables
const requiredEnvVars = {
  MAXIM_API_KEY: process.env.MAXIM_API_KEY,
  MAXIM_WORKSPACE_ID: process.env.MAXIM_WORKSPACE_ID,
  OPENAI_API_KEY: process.env.OPENAI_API_KEY,
};

for (const [key, value] of Object.entries(requiredEnvVars)) {
  if (!value) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
}

const MAXIM_API_KEY = requiredEnvVars.MAXIM_API_KEY!;
const MAXIM_WORKSPACE_ID = requiredEnvVars.MAXIM_WORKSPACE_ID!;

// Initialize Maxim SDK
const maxim = new Maxim({ apiKey: MAXIM_API_KEY });

// Define data structure for HR policy Q&A
const dataStructure = createDataStructure({
  Input: "INPUT",
  "Expected Output": "EXPECTED_OUTPUT",
  Context: "CONTEXT_TO_EVALUATE",
});

// HR policy dataset for employee support bot testing
const hrPolicyDataset = [
  {
    Input: "What is the company's remote work policy?",
    "Expected Output":
      "Employees can work remotely up to 3 days per week with manager approval. Full remote work requires special approval and is evaluated case-by-case.",
    Context: "HR Policy 4.2: Remote Work Guidelines - Hybrid work model with flexibility for individual needs and business requirements.",
  },
  {
    Input: "How much paid time off do I get as a new employee?",
    "Expected Output":
      "New employees receive 15 days of PTO annually, which increases to 20 days after 2 years and 25 days after 5 years of service.",
    Context: "Benefits Package: Paid Time Off accrual schedule based on tenure with additional sick leave and personal days.",
  },
  {
    Input: "What is the process for reporting workplace harassment?",
    "Expected Output":
      "Report incidents immediately to HR or your manager. You can also use the anonymous hotline at 1-800-ETHICS or submit through the employee portal.",
    Context: "Employee Code of Conduct: Zero tolerance policy with multiple reporting channels to ensure safe workplace environment.",
  },
  {
    Input: "Can I change my health insurance plan outside open enrollment?",
    "Expected Output":
      "Health insurance changes are only allowed during open enrollment unless you have a qualifying life event such as marriage, birth, or job change.",
    Context:
      "Benefits Administration: Annual open enrollment period with exceptions for qualifying life events as defined by IRS regulations.",
  },
  {
    Input: "What training is required for new managers?",
    "Expected Output":
      "New managers must complete a 40-hour leadership training program within 90 days, including modules on performance management, team building, and compliance.",
    Context:
      "Professional Development: Comprehensive management training program with ongoing education requirements and mentorship opportunities.",
  },
];

// Intelligent HR workflow using OpenAI
async function hrPolicyWorkflow(data: Data<typeof dataStructure>) {
  const startTime = Date.now();
  const sessionId = `hr_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`;

  console.log(`[${sessionId}] Processing HR query: ${data.Input}`);

  try {
    // Handle context properly
    const contextString = Array.isArray(data.Context) ? data.Context.join("\n") : data.Context;

    // Generate HR-focused response
    const aiResponse = await generateResponse(
      data.Input,
      contextString,
      "You are a helpful HR assistant providing accurate, policy-based answers to employee questions. Be professional, clear, and reference relevant policies when appropriate."
    );

    const endTime = Date.now();
    console.log(`[${sessionId}] HR response generated in ${endTime - startTime}ms`);

    return {
      data: aiResponse.response,
      retrievedContextToEvaluate: data.Context,
      meta: {
        sessionId,
        usage: aiResponse.usage,
        cost: aiResponse.cost,
        hrSpecific: {
          queryType: categorizeHRQuery(data.Input),
          policyReferenced: extractPolicyReference(contextString),
          responseType: "policy-based",
        },
        performance: {
          processingTime: endTime - startTime,
          responseLength: aiResponse.response.length,
          efficiency: aiResponse.usage.latency < 2500 ? "optimal" : "acceptable",
        },
        modelUsed: "gpt-3.5-turbo",
        workflowType: "hr-policy-assistant",
        timestamp: new Date().toISOString(),
      },
    };
  } catch (error) {
    console.error(`[${sessionId}] HR workflow failed: ${error}`);
    throw new Error(`HR policy workflow processing failed: ${error}`);
  }
}

// Helper functions for HR-specific analysis
function categorizeHRQuery(input: string): string {
  const inputLower = input.toLowerCase();

  if (inputLower.includes("remote") || inputLower.includes("work from home")) return "remote-work";
  if (inputLower.includes("pto") || inputLower.includes("time off") || inputLower.includes("vacation")) return "time-off";
  if (inputLower.includes("harassment") || inputLower.includes("report") || inputLower.includes("ethics")) return "conduct";
  if (inputLower.includes("insurance") || inputLower.includes("benefits") || inputLower.includes("health")) return "benefits";
  if (inputLower.includes("training") || inputLower.includes("manager") || inputLower.includes("development")) return "training";

  return "general";
}

function extractPolicyReference(context: string): string {
  if (!context) return "none";

  const policyMatch = context.match(/(?:Policy|Code|Guidelines?|Package)\s+[\d.]+/i);
  return policyMatch ? policyMatch[0] : "general-policy";
}

console.log("👥 Local Dataset + Local Workflow: HR Policy Assistant");
console.log("=====================================================\n");
console.log("This example demonstrates complete local control over both data and processing.");
console.log("Perfect for: Custom domains, proprietary data, specialized workflows\n");

// Run completely local test
const result = await maxim
  .createTestRun(`HR Policy Assistant - ${new Date().toISOString()}`, MAXIM_WORKSPACE_ID)
  .withDataStructure(dataStructure)
  .withData(hrPolicyDataset) // Local dataset
  .yieldsOutput(hrPolicyWorkflow) // Local AI workflow
  .withEvaluators("Faithfulness", "Semantic Similarity")
  .withConcurrency(3) // Can handle higher concurrency with local control
  .run();

// Display comprehensive results
console.log("📊 HR Policy Assistant Test Results");
console.log("=====================================");
console.log(`📋 Total HR scenarios tested: ${hrPolicyDataset.length}`);
console.log(`📝 Query types: ${[...new Set(hrPolicyDataset.map(d => categorizeHRQuery(d.Input)))].join(", ")}`);
console.log(`❌ Failed entries: ${result.failedEntryIndices.length > 0 ? result.failedEntryIndices.join(", ") : "None"}`);
console.log(`🔗 View detailed results: ${result.testRunResult.link}`);
console.log(`📈 Summary: ${JSON.stringify(result.testRunResult.result[0], null, 2)}`);

console.log("\n🎯 Local Dataset + Local Workflow Benefits:");
console.log("• Complete control over test data and processing logic");
console.log("• Perfect for proprietary or sensitive data");
console.log("• Rapid iteration and testing of custom workflows");
console.log("• Domain-specific optimization and customization");
console.log("• No dependency on external hosted services");
console.log("• Ideal for specialized use cases and business logic");

await maxim.cleanup();
