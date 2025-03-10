package main

import (
	"log"
	"os"

	"github.com/joho/godotenv"

	"github.com/maximhq/maxim-go"
	"github.com/maximhq/maxim-go/logging"
)

var maximClient *maxim.Maxim
var logger *logging.Logger
var openAIKey string

func init() {
	var err error
	err = godotenv.Load()
	if err != nil {
		log.Println("Warning: Error loading .env file:", err)
	}
	openAIKey = os.Getenv("OPENAI_API_KEY")
	if openAIKey == "" {
		log.Fatal("OPENAI_API_KEY environment variable is not set")
	}
	// Initialize the OpenAI client with your API key
	// If not passed, it picks up MAXIM_API_KEY
	maximClient = maxim.Init(&maxim.MaximSDKConfig{Debug: true})
	defer maximClient.Cleanup()
	logger, err = maximClient.GetLogger(&logging.LoggerConfig{})
	if err != nil {
		log.Fatal("Error initializing logger:", err)
	}
}

func main() {
	// manualTracing()
	usingMiddleware()
}
