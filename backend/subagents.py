"""
Reusable Intelligence Subagents for Physical AI Book

This module implements reusable code subagents and agent skills to handle
repetitive tasks or queries in the Physical AI book. These subagents can be
invoked from different chapters or sections to assist the user intelligently.
"""

import os
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import cohere
from qdrant_client import QdrantClient
from qdrant_client.http import models
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Cohere client
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
cohere_client = cohere.Client(COHERE_API_KEY)

# Initialize Qdrant client (cloud instance)
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

class QueryRequest(BaseModel):
    query: str
    context: Optional[str] = None
    max_results: int = 5

class SearchResult(BaseModel):
    text: str
    title: str
    url: str
    score: float

class SubagentResponse(BaseModel):
    answer: str
    sources: List[SearchResult]
    confidence: float
    subagent_used: str

class BaseSubagent:
    """Base class for all subagents"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    async def execute(self, query: str, context: Optional[str] = None) -> SubagentResponse:
        """Execute the subagent with the given query and context"""
        raise NotImplementedError("Subclasses must implement execute method")

class KnowledgeRetrievalSubagent(BaseSubagent):
    """Subagent for retrieving knowledge from the Physical AI documentation"""

    def __init__(self):
        super().__init__(
            name="KnowledgeRetrieval",
            description="Retrieves relevant information from Physical AI documentation using vector search"
        )
        self.collection_name = "physical_ai_docs"

    def execute(self, query: str, context: Optional[str] = None) -> SubagentResponse:
        """Execute knowledge retrieval using Qdrant vector search"""
        try:
            # Embed the query using Cohere
            response = cohere_client.embed(
                texts=[query],
                model="embed-multilingual-v2.0",
                input_type="search_query"
            )
            query_embedding = response.embeddings[0]

            # Search Qdrant for similar documents
            search_result = qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=5,
                with_payload=True
            )

            results = []
            for hit in search_result:
                results.append(SearchResult(
                    text=hit.payload["text"][:200] + "..." if len(hit.payload["text"]) > 200 else hit.payload["text"],
                    title=hit.payload["title"],
                    url=hit.payload["url"],
                    score=hit.score
                ))

            # Generate answer using the retrieved context
            if results:
                context_text = "\n\n".join([f"Source: {r.title} ({r.url})\n{r.text[:500]}..." for r in results])

                # Create prompt for the LLM
                prompt = f"""You are a helpful assistant for the Physical AI textbook. Use the provided context to answer the user's question accurately and concisely. If the context doesn't contain enough information to answer the question, say so.

Context:
{context_text}

Question: {query}

Answer: """

                # Use Cohere's generate API to create the answer
                gen_response = cohere_client.generate(
                    model='command-r-plus',
                    prompt=prompt,
                    max_tokens=500,
                    temperature=0.3,
                )

                answer = gen_response.generations[0].text.strip()
            else:
                answer = "I couldn't find any relevant information to answer your question."

            # Calculate confidence based on highest score
            confidence = max([r.score for r in results]) if results else 0.0

            return SubagentResponse(
                answer=answer,
                sources=results,
                confidence=confidence,
                subagent_used=self.name
            )

        except Exception as e:
            logger.error(f"Error in KnowledgeRetrievalSubagent: {str(e)}")
            return SubagentResponse(
                answer="Sorry, I encountered an error while retrieving information. Please try again.",
                sources=[],
                confidence=0.0,
                subagent_used=self.name
            )

class ExplanationSubagent(BaseSubagent):
    """Subagent for explaining complex Physical AI concepts in simple terms"""

    def __init__(self):
        super().__init__(
            name="Explanation",
            description="Explains complex Physical AI concepts in simple, understandable terms"
        )

    def execute(self, query: str, context: Optional[str] = None) -> SubagentResponse:
        """Explain complex concepts in simple terms"""
        try:
            # Create prompt for explanation
            prompt = f"""Explain the following Physical AI concept in simple terms that a beginner can understand:

Concept: {query}

Explanation: """

            # Use Cohere to generate explanation
            response = cohere_client.generate(
                model='command-r-plus',
                prompt=prompt,
                max_tokens=500,
                temperature=0.5,
            )

            explanation = response.generations[0].text.strip()

            return SubagentResponse(
                answer=explanation,
                sources=[],
                confidence=0.8,  # High confidence for explanation
                subagent_used=self.name
            )

        except Exception as e:
            logger.error(f"Error in ExplanationSubagent: {str(e)}")
            return SubagentResponse(
                answer="Sorry, I encountered an error while generating the explanation. Please try again.",
                sources=[],
                confidence=0.0,
                subagent_used=self.name
            )

class ExampleGeneratorSubagent(BaseSubagent):
    """Subagent for generating practical examples for Physical AI concepts"""

    def __init__(self):
        super().__init__(
            name="ExampleGenerator",
            description="Generates practical examples for Physical AI concepts"
        )

    def execute(self, query: str, context: Optional[str] = None) -> SubagentResponse:
        """Generate practical examples for concepts"""
        try:
            # Create prompt for example generation
            prompt = f"""Generate a practical example for the following Physical AI concept:

Concept: {query}

Example: """

            # Use Cohere to generate example
            response = cohere_client.generate(
                model='command-r-plus',
                prompt=prompt,
                max_tokens=500,
                temperature=0.7,
            )

            example = response.generations[0].text.strip()

            return SubagentResponse(
                answer=example,
                sources=[],
                confidence=0.7,
                subagent_used=self.name
            )

        except Exception as e:
            logger.error(f"Error in ExampleGeneratorSubagent: {str(e)}")
            return SubagentResponse(
                answer="Sorry, I encountered an error while generating the example. Please try again.",
                sources=[],
                confidence=0.0,
                subagent_used=self.name
            )

class CodeGeneratorSubagent(BaseSubagent):
    """Subagent for generating code examples for Physical AI implementations"""

    def __init__(self):
        super().__init__(
            name="CodeGenerator",
            description="Generates code examples for Physical AI implementations"
        )

    def execute(self, query: str, context: Optional[str] = None) -> SubagentResponse:
        """Generate code examples for implementations"""
        try:
            # Create prompt for code generation
            prompt = f"""Generate a Python code example for implementing the following Physical AI concept:

Concept: {query}

Code Example:
```python
"""

            # Use Cohere to generate code
            response = cohere_client.generate(
                model='command-r-plus',
                prompt=prompt,
                max_tokens=800,
                temperature=0.3,
                stop_sequences=["```", "Explanation:", "Code:"]
            )

            code = response.generations[0].text.strip()

            # Format the response with proper code block
            formatted_answer = f"```python\n{code}\n```"

            return SubagentResponse(
                answer=formatted_answer,
                sources=[],
                confidence=0.75,
                subagent_used=self.name
            )

        except Exception as e:
            logger.error(f"Error in CodeGeneratorSubagent: {str(e)}")
            return SubagentResponse(
                answer="Sorry, I encountered an error while generating the code example. Please try again.",
                sources=[],
                confidence=0.0,
                subagent_used=self.name
            )

class SubagentOrchestrator:
    """Orchestrates the execution of different subagents based on the query"""

    def __init__(self):
        self.subagents = {
            "knowledge": KnowledgeRetrievalSubagent(),
            "explanation": ExplanationSubagent(),
            "example": ExampleGeneratorSubagent(),
            "code": CodeGeneratorSubagent()
        }

    def determine_subagent(self, query: str) -> str:
        """Determine which subagent to use based on the query"""
        query_lower = query.lower()

        # Keywords for knowledge retrieval
        knowledge_keywords = ["what is", "define", "explain", "describe", "tell me about", "how does", "why"]

        # Keywords for explanation
        explanation_keywords = ["simplify", "simple terms", "beginner", "easy to understand"]

        # Keywords for example generation
        example_keywords = ["example", "show me", "demonstrate", "practical", "application"]

        # Keywords for code generation
        code_keywords = ["code", "implement", "python", "function", "class", "algorithm"]

        # Check for code keywords first (most specific)
        for keyword in code_keywords:
            if keyword in query_lower:
                return "code"

        # Then check for example keywords
        for keyword in example_keywords:
            if keyword in query_lower:
                return "example"

        # Then check for explanation keywords
        for keyword in explanation_keywords:
            if keyword in query_lower:
                return "explanation"

        # Default to knowledge retrieval for general queries
        for keyword in knowledge_keywords:
            if keyword in query_lower:
                return "knowledge"

        # If no specific keywords found, default to knowledge retrieval
        return "knowledge"

    def execute_query(self, query: str, context: Optional[str] = None, preferred_subagent: Optional[str] = None) -> SubagentResponse:
        """Execute a query using the appropriate subagent"""
        if preferred_subagent and preferred_subagent in self.subagents:
            subagent = self.subagents[preferred_subagent]
        else:
            subagent_name = self.determine_subagent(query)
            subagent = self.subagents[subagent_name]

        return subagent.execute(query, context)

# Global orchestrator instance
subagent_orchestrator = SubagentOrchestrator()

def get_subagent_response(query: str, context: Optional[str] = None, preferred_subagent: Optional[str] = None) -> SubagentResponse:
    """Get response from the appropriate subagent"""
    return subagent_orchestrator.execute_query(query, context, preferred_subagent)

# Example usage
if __name__ == "__main__":
    # Example usage of the subagents
    query = "What is reinforcement learning in robotics?"
    response = get_subagent_response(query)
    print(f"Answer: {response.answer}")
    print(f"Sources: {len(response.sources)}")
    print(f"Confidence: {response.confidence}")
    print(f"Subagent used: {response.subagent_used}")