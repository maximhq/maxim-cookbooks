# Maxim-Go OpenAI Cookbook

This folder contains examples of how to use the [maxim-go](https://github.com/maximhq/maxim-go) SDK to monitor and trace your AI applications using OpenAI SDK.

## Getting Started

To run the examples, you'll need to set your OpenAI API key:

```bash
export OPENAI_KEY=
export MAXIM_API_KEY=
export MAXIM_LOG_REPO_ID=
```

Or create a `.env` file in the root directory with the following content:

```
OPENAI_API_KEY=
MAXIM_API_KEY=
MAXIM_LOG_REPO_ID=
```

### Initialization

```go
// To initialize the Maxim client
maximClient = maxim.Init(&maxim.MaximSDKConfig{Debug: true})
defer maximClient.Cleanup()

// To initialize the logger
logger, err = maximClient.GetLogger(&logging.LoggerConfig{})
if err != nil {
 log.Fatal("Error initializing logger:", err)
}
```

### Manual Tracing

In `openai/manual.go`, you'll find an example of how to manually create and manage traces in Maxim. This approach gives you complete control over the tracing process.

```go
traceId := uuid.New().String()
trace := logger.Trace(&logging.TraceConfig{
 Id:   traceId,
 Name: maxim.StrPtr("Main trace"),
})
// And pass all the other components as written in manual.go
defer trace.End()
```

### Using Middleware (Easy to integrate)

The `openai/usingMiddleware.go` example shows how to set up integration with middleware.

For this, you just have to pass MaximOpenAIMiddleware while creating the OpenAI client.

```go
import (
	"context"

	"github.com/maximhq/maxim-go/middlewares"
	"github.com/openai/openai-go"
	"github.com/openai/openai-go/option"
)

openAiClient := openai.NewClient(
	option.WithAPIKey(openAIKey),
	option.WithMiddleware(middlewares.MaximOpenAIMiddleware),
)
```

If you want to track other services, you can create trace outside. And pass into the context you are using for calling `Chat.Completions`.

```go
// Create trace
traceId := uuid.New().String()
trace := logger.Trace(&logging.TraceConfig{
 Id:   traceId,
 Name: maxim.StrPtr("Main trace"),
})
defer trace.End()

ctx := context.WithValue(context.Background(), "maxim.traceId", traceId)

// Call OpenAI with the context containing the trace ID
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
```

This will attach LLM calls to the trace with ID `traceId`.

## Project Structure

- `main.go`: Sets up environment, initializes clients and loggers
- `manual.go`: Shows how to manually create and manage traces
- `usingMiddleware.go`: Demonstrates similar functionality with OpenAI client middleware approach (automated)

## Dependencies

- [github.com/maximhq/maxim-go](https://github.com/maximhq/maxim-go) - Maxim SDK for Go
- [github.com/openai/openai-go](https://github.com/openai/openai-go) - OpenAI API client for Go

## License

[MIT](LICENSE)
