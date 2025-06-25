#!/usr/bin/env python3
"""
Optimized HTML to Vector Database Processor
With debugging, progress tracking, and performance optimizations.
"""

import os
import re
import uuid
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from bs4 import BeautifulSoup
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np

# Configuration
HTML_DIRECTORY = "../data"
VECTOR_DB_PATH = "./philosophy_vectordb"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
COLLECTION_NAME = "philosophy_entries"
BATCH_SIZE = 50  # Process files in smaller batches

class OptimizedHTMLToVectorDB:
    def __init__(self, html_dir: str, db_path: str, model_name: str = EMBEDDING_MODEL):
        self.html_dir = Path(html_dir)
        self.db_path = Path(db_path)
        self.model_name = model_name
        
        # Initialize embedding model
        print(f"Loading embedding model: {model_name}")
        start_time = time.time()
        self.embedding_model = SentenceTransformer(model_name)
        print(f"Model loaded in {time.time() - start_time:.2f} seconds")
        
        # Initialize Chroma client
        self.db_path.mkdir(exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Philosophy encyclopedia entries"}
        )
    
    def get_file_size(self, filepath: Path) -> str:
        """Get human readable file size."""
        size = filepath.stat().st_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"
    
    def extract_text_from_html(self, html_content: str, filename: str) -> Dict[str, str]:
        """Extract clean text and metadata from HTML with timing."""
        start_time = time.time()
        
        # Limit HTML size for processing (skip very large files)
        if len(html_content) > 10_000_000:  # 10MB limit
            print(f"    WARNING: File {filename} is very large ({len(html_content):,} chars), truncating...")
            html_content = html_content[:10_000_000]
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try to extract title
        title = None
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
        
        # Try to find main content
        main_content = None
        content_selectors = [
            '#main-text', '.entry-content', '#content', 'main', '.main-content',
            'article', '.article', '#article', '.post-content', '.entry-text'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                main_content = content_elem.get_text()
                break
        
        # Fallback: get all text
        if not main_content:
            main_content = soup.get_text()
        
        # Clean up text more efficiently
        main_content = re.sub(r'\s+', ' ', main_content).strip()
        
        # Limit content size (very long texts can cause issues)
        if len(main_content) > 1_000_000:  # 1MB text limit
            print(f"    WARNING: Extracted text is very long ({len(main_content):,} chars), truncating...")
            main_content = main_content[:1_000_000]
        
        entry_name = Path(filename).stem
        
        extract_time = time.time() - start_time
        print(f"    Text extraction: {extract_time:.2f}s, {len(main_content):,} chars")
        
        return {
            'title': title or entry_name.title(),
            'content': main_content,
            'entry_name': entry_name,
            'filename': filename
        }
    
    def chunk_text_optimized(self, text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
        """Optimized text chunking with better sentence boundary detection."""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            
            # Try to break at sentence boundary (more efficient)
            if end < len(text):
                # Look backwards from end for sentence ending
                search_start = max(start, end - 200)  # Don't search too far back
                
                for i in range(end - 1, search_start - 1, -1):
                    if text[i] in '.!?' and i + 1 < len(text) and text[i + 1].isspace():
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk and len(chunk) > 50:  # Skip very short chunks
                chunks.append(chunk)
            
            # Move start position
            start = end - overlap
            if start >= len(text) - overlap:  # Avoid infinite loop
                break
        
        return chunks
    
    def process_single_file(self, html_file: Path, file_index: int, total_files: int) -> List[Dict[str, Any]]:
        """Process a single HTML file with detailed timing."""
        print(f"\n[{file_index}/{total_files}] Processing: {html_file.name}")
        print(f"    File size: {self.get_file_size(html_file)}")
        
        start_time = time.time()
        documents = []
        
        try:
            # Read file
            read_start = time.time()
            with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            print(f"    File read: {time.time() - read_start:.2f}s")
            
            # Extract text and metadata
            extracted = self.extract_text_from_html(html_content, html_file.name)
            
            # Chunk the content
            chunk_start = time.time()
            chunks = self.chunk_text_optimized(extracted['content'])
            print(f"    Chunking: {time.time() - chunk_start:.2f}s, {len(chunks)} chunks")
            
            # Create document entries
            for j, chunk in enumerate(chunks):
                doc = {
                    'id': f"{extracted['entry_name']}_chunk_{j}",
                    'text': chunk,
                    'metadata': {
                        'entry_name': extracted['entry_name'],
                        'title': extracted['title'],
                        'filename': extracted['filename'],
                        'chunk_index': j,
                        'total_chunks': len(chunks),
                        'processed_at': datetime.now().isoformat()
                    }
                }
                documents.append(doc)
            
            total_time = time.time() - start_time
            print(f"    ✓ Completed in {total_time:.2f}s")
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
        
        return documents
    
    def process_html_files_batched(self, max_files: Optional[int] = None) -> List[Dict[str, Any]]:
        """Process HTML files in batches for better memory management."""
        all_documents = []
        html_files = list(self.html_dir.glob("*.html"))
        
        if max_files:
            html_files = html_files[:max_files]
            print(f"Limiting to first {max_files} files for testing")
        
        print(f"Found {len(html_files)} HTML files to process")
        
        # Process in batches
        for batch_start in range(0, len(html_files), BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, len(html_files))
            batch_files = html_files[batch_start:batch_end]
            
            print(f"\n{'='*60}")
            print(f"Processing batch {batch_start//BATCH_SIZE + 1}/{(len(html_files) + BATCH_SIZE - 1)//BATCH_SIZE}")
            print(f"Files {batch_start + 1} to {batch_end} of {len(html_files)}")
            print(f"{'='*60}")
            
            batch_documents = []
            batch_start_time = time.time()
            
            for i, html_file in enumerate(batch_files):
                file_docs = self.process_single_file(html_file, batch_start + i + 1, len(html_files))
                batch_documents.extend(file_docs)
            
            batch_time = time.time() - batch_start_time
            print(f"\nBatch completed in {batch_time:.2f}s")
            print(f"Documents in batch: {len(batch_documents)}")
            print(f"Average time per file: {batch_time/len(batch_files):.2f}s")
            
            all_documents.extend(batch_documents)
            
            # Store batch immediately to avoid memory issues
            if batch_documents:
                print("Storing batch in vector database...")
                self.store_in_vectordb_batch(batch_documents)
        
        return all_documents
    
    def generate_embeddings_batched(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Generate embeddings in batches to avoid memory issues."""
        print(f"Generating embeddings for {len(texts)} texts in batches of {batch_size}...")
        
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            print(f"  Embedding batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
            
            batch_embeddings = self.embedding_model.encode(batch_texts, show_progress_bar=False)
            all_embeddings.append(batch_embeddings)
        
        return np.vstack(all_embeddings)
    
    def store_in_vectordb_batch(self, documents: List[Dict[str, Any]]):
        """Store a batch of documents in the vector database."""
        if not documents:
            return
        
        print(f"Storing {len(documents)} documents...")
        start_time = time.time()
        
        # Extract texts
        texts = [doc['text'] for doc in documents]
        
        # Generate embeddings
        embeddings = self.generate_embeddings_batched(texts)
        
        # Prepare data
        ids = [doc['id'] for doc in documents]
        metadatas = [doc['metadata'] for doc in documents]
        
        # Store in Chroma (in smaller sub-batches)
        chroma_batch_size = 100
        for i in range(0, len(documents), chroma_batch_size):
            end = min(i + chroma_batch_size, len(documents))
            
            self.collection.add(
                embeddings=embeddings[i:end].tolist(),
                documents=texts[i:end],
                metadatas=metadatas[i:end],
                ids=ids[i:end]
            )
        
        store_time = time.time() - start_time
        print(f"✓ Stored in {store_time:.2f}s")
    
    def query(self, query_text: str, n_results: int = 5) -> Dict[str, Any]:
        """Query the vector database."""
        query_embedding = self.embedding_model.encode([query_text])
        
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results
        )
        
        return {
            'query': query_text,
            'results': [
                {
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                }
                for i in range(len(results['ids'][0]))
            ]
        }
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        count = self.collection.count()
        
        # Get sample
        sample_size = min(10, count)
        sample = self.collection.get(limit=sample_size) if count > 0 else {'metadatas': []}
        
        entry_names = set()
        if sample['metadatas']:
            entry_names = {meta.get('entry_name', 'unknown') for meta in sample['metadatas']}
        
        return {
            'total_chunks': count,
            'embedding_model': self.model_name,
            'collection_name': COLLECTION_NAME,
            'sample_entries': list(entry_names),
            'database_path': str(self.db_path)
        }

def main():
    """Main function with testing options."""
    print("Optimized HTML to Vector Database Processor")
    print("=" * 60)
    
    processor = OptimizedHTMLToVectorDB(HTML_DIRECTORY, VECTOR_DB_PATH)
    
    # Check directory
    if not processor.html_dir.exists():
        print(f"Error: Directory '{HTML_DIRECTORY}' not found!")
        return
    
    html_files = list(processor.html_dir.glob("*.html"))
    if not html_files:
        print(f"Error: No HTML files found!")
        return
    
    print(f"Found {len(html_files)} HTML files")
    
    # For testing, process only a few files first
    test_mode = input("Test with first 5 files only? (y/n): ").lower().strip() == 'y'
    max_files = 5 if test_mode else None
    
    # Process files
    start_time = time.time()
    documents = processor.process_html_files_batched(max_files=max_files)
    total_time = time.time() - start_time
    
    print(f"\n{'='*60}")
    print("PROCESSING COMPLETE")
    print(f"Total time: {total_time:.2f}s")
    print(f"Total documents created: {len(documents)}")
    if documents:
        print(f"Average time per document: {total_time/len(documents):.3f}s")
    
    # Show stats
    stats = processor.get_collection_stats()
    print(f"Database chunks: {stats['total_chunks']}")
    
    # Test query
    if stats['total_chunks'] > 0:
        print("\nTesting query...")
        results = processor.query("consciousness", n_results=3)
        for i, result in enumerate(results['results']):
            print(f"  {i+1}. {result['metadata']['entry_name']}")

if __name__ == "__main__":
    main()