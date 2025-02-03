import { AzureChatOpenAI } from "@langchain/openai";
import { Maxim } from "@maximai/maxim-js";
import { MaximLangchainTracer } from "@maximai/maxim-js-langchain";
import { z } from "zod";
import { tool } from "@langchain/core/tools";

import "dotenv/config";


async function main() {
    // initialize maxim logger
    const repoId = process.env.MAXIM_LOG_REPO_ID!;
    const maxim = new Maxim({
        apiKey: process.env.MAXIM_API_KEY!,
    });
    const logger = await maxim.logger({ id: repoId });

    if (!logger) {
        throw new Error("Failed to create logger");
    }

    const query = "Hi Azure OpenAI, what is 3 + 5?";
    const maximTracer = new MaximLangchainTracer(logger);

    // initialize llm
    const llm = new AzureChatOpenAI({
        openAIApiKey: process.env.AZURE_OPENAI_API_KEY,
        openAIApiVersion: process.env.AZURE_OPENAI_API_VERSION,
        deploymentName: process.env.AZURE_OPENAI_API_DEPLOYMENT_NAME,
        azureOpenAIEndpoint: process.env.AZURE_OPENAI_ENDPOINT,
        model: "gpt-4o-mini",
        temperature: 0,
        topP: 1,
        frequencyPenalty: 0,
        callbacks: [maximTracer],
        maxTokens: 4096,
        n: 1,
        metadata: {
            maxim: { generationName: "generation", generationTags: { test: "azure openai tool calls" } },
        },
    });

    // define the tool
    const calculatorSchema = z.object({
        operation: z
            .enum(["add", "subtract", "multiply", "divide"])
            .describe("The type of operation to execute."),
        number1: z.number().describe("The first number to operate on."),
        number2: z.number().describe("The second number to operate on."),
    });

    const calculatorTool = tool(
        async ({ operation, number1, number2 }) => {
            // Functions must return strings
            if (operation === "add") {
                return `${number1 + number2}`;
            } else if (operation === "subtract") {
                return `${number1 - number2}`;
            } else if (operation === "multiply") {
                return `${number1 * number2}`;
            } else if (operation === "divide") {
                return `${number1 / number2}`;
            } else {
                throw new Error("Invalid operation.");
            }
        },
        {
            name: "calculator",
            description: "Can perform mathematical operations.",
            schema: calculatorSchema,
        }
    );

    const llmWithTools = llm.bindTools([calculatorTool]);

    await llmWithTools.invoke(query);

    await maxim.cleanup();
}

main();