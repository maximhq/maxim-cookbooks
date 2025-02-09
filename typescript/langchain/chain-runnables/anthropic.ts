import { ChatAnthropic } from "@langchain/anthropic";
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

    const llm = new ChatAnthropic({
        anthropicApiKey: process.env.ANTHROPIC_API_KEY,
        model: "claude-3-5-sonnet-20241022",
        temperature: 0,
        topP: 1,
        callbacks: [maximTracer],
        maxTokens: 4096,
        metadata: {
            maxim: { generationName: "generation", generationTags: { test: "anthropic" } },
        },
    });

    const prompt = ChatPromptTemplate.fromTemplate("Explain {topic} like I am 5 years old.");
    const chain = prompt.pipe(llm).pipe(new StringOutputParser());

    await chain.invoke({ topic: "machine learning" });

    await maxim.cleanup();
}

main();