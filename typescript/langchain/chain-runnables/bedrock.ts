import { ChatBedrockConverse } from "@langchain/aws";
import { Maxim } from "@maximai/maxim-js";
import { MaximLangchainTracer } from "@maximai/maxim-js-langchain";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { ChatPromptTemplate } from "@langchain/core/prompts";

import "dotenv/config";


async function main() {
    const repoId = process.env.MAXIM_LOG_REPO_ID!;
    const maxim = new Maxim({
        apiKey: process.env.MAXIM_API_KEY!,
    });
    const logger = await maxim.logger({ id: repoId });

    if (!logger) {
        throw new Error("Failed to create logger");
    }

    const maximTracer = new MaximLangchainTracer(logger);

    const llm = new ChatBedrockConverse({
        region: process.env.BEDROCK_AWS_REGION ?? "us-east-1",
        credentials: {
            secretAccessKey: process.env.BEDROCK_AWS_SECRET_ACCESS_KEY!,
            accessKeyId: process.env.BEDROCK_AWS_ACCESS_KEY_ID!,
        },
        model: "anthropic.claude-3-haiku-20240307-v1:0",
        // model: "meta.llama3-8b-instruct-v1:0",
        temperature: 0,
        topP: 1,
        callbacks: [maximTracer],
        metadata: {
            maxim: { generationName: "generation", generationTags: { test: "bedrock" } },
        },
    });

    const prompt = ChatPromptTemplate.fromTemplate("Explain {topic} like I am 5 years old.");
    const chain = prompt.pipe(llm).pipe(new StringOutputParser());

    await chain.invoke({ topic: "machine learning" });

    await maxim.cleanup();
}

main();