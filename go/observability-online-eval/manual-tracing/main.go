package main

import (
	"log"
	"time"

	"github.com/google/uuid"
	"github.com/joho/godotenv"
	"github.com/maximhq/maxim-go"
	"github.com/maximhq/maxim-go/logging"
)

var maximClient *maxim.Maxim
var logger *logging.Logger

func init(){
	var err error
	err = godotenv.Overload()
	if err != nil {
		log.Println("Warning: Error loading .env file:", err)
	}
	maximClient = maxim.Init(&maxim.MaximSDKConfig{Debug: true})	
	logger, err = maximClient.GetLogger(&logging.LoggerConfig{})
	if err != nil {
		log.Fatal("Error initializing logger:", err)
	}
}

// In this flow
// We will create a trace
// Then add a span to it
// And then add a generation to the span
func main(){
	
	trace := logger.Trace(&logging.TraceConfig{
		Id: uuid.New().String(),
		Name: maxim.StrPtr("test trace"),
	})
	span := trace.AddSpan(&logging.SpanConfig{
		Id: uuid.New().String(),
		Name: maxim.StrPtr("test span"),
	})
	generation := span.AddGeneration(&logging.GenerationConfig{
		Id: uuid.New().String(),
		Name: maxim.StrPtr("test generation"),
		Provider: "openai",
		Model: "gpt-4o",
		Messages: []logging.CompletionRequest{
			{
				Role: "user",
				Content: "Hello, world!",
			},
		},
		ModelParameters: map[string]interface{}{
			"temperature": 0.5,
		},
	})
	time.Sleep(1 * time.Second)
	generation.SetResult(map[string]interface{}{
		"id": uuid.New().String(),
		"model": "gpt-4o",
		"created": time.Now().Unix(),
		"choices": []map[string]interface{}{
			{
				"message": map[string]interface{}{
					"role": "assistant",
					"content": "Hello, world!",
				},
			},
		},
		"usage": map[string]interface{}{
			"prompt_tokens": 10,
			"completion_tokens": 10,
			"total_tokens": 20,
		},
	})	
	span.End()
	trace.End()	
	logger.Flush()
}