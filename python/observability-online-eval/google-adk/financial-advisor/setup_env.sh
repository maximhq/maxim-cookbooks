#!/bin/bash

# Setup script for Financial Advisor Agent with Maxim Instrumentation
# This script helps set up the required environment variables

echo "🔑 Setting up environment for Financial Advisor Agent with Maxim"
echo "=================================================================="

# Check if .env file exists
if [ -f ".env" ]; then
    echo "📄 Loading existing .env file..."
    source .env
else
    echo "📄 Creating new .env file..."
    touch .env
fi

# Function to prompt for environment variable
prompt_for_var() {
    local var_name=$1
    local var_description=$2
    local current_value=${!var_name}
    
    if [ -n "$current_value" ]; then
        echo "✅ $var_name is already set: $current_value"
        read -p "   Do you want to change it? (y/N): " change_it
        if [[ $change_it =~ ^[Yy]$ ]]; then
            read -p "   Enter new $var_description: " new_value
            export $var_name="$new_value"
            echo "$var_name=$new_value" >> .env
        fi
    else
        read -p "🔑 Enter $var_description: " new_value
        export $var_name="$new_value"
        echo "$var_name=$new_value" >> .env
    fi
}

echo ""
echo "📋 Required Environment Variables:"
echo ""

# Google Cloud Project ID
prompt_for_var "GOOGLE_CLOUD_PROJECT" "Google Cloud Project ID"

# Google Cloud Location
prompt_for_var "GOOGLE_CLOUD_LOCATION" "Google Cloud Location (e.g., us-central1)"

# Google API Key
prompt_for_var "GOOGLE_API_KEY" "Google API Key"

# Optional: Google Cloud Storage Bucket
read -p "🗄️  Enter Google Cloud Storage Bucket (optional): " bucket
if [ -n "$bucket" ]; then
    export GOOGLE_CLOUD_STORAGE_BUCKET="$bucket"
    echo "GOOGLE_CLOUD_STORAGE_BUCKET=$bucket" >> .env
fi

echo ""
echo "✅ Environment setup complete!"
echo ""
echo "📝 To use these variables in your current session, run:"
echo "   source .env"
echo ""
echo "🚀 To test the agent with Maxim instrumentation, run:"
echo "   python test_with_maxim.py"
echo ""
echo "📊 The agent will be instrumented with Maxim to track:"
echo "   - LLM calls and token usage"
echo "   - Tool executions and results"
echo "   - Agent performance metrics"
echo "   - Error tracking and debugging"
