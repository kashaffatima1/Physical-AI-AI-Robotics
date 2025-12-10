#!/usr/bin/env python3
"""
AI-Powered Summary Generator for Physical AI Textbook
This module provides an endpoint for generating chapter summaries
"""

import json
from flask import Flask, request, jsonify
import re
from typing import List, Dict, Optional


class SummaryGenerator:
    """A class to generate summaries for Physical AI textbook content"""

    def __init__(self):
        self.max_summary_length = 300  # Maximum characters for summary
        self.min_summary_length = 50   # Minimum characters for summary

    def generate_summary(self, text: str, max_sentences: int = 3) -> str:
        """
        Generate a summary of the provided text

        Args:
            text: Input text to summarize
            max_sentences: Maximum number of sentences in the summary

        Returns:
            A summary of the text
        """
        if not text or len(text.strip()) < 10:
            return "Text too short to summarize."

        # Clean up the text
        cleaned_text = self._clean_text(text)

        # Split into sentences
        sentences = self._split_into_sentences(cleaned_text)

        if len(sentences) <= max_sentences:
            return ' '.join(sentences)

        # Select important sentences (first, middle, and last)
        summary_sentences = self._select_important_sentences(sentences, max_sentences)

        summary = ' '.join(summary_sentences)

        # Ensure the summary is within length limits
        if len(summary) > self.max_summary_length:
            summary = summary[:self.max_summary_length] + "..."

        return summary

    def _clean_text(self, text: str) -> str:
        """Clean the input text by removing extra whitespace and formatting"""
        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Remove italics
        text = re.sub(r'`(.*?)`', r'\1', text)        # Remove code formatting
        text = re.sub(r'#+\s+', '', text)             # Remove header markers
        text = re.sub(r'\[.*?\]\(.*?\)', r'\1', text) # Remove links

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Split on sentence-ending punctuation
        sentences = re.split(r'[.!?]+', text)

        # Clean up sentences and remove empty ones
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def _select_important_sentences(self, sentences: List[str], max_sentences: int) -> List[str]:
        """Select the most important sentences for the summary"""
        if len(sentences) <= max_sentences:
            return sentences

        # Simple strategy: take first, middle, and last sentences
        selected = []

        if max_sentences >= 1:
            selected.append(sentences[0])  # First sentence

        if max_sentences >= 2 and len(sentences) > 1:
            selected.append(sentences[len(sentences)//2])  # Middle sentence

        if max_sentences >= 3 and len(sentences) > 2:
            selected.append(sentences[-1])  # Last sentence

        # If we need more sentences, add them from the beginning
        for i in range(1, min(max_sentences - len(selected), len(sentences))):
            if len(selected) < max_sentences:
                # Avoid adding the same sentence again
                if i < len(sentences) and sentences[i] not in selected:
                    selected.append(sentences[i])

        return selected[:max_sentences]


# Initialize Flask app
app = Flask(__name__)
summary_generator = SummaryGenerator()


@app.route('/summarize', methods=['POST'])
def summarize_text():
    """
    API endpoint to generate summary for provided text
    Expected JSON format: {"text": "your text here", "max_sentences": 3}
    """
    try:
        data = request.get_json()

        if not data or 'text' not in data:
            return jsonify({
                'error': 'Missing text in request body',
                'message': 'Please provide text to summarize in the request body'
            }), 400

        text = data['text']
        max_sentences = data.get('max_sentences', 3)

        # Validate max_sentences
        if not isinstance(max_sentences, int) or max_sentences < 1 or max_sentences > 10:
            max_sentences = 3

        summary = summary_generator.generate_summary(text, max_sentences)

        return jsonify({
            'summary': summary,
            'original_length': len(text),
            'summary_length': len(summary),
            'compression_ratio': round(len(summary) / len(text), 2) if len(text) > 0 else 0
        })

    except Exception as e:
        return jsonify({
            'error': 'An error occurred while generating summary',
            'message': str(e)
        }), 500


@app.route('/summarize/chapter', methods=['POST'])
def summarize_chapter():
    """
    API endpoint to generate summary for a textbook chapter
    Expected JSON format: {"title": "Chapter Title", "content": "chapter content", "module": "module-1"}
    """
    try:
        data = request.get_json()

        if not data or 'content' not in data:
            return jsonify({
                'error': 'Missing content in request body',
                'message': 'Please provide chapter content to summarize'
            }), 400

        title = data.get('title', 'Untitled Chapter')
        content = data['content']
        module = data.get('module', 'unknown')

        # Generate summary
        summary = summary_generator.generate_summary(content, max_sentences=5)

        # Create a more detailed response for textbook chapters
        return jsonify({
            'title': title,
            'module': module,
            'summary': summary,
            'original_length': len(content),
            'summary_length': len(summary),
            'compression_ratio': round(len(summary) / len(content), 2) if len(content) > 0 else 0,
            'key_topics': extract_key_topics(content)
        })

    except Exception as e:
        return jsonify({
            'error': 'An error occurred while generating chapter summary',
            'message': str(e)
        }), 500


def extract_key_topics(text: str) -> List[str]:
    """
    Extract key topics from the text based on headings and important terms
    """
    # Look for headings (lines that might be section titles)
    heading_pattern = r'##\s+(.+)'
    headings = re.findall(heading_pattern, text)

    # Common Physical AI terms that might indicate key topics
    physical_ai_terms = [
        'Physical AI', 'Embodied Cognition', 'Humanoid Robotics',
        'Degrees of Freedom', 'Kinematics', 'Balance Control',
        'Sensorimotor Loop', 'ROS 2', 'Gazebo', 'Simulation',
        'Perception', 'Cognition', 'Control Systems'
    ]

    found_topics = []
    text_lower = text.lower()

    for term in physical_ai_terms:
        if term.lower() in text_lower:
            found_topics.append(term)

    # Combine headings and found terms
    all_topics = list(set(headings + found_topics))

    # Return top 5 topics
    return all_topics[:5]


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Physical AI Textbook Summary Generator',
        'version': '1.0.0'
    })


if __name__ == '__main__':
    print("Starting Physical AI Textbook Summary Generator...")
    print("API endpoints:")
    print("  POST /summarize - Generate summary for text")
    print("  POST /summarize/chapter - Generate summary for textbook chapter")
    print("  GET  /health - Health check")
    app.run(host='0.0.0.0', port=5001, debug=True)