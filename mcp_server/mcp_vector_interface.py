#!/usr/bin/env python3
"""
MCP Vector Database Interface (Docker Version)
Provides query functions for MCP servers to access the philosophy vector database.
"""

import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Configuration - Docker paths
VECTOR_DB_PATH = "./philosophy_vectordb"  # Mounted volume in Docker
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "philosophy_entries"

class PhilosophyVectorDB:
    """Interface class for querying the philosophy vector database."""
    
    def __init__(self, db_path: str = VECTOR_DB_PATH, model_name: str = EMBEDDING_MODEL):
        self.db_path = Path(db_path)
        self.model_name = model_name
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"Vector database not found at {db_path}")
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(model_name)
        
        # Initialize Chroma client
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get collection
        self.collection = self.chroma_client.get_collection(name=COLLECTION_NAME)
    
    def search(self, query: str, n_results: int = 5, entry_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Search the vector database for relevant content.
        
        Args:
            query: The search query
            n_results: Number of results to return
            entry_filter: Optional filter by entry name
            
        Returns:
            Dictionary with search results
        """
        query_embedding = self.embedding_model.encode([query])
        
        # Build where clause for filtering
        where_clause = None
        if entry_filter:
            where_clause = {"entry_name": entry_filter}
        
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results,
            where=where_clause
        )
        
        return {
            'query': query,
            'filter': entry_filter,
            'total_results': len(results['ids'][0]),
            'results': [
                {
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'entry_name': results['metadatas'][0][i]['entry_name'],
                    'title': results['metadatas'][0][i]['title'],
                    'chunk_index': results['metadatas'][0][i]['chunk_index'],
                    'relevance_score': 1 - results['distances'][0][i] if 'distances' in results else None
                }
                for i in range(len(results['ids'][0]))
            ]
        }
    
    def get_entry_content(self, entry_name: str) -> Dict[str, Any]:
        """
        Get all content for a specific entry.
        
        Args:
            entry_name: Name of the philosophy entry
            
        Returns:
            Dictionary with all chunks for the entry
        """
        results = self.collection.get(
            where={"entry_name": entry_name}
        )
        
        if not results['ids']:
            return {
                'entry_name': entry_name,
                'found': False,
                'chunks': []
            }
        
        # Sort chunks by index
        chunks_data = list(zip(
            results['ids'],
            results['documents'],
            results['metadatas']
        ))
        chunks_data.sort(key=lambda x: x[2]['chunk_index'])
        
        return {
            'entry_name': entry_name,
            'found': True,
            'title': chunks_data[0][2]['title'],
            'total_chunks': len(chunks_data),
            'chunks': [
                {
                    'id': chunk_id,
                    'text': doc,
                    'chunk_index': meta['chunk_index']
                }
                for chunk_id, doc, meta in chunks_data
            ]
        }
    
    def list_entries(self) -> Dict[str, Any]:
        """
        List all available philosophy entries.
        
        Returns:
            Dictionary with entry information
        """
        # Get a sample of all documents to extract entry names
        all_results = self.collection.get()
        
        entries = {}
        for metadata in all_results['metadatas']:
            entry_name = metadata['entry_name']
            if entry_name not in entries:
                entries[entry_name] = {
                    'name': entry_name,
                    'title': metadata['title'],
                    'chunks': 0
                }
            entries[entry_name]['chunks'] += 1
        
        return {
            'total_entries': len(entries),
            'entries': list(entries.values())
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        count = self.collection.count()
        entries_info = self.list_entries()
        
        return {
            'total_chunks': count,
            'total_entries': entries_info['total_entries'],
            'embedding_model': self.model_name,
            'database_path': str(self.db_path),
            'collection_name': COLLECTION_NAME
        }

# MCP Server compatible functions
def mcp_search(query: str, n_results: int = 5, entry_filter: Optional[str] = None) -> str:
    """MCP-compatible search function."""
    try:
        db = PhilosophyVectorDB()
        results = db.search(query, n_results, entry_filter)
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

def mcp_get_entry(entry_name: str) -> str:
    """MCP-compatible function to get full entry content."""
    try:
        db = PhilosophyVectorDB()
        results = db.get_entry_content(entry_name)
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

def mcp_list_entries() -> str:
    """MCP-compatible function to list all entries."""
    try:
        db = PhilosophyVectorDB()
        results = db.list_entries()
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

def mcp_get_stats() -> str:
    """MCP-compatible function to get database stats."""
    try:
        db = PhilosophyVectorDB()
        results = db.get_stats()
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

# Command line interface for testing
def main():
    """Command line interface for testing the vector database."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python mcp_vector_interface.py search 'your query'")
        print("  python mcp_vector_interface.py entry 'entry_name'")
        print("  python mcp_vector_interface.py list")
        print("  python mcp_vector_interface.py stats")
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == "search":
            if len(sys.argv) < 3:
                print("Please provide a search query")
                return
            query = sys.argv[2]
            n_results = int(sys.argv[3]) if len(sys.argv) > 3 else 5
            print(mcp_search(query, n_results))
        
        elif command == "entry":
            if len(sys.argv) < 3:
                print("Please provide an entry name")
                return
            entry_name = sys.argv[2]
            print(mcp_get_entry(entry_name))
        
        elif command == "list":
            print(mcp_list_entries())
        
        elif command == "stats":
            print(mcp_get_stats())
        
        else:
            print(f"Unknown command: {command}")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()