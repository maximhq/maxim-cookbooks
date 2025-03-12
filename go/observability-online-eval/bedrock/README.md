# Maxim-Go Bedrock Cookbook

This folder contains examples of how to use the [maxim-go](https://github.com/maximhq/maxim-go) SDK to monitor and trace your AI applications using Bedrock.

## Getting Started

To run the examples, you'll need to set your Berdock API key:

```bash
export MAXIM_API_KEY=
export MAXIM_LOG_REPO_ID=
export AWS_ACCESS_KEY=
export AWS_SECRET_KEY=
export AWS_REGION=
```

Or create a `.env` file in the root directory with the following content:

```
MAXIM_API_KEY=
MAXIM_LOG_REPO_ID=
AWS_ACCESS_KEY=
AWS_SECRET_KEY=
AWS_REGION=
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

In `manual.go`, you'll find an example of how to manually create and manage traces in Maxim. This approach gives you complete control over the tracing process.

```go
traceId := uuid.New().String()
trace := logger.Trace(&logging.TraceConfig{
	Id:   traceId,
	Name: maxim.StrPtr("Main trace"),
})
defer trace.End()
```

### Using MaximBedrockHTTPClient (One line to integrate)

```go
import (
	"context"

	"github.com/maximhq/maxim-go/middlewares"

	"github.com/aws/aws-sdk-go-v2/config"
)

cfg, err := config.LoadDefaultConfig(context.Background(),
config.WithRegion(awsRegion),
config.WithCredentialsProvider(credentials.NewStaticCredentialsProvider(
	awsAccessKey, // AWS Access Key
	awsSecretKey, // AWS Secret Key
	"",           // Session token (optional)
)),
// Add MaximBedrockHTTPClient
config.WithHTTPClient(middlewares.NewMaximBedrockHTTPClient(logger)),
// And you are done
)
```

If you want to track other services, you can create trace outside. And pass into the context you are using for calling converse.

```go
// Create trace
traceId := uuid.New().String()
trace := logger.Trace(&logging.TraceConfig{
	Id:   traceId,
	Name: maxim.StrPtr("Main trace"),
})
defer trace.End()

ctx := context.WithValue(context.Background(), "maxim.traceId", traceId)

// Call converse
output, err := brc.Converse(ctx, &bedrockruntime.ConverseInput {
		ModelId:  aws.String(ClaudeModeId),
		System:   systemMessage,
		Messages: messages,
		InferenceConfig: &types.InferenceConfiguration{
			Temperature: aws.Float32(0.2),
	},...
```

This will attach LLM call made with converse to trace with ID `traceId`.

## Project Structure

- `main.go`: Sets up environment, initializes clients and loggers
- `manual.go`: Shows how to manually create and manage traces
- `withHttpClient.go`: Demonstrates how to use the MaximBedrockHTTPClient middleware for automated tracing

## Dependencies

- [github.com/maximhq/maxim-go](https://github.com/maximhq/maxim-go) - Maxim SDK for Go
- [github.com/aws/aws-sdk-go-v2/service/bedrockruntime](https://github.com/aws/aws-sdk-go-v2/tree/main/service/bedrockruntime) - AWS Bedrock Runtime SDK for Go
- [github.com/aws/aws-sdk-go-v2/config](https://github.com/aws/aws-sdk-go-v2/tree/main/config) - AWS SDK configuration package
- [github.com/aws/aws-sdk-go-v2/credentials](https://github.com/aws/aws-sdk-go-v2/tree/main/credentials) - AWS credentials providers

## License

[MIT](LICENSE)
