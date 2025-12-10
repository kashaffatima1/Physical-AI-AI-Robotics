#!/usr/bin/env python3
"""
RAG-based Chatbot for Physical AI Textbook
This module provides a Retrieval-Augmented Generation chatbot for textbook content queries
"""

import os
import json
import re
from flask import Flask, request, jsonify
from typing import List, Dict, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import pickle
import hashlib
from datetime import datetime


# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')


class TextbookRAG:
    """Retrieval-Augmented Generation system for Physical AI textbook"""

    def __init__(self):
        self.documents = []  # List of document texts
        self.document_metadata = []  # Metadata for each document
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=10000,
            ngram_range=(1, 2)
        )
        self.document_vectors = None
        self.chunks = []  # Text chunks for retrieval
        self.chunk_vectors = None
        self.chunk_metadata = []  # Metadata for each chunk

    def load_textbook_content(self, content_dir: str = "physical-ai-textbook/docs"):
        """Load textbook content from markdown files"""
        import os

        self.documents = []
        self.document_metadata = []

        for root, dirs, files in os.walk(content_dir):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                        # Add to documents
                        self.documents.append(content)
                        self.document_metadata.append({
                            'file_path': file_path,
                            'title': os.path.basename(file_path),
                            'module': os.path.basename(root)
                        })

        print(f"Loaded {len(self.documents)} documents")

    def chunk_text(self, max_chunk_size: int = 500):
        """Split documents into chunks for retrieval"""
        self.chunks = []
        self.chunk_metadata = []

        for doc_idx, doc in enumerate(self.documents):
            # Split into sentences
            sentences = sent_tokenize(doc)

            current_chunk = ""
            current_metadata = self.document_metadata[doc_idx].copy()

            for sentence in sentences:
                if len(current_chunk) + len(sentence) < max_chunk_size:
                    current_chunk += " " + sentence
                else:
                    # Save current chunk
                    if current_chunk.strip():
                        self.chunks.append(current_chunk.strip())
                        current_metadata['chunk_id'] = len(self.chunks) - 1
                        self.chunk_metadata.append(current_metadata.copy())

                    # Start new chunk
                    current_chunk = sentence

            # Add last chunk if it exists
            if current_chunk.strip():
                self.chunks.append(current_chunk.strip())
                current_metadata['chunk_id'] = len(self.chunks) - 1
                self.chunk_metadata.append(current_metadata.copy())

        print(f"Created {len(self.chunks)} text chunks")

    def build_index(self):
        """Build TF-IDF index for retrieval"""
        if not self.chunks:
            raise ValueError("No chunks available. Call chunk_text() first.")

        # Fit vectorizer on chunks
        self.chunk_vectors = self.vectorizer.fit_transform(self.chunks)
        print("Index built successfully")

    def retrieve_relevant_chunks(self, query: str, top_k: int = 3) -> List[Tuple[str, Dict]]:
        """Retrieve most relevant chunks for a query"""
        if self.chunk_vectors is None:
            raise ValueError("Index not built. Call build_index() first.")

        # Transform query
        query_vector = self.vectorizer.transform([query])

        # Calculate similarities
        similarities = cosine_similarity(query_vector, self.chunk_vectors).flatten()

        # Get top-k most similar chunks
        top_indices = similarities.argsort()[-top_k:][::-1]

        results = []
        for idx in top_indices:
            if similarities[idx] > 0.1:  # Only return chunks with significant similarity
                results.append((self.chunks[idx], self.chunk_metadata[idx]))

        return results

    def generate_response(self, query: str, context_chunks: List[str]) -> str:
        """Generate response using retrieved context"""
        if not context_chunks:
            return "I couldn't find relevant information in the textbook to answer your question."

        # Combine context chunks
        context = " ".join(context_chunks)

        # Create a prompt for response generation
        prompt = f"""
        Based on the following textbook content, please answer the question:

        Context: {context}

        Question: {query}

        Please provide a comprehensive answer based on the provided context.
        If the context doesn't contain enough information to answer the question,
        please say so.
        """

        # For now, we'll return a simple response based on context
        # In a real implementation, you would use a language model here
        response = self._simple_response_generation(query, context)
        return response

    def _simple_response_generation(self, query: str, context: str) -> str:
        """Simple response generation (in a real system, use a language model)"""
        # Extract key terms from query
        query_words = set(word_tokenize(query.lower()))

        # Find sentences in context that contain query terms
        sentences = sent_tokenize(context)
        relevant_sentences = []

        for sentence in sentences:
            sentence_words = set(word_tokenize(sentence.lower()))
            if query_words.intersection(sentence_words):
                relevant_sentences.append(sentence)

        if relevant_sentences:
            # Return the most relevant sentences
            response = "Based on the textbook: " + " ".join(relevant_sentences[:3])
        else:
            # If no direct matches, return the first few sentences of context
            response = "Based on the textbook: " + " ".join(sentences[:3])

        # Add a note about the response being generated
        response += "\n\nNote: This response is generated based on textbook content retrieval. For complete information, please refer to the original textbook sections."

        return response

    def query(self, question: str, top_k: int = 3) -> Dict:
        """Main query interface"""
        # Retrieve relevant chunks
        relevant_chunks_with_meta = self.retrieve_relevant_chunks(question, top_k)

        if not relevant_chunks_with_meta:
            return {
                'question': question,
                'answer': "I couldn't find relevant information in the textbook to answer your question.",
                'sources': [],
                'confidence': 0.0
            }

        # Extract just the text chunks
        chunks = [chunk for chunk, meta in relevant_chunks_with_meta]
        metas = [meta for chunk, meta in relevant_chunks_with_meta]

        # Generate response
        answer = self.generate_response(question, chunks)

        # Calculate confidence based on similarity scores
        confidence = np.mean([0.8 for _ in chunks])  # Simplified confidence calculation

        return {
            'question': question,
            'answer': answer,
            'sources': metas,
            'confidence': float(confidence)
        }


# Initialize Flask app
app = Flask(__name__)
rag_system = TextbookRAG()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Physical AI Textbook RAG Chatbot',
        'version': '1.0.0'
    })


@app.route('/query', methods=['POST'])
def handle_query():
    """Handle a query to the RAG system"""
    try:
        data = request.get_json()

        if not data or 'question' not in data:
            return jsonify({
                'error': 'Missing question in request body',
                'message': 'Please provide a question to answer'
            }), 400

        question = data['question']
        top_k = data.get('top_k', 3)

        # Perform RAG query
        result = rag_system.query(question, top_k=top_k)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'error': 'An error occurred while processing the query',
            'message': str(e)
        }), 500


@app.route('/initialize', methods=['POST'])
def initialize_rag():
    """Initialize the RAG system with textbook content"""
    try:
        data = request.get_json()
        content_dir = data.get('content_dir', 'physical-ai-textbook/docs')

        # Load textbook content
        rag_system.load_textbook_content(content_dir)

        # Chunk the text
        rag_system.chunk_text()

        # Build the index
        rag_system.build_index()

        return jsonify({
            'status': 'success',
            'message': f'RAG system initialized with {len(rag_system.chunks)} chunks from {len(rag_system.documents)} documents',
            'content_dir': content_dir
        })

    except Exception as e:
        return jsonify({
            'error': 'An error occurred while initializing RAG system',
            'message': str(e)
        }), 500


@app.route('/search', methods=['POST'])
def search_content():
    """Search for content in the textbook"""
    try:
        data = request.get_json()

        if not data or 'query' not in data:
            return jsonify({
                'error': 'Missing query in request body',
                'message': 'Please provide a search query'
            }), 400

        query = data['query']
        top_k = data.get('top_k', 5)

        # Retrieve relevant chunks
        relevant_chunks_with_meta = rag_system.retrieve_relevant_chunks(query, top_k)

        results = []
        for chunk, meta in relevant_chunks_with_meta:
            results.append({
                'content': chunk[:500] + "..." if len(chunk) > 500 else chunk,  # Truncate long content
                'metadata': meta,
                'preview': chunk[:200] + "..." if len(chunk) > 200 else chunk
            })

        return jsonify({
            'query': query,
            'results': results,
            'count': len(results)
        })

    except Exception as e:
        return jsonify({
            'error': 'An error occurred while searching content',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    print("Starting Physical AI Textbook RAG Chatbot...")
    print("Important: Initialize the RAG system first by calling /initialize endpoint")
    print("API endpoints:")
    print("  POST /initialize - Initialize RAG with textbook content")
    print("  POST /query - Ask questions about textbook content")
    print("  POST /search - Search for content in textbook")
    print("  GET  /health - Health check")

    # Note: In a real deployment, you would initialize the RAG system here
    # For this example, we'll just start the server
    app.run(host='0.0.0.0', port=5003, debug=True)