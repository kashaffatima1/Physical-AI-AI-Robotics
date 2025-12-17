import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import cohere
from qdrant_client import QdrantClient
from qdrant_client.http import models
import time
from typing import List, Dict, Tuple
import logging
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
from datetime import datetime
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

# Import auth functionality
from auth import (
    UserSignup, UserSignin, UserBackground,
    authenticate_user, get_user_by_email, hash_password,
    save_user_background, get_user_background,
    save_user_preference, get_user_preference,
    translate_to_urdu, create_session_token
)

# Import subagents functionality
from subagents import get_subagent_response, SubagentResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Physical AI RAG Chatbot", version="1.0.0")

# Initialize Cohere client
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
cohere_client = cohere.Client(COHERE_API_KEY or "zP5jUzqW9QmHV0fCPGPeTSHIcUJsSzmP7DoHofdh")

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    session_id: str = None

class QuerySelectedTextRequest(BaseModel):
    query: str
    selected_text: str
    session_id: str = None

class SearchResult(BaseModel):
    text: str
    title: str
    url: str
    score: float

class QueryResponse(BaseModel):
    answer: str
    sources: List[SearchResult]
    session_id: str

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime

# Initialize Qdrant client (cloud instance)
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
qdrant_client = QdrantClient(
    url=QDRANT_URL or "https://0dcd6099-1f6a-4ebc-9e7f-fb24673ab04a.us-east4-0.gcp.cloud.qdrant.io:6333",
    api_key=QDRANT_API_KEY or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.EFkxLEym79ei9sLvc5GYMU383zOLnbVo2SygDsyafAE",
)

# Initialize Neon Postgres connection
DATABASE_URL = os.getenv("DATABASE_URL")
conn = None
try:
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')

        # Create tables if they don't exist
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT REFERENCES chat_sessions(id),
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            conn.commit()
        logger.info("Connected to Neon Postgres and initialized tables")
    else:
        logger.warning("DATABASE_URL not set, chat history will not be persisted")
except Exception as e:
    logger.error(f"Error connecting to Neon Postgres: {str(e)}")
    conn = None

def is_valid_url(url: str, text: str = "") -> bool:
    """Skip invalid/fallback URLs or 404 pages"""
    invalid_patterns = ["#__docusaurus_skipToContent_fallback", "/404", "Page Not Found"]
    for pat in invalid_patterns:
        if pat in url or pat in text:
            return False
    return True

def get_urls_from_sitemap(sitemap_url: str) -> List[str]:
    """Fetch all URLs listed in a sitemap XML"""
    try:
        response = requests.get(sitemap_url)
        soup = BeautifulSoup(response.content, "xml")
        urls = [loc.get_text() for loc in soup.find_all("loc") if is_valid_url(loc.get_text())]
        logger.info(f"Found {len(urls)} valid URLs in sitemap")
        return urls
    except Exception as e:
        logger.error(f"Error fetching sitemap: {str(e)}")
        return []

def extract_text_url(url: str) -> Tuple[str, str, str]:
    """Extract and clean text from a given URL"""
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Extract title
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else ""

        # Find main content - added more selectors for Docusaurus
        content_selectors = [
            'article',  # Main article content
            '.markdown',  # Docusaurus markdown content
            '.theme-doc-markdown',  # Docusaurus theme markdown
            '.main-wrapper',  # Main content wrapper
            'main',  # Main content area
            '.container',  # Container with content
            '[role="main"]'  # Main role
        ]

        content = None
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                break

        if not content:
            content = soup.body

        if content:
            text = content.get_text(separator='\n')
            lines = [line.strip() for line in text.splitlines()]
            text = '\n'.join(line for line in lines if line)
        else:
            text = ""

        if not is_valid_url(url, text):
            logger.info(f"Skipping invalid/fallback page: {url}")
            return "", "", url

        return title, text, url

    except Exception as e:
        logger.error(f"Error extracting text from {url}: {str(e)}")
        return "", "", url

def collection(text: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
    """Chunk text into smaller pieces with overlap"""
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        if end > text_length:
            end = text_length

        chunk_text = text[start:end]
        chunk_data = {
            'text': chunk_text,
            'start_idx': start,
            'end_idx': end
        }
        chunks.append(chunk_data)

        start += chunk_size - overlap
        if start >= text_length:
            break

    return chunks

def rag_embedding(texts: List[str]) -> List[List[float]]:
    """Generate embeddings using Cohere Embed v2"""
    if not texts:
        return []

    batch_size = 96
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            response = cohere_client.embed(
                texts=batch,
                model="embed-multilingual-v2.0",
                input_type="search_document"
            )
            all_embeddings.extend([embedding for embedding in response.embeddings])
            time.sleep(0.1)
        except Exception as e:
            logger.error(f"Error generating embeddings for batch: {str(e)}")
            all_embeddings.extend([[0.0]*768 for _ in range(len(batch))])

    return all_embeddings

def embed_query(query: str) -> List[float]:
    """Embed a single query using Cohere"""
    try:
        response = cohere_client.embed(
            texts=[query],
            model="embed-multilingual-v2.0",
            input_type="search_query"
        )
        return response.embeddings[0]
    except Exception as e:
        logger.error(f"Error generating query embedding: {str(e)}")
        return [0.0] * 768

def search_qdrant(query_embedding: List[float], top_k: int = 5) -> List[Dict]:
    """Search Qdrant for similar documents"""
    collection_name = "physical_ai_docs"

    try:
        search_result = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=top_k,
            with_payload=True
        )

        results = []
        for hit in search_result:
            results.append({
                "text": hit.payload["text"],
                "title": hit.payload["title"],
                "url": hit.payload["url"],
                "score": hit.score
            })

        return results
    except Exception as e:
        logger.error(f"Error searching Qdrant: {str(e)}")
        return []

def get_or_create_session(session_id: str = None) -> str:
    """Get existing session or create a new one"""
    if not session_id:
        session_id = str(uuid.uuid4())

    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO chat_sessions (id) VALUES (%s) ON CONFLICT (id) DO NOTHING",
                    (session_id,)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")

    return session_id

def save_chat_message(session_id: str, role: str, content: str):
    """Save a chat message to the database"""
    if not conn:
        return

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO chat_messages (session_id, role, content) VALUES (%s, %s, %s)",
                (session_id, role, content)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Error saving chat message: {str(e)}")

def get_chat_history(session_id: str) -> List[Dict]:
    """Retrieve chat history for a session"""
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT role, content, timestamp FROM chat_messages WHERE session_id = %s ORDER BY timestamp",
                (session_id,)
            )
            messages = cursor.fetchall()
            return [dict(msg) for msg in messages]
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        return []

def generate_answer_with_context(query: str, context_chunks: List[Dict], chat_history: List[Dict] = None) -> str:
    """Generate an answer using the LLM with context from retrieved documents"""
    if not context_chunks:
        return "I couldn't find any relevant information to answer your question."

    # Build context from retrieved chunks
    context_text = "\n\n".join([f"Source: {chunk['title']} ({chunk['url']})\n{chunk['text'][:500]}..." for chunk in context_chunks])

    # Build conversation history if available
    history_text = ""
    if chat_history:
        history_text = "\n".join([f"{msg['role'].title()}: {msg['content']}" for msg in chat_history[-5:]])  # Use last 5 messages

    # Create prompt for the LLM
    prompt = f"""You are a helpful assistant for the Physical AI textbook. Use the provided context to answer the user's question accurately and concisely. If the context doesn't contain enough information to answer the question, say so.

Context:
{context_text}

Conversation History:
{history_text}

Question: {query}

Answer: """

    try:
        # Use Cohere's generate API to create the answer
        response = cohere_client.generate(
            model='command-r-plus',  # Using a more capable model
            prompt=prompt,
            max_tokens=500,
            temperature=0.3,
            stop_sequences=["Question:", "User:", "\n\n"]
        )

        return response.generations[0].text.strip()
    except Exception as e:
        logger.error(f"Error generating answer: {str(e)}")
        return "Sorry, I encountered an error while generating the answer. Please try again."

def save_to_qdrant(embeddings: List[List[float]], chunks: List[Dict], titles: List[str], urls: List[str]):
    """Save embeddings to Qdrant with metadata"""
    collection_name = "physical_ai_docs"

    try:
        qdrant_client.get_collection(collection_name)
        logger.info(f"Collection {collection_name} already exists")
    except:
        logger.info(f"Creating collection {collection_name}")
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
        )

    points = []
    for i, (embedding, chunk, title, url) in enumerate(zip(embeddings, chunks, titles, urls)):
        point = models.PointStruct(
            id=i,
            vector=embedding,
            payload={
                "text": chunk['text'],
                "title": title,
                "url": url,
                "start_idx": chunk['start_idx'],
                "end_idx": chunk['end_idx'],
                "chunk_id": f"{url}_{chunk['start_idx']}_{chunk['end_idx']}"
            }
        )
        points.append(point)

    qdrant_client.upsert(
        collection_name=collection_name,
        points=points
    )

    logger.info(f"Successfully saved {len(points)} embeddings to Qdrant")

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """Handle a query and return the answer with sources"""
    try:
        # Get or create session
        session_id = get_or_create_session(request.session_id)

        # Embed the query
        query_embedding = embed_query(request.query)

        # Search Qdrant for relevant documents
        search_results = search_qdrant(query_embedding, top_k=5)

        # Get chat history for context
        chat_history = get_chat_history(session_id)

        # Generate answer using context
        answer = generate_answer_with_context(request.query, search_results, chat_history)

        # Convert search results to response format
        sources = [
            SearchResult(
                text=chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                title=chunk["title"],
                url=chunk["url"],
                score=chunk["score"]
            )
            for chunk in search_results
        ]

        # Save user message and assistant response to history
        save_chat_message(session_id, "user", request.query)
        save_chat_message(session_id, "assistant", answer)

        return QueryResponse(
            answer=answer,
            sources=sources,
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Error in query endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.post("/query_selected_text", response_model=QueryResponse)
async def query_selected_text_endpoint(request: QuerySelectedTextRequest):
    """Handle a query about selected text and return the answer with sources"""
    try:
        # Get or create session
        session_id = get_or_create_session(request.session_id)

        # Create a combined query that includes the selected text
        combined_query = f"Based on this selected text: '{request.selected_text}', {request.query}"

        # Embed the combined query
        query_embedding = embed_query(combined_query)

        # Search Qdrant for relevant documents
        search_results = search_qdrant(query_embedding, top_k=5)

        # Get chat history for context
        chat_history = get_chat_history(session_id)

        # Generate answer using context
        answer = generate_answer_with_context(combined_query, search_results, chat_history)

        # Convert search results to response format
        sources = [
            SearchResult(
                text=chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                title=chunk["title"],
                url=chunk["url"],
                score=chunk["score"]
            )
            for chunk in search_results
        ]

        # Save user message and assistant response to history
        user_message = f"Query: {request.query}\nSelected Text: {request.selected_text}"
        save_chat_message(session_id, "user", user_message)
        save_chat_message(session_id, "assistant", answer)

        return QueryResponse(
            answer=answer,
            sources=sources,
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Error in query_selected_text endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


# Mount static files (frontend) - only if directory exists
import os
frontend_static_path = "../frontend/dist"
if os.path.exists(frontend_static_path):
    app.mount("/static", StaticFiles(directory=frontend_static_path, html=True), name="static")
else:
    logger.warning(f"Frontend dist directory does not exist: {frontend_static_path}")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main page"""
    try:
        with open("../frontend/dist/index.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        # Fallback for development
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Physical AI Chatbot</title>
        </head>
        <body>
            <div id="root"></div>
            <script type="module" src="/src/index.jsx"></script>
        </body>
        </html>
        """)


@app.post("/api/auth/signup")
async def signup(request: UserSignup):
    """User signup endpoint"""
    try:
        # Check if user already exists
        existing_user = get_user_by_email(request.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")

        # Hash the password
        password_hash = hash_password(request.password)

        # Connect to database and create user
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()

        # Generate user ID
        user_id = str(uuid.uuid4())

        # Insert user into database
        cur.execute("""
            INSERT INTO users (id, email, password_hash)
            VALUES (%s, %s, %s)
        """, (user_id, request.email, password_hash))

        conn.commit()
        cur.close()
        conn.close()

        # Save user background information
        save_user_background(user_id, request.software_experience, request.hardware_experience)

        # Create a session token
        session_token = create_session_token(user_id)

        return {
            "message": "User created successfully",
            "user_id": user_id,
            "email": request.email,
            "session_token": session_token
        }
    except Exception as e:
        logger.error(f"Error in signup endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during signup: {str(e)}")


@app.post("/api/auth/signin")
async def signin(request: UserSignin):
    """User signin endpoint"""
    try:
        user = authenticate_user(request.email, request.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Create a session token
        session_token = create_session_token(user['id'])

        # Get user background
        background = get_user_background(user['id'])

        return {
            "message": "Sign in successful",
            "user_id": user['id'],
            "email": user['email'],
            "session_token": session_token,
            "background": background
        }
    except Exception as e:
        logger.error(f"Error in signin endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during signin: {str(e)}")


@app.post("/api/auth/profile")
async def get_user_profile(request: Request):
    """Get user profile information"""
    try:
        # In a real implementation, you'd validate the session token from headers
        # For now, we'll simulate getting user_id from a header
        user_id = request.headers.get("user-id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not provided")

        # Get user background
        background = get_user_background(user_id)

        return {
            "user_id": user_id,
            "background": background
        }
    except Exception as e:
        logger.error(f"Error in get_user_profile endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving profile: {str(e)}")


@app.post("/api/auth/update-background")
async def update_user_background(request: UserBackground):
    """Update user background information"""
    try:
        save_user_background(request.user_id, request.software_experience, request.hardware_experience)

        return {
            "message": "Background updated successfully",
            "user_id": request.user_id
        }
    except Exception as e:
        logger.error(f"Error in update_user_background endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating background: {str(e)}")


@app.post("/api/auth/personalize")
async def set_personalization(request: Request):
    """Set personalization preferences for a chapter"""
    try:
        # Get user ID and chapter ID from request
        user_id = request.headers.get("user-id")
        chapter_id = request.headers.get("chapter-id")

        if not user_id or not chapter_id:
            raise HTTPException(status_code=400, detail="User ID and Chapter ID required")

        # Get preferences from request body
        body = await request.json()
        language = body.get("language", "en")
        difficulty = body.get("difficulty", 2)
        hide_advanced = body.get("hide_advanced", False)
        hide_code = body.get("hide_code", False)

        # Save preferences
        save_user_preference(user_id, chapter_id, language, difficulty, hide_advanced, hide_code)

        return {
            "message": "Personalization settings saved successfully",
            "user_id": user_id,
            "chapter_id": chapter_id
        }
    except Exception as e:
        logger.error(f"Error in set_personalization endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error setting personalization: {str(e)}")


@app.post("/api/auth/get-personalize")
async def get_personalization(request: Request):
    """Get personalization preferences for a chapter"""
    try:
        # Get user ID and chapter ID from request
        user_id = request.headers.get("user-id")
        chapter_id = request.headers.get("chapter-id")

        if not user_id or not chapter_id:
            raise HTTPException(status_code=400, detail="User ID and Chapter ID required")

        # Get preferences
        preferences = get_user_preference(user_id, chapter_id)

        if not preferences:
            # Return default preferences if none exist
            return {
                "language": "en",
                "difficulty": 2,
                "hide_advanced": False,
                "hide_code": False
            }

        return {
            "language": preferences["language_preference"],
            "difficulty": preferences["difficulty_level"],
            "hide_advanced": preferences["hide_advanced_examples"],
            "hide_code": preferences["hide_code_examples"]
        }
    except Exception as e:
        logger.error(f"Error in get_personalization endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting personalization: {str(e)}")


@app.post("/api/auth/translate-to-urdu")
async def translate_to_urdu_endpoint(request: Request):
    """Translate content to Urdu"""
    try:
        body = await request.json()
        text = body.get("text", "")

        if not text:
            raise HTTPException(status_code=400, detail="Text to translate is required")

        # Translate the text to Urdu
        translated_text = translate_to_urdu(text)

        return {
            "original_text": text,
            "translated_text": translated_text,
            "language": "ur"
        }
    except Exception as e:
        logger.error(f"Error in translate_to_urdu endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error translating text: {str(e)}")


@app.post("/api/subagents/query")
async def subagent_query_endpoint(request: Request):
    """Query the subagent system for intelligent responses"""
    try:
        body = await request.json()
        query = body.get("query", "")
        context = body.get("context", None)
        preferred_subagent = body.get("preferred_subagent", None)

        if not query:
            raise HTTPException(status_code=400, detail="Query is required")

        # Get response from the appropriate subagent
        response = get_subagent_response(query, context, preferred_subagent)

        return {
            "answer": response.answer,
            "sources": [source.dict() for source in response.sources],
            "confidence": response.confidence,
            "subagent_used": response.subagent_used
        }
    except Exception as e:
        logger.error(f"Error in subagent_query_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing subagent query: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

def execute():
    """Main function to execute the RAG embedding pipeline"""
    logger.info("Starting RAG embedding pipeline...")

    # Fetch URLs from sitemap
    sitemap_url = "https://physical-ai-ai-robotics.vercel.app/sitemap.xml"
    urls = get_urls_from_sitemap(sitemap_url)
    logger.info(f"Fetched {len(urls)} URLs from sitemap")

    # Extract text from each URL
    all_chunks = []
    all_titles = []
    all_urls = []

    for i, url in enumerate(urls):
        logger.info(f"Processing {i+1}/{len(urls)}: {url}")
        title, text, original_url = extract_text_url(url)
        if text.strip():
            chunks = collection(text)
            for chunk in chunks:
                all_chunks.append(chunk)
                all_titles.append(title)
                all_urls.append(original_url)

    logger.info(f"Created {len(all_chunks)} text chunks")
    if not all_chunks:
        logger.warning("No text chunks created. Exiting.")
        return

    # Generate embeddings
    texts_for_embedding = [chunk['text'] for chunk in all_chunks]
    logger.info("Generating embeddings...")
    embeddings = rag_embedding(texts_for_embedding)
    logger.info(f"Generated {len(embeddings)} embeddings")

    # Save to Qdrant
    logger.info("Saving embeddings to Qdrant...")
    save_to_qdrant(embeddings, all_chunks, all_titles, all_urls)
    logger.info("RAG embedding pipeline completed successfully!")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "crawl":
        # Run the crawling pipeline
        execute()
    else:
        # Start the uvicorn server for the API/website
        uvicorn.run(app, host="0.0.0.0", port=8000)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for testing, you can restrict to frontend URL later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
