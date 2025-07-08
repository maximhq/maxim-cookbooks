import { createCustomEvaluator, createDataStructure, Data, Maxim } from "@maximai/maxim-js";
import "dotenv/config";

let apiKey: string, workspaceId: string, datasetId: string;
if (!process.env.MAXIM_API_KEY) throw new Error("Missing MAXIM_API_KEY environment variable");
if (!process.env.MAXIM_WORKSPACE_ID) throw new Error("Missing MAXIM_WORKSPACE_ID environment variable");
if (!process.env.MAXIM_DATASET_ID) throw new Error("Missing MAXIM_DATASET_ID environment variable");
apiKey = process.env.MAXIM_API_KEY;
workspaceId = process.env.MAXIM_WORKSPACE_ID;
datasetId = process.env.MAXIM_DATASET_ID;

const maxim = new Maxim({ apiKey });

const dataStructure = createDataStructure({
  Input: "INPUT",
  "Expected Output": "EXPECTED_OUTPUT",
  Context: "CONTEXT_TO_EVALUATE",
});

// Define local workflow function
async function localWorkflow(data: Data<typeof dataStructure>) {
  const startTime = Date.now();
  console.log(`Processing: ${data.Input}`);

  // Simulate AI processing
  await new Promise(resolve => setTimeout(resolve, 600));

  // Mock intelligent response generation
  const inputLower = data.Input.toLowerCase();
  let response: string;

  if (inputLower.includes("summarize") || inputLower.includes("summary")) {
    response = `Summary: ${data.Context ? Array.isArray(data.Context) ? data.Context.join("\n").substring(0, 100) : data.Context.substring(0, 100) : "Based on available information"}...`;
  } else if (inputLower.includes("explain") || inputLower.includes("what")) {
    response = `Explanation: ${data.Input} can be understood as follows based on the provided context.`;
  } else if (inputLower.includes("compare") || inputLower.includes("vs")) {
    response = "Comparison analysis shows similarities and differences between the mentioned elements.";
  } else {
    response = `Response to "${data.Input}": Based on the available context, here is the relevant information.`;
  }

  const endTime = Date.now();

  return {
    data: response,
    retrievedContextToEvaluate: data.Context,
    meta: {
      usage: {
        completionTokens: response.split(" ").length,
        promptTokens: data.Input.split(" ").length,
        totalTokens: response.split(" ").length + data.Input.split(" ").length,
        latency: endTime - startTime,
      },
      cost: {
        input: 0.03 * data.Input.split(" ").length,
        output: 0.03 * response.split(" ").length,
        total: 0.03 * (response.split(" ").length + data.Input.split(" ").length),
      },
      modelUsed: "local-intelligent-responder-v1.0",
    },
  };
}

// Custom evaluator for response completeness
const completenessEvaluator = createCustomEvaluator<typeof dataStructure>(
  "completeness-evaluator",
  async (result, data) => {
    const response = await evaluateCompleteness(result.output, data.Input, data["Expected Output"]);
    return {
      score: response.score,
      reasoning: response.reasoning,
    };
  },
  {
    onEachEntry: {
      scoreShouldBe: ">=",
      value: 0.6,
    },
    forTestrunOverall: {
      overallShouldBe: ">=",
      value: 70,
      for: "percentageOfPassedResults",
    },
  }
);

// Custom evaluator for response tone appropriateness
const toneEvaluator = createCustomEvaluator<typeof dataStructure>(
  "tone-evaluator",
  async (result, data) => {
    const response = await evaluateTone(result.output, data.Input);
    return {
      score: response.score,
      reasoning: response.reasoning,
    };
  },
  {
    onEachEntry: {
      scoreShouldBe: "=",
      value: true,
    },
    forTestrunOverall: {
      overallShouldBe: ">=",
      value: 85,
      for: "percentageOfPassedResults",
    },
  }
);

const result = await maxim
  .createTestRun(`local evaluators local workflow test on ${Date.now()}`, workspaceId)
  .withDataStructure(dataStructure)
  .withData(datasetId)
  .yieldsOutput(localWorkflow)
  .withEvaluators("Bias", completenessEvaluator, toneEvaluator)
  .withConcurrency(3)
  .run();

console.log("\n\n========Test run results========");
console.log("\nFailed values: ", result.failedEntryIndices);
console.log("\nTest run link: ", result.testRunResult.link);
console.log("\nFinal result: ", result.testRunResult.result[0]);

await maxim.cleanup();

// Helper function to evaluate response completeness
async function evaluateCompleteness(output: string, input: string, expectedOutput: string) {
  // Simulate evaluation processing time
  await new Promise(resolve => setTimeout(resolve, 400));

  const outputWords = output.toLowerCase().split(/\s+/);
  const expectedWords = expectedOutput.toLowerCase().split(/\s+/);
  const inputWords = input.toLowerCase().split(/\s+/);

  // Check if response addresses the input question
  const inputKeywords = inputWords.filter(word => word.length > 3);
  const addressedKeywords = inputKeywords.filter(keyword => outputWords.some(word => word.includes(keyword) || keyword.includes(word)));

  // Check content overlap with expected output
  const expectedKeywords = expectedWords.filter(word => word.length > 3);
  const overlappingKeywords = expectedKeywords.filter(keyword =>
    outputWords.some(word => word.includes(keyword) || keyword.includes(word))
  );

  const addressingRatio = inputKeywords.length > 0 ? addressedKeywords.length / inputKeywords.length : 1;
  const contentRatio = expectedKeywords.length > 0 ? overlappingKeywords.length / expectedKeywords.length : 0.5;

  const score = addressingRatio * 0.6 + contentRatio * 0.4;

  return {
    score,
    reasoning: `Completeness analysis: ${addressedKeywords.length}/${inputKeywords.length} input keywords addressed (${(
      addressingRatio * 100
    ).toFixed(1)}%), ${overlappingKeywords.length}/${expectedKeywords.length} expected content keywords present (${(
      contentRatio * 100
    ).toFixed(1)}%). Overall score: ${score.toFixed(2)}`,
  };
}

// Helper function to evaluate tone appropriateness
async function evaluateTone(output: string, input: string) {
  // Simulate evaluation processing time
  await new Promise(resolve => setTimeout(resolve, 300));

  const outputLower = output.toLowerCase();
  const inputLower = input.toLowerCase();

  // Determine expected tone based on input
  let expectedTone: string;
  let appropriateToneWords: string[];
  let inappropriateToneWords: string[];

  if (inputLower.includes("explain") || inputLower.includes("what") || inputLower.includes("how")) {
    expectedTone = "informative";
    appropriateToneWords = ["based", "information", "shows", "indicates", "according", "evidence", "data"];
    inappropriateToneWords = ["maybe", "i think", "probably", "guess", "whatever"];
  } else if (inputLower.includes("summarize") || inputLower.includes("summary")) {
    expectedTone = "concise";
    appropriateToneWords = ["summary", "key", "main", "important", "essential", "brief"];
    inappropriateToneWords = ["furthermore", "additionally", "moreover", "extensive", "detailed"];
  } else if (inputLower.includes("compare") || inputLower.includes("vs")) {
    expectedTone = "analytical";
    appropriateToneWords = ["comparison", "difference", "similarity", "contrast", "whereas", "however"];
    inappropriateToneWords = ["definitely", "absolutely", "never", "always", "impossible"];
  } else {
    expectedTone = "helpful";
    appropriateToneWords = ["help", "assist", "provide", "information", "answer"];
    inappropriateToneWords = ["don't know", "can't help", "impossible", "useless"];
  }

  const appropriateCount = appropriateToneWords.filter(word => outputLower.includes(word)).length;
  const inappropriateCount = inappropriateToneWords.filter(word => outputLower.includes(word)).length;

  // Tone is appropriate if it has some appropriate words and no inappropriate ones
  const hasAppropriateIndicators = appropriateCount > 0;
  const hasNoInappropriate = inappropriateCount === 0;

  const score = hasAppropriateIndicators && hasNoInappropriate;

  return {
    score,
    reasoning: `Tone evaluation for ${expectedTone} tone: Found ${appropriateCount} appropriate indicators, ${inappropriateCount} inappropriate indicators. Expected tone words: [${appropriateToneWords.join(
      ", "
    )}]. Result: ${score ? "Appropriate" : "Needs improvement"}`,
  };
}
