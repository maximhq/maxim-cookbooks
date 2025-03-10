# Maxim-Go OpenAI Cookbook

This folder contains examples of how to use the [maxim-go](https://github.com/maximhq/maxim-go) SDK to monitor and trace your AI applications using Azure OpenAI SDK.

## Getting Started

To run the examples, you'll need to set your OpenAI API key:

```bash
export AZURE_OPENAI_API_KEY=
export AZURE_OPENAI_BASE_URL=
export AZURE_DEPLOYMENT_NAME=
export MAXIM_API_KEY=
export MAXIM_LOG_REPO_ID=
```

Or create a `.env` file in the root directory with the following content:

```
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_BASE_URL=
AZURE_DEPLOYMENT_NAME=
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

The `openai/withTransport.go` example shows how to set up integration with middleware.

For this, you just have to pass MaximOpenAITransport while creating the Azure client.

```go
import (
	"context"

	"github.com/Azure/azure-sdk-for-go/sdk/ai/azopenai"
	"github.com/Azure/azure-sdk-for-go/sdk/azcore"
	"github.com/maximhq/maxim-go/middlewares"
)

keyCredential := azcore.NewKeyCredential(azureOpenAIKey)
clientOptions := azopenai.ClientOptions{}
clientOptions.Transport = &middlewares.MaximOpenAITransport{
	Logger: logger, // This is maxim logger
}
azOpenai, err := azopenai.NewClientWithKeyCredential(azureOpenAIBaseURL, keyCredential, &clientOptions)
if err != nil {
	panic(err)
}
```

If you want to track other services, you can create trace outside. And pass into the context you are using for calling `GetChatCompletions`.

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
```

This will attach LLM calls to the trace with ID `traceId`.

## Project Structure

- `azure/main.go`: Sets up environment, initializes clients and loggers
- `azure/manual.go`: Shows how to manually create and manage traces
- `azure/usingTransport.go`: Demonstrates similar functionality with MAximOpenAITransport (automated)

## Dependencies

- [github.com/maximhq/maxim-go](https://github.com/maximhq/maxim-go) - Maxim SDK for Go
- [github.com/Azure/azure-sdk-for-go/sdk/ai/azopenai](https://github.com/Azure/azure-sdk-for-go/tree/main/sdk/ai/azopenai) - Azure OpenAI API client for Go

## License

[MIT](LICENSE)
