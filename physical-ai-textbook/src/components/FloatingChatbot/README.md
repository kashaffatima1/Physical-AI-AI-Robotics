# Physical AI RAG Chatbot Integration

This repository contains a floating RAG chatbot component for the Physical AI textbook Docusaurus website. The chatbot integrates with the backend RAG system to provide intelligent responses based on the textbook content.

## Features

- **Floating Widget**: Small chatbot widget at the bottom-right corner of all pages
- **RAG Integration**: Uses existing backend endpoints (`/query` and `/query_selected_text`)
- **Session Management**: Maintains chat history with unique session IDs
- **Source Citations**: Displays relevant sources with title, URL, and similarity score
- **Text Selection**: Allows queries about user-selected text in the book content
- **Error Handling**: Proper error states and loading indicators
- **Responsive Design**: Works on all device sizes with minimal visual footprint
- **Local & Vercel**: Compatible with both localhost (frontend: 3000, backend: 8000) and Vercel deployment

## Architecture

The chatbot integrates with:

- **main.py backend**: FastAPI endpoints for RAG queries
- **Qdrant**: Vector database for document similarity search
- **Cohere**: Embeddings and text generation

## Integration with Docusaurus

The chatbot is integrated into all pages via the custom Layout theme component:

```
src/
├── theme/
│   └── Layout/
│       └── index.js  # Wraps default layout with FloatingChatbot
└── components/
    └── FloatingChatbot/
        ├── FloatingChatbot.jsx  # Main React component
        └── FloatingChatbot.css  # Styles for the component
```

## Configuration

### Backend URL

Update the backend URL in `FloatingChatbot.jsx`:

```javascript
const backendUrl = process.env.NODE_ENV === 'development'
  ? 'http://127.0.0.1:8000'  // Local development
  : 'https://your-backend-deployment-url.vercel.app'; // Production
```

### Environment Variables

For Vercel deployment, set the production backend URL as an environment variable in your Vercel project settings.

## Deployment

### Local Development

1. Start the backend server:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. Start the Docusaurus site:
   ```bash
   cd physical-ai-textbook
   npm start
   ```

### Vercel Deployment

1. Deploy the backend to Vercel (separate project)
2. Update the production backend URL in the frontend code
3. Deploy the Docusaurus site to Vercel

## How It Works

1. **Text Selection**: The chatbot detects selected text on the page and offers quick query options
2. **Session Management**: Each chat session gets a unique ID maintained in component state
3. **Query Processing**: Questions are sent to the appropriate backend endpoint:
   - Regular queries → `/query` endpoint
   - Selected text queries → `/query_selected_text` endpoint
4. **Response Generation**: The backend uses RAG (Retrieval Augmented Generation) with:
   - Qdrant for vector similarity search
   - Cohere for embeddings and answer generation
5. **Source Display**: Relevant sources with titles, URLs, and similarity scores are shown

## Customization

The chatbot can be customized by modifying:

- `FloatingChatbot.css`: Visual styling and appearance
- `FloatingChatbot.jsx`: Functionality and behavior
- Colors and styling can be adjusted in the CSS variables

## Troubleshooting

- Ensure the backend server is running when testing locally
- Check browser console for any CORS or network errors
- Verify the backend URL is correctly configured for the environment
- Make sure the Qdrant database has been populated with textbook content