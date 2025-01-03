import { ChatOpenAI } from "@langchain/openai";
import { Maxim } from "@maximai/maxim-js";
import { MaximLangchainTracer } from "@maximai/maxim-js-langchain";

import { config } from 'dotenv';

config();


async function main() {
    const repoId = process.env.MAXIM_LOG_REPO_ID!;
    const maxim = new Maxim({        
        apiKey: process.env.MAXIM_API_KEY!,
        debug: true,
    });
    const logger = await maxim.logger({ id: repoId });
    const query = "this 3+5 and new";
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
            maxim: { generationName: "gen1", generationTags: { tag: "test" } },
        },
    });
    await llm.invoke(query);
    await maxim.cleanup();
}

main();