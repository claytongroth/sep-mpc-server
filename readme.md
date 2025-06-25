# Stanford Encyclopedia of Philosophy MCP Server

A Model Context Protocol (MCP) server that provides semantic search access to the complete Stanford Encyclopedia of Philosophy through vector embeddings and ChromaDB.

## 🎯 Features

- **Complete SEP Database**: Access to all ~1840 philosophy articles
- **Vector Search**: Semantic search using sentence transformers (all-MiniLM-L6-v2)
- **Docker Containerized**: Easy deployment and consistent environment
- **Claude Desktop Integration**: Direct integration with Claude Desktop client
- **Chunked Content**: Smart text chunking for optimal retrieval accuracy
- **MCP Protocol**: Full Model Context Protocol compliance

## 📋 Prerequisites

- **Python 3.11+**
- **Docker Desktop** 
- **Claude Desktop application**
- **~10GB disk space** for complete database
- **Internet connection** for initial scraping and model downloads

## 🏗️ Project Structure

```
SEP_MCP_SERVER/
├── scraper/
│   └── SEP_scraper.py           # Stanford Encyclopedia scraper
├── vectorization/
│   ├── vectorize_html.py        # HTML to vector conversion
│   └── philosophy_vectordb/     # ChromaDB vector database
├── mcp_server/
│   ├── philosophy_mcp_server.py # Main MCP server
│   ├── mcp_vector_interface.py  # Vector search interface  
│   ├── Dockerfile               # Container definition
│   ├── docker-compose.yml       # Docker Compose config
│   ├── docker_helper.sh         # Helper scripts
│   ├── requirements.txt         # Python dependencies
│   └── test_mcp_server.py       # Server tests
└── README.md                    # This file
```

## 🚀 Complete Setup Guide

### Step 1: Scrape Stanford Encyclopedia of Philosophy

```bash
# Navigate to scraper directory
cd scraper

# Install dependencies
pip install requests beautifulsoup4 lxml

# Run the scraper (takes 30-60 minutes)
python SEP_scraper.py

# Verify scraping results
ls ../data/*.html | wc -l  # Should show ~1840 files
```

**Expected output**: ~1840 HTML files in the `data/` directory

### Step 2: Vectorize Philosophy Content

```bash
# Navigate to vectorization directory
cd ../vectorization

# Install vectorization dependencies
pip install chromadb sentence-transformers beautifulsoup4 torch

# Run vectorization (takes 2-4 hours depending on hardware)
python vectorize_html.py

# Verify database creation
ls -la philosophy_vectordb/
```

**Expected output**: ChromaDB database in `philosophy_vectordb/` directory

### Step 3: Build Docker Container

```bash
# Navigate to MCP server directory
cd ../mcp_server

# Build the Docker image
docker build -t philosophy-mcp .

# Verify image was created
docker images | grep philosophy-mcp
```

### Step 4: Test Docker Container

```bash
# Test database stats
docker run --rm -it \
  -v /absolute/path/to/SEP_MCP_SERVER/vectorization/philosophy_vectordb:/app/philosophy_vectordb:rw \
  philosophy-mcp \
  python3 mcp_vector_interface.py stats

# Test search functionality  
docker run --rm -it \
  -v /absolute/path/to/SEP_MCP_SERVER/vectorization/philosophy_vectordb:/app/philosophy_vectordb:rw \
  philosophy-mcp \
  python3 mcp_vector_interface.py search "consciousness" 3

# List available entries
docker run --rm -it \
  -v /absolute/path/to/SEP_MCP_SERVER/vectorization/philosophy_vectordb:/app/philosophy_vectordb:rw \
  philosophy-mcp \
  python3 mcp_vector_interface.py list
```

**Replace `/absolute/path/to/SEP_MCP_SERVER` with your actual project path!**

### Step 5: Configure Claude Desktop

**Edit Claude Desktop configuration**:

**On macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**On Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "sep": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm", "-v",
        "/absolute/path/to/SEP_MCP_SERVER/vectorization/philosophy_vectordb:/app/philosophy_vectordb:rw",
        "philosophy-mcp"
      ]
    }
  }
}
```

**⚠️ IMPORTANT**: Replace `/absolute/path/to/SEP_MCP_SERVER` with your actual full path!

### Step 6: Restart Claude Desktop

1. **Quit Claude Desktop completely**
2. **Restart Claude Desktop**
3. **Look for the MCP server connection** in the interface

## 🧪 Testing Your Setup

### Test Commands

```bash
# Check database statistics
docker run --rm -it \
  -v /your/path/SEP_MCP_SERVER/vectorization/philosophy_vectordb:/app/philosophy_vectordb:rw \
  philosophy-mcp \
  python3 mcp_vector_interface.py stats

# Search for specific topics
docker run --rm -it \
  -v /your/path/SEP_MCP_SERVER/vectorization/philosophy_vectordb:/app/philosophy_vectordb:rw \
  philosophy-mcp \
  python3 mcp_vector_interface.py search "category theory" 5

docker run --rm -it \
  -v /your/path/SEP_MCP_SERVER/vectorization/philosophy_vectordb:/app/philosophy_vectordb:rw \
  philosophy-mcp \
  python3 mcp_vector_interface.py search "free will" 3
```

### Expected Results

- **Stats should show**: ~1840 entries, thousands of chunks
- **Search should return**: Relevant philosophy passages with relevance scores
- **Claude Desktop should show**: SEP tool available in the interface

## 🛠️ Troubleshooting

### Common Issues

**1. "readonly database" error**
```bash
# Solution: Use :rw instead of :ro in volume mount
-v /path/to/philosophy_vectordb:/app/philosophy_vectordb:rw
```

**2. "No such file or directory"**
```bash
# Solution: Use absolute path, not relative path
# Wrong: -v ./vectorization/philosophy_vectordb:/app/philosophy_vectordb:rw  
# Right: -v /Users/username/SEP_MCP_SERVER/vectorization/philosophy_vectordb:/app/philosophy_vectordb:rw
```

**3. Claude Desktop not connecting**
- Ensure Docker is running
- Check config file path and syntax
- Restart Claude Desktop completely
- Verify volume mount path is correct

**4. Empty search results**
- Verify database was created properly
- Check that vectorization completed successfully
- Test with Docker commands first

### Debug Commands

```bash
# Check if database exists
ls -la vectorization/philosophy_vectordb/

# Test container without volume (should fail gracefully)
docker run --rm -it philosophy-mcp python3 mcp_vector_interface.py stats

# Check Docker container logs
docker run --rm -it philosophy-mcp ls -la /app/

# Verify Python dependencies in container
docker run --rm -it philosophy-mcp pip list
```

## 📚 Usage Examples

Once connected to Claude Desktop, you can ask questions like:

- "Search for information about consciousness in the Stanford Encyclopedia"
- "What does the SEP say about free will?"
- "Find articles related to category theory"
- "Search for content about phenomenology"

## 🔧 Advanced Configuration

### Performance Tuning

- **Chunk size**: Modify `chunk_size` in `vectorize_html.py` for different granularity
- **Model selection**: Change embedding model in vectorization script
- **Memory limits**: Add Docker memory constraints if needed

### Updating Content

```bash
# Re-scrape new/updated articles
cd scraper && python SEP_scraper.py

# Re-vectorize (preserves existing, adds new)
cd vectorization && python vectorize_html.py

# Rebuild container if server code changed
cd mcp_server && docker build -t philosophy-mcp .
```

## 🎉 Success Indicators

✅ **~1840 HTML files** in `data/` directory  
✅ **ChromaDB database** created in `philosophy_vectordb/`  
✅ **Docker container** builds successfully  
✅ **Search commands** return relevant results  
✅ **Claude Desktop** shows SEP tools available  
✅ **MCP server** responds to philosophy queries  

## 📞 Support

If you encounter issues:
1. Verify all prerequisites are installed
2. Check file paths are absolute and correct
3. Ensure Docker Desktop is running
4. Test Docker commands before Claude integration
5. Check Claude Desktop configuration syntax

---

**Total setup time**: 3-5 hours (mostly automated processing)  
**Database size**: ~2-3GB after vectorization  
**Performance**: Sub-second search responses


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