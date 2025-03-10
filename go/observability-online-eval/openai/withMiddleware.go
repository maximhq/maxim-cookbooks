package main

import (
	"context"

	"github.com/maximhq/maxim-go/middlewares"
	"github.com/openai/openai-go"
	"github.com/openai/openai-go/option"
)

func usingMiddleware() {
	defer logger.Flush()
	openAiClient := openai.NewClient(
		option.WithAPIKey(openAIKey),
		option.WithMiddleware(middlewares.MaximOpenAIMiddleware),
	)
	// traceId := uuid.New().String()
	// Create a context
	ctx := context.Background()
	// If you don't pass this logger, SDK will try to create a new logger using ENV variables
	// Required ENV variables are: MAXIM_API_KEY and MAXIM_LOG_REPO_ID
	ctx = context.WithValue(ctx, "maxim.logger", logger)
	// Create a chat completion request
	chatCompletion, err := openAiClient.Chat.Completions.New(ctx, openai.ChatCompletionNewParams{
		Messages: openai.F([]openai.ChatCompletionMessageParamUnion{
			openai.SystemMessage("You are a helpful assistant"),
			openai.UserMessage("What the temperature is in New York?"),
		}),
		Tools: openai.F([]openai.ChatCompletionToolParam{
			{
				Type: openai.F(openai.ChatCompletionToolTypeFunction),
				Function: openai.F(openai.FunctionDefinitionParam{
					Name:        openai.String("get_current_weather"),
					Description: openai.String("Get the current weather in a given location"),
					Parameters: openai.F(openai.FunctionParameters(map[string]any{
						"type": "object",
						"properties": map[string]any{
							"location": map[string]any{
								"type":        "string",
								"description": "The city or location to get weather information for",
							},
						},
						"required": []string{"location"},
					})),
				}),
			},
		}),
		Temperature: openai.Float(0.2),
		Model:       openai.F(openai.ChatModelGPT4o),
	})
	if err != nil {
		panic(err.Error())
	}
	println(chatCompletion.Choices[0].Message.Content)

}
