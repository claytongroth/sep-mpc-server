```sh

pip install mcp sentence-transformers chromadb beautifulsoup4 numpy


```


# Config to add:

```json
{
  "mcpServers": {
    "sep": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm", "-v",
        "/Users/claytongroth/DEV/SEP_MCP_SERVER/vectorization/philosophy_vectordb:/app/philosophy_vectordb:rw",
        "philosophy-mcp"
      ]
    }
  }
}
```