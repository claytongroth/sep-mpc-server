#!/usr/bin/env python3
"""
Philosophy MCP Server
Provides Claude with access to the Stanford Encyclopedia of Philosophy vector database
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
)

# Import our vector database interface
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_vector_interface import PhilosophyVectorDB

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("philosophy-mcp-server")

class PhilosophyMCPServer:
    def __init__(self):
        self.db = None
        self.server = Server("philosophy-server")
        self.setup_tools()
    
    def setup_tools(self):
        """Define the tools that Claude can use."""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List all available tools."""
            return [
                Tool(
                    name="search_philosophy",
                    description="Search the Stanford Encyclopedia of Philosophy for relevant content about philosophical topics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query about philosophical topics"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return (default: 5)",
                                "default": 5,
                                "minimum": 1,
                                "maximum": 20
                            },
                            "entry_filter": {
                                "type": "string",
                                "description": "Optional filter to search within a specific entry only",
                                "default": None
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_philosophy_entry",
                    description="Get the complete content of a specific philosophy entry",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "entry_name": {
                                "type": "string",
                                "description": "The name of the philosophy entry to retrieve (e.g., 'consciousness', 'free-will')"
                            }
                        },
                        "required": ["entry_name"]
                    }
                ),
                Tool(
                    name="list_philosophy_entries",
                    description="List all available philosophy entries in the database",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_philosophy_stats",
                    description="Get statistics about the philosophy database",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls from Claude."""
            
            # Initialize database if needed
            if self.db is None:
                try:
                    self.db = PhilosophyVectorDB()
                    logger.info("Philosophy vector database initialized")
                except Exception as e:
                    logger.error(f"Failed to initialize database: {e}")
                    return [TextContent(
                        type="text",
                        text=f"Error: Could not initialize philosophy database: {str(e)}"
                    )]
            
            try:
                if name == "search_philosophy":
                    return await self._handle_search(arguments)
                elif name == "get_philosophy_entry":
                    return await self._handle_get_entry(arguments)
                elif name == "list_philosophy_entries":
                    return await self._handle_list_entries(arguments)
                elif name == "get_philosophy_stats":
                    return await self._handle_get_stats(arguments)
                else:
                    return [TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )]
            
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )]
    
    async def _handle_search(self, arguments: dict) -> list[TextContent]:
        """Handle philosophy search requests."""
        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 5)
        entry_filter = arguments.get("entry_filter")
        
        if not query:
            return [TextContent(
                type="text",
                text="Error: Search query is required"
            )]
        
        logger.info(f"Searching for: '{query}' (max_results: {max_results})")
        
        results = self.db.search(query, n_results=max_results, entry_filter=entry_filter)
        
        if not results['results']:
            return [TextContent(
                type="text",
                text=f"No results found for query: '{query}'"
            )]
        
        # Format results for Claude
        response_text = f"Found {len(results['results'])} results for '{query}':\n\n"
        
        for i, result in enumerate(results['results'], 1):
            relevance = f" (relevance: {result['relevance_score']:.3f})" if result['relevance_score'] else ""
            response_text += f"**{i}. {result['title']} - {result['entry_name']}**{relevance}\n"
            response_text += f"{result['text'][:300]}{'...' if len(result['text']) > 300 else ''}\n\n"
        
        return [TextContent(type="text", text=response_text)]
    
    async def _handle_get_entry(self, arguments: dict) -> list[TextContent]:
        """Handle requests for specific philosophy entries."""
        entry_name = arguments.get("entry_name", "")
        
        if not entry_name:
            return [TextContent(
                type="text",
                text="Error: Entry name is required"
            )]
        
        logger.info(f"Getting entry: '{entry_name}'")
        
        result = self.db.get_entry_content(entry_name)
        
        if not result['found']:
            return [TextContent(
                type="text",
                text=f"Entry '{entry_name}' not found in the database"
            )]
        
        # Combine all chunks into full text
        full_text = "\n\n".join([chunk['text'] for chunk in result['chunks']])
        
        response_text = f"**{result['title']}**\n\n"
        response_text += f"Entry: {result['entry_name']}\n"
        response_text += f"Total chunks: {result['total_chunks']}\n\n"
        response_text += full_text
        
        return [TextContent(type="text", text=response_text)]
    
    async def _handle_list_entries(self, arguments: dict) -> list[TextContent]:
        """Handle requests to list all available entries."""
        logger.info("Listing all philosophy entries")
        
        result = self.db.list_entries()
        
        response_text = f"**Philosophy Database Entries** ({result['total_entries']} entries)\n\n"
        
        # Sort entries alphabetically
        sorted_entries = sorted(result['entries'], key=lambda x: x['name'])
        
        for entry in sorted_entries:
            response_text += f"• **{entry['name']}**: {entry['title']} ({entry['chunks']} chunks)\n"
        
        return [TextContent(type="text", text=response_text)]
    
    async def _handle_get_stats(self, arguments: dict) -> list[TextContent]:
        """Handle requests for database statistics."""
        logger.info("Getting database statistics")
        
        stats = self.db.get_stats()
        
        response_text = "**Philosophy Database Statistics**\n\n"
        response_text += f"• Total entries: {stats['total_entries']}\n"
        response_text += f"• Total text chunks: {stats['total_chunks']}\n"
        response_text += f"• Embedding model: {stats['embedding_model']}\n"
        response_text += f"• Database path: {stats['database_path']}\n"
        response_text += f"• Collection name: {stats['collection_name']}\n"
        
        return [TextContent(type="text", text=response_text)]

async def main():
    """Main function to run the MCP server."""
    logger.info("Starting Philosophy MCP Server")
    
    # Create server instance
    mcp_server = PhilosophyMCPServer()
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.server.run(
            read_stream,
            write_stream,
            mcp_server.server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())