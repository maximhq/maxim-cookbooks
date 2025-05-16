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
var azureOpenAIKey string
var azureOpenAIBaseURL string
var azureDeploymentName string

func init() {
	var err error
	err = godotenv.Overload()
	if err != nil {
		log.Println("Warning: Error loading .env file:", err)
	}	
	azureOpenAIKey = os.Getenv("AZURE_OPENAI_API_KEY")
	if azureOpenAIKey == "" {
		log.Fatal("AZURE_OPENAI_API_KEY environment variable is not set")
	}
	azureOpenAIBaseURL = os.Getenv("AZURE_OPENAI_BASE_URL")
	if azureOpenAIBaseURL == "" {
		log.Fatal("AZURE_OPENAI_BASE_URL environment variable is not set")
	}
	azureDeploymentName = os.Getenv("AZURE_DEPLOYMENT_NAME")
	if azureDeploymentName == "" {
		log.Fatal("AZURE_DEPLOYMENT_NAME environment variable is not set")
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
	usingMaximOpenAITransport()
}
