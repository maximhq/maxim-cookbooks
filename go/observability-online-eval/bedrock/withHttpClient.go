package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"

	"github.com/maximhq/maxim-go/middlewares"

	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/bedrockruntime"
	"github.com/aws/aws-sdk-go-v2/service/bedrockruntime/document"
	"github.com/aws/aws-sdk-go-v2/service/bedrockruntime/types"
	"github.com/aws/aws-sdk-go/aws"
)

// manualTracing demonstrates how to manually create and manage traces
// in Maxim. This function creates all required components (trace, generation)
// and sends the data to the Maxim backend, allowing for complete control
// over the tracing process. It establishes a trace, adds a generation,
// makes an OpenAI API call, and records the result.
func usingMaximBedrockHTTPClient() {
	defer logger.Flush()
	// Configure AWS credentials with access key, secret key and region
	cfg, err := config.LoadDefaultConfig(context.Background(),
		config.WithRegion(awsRegion),
		config.WithCredentialsProvider(credentials.NewStaticCredentialsProvider(
			awsAccessKey, // AWS Access Key
			awsSecretKey, // AWS Secret Key
			"",           // Session token (optional)
		)),
		config.WithHTTPClient(middlewares.NewMaximBedrockHTTPClient(logger)),
	)
	if err != nil {
		log.Fatal(err)
	}
	brc := bedrockruntime.NewFromConfig(cfg)
	ctx := context.Background()
	systemMessage := []types.SystemContentBlock{
		&types.SystemContentBlockMemberText{
			Value: "You are a helpful assistant",
		},
	}
	messages := []types.Message{
		{
			Role: types.ConversationRoleUser,
			Content: []types.ContentBlock{
				&types.ContentBlockMemberText{
					Value: "What's the current weather in New York City?",
				},
			},
		},
	}
	// Invoke model
	output, err := brc.Converse(ctx, &bedrockruntime.ConverseInput{
		ModelId:  aws.String(ClaudeModeId),
		System:   systemMessage,
		Messages: messages,
		InferenceConfig: &types.InferenceConfiguration{
			Temperature: aws.Float32(0.2),
		},
		ToolConfig: &types.ToolConfiguration{
			Tools: []types.Tool{
				&types.ToolMemberToolSpec{
					Value: types.ToolSpecification{
						Name:        aws.String("get_current_weather"),
						Description: aws.String("Get current weather data for location"),
						InputSchema: &types.ToolInputSchemaMemberJson{
							Value: document.NewLazyDocument(map[string]interface{}{
								"type": "object",
								"properties": map[string]interface{}{
									"location": map[string]interface{}{
										"type":        "string",
										"description": "location name",
									},
								},
								"required": []string{"location"},
							}),
						},
					},
				},
			},
		},
	})
	// Create a chat completion request
	if err != nil {
		panic(err.Error())
	}
	// Setting the result for the generation
	// We handle ConverseOutput
	jsonOutput, err := json.MarshalIndent(output, "", "  ")
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println(string(jsonOutput))
}
