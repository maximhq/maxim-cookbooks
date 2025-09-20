import * as MaximSDK from '@maximai/maxim-js';

let maximClient: any | null = null;
let loggerInstance: any | null = null;

const ENV_API_KEY = process.env.EXPO_PUBLIC_MAXIM_API_KEY;
const ENV_REPOSITORY_ID = process.env.EXPO_PUBLIC_MAXIM_REPOSITORY_ID;

export type MaximConfig = {
  apiKey?: string;
  baseUrl?: string;
  promptManagement?: boolean;
  debug?: boolean;
};

function getSdk(): any {
  return MaximSDK;
}

export function getVariableType(): any {
  const sdk = getSdk();
  return sdk.VariableType;
}

export async function initMaxim(config: MaximConfig): Promise<void> {
  if (maximClient) return;
  const sdk = getSdk();
  const { Maxim } = sdk;
  maximClient = new Maxim({
    apiKey: config.apiKey ?? ENV_API_KEY,
    baseUrl: config.baseUrl,
    promptManagement: config.promptManagement ?? true,
    debug: config.debug,
  });
}

export async function ensureInitialized(): Promise<void> {
  if (!maximClient) {
    await initMaxim({});
  }
  if (
    !loggerInstance &&
    ENV_REPOSITORY_ID &&
    typeof maximClient?.logger === "function"
  ) {
    loggerInstance = await maximClient.logger({ id: ENV_REPOSITORY_ID });
  }
}

export function isInitialized(): boolean {
  return !!maximClient;
}

export async function getClient(): Promise<any> {
  await ensureInitialized();
  return maximClient;
}

// Logger
export async function createLogger(
  config: Record<string, unknown>
): Promise<any | undefined> {
  await ensureInitialized();
  if (loggerInstance) return loggerInstance;
  if (typeof maximClient.logger === "function") {
    loggerInstance = await maximClient.logger(config);
  }
  return loggerInstance;
}

// Sessions, Traces, Spans via logger if available
export function createSession(
  config: Record<string, unknown>
): any | undefined {
  if (!loggerInstance) return undefined;
  if (typeof loggerInstance.session === "function") {
    return loggerInstance.session(config);
  }
  return undefined;
}

export function createTrace(
  session: any,
  config: Record<string, unknown>
): any | undefined {
  if (!session) return undefined;
  if (typeof session.trace === "function") {
    return session.trace(config);
  }
  return undefined;
}

export function endTrace(trace: any): void {
  if (trace && typeof trace.end === "function") {
    trace.end();
  }
}

// Rule builders (QueryBuilder)
export async function getQueryBuilder(): Promise<any> {
  const sdk = getSdk();
  if (!sdk?.QueryBuilder)
    throw new Error("QueryBuilder not available in maxim-js");
  return sdk.QueryBuilder;
}

export async function buildRule(
  options: {
    folder?: string;
    deploymentVars?: Record<string, string>;
    tags?: Record<string, string>;
  } = {}
): Promise<any> {
  const QueryBuilder = await getQueryBuilder();
  let qb = new QueryBuilder();
  if (options.folder) qb = qb.folder(options.folder);
  if (options.deploymentVars) {
    for (const [key, value] of Object.entries(options.deploymentVars)) {
      qb = qb.deploymentVar(key, value);
    }
  }
  if (options.tags) {
    for (const [key, value] of Object.entries(options.tags)) {
      qb = qb.tag(key, value);
    }
  }
  return qb.build();
}

// Prompts and Prompt Chains
export async function getPrompt(
  promptId: string,
  rule: any
): Promise<any | undefined> {
  await ensureInitialized();
  if (typeof maximClient.getPrompt === "function") {
    return await maximClient.getPrompt(promptId, rule);
  }
  return undefined;
}

export async function getPrompts(rule: any): Promise<any[] | undefined> {
  await ensureInitialized();
  if (typeof maximClient.getPrompts === "function") {
    return await maximClient.getPrompts(rule);
  }
  return undefined;
}

export async function getPromptChain(
  promptChainId: string,
  rule: any
): Promise<any | undefined> {
  await ensureInitialized();
  if (typeof maximClient.getPromptChain === "function") {
    return await maximClient.getPromptChain(promptChainId, rule);
  }
  return undefined;
}

export async function getPromptChains(rule: any): Promise<any[] | undefined> {
  await ensureInitialized();
  if (typeof maximClient.getPromptChains === "function") {
    return await maximClient.getPromptChains(rule);
  }
  return undefined;
}

// Datasets
export async function addDatasetEntries(
  datasetId: string,
  entries: any[]
): Promise<void> {
  await ensureInitialized();
  if (typeof maximClient.addDatasetEntries === "function") {
    await maximClient.addDatasetEntries(datasetId, entries);
  }
}

export async function getDatasetRows(datasetId: string): Promise<any | undefined> {
  await ensureInitialized();
  if (typeof maximClient.getDatasetRows === "function") {
    return await maximClient.getDatasetRows(datasetId);
  }
  return undefined;
}

// Folders
export async function getFolderById(
  folderId: string
): Promise<any | undefined> {
  await ensureInitialized();
  if (typeof maximClient.getFolderById === "function") {
    return await maximClient.getFolderById(folderId);
  }
  return undefined;
}

export async function getFolders(): Promise<any[] | undefined> {
  await ensureInitialized();
  if (typeof maximClient.getFolders === "function") {
    return await maximClient.getFolders();
  }
  return undefined;
}

// Test runs
export function createTestRun(
  name: string,
  workspaceId: string
): any | undefined {
  if (!maximClient) return undefined;
  if (typeof maximClient.createTestRun === "function") {
    return maximClient.createTestRun(name, workspaceId);
  }
  return undefined;
}

export function getRepositoryId(): string | undefined {
  return ENV_REPOSITORY_ID;
}

// Cleanup
export async function cleanup(): Promise<void> {
  if (!maximClient) return;
  if (typeof maximClient.cleanup === "function") {
    await maximClient.cleanup();
  }
  maximClient = null;
  loggerInstance = null;
}
