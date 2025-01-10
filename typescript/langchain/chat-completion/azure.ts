import { AzureChatOpenAI } from "@langchain/openai";
import { Maxim } from "@maximai/maxim-js";
import { MaximLangchainTracer } from "@maximai/maxim-js-langchain";

import "dotenv/config";


async function main() {
    const repoId = process.env.MAXIM_LOG_REPO_ID!;
    const maxim = new Maxim({
        apiKey: process.env.MAXIM_API_KEY!,
    });
    const logger = await maxim.logger({ id: repoId });
    const query = "Hi, Azure OpenAI. What is 3 + 5?";
    const maximTracer = new MaximLangchainTracer(logger);

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
            maxim: { generationName: "generation", generationTags: { test: "azure" } },
        },
    });
    await llm.invoke(query)

    await maxim.cleanup();
}

main();