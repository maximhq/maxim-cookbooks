import { ChatOpenAI } from "@langchain/openai";
import { Maxim } from "@maximai/maxim-js";

import { MaximLangchainTracer } from "@maximai/maxim-js-langchain";
import { v4 as uuid } from "uuid";

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

  const query = "Hi OpenAI, what is 3 + 2?";
  const maximTracer = new MaximLangchainTracer(logger);
  const trace = logger.trace({ id: uuid(), name: "maths" });

  trace.input(query);

  const llm = new ChatOpenAI({
    openAIApiKey: process.env.OPENAI_API_KEY,
    modelName: "gpt-4o-mini",
    temperature: 0,
    topP: 1,
    frequencyPenalty: 0,
    callbacks: [maximTracer],
    maxTokens: 4096,
    n: 1,
  });

  const result = await llm.invoke(query, {
    metadata: {
      maxim: {
        traceId: trace.id,
        generationName: "gen1",
        generationTags: { test: "openai", demo: "langchain" },
      },
    },
  });

  trace.output(JSON.stringify(result.content));

  trace.end();

  await maxim.cleanup();
}

main();
