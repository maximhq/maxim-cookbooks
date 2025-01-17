import { ChatOpenAI } from "@langchain/openai";
import { Maxim } from "@maximai/maxim-js";
import { MaximLangchainTracer } from "@maximai/maxim-js-langchain";

import "dotenv/config";


async function main() {
    const repoId = process.env.MAXIM_LOG_REPO_ID!;
    const maxim = new Maxim({
        apiKey: process.env.MAXIM_API_KEY!,
    });
    const logger = await maxim.logger({ id: repoId });
    const query = "Hi OpenAI, what is 3 + 5?";
    const maximTracer = new MaximLangchainTracer(logger);

    const llm = new ChatOpenAI({
        openAIApiKey: process.env.OPENAI_API_KEY,
        modelName: "gpt-4o-mini",
        temperature: 0,
        topP: 1,
        frequencyPenalty: 0,
        callbacks: [maximTracer],
        maxTokens: 4096,
        n: 1,
        streaming: true,
        metadata: {
            maxim: { generationName: "gen1", generationTags: { test: "openai streaming" } },
        },
    });
    const chunks = await llm.stream(query);
    const result = [];
    // await for each chunk is required before calling maxim.cleanup
    for await (const chunk of chunks) {
        result.push(chunk);
    }
    console.log(result);

    await maxim.cleanup();
}

main();