package main

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/Azure/azure-sdk-for-go/sdk/ai/azopenai"
	"github.com/Azure/azure-sdk-for-go/sdk/azcore"
	"github.com/Azure/azure-sdk-for-go/sdk/azcore/to"
	"github.com/maximhq/maxim-go/middlewares"
)

// manualTracing demonstrates how to manually create and manage traces
// in Maxim. This function creates all required components (trace, generation)
// and sends the data to the Maxim backend, allowing for complete control
// over the tracing process. It establishes a trace, adds a generation,
// makes an OpenAI API call, and records the result.
func usingMaximOpenAITransport() {
	keyCredential := azcore.NewKeyCredential(azureOpenAIKey)
	clientOptions := azopenai.ClientOptions{}
	clientOptions.Transport = &middlewares.MaximOpenAITransport{
		Logger: logger,
	}
	azOpenai, err := azopenai.NewClientWithKeyCredential(azureOpenAIBaseURL, keyCredential, &clientOptions)
	if err != nil {
		panic(err)
	}
	defer logger.Flush()
	messages := []azopenai.ChatRequestMessageClassification{
		&azopenai.ChatRequestSystemMessage{Content: azopenai.NewChatRequestSystemMessageContent("You are a helpful assistant. You will talk like a pirate.")},
		&azopenai.ChatRequestUserMessage{Content: azopenai.NewChatRequestUserMessageContent("Get the current weather in New York City")},
	}
	// Function call
	jsonBytes, err := json.Marshal(map[string]any{
		"required": []string{"location"},
		"type":     "object",
		"properties": map[string]any{
			"location": map[string]any{
				"type":        "string",
				"description": "The city and state, e.g. San Francisco, CA",
			},
			"unit": map[string]any{
				"type": "string",
				"enum": []string{"celsius", "fahrenheit"},
			},
		},
	})
	if err != nil {
		panic(err)
	}
	funcDef := &azopenai.ChatCompletionsFunctionToolDefinitionFunction{
		Name:        to.Ptr("get_current_weather"),
		Description: to.Ptr("Get the current weather in a given location"),
		Parameters:  jsonBytes,
	}
	// Create a context
	ctx := context.Background()
	// Adding tags
	ctx = context.WithValue(ctx, "maxim.tags", map[string]string{"env": "prod", "model": "gpt-4o-mini"})
	// Create a chat completion request
	chatCompletion, err := azOpenai.GetChatCompletions(ctx, azopenai.ChatCompletionsOptions{
		Messages:       messages,
		DeploymentName: &azureDeploymentName,
		Tools: []azopenai.ChatCompletionsToolDefinitionClassification{
			&azopenai.ChatCompletionsFunctionToolDefinition{
				Function: funcDef,
			},
		},
		Temperature: to.Ptr[float32](0.0),
	}, nil)
	if err != nil {
		panic(err.Error())
	}
	fmt.Printf("%+v", chatCompletion)
}
