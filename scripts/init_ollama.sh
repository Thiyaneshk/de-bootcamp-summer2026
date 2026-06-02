#!/bin/bash
#
# Phase 5: Ollama Initialization Script
#
# Check connectivity and setup local LLM models for RAG integration.
#

echo "de-bootcamp-summer2026: Ollama Initialization"
echo "=============================================="

OLLAMA_URL="http://localhost:11434"

# Check if Ollama is running
echo "Checking if Ollama service is running..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$OLLAMA_URL/api/tags")

if [ "$HTTP_STATUS" -ne 200 ]; then
    echo "❌ Error: Ollama is not running at $OLLAMA_URL"
    echo ""
    echo "Please start Ollama:"
    echo "  1. If running locally, open the Ollama app on your Mac."
    echo "  2. If using Docker Compose, run:"
    echo "     docker-compose --profile phase5 up -d ollama"
    echo ""
    exit 1
fi

echo "✅ Ollama is running!"
echo ""

# Query available models
echo "Installed models:"
curl -s "$OLLAMA_URL/api/tags" | grep -o '"name":"[^"]*"' | sed 's/"name":"//; s/"//'

# Check if we have models installed. If not, pull a lightweight model
MODEL_COUNT=$(curl -s "$OLLAMA_URL/api/tags" | grep -o '"name"' | wc -l)

if [ "$MODEL_COUNT" -eq 0 ]; then
    DEFAULT_MODEL="smollm:135m"
    echo ""
    echo "⚠️ No models found in your Ollama instance."
    echo "Pulling lightweight model '$DEFAULT_MODEL' for verification (approx 270MB)..."
    curl -X POST "$OLLAMA_URL/api/pull" -d "{\"name\":\"$DEFAULT_MODEL\"}"
    echo ""
    echo "Installed models after pull:"
    curl -s "$OLLAMA_URL/api/tags" | grep -o '"name":"[^"]*"' | sed 's/"name":"//; s/"//'
fi

echo ""
echo "🎉 Ollama setup check complete!"
