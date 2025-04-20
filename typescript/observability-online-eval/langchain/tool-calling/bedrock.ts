import { ChatBedrockConverse } from "@langchain/aws";
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

    const query = "Hi Bedrock, what is 3 + 5?";
    const maximTracer = new MaximLangchainTracer(logger);

    // initialize llm
    const llm = new ChatBedrockConverse({
        region: process.env.BEDROCK_AWS_REGION ?? "us-east-1",
        credentials: {
            secretAccessKey: process.env.BEDROCK_AWS_SECRET_ACCESS_KEY!,
            accessKeyId: process.env.BEDROCK_AWS_ACCESS_KEY_ID!,
        },
        model: "anthropic.claude-3-haiku-20240307-v1:0",
        temperature: 0,
        topP: 1,
        callbacks: [maximTracer],
        metadata: {
            maxim: { generationName: "generation", generationTags: { test: "bedrock tool calls" } },
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