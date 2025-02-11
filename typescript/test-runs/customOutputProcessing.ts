import { createDataStructure, Maxim } from "@maximai/maxim-js";
import "dotenv/config";

let apiKey: string, workspaceId: string, datasetId: string;
if (!process.env.MAXIM_API_KEY)
    throw new Error("Missing MAXIM_API_KEY environment variable");
if (!process.env.MAXIM_WORKSPACE_ID)
    throw new Error("Missing MAXIM_WORKSPACE_ID environment variable");
if (!process.env.MAXIM_DATASET_ID)
    throw new Error("Missing MAXIM_DATASET_ID environment variable");
apiKey = process.env.MAXIM_API_KEY;
workspaceId = process.env.MAXIM_WORKSPACE_ID;
datasetId = process.env.MAXIM_DATASET_ID;

const maxim = new Maxim({ apiKey });

const dataStructure = createDataStructure({
    Input: "INPUT",
    "Expected Output": "EXPECTED_OUTPUT",
    Context: "VARIABLE",
});

const result = await maxim
    .createTestRun(`sdk test run on ${Date.now()}`, workspaceId)
    .withDataStructure(dataStructure)
    .withData(datasetId)
    .yieldsOutput(async (data) => {
        const startTime = Date.now();
        const response = await mockLLMCall(data.Input, data.Context);

        // throw new Error("This is a mock error"); // throwing from this function will cause the entry to be marked as failed and you will recieve the index of the failed entry in the `failedEntryIndices` array

        return {
            data: response[0].choices[0].message.content,
            retrievedContextToEvaluate: response[1], // Optional, if you are retrieving context for the LLM call and not using from dataset, you can pass it here
            meta: {
                // `meta` is optional; used for tracking metadata relating to the LLM call
                usage: {
                    completionTokens: response[0].usage.completion_tokens,
                    promptTokens: response[0].usage.prompt_tokens,
                    totalTokens: response[0].usage.total_tokens,
                    latency: Date.now() - startTime,
                },
                cost: {
                    input: response[0].usage.prompt_tokens * 0.03, // Assuming cost of 0.03 tokens per token
                    output: response[0].usage.completion_tokens * 0.03,
                    total:
                        (response[0].usage.prompt_tokens +
                            response[0].usage.completion_tokens) *
                        0.03,
                },
            },
        };
    })
    .withEvaluators("Faithfulness", "Semantic Similarity")
    .run();

console.log("\n\n========Test run results========");
console.log("\nFailed values: ", result.failedEntryIndices);
console.log("\nTest run link: ", result.testRunResult.link);
console.log("\nFinal result: ", result.testRunResult.result[0]);

await maxim.cleanup();

async function mockLLMCall(input: string, context?: string | string[]) {
    const model = "gpt-3.5-turbo";
    const temperature = 0.7;
    const maxTokens = 500;

    const stringContext = context
        ? Array.isArray(context)
            ? context.join("\n")
            : context
        : undefined;

    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // Calculate mock token counts
    const promptTokens = Math.ceil(
        (input.length + (stringContext?.length ?? 0)) / 4,
    );
    const completionTokens = Math.ceil(maxTokens * 0.7); // Simulate using 70% of max tokens

    // Generate a mock response based on input
    const mockResponse = `This is a mock response to: "${input}". ${
        stringContext ? `Taking into account the context: "${stringContext}".` : ""
    }`;

    return [
        {
            id: `chatcmpl-${Math.random().toString(36).substr(2, 9)}`,
            object: "chat.completion",
            created: Date.now(),
            model,
            choices: [
                {
                    index: 0,
                    message: {
                        role: "assistant",
                        content: mockResponse,
                    },
                    finish_reason: "stop",
                },
            ],
            usage: {
                prompt_tokens: promptTokens,
                completion_tokens: completionTokens,
                total_tokens: promptTokens + completionTokens,
            },
        },
        stringContext,
    ] as const;
}
