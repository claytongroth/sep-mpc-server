#!/bin/bash
# Docker Helper Script for Philosophy MCP Server
# Save as: mcp_server/docker_helper.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
IMAGE_NAME="philosophy-mcp"

echo "🐳 Philosophy MCP Server - Docker Helper"
echo "========================================"

case "${1:-help}" in
    "build")
        echo "🔨 Building Docker image..."
        cd "$SCRIPT_DIR"
        docker build -t "$IMAGE_NAME" .
        echo "✅ Build complete!"
        ;;
    
    "test")
        echo "🧪 Testing vector database access..."
        docker run --rm -it \
            -v "$PROJECT_ROOT/vectorization/philosophy_vectordb:/app/philosophy_vectordb:ro" \
            "$IMAGE_NAME" \
            python3 mcp_vector_interface.py stats
        ;;
    
    "search")
        if [ -z "$2" ]; then
            echo "Usage: $0 search 'your query'"
            exit 1
        fi
        echo "🔍 Searching for: $2"
        docker run --rm -it \
            -v "$PROJECT_ROOT/vectorization/philosophy_vectordb:/app/philosophy_vectordb:ro" \
            "$IMAGE_NAME" \
            python3 mcp_vector_interface.py search "$2"
        ;;
    
    "run")
        echo "🚀 Running MCP server..."
        docker run --rm -i \
            -v "$PROJECT_ROOT/vectorization/philosophy_vectordb:/app/philosophy_vectordb:ro" \
            "$IMAGE_NAME"
        ;;
    
    "shell")
        echo "🐚 Opening shell in container..."
        docker run --rm -it \
            -v "$PROJECT_ROOT/vectorization/philosophy_vectordb:/app/philosophy_vectordb:ro" \
            "$IMAGE_NAME" \
            /bin/bash
        ;;
    
    "clean")
        echo "🧹 Cleaning up Docker resources..."
        docker rmi "$IMAGE_NAME" 2>/dev/null || echo "Image not found"
        docker system prune -f
        echo "✅ Cleanup complete!"
        ;;
    
    "logs")
        echo "📋 Recent Docker logs..."
        docker logs $(docker ps -q --filter ancestor="$IMAGE_NAME") 2>/dev/null || echo "No running containers found"
        ;;
    
    "config")
        echo "📝 Claude Desktop configuration:"
        echo "{"
        echo "  \"mcpServers\": {"
        echo "    \"sep\": {"
        echo "      \"command\": \"docker\","
        echo "      \"args\": ["
        echo "        \"run\","
        echo "        \"-i\","
        echo "        \"--rm\","
        echo "        \"-v\","
        echo "        \"$PROJECT_ROOT/vectorization/philosophy_vectordb:/app/philosophy_vectordb:ro\","
        echo "        \"$IMAGE_NAME\""
        echo "      ]"
        echo "    }"
        echo "  }"
        echo "}"
        ;;
    
    "help"|*)
        echo "Available commands:"
        echo "  build   - Build the Docker image"
        echo "  test    - Test vector database access"
        echo "  search  - Search the database (usage: search 'query')"
        echo "  run     - Run the MCP server"
        echo "  shell   - Open interactive shell in container"
        echo "  clean   - Remove image and clean up"
        echo "  logs    - Show container logs"
        echo "  config  - Show Claude Desktop configuration"
        echo "  help    - Show this help"
        ;;
esac