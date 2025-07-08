import { createDataStructure, Data, Maxim } from "@maximai/maxim-js";
import "dotenv/config";
import { generateResponse } from "../utils/openai-helper.js";

// Validate required environment variables
const requiredEnvVars = {
  MAXIM_API_KEY: process.env.MAXIM_API_KEY,
  MAXIM_WORKSPACE_ID: process.env.MAXIM_WORKSPACE_ID,
  OPENAI_API_KEY: process.env.OPENAI_API_KEY,
};

for (const [key, value] of Object.entries(requiredEnvVars)) {
  if (!value) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
}

const MAXIM_API_KEY = requiredEnvVars.MAXIM_API_KEY!;
const MAXIM_WORKSPACE_ID = requiredEnvVars.MAXIM_WORKSPACE_ID!;

// Initialize Maxim SDK
const maxim = new Maxim({ apiKey: MAXIM_API_KEY });

// Define comprehensive data structure with rich metadata
const dataStructure = createDataStructure({
  Question: "INPUT",
  "Expected Answer": "EXPECTED_OUTPUT",
  "Domain Context": "CONTEXT_TO_EVALUATE",
  "Difficulty Level": "VARIABLE",
  Category: "VARIABLE",
});

// Technical knowledge base with diverse difficulty levels and categories
const technicalDataset = [
  {
    Question: "Explain the key differences between microservices and monolithic architecture",
    "Expected Answer":
      "Microservices break applications into small, independent services, while monoliths are single deployable units. Microservices offer better scalability and technology diversity but add complexity.",
    "Domain Context": "Software architecture patterns, distributed systems design, enterprise application development best practices",
    "Difficulty Level": "Intermediate",
    Category: "Software Architecture",
  },
  {
    Question: "How does gradient descent optimization work in machine learning?",
    "Expected Answer":
      "Gradient descent minimizes loss functions by iteratively moving in the direction of steepest descent. It calculates gradients and updates parameters to find optimal solutions.",
    "Domain Context": "Machine learning fundamentals, optimization algorithms, neural network training methods",
    "Difficulty Level": "Advanced",
    Category: "Machine Learning",
  },
  {
    Question: "What is the difference between var, let, and const in JavaScript?",
    "Expected Answer":
      "var has function scope and can be redeclared, let has block scope and can be reassigned, const has block scope and cannot be reassigned after declaration.",
    "Domain Context": "JavaScript language fundamentals, variable declaration patterns, ES6+ features",
    "Difficulty Level": "Beginner",
    Category: "Programming Languages",
  },
  {
    Question: "Explain database normalization and when to denormalize",
    "Expected Answer":
      "Normalization eliminates data redundancy by organizing data into related tables. Denormalization intentionally introduces redundancy to improve query performance in specific scenarios.",
    "Domain Context": "Database design principles, relational database theory, performance optimization strategies",
    "Difficulty Level": "Intermediate",
    Category: "Database Design",
  },
  {
    Question: "How do you implement proper error handling in asynchronous JavaScript code?",
    "Expected Answer":
      "Use try-catch blocks with async/await, handle Promise rejections with .catch(), implement global error handlers, and validate inputs before processing.",
    "Domain Context": "Asynchronous programming patterns, error handling best practices, Promise-based error management",
    "Difficulty Level": "Advanced",
    Category: "Asynchronous Programming",
  },
];

// Enhanced output processor using real OpenAI
async function enhancedTechnicalProcessor(data: Data<typeof dataStructure>) {
  const startTime = Date.now();
  const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;
  const category = Array.isArray(data.Category) ? data.Category.join(", ") : data.Category;
  const difficulty = Array.isArray(data["Difficulty Level"]) ? data["Difficulty Level"].join(", ") : data["Difficulty Level"];

  console.log(`[${sessionId}] Processing ${category} question (${difficulty})`);

  try {
    // Create specialized system prompt based on category and difficulty
    const systemPrompt = createSystemPrompt(category, difficulty);

    // Handle context properly
    const contextString = Array.isArray(data["Domain Context"]) ? data["Domain Context"].join("\n") : data["Domain Context"];

    // Generate response using OpenAI
    const aiResponse = await generateResponse(data.Question, contextString, systemPrompt);

    const endTime = Date.now();

    // Calculate difficulty-based cost multipliers
    const difficultyMultiplier = getDifficultyMultiplier(difficulty);
    const categoryMultiplier = getCategoryMultiplier(category);

    return {
      data: aiResponse.response,
      retrievedContextToEvaluate: data["Domain Context"],
      meta: {
        sessionId,
        usage: {
          ...aiResponse.usage,
          efficiency: aiResponse.usage.latency <= 3000 ? "optimal" : "slow",
        },
        cost: {
          ...aiResponse.cost,
          difficultyMultiplier,
          categoryMultiplier,
          adjustedTotal: aiResponse.cost.total * difficultyMultiplier * categoryMultiplier,
        },
        context: {
          difficulty: data["Difficulty Level"],
          category: data.Category,
          questionComplexity: analyzeQuestionComplexity(data.Question),
          expectedLength: data["Expected Answer"].length,
        },
        performance: {
          processingTime: endTime - startTime,
          responseQuality: aiResponse.response.length > 50 ? "detailed" : "brief",
          contextUtilization: contextString ? "enhanced" : "basic",
        },
        modelUsed: "gpt-3.5-turbo",
        timestamp: new Date().toISOString(),
      },
    };
  } catch (error) {
    console.error(`[${sessionId}] Processing failed: ${error}`);
    throw error;
  }
}

// Helper functions for enhanced processing
function createSystemPrompt(category: string, difficulty: string): string {
  const basePrompt = "You are an expert technical educator providing clear, accurate explanations.";

  if (difficulty === "Beginner") {
    return `${basePrompt} Explain concepts in simple terms with practical examples. Avoid jargon.`;
  } else if (difficulty === "Advanced") {
    return `${basePrompt} Provide comprehensive, technical explanations with implementation details and best practices.`;
  } else {
    return `${basePrompt} Balance technical depth with clarity, suitable for intermediate practitioners.`;
  }
}

function getDifficultyMultiplier(difficulty: string): number {
  const multipliers: Record<string, number> = {
    Beginner: 1.0,
    Intermediate: 1.2,
    Advanced: 1.5,
  };
  return multipliers[difficulty] || 1.0;
}

function getCategoryMultiplier(category: string): number {
  const multipliers: Record<string, number> = {
    "Machine Learning": 1.3,
    "Software Architecture": 1.2,
    "Database Design": 1.1,
    "Programming Languages": 1.0,
    "Asynchronous Programming": 1.1,
  };
  return multipliers[category] || 1.0;
}

function analyzeQuestionComplexity(question: string): string {
  const wordCount = question.split(/\s+/).length;
  if (wordCount <= 8) return "simple";
  if (wordCount <= 15) return "moderate";
  return "complex";
}

console.log("🧠 Enhanced Technical Knowledge Test");
console.log("=====================================\n");

// Run test with enhanced manual data and real OpenAI processing
const result = await maxim
  .createTestRun(`Enhanced Technical Test - ${new Date().toISOString()}`, MAXIM_WORKSPACE_ID)
  .withDataStructure(dataStructure)
  .withData(technicalDataset)
  .yieldsOutput(enhancedTechnicalProcessor)
  .withEvaluators("Faithfulness", "Semantic Similarity", "Clarity")
  .withConcurrency(2) // Moderate concurrency for OpenAI calls
  .run();

// Display comprehensive results
console.log("📊 Enhanced Technical Test Results");
console.log("=====================================");
console.log(`📚 Total test cases: ${technicalDataset.length}`);
console.log(`📂 Categories: ${[...new Set(technicalDataset.map(d => d.Category))].join(", ")}`);
console.log(`📈 Difficulty levels: ${[...new Set(technicalDataset.map(d => d["Difficulty Level"]))].join(", ")}`);
console.log(`❌ Failed entries: ${result.failedEntryIndices.length > 0 ? result.failedEntryIndices.join(", ") : "None"}`);
console.log(`🔗 View detailed results: ${result.testRunResult.link}`);
console.log(`📋 Summary: ${JSON.stringify(result.testRunResult.result[0], null, 2)}`);

console.log("\n🚀 Enhanced Features Demonstrated:");
console.log("• Real OpenAI integration with context-aware processing");
console.log("• Difficulty-based system prompt optimization");
console.log("• Category-specific cost multipliers");
console.log("• Comprehensive metadata tracking and analysis");
console.log("• Question complexity assessment");
console.log("• Performance and efficiency monitoring");

await maxim.cleanup();
