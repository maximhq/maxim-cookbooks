package main

import (
	"log"
	"os"

	"github.com/google/uuid"
	"github.com/joho/godotenv"
	"github.com/maximhq/maxim-go"
	"github.com/maximhq/maxim-go/logging"
)

var maximClient *maxim.Maxim
var logger *logging.Logger
var openAIKey string

func init() {
	var err error
	err = godotenv.Overload()
	if err != nil {
		log.Println("Warning: Error loading .env file:", err)
	}
	openAIKey = os.Getenv("OPENAI_API_KEY")
	if openAIKey == "" {
		log.Fatal("OPENAI_API_KEY environment variable is not set")
	}
	// Initialize the OpenAI client with your API key
	// If not passed, it picks up MAXIM_API_KEY
	maximClient = maxim.Init(&maxim.MaximSDKConfig{Debug: true,ApiKey: os.Getenv("MAXIM_API_KEY")})
	defer maximClient.Cleanup()
	logger, err = maximClient.GetLogger(&logging.LoggerConfig{})
	if err != nil {
		log.Fatal("Error initializing logger:", err)
	}
}

func main() {
	traceId := uuid.New().String()
	trace := logger.Trace(&logging.TraceConfig{
		Name: maxim.StrPtr("toolCall"),
		Id:   traceId,
	})
	defer trace.End()
	spanId := uuid.New().String()
	span := trace.AddSpan(&logging.SpanConfig{
		Name: maxim.StrPtr("toolCall"),
		Id:   spanId,
	})
	defer span.End()
	toolCallId := uuid.New().String()
	toolCallConfig := &logging.ToolCallConfig{
		Id:          toolCallId,
		SpanId:      maxim.StrPtr(spanId),
		Name:        maxim.StrPtr("toolCallName"),
		Description: maxim.StrPtr("toolCallDescription"),
		Args:        maxim.StrPtr("toolCallArgs"),
	}
	toolCall := span.AddToolCall(toolCallConfig)
	defer toolCall.End()
	logger.Flush()
}
