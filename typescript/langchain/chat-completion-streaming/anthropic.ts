import { ChatAnthropic } from "@langchain/anthropic";
import { Maxim } from "@maximai/maxim-js";
import { MaximLangchainTracer } from "@maximai/maxim-js-langchain";

import "dotenv/config";


async function main() {
    const repoId = process.env.MAXIM_LOG_REPO_ID!;
    const maxim = new Maxim({
        apiKey: process.env.MAXIM_API_KEY!,
    });
    const logger = await maxim.logger({ id: repoId });
    const query = "Hi Anthropic, what is 3 + 5?";
    const maximTracer = new MaximLangchainTracer(logger);

    const llm = new ChatAnthropic({
        anthropicApiKey: process.env.ANTHROPIC_API_KEY,
        model: "claude-3-5-sonnet-20241022",
        temperature: 0,
        topP: 1,
        callbacks: [maximTracer],
        maxTokens: 4096,
        streaming: true,
        metadata: {
            maxim: { generationName: "generation", generationTags: { test: "anthropic streaming" } },
        },
    });
    const chunks = await llm.stream(query)
    const result = [];
    // await for each chunk is required before calling maxim.cleanup
    for await (const chunk of chunks) {
        result.push(chunk);
    }
    await maxim.cleanup();
}

main();