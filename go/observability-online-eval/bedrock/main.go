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
var awsAccessKey string
var awsSecretKey string
var awsRegion string

const ClaudeModeId = "anthropic.claude-3-5-sonnet-20240620-v1:0"

func init() {
	var err error
	err = godotenv.Overload()
	if err != nil {
		log.Println("Warning: Error loading .env file:", err)
	}
	awsAccessKey = os.Getenv("AWS_ACCESS_KEY")
	if awsAccessKey == "" {
		log.Fatal("AWS_ACCESS_KEY environment variable is not set")
	}
	awsSecretKey = os.Getenv("AWS_SECRET_KEY")
	if awsSecretKey == "" {
		log.Fatal("AWS_SECRET_KEY environment variable is not set")
	}
	awsRegion = os.Getenv("AWS_REGION")
	if awsRegion == "" {
		log.Fatal("AWS_REGION environment variable is not set")
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
	manualTracing()
	usingMaximBedrockHTTPClient()
}
