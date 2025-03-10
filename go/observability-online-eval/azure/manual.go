package main

import (
	"context"

	"github.com/google/uuid"
	"github.com/maximhq/maxim-go"
	"github.com/maximhq/maxim-go/logging"
	"github.com/openai/openai-go"

	"github.com/Azure/azure-sdk-for-go/sdk/ai/azopenai"
	"github.com/Azure/azure-sdk-for-go/sdk/azcore"
)

// manualTracing demonstrates how to manually create and manage traces
// in Maxim. This function creates all required components (trace, generation)
// and sends the data to the Maxim backend, allowing for complete control
// over the tracing process. It establishes a trace, adds a generation,
// makes an OpenAI API call, and records the result.
func manualTracing() {
	keyCredential := azcore.NewKeyCredential(azureOpenAIKey)
	azOpenai, err := azopenai.NewClientWithKeyCredential(azureOpenAIBaseURL, keyCredential, nil)
	if err != nil {
		panic(err)
	}
	defer logger.Flush()
	traceId := uuid.New().String()
	trace := logger.Trace(&logging.TraceConfig{
		Id:   traceId,
		Name: maxim.StrPtr("Main trace"),
	})
	defer trace.End()
	messages := []azopenai.ChatRequestMessageClassification{
		&azopenai.ChatRequestSystemMessage{Content: azopenai.NewChatRequestSystemMessageContent("You are a helpful assistant. You will talk like a pirate.")},
		&azopenai.ChatRequestUserMessage{Content: azopenai.NewChatRequestUserMessageContent("Say hi")},
	}
	generation := trace.AddGeneration(&logging.GenerationConfig{
		Id:       uuid.New().String(),
		Name:     maxim.StrPtr("Generation name"),
		Model:    openai.ChatModelGPT4o,
		Provider: logging.ProviderOpenAI,
	})
	for _, message := range messages {
		switch msg := message.(type) {
		case *azopenai.ChatRequestSystemMessage:
			generation.AddMessage(logging.CompletionRequest{
				Role:    "system",
				Content: *msg.Content,
			})
		case *azopenai.ChatRequestUserMessage:
			generation.AddMessage(logging.CompletionRequest{
				Role:    "user",
				Content: *msg.Content,
			})
		case *azopenai.ChatRequestAssistantMessage:
			generation.AddMessage(logging.CompletionRequest{
				Role:    "assistant",
				Content: *msg.Content,
			})
		case *azopenai.ChatRequestToolMessage:
			generation.AddMessage(logging.CompletionRequest{
				Role:    "Tool",
				Content: *msg.Content,
			})
		}
	}
	defer generation.End()
	// Create a context
	ctx := context.Background()
	// Create a chat completion request
	chatCompletion, err := azOpenai.GetChatCompletions(ctx, azopenai.ChatCompletionsOptions{
		Messages:       messages,
		DeploymentName: &azureDeploymentName,
	}, nil)
	if err != nil {
		panic(err.Error())
	}
	generation.SetResult(chatCompletion)
	println(*chatCompletion.Choices[0].Message.Content)
}
