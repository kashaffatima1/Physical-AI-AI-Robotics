# Physical AI RAG Chatbot

This project implements a RAG (Retrieval-Augmented Generation) chatbot for Physical AI documentation using FastAPI backend and React frontend.

## Architecture

- **Backend**: FastAPI application with Qdrant vector search and Neon Postgres for chat history
- **Frontend**: React chat interface with source citations
- **Deployment**: Separate Vercel deployments for backend and frontend

## Features

- Query endpoint (`/query`) for general questions
- Selected text query endpoint (`/query_selected_text`) for context-specific questions
- Source citations with titles and URLs
- Chat session management
- Text selection functionality

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev  # for development
npm run build  # to build for production
```

## Vercel Deployment

### Backend Deployment
1. Navigate to `backend/` directory
2. Deploy using Vercel CLI: `vercel --cwd backend`
3. Note the deployment URL

### Frontend Deployment
1. Update `frontend/vercel.json` with your backend URL:
   ```json
   {
     "rewrites": [
       {
         "source": "/api/:path*",
         "destination": "https://your-backend-deployment-url.vercel.app/api/:path*"
       }
     ]
   }
   ```
2. Navigate to `frontend/` directory
3. Deploy using Vercel CLI: `vercel --cwd frontend`

## Environment Variables

### Backend
- `COHERE_API_KEY`: Cohere API key for embeddings and generation
- `QDRANT_URL`: Qdrant cloud instance URL
- `QDRANT_API_KEY`: Qdrant API key
- `DATABASE_URL`: Neon Postgres database URL (optional for chat history)

## API Endpoints

- `POST /query` - General query endpoint
- `POST /query_selected_text` - Query with selected text context
- `GET /health` - Health check

## Project Structure

```
physical-ai-fresh/
├── backend/
│   ├── main.py          # Main application with crawling functionality
│   ├── api.py           # Vercel-compatible API endpoints
│   ├── requirements.txt # Python dependencies
│   └── vercel.json      # Vercel configuration for backend
└── frontend/
    ├── src/
    │   ├── App.jsx      # Main React component
    │   └── Chat.css     # Chat UI styles
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── vercel.json      # Vercel configuration for frontend
```