import { tool } from "@langchain/core/tools";
import { z } from "zod";
import { ChatOpenAI } from "@langchain/openai";
import { Maxim } from "@maximai/maxim-js";
import { MaximLangchainTracer } from "@maximai/maxim-js-langchain";

import "dotenv/config";


async function main() {

    // initialize maxim logger
    const repoId = process.env.MAXIM_LOG_REPO_ID!;
    const maxim = new Maxim({
        apiKey: process.env.MAXIM_API_KEY!,
    });
    const logger = await maxim.logger({ id: repoId });

    const maximTracer = new MaximLangchainTracer(logger);

    // initialize llm
    const llm = new ChatOpenAI({
        openAIApiKey: process.env.OPENAI_API_KEY,
        modelName: "gpt-4o-mini",
        temperature: 0,
        topP: 1,
        frequencyPenalty: 0,
        callbacks: [maximTracer],
        maxTokens: 4096,
        n: 1,
        metadata: {
            maxim: { generationName: "gen1", generationTags: { test: "test openai tool" } },
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

    await llmWithTools.invoke("Hi OpenAI, What is 3 * 12?");

    await maxim.cleanup();
}

main();