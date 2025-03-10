package main

import (
	"context"

	"github.com/google/uuid"
	"github.com/maximhq/maxim-go"
	"github.com/maximhq/maxim-go/logging"
	"github.com/openai/openai-go"
	"github.com/openai/openai-go/option"
)

// manualTracing demonstrates how to manually create and manage traces
// in Maxim. This function creates all required components (trace, generation)
// and sends the data to the Maxim backend, allowing for complete control
// over the tracing process. It establishes a trace, adds a generation,
// makes an OpenAI API call, and records the result.
func manualTracing() {
	openAiClient := openai.NewClient(
		option.WithAPIKey(openAIKey),
	)
	defer logger.Flush()

	traceId := uuid.New().String()
	trace := logger.Trace(&logging.TraceConfig{
		Id:   traceId,
		Name: maxim.StrPtr("Main trace"),
	})
	defer trace.End()
	generation := trace.AddGeneration(&logging.GenerationConfig{
		Id:   uuid.New().String(),
		Name: maxim.StrPtr("Generation name"),
		Messages: []logging.CompletionRequest{
			{
				Role:    "user",
				Content: "Say this is a test",
			},
		},
		Model:    openai.ChatModelGPT4o,
		Provider: logging.ProviderOpenAI,
	})
	defer generation.End()
	// Create a context
	ctx := context.Background()
	// Create a chat completion request
	chatCompletion, err := openAiClient.Chat.Completions.New(ctx, openai.ChatCompletionNewParams{
		Messages: openai.F([]openai.ChatCompletionMessageParamUnion{
			openai.UserMessage("Say this is a test"),
		}),
		Model: openai.F(openai.ChatModelGPT4o),
	})
	if err != nil {
		panic(err.Error())
	}
	generation.SetResult(chatCompletion)
	println(chatCompletion.Choices[0].Message.Content)
}
