# Physical AI Book - Enhanced Features Setup Guide

## Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL database (for user data)
- Qdrant vector database
- Cohere API key
- Google Translate API (optional, for production)

## Backend Setup

### 1. Environment Variables

Create a `.env` file in the backend directory:

```bash
COHERE_API_KEY=your_cohere_api_key
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
DATABASE_URL=your_postgres_connection_string
AUTH_SECRET=your_auth_secret_key_change_this
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Run the Application

```bash
# For development
python main.py

# Or with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Run Development Server

```bash
npm run dev
```

### 3. Build for Production

```bash
npm run build
```

## Docusaurus Setup (Physical AI Textbook)

### 1. Install Dependencies

```bash
cd physical-ai-textbook
npm install
```

### 2. Run Development Server

```bash
npm start
```

## Database Setup

The application automatically creates the required tables on first run. The schema includes:

- `users` - Authentication data
- `user_profiles` - User background information
- `user_preferences` - Personalization settings

## API Endpoints

### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/signin` - Login user
- `POST /api/auth/profile` - Get user profile

### Personalization
- `POST /api/auth/personalize` - Set chapter preferences
- `POST /api/auth/get-personalize` - Get chapter preferences

### Translation
- `POST /api/auth/translate-to-urdu` - Translate content to Urdu

### Subagents
- `POST /api/subagents/query` - Intelligent query processing

### Original RAG Endpoints
- `POST /api/query` - General queries
- `POST /api/query_selected_text` - Queries with selected text context

## Frontend Components

### Floating Chatbot
The enhanced floating chatbot is located at:
`physical-ai-textbook/src/components/FloatingChatbot/`

Features:
- Authentication UI
- Session management
- Integration with all new features

### Personalization Button
Component for chapter customization:
`physical-ai-textbook/src/components/PersonalizationButton/`

### Urdu Translation Button
Component for content translation:
`physical-ai-textbook/src/components/UrduTranslationButton/`

## Testing

Run the test script to verify all features:

```bash
python test_features.py
```

This tests:
- Authentication flow
- Personalization settings
- Translation functionality
- Subagent responses

## Deployment

### Vercel Deployment

The project is configured for Vercel deployment:

1. Backend: Deploy the FastAPI application
2. Frontend: Deploy the Docusaurus site
3. Configure environment variables in Vercel dashboard

### Environment Variables for Production

Make sure to set all required environment variables in your deployment platform:

- `COHERE_API_KEY`
- `QDRANT_URL`
- `QDRANT_API_KEY`
- `DATABASE_URL`
- `AUTH_SECRET`

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Ensure `DATABASE_URL` is correctly configured
   - Check that the database is accessible from your deployment environment

2. **Cohere API Issues**
   - Verify your API key is valid
   - Check rate limits if experiencing timeouts

3. **Translation Issues**
   - The `googletrans` library may have rate limits
   - Consider implementing caching for frequently translated content

4. **Subagent Performance**
   - Monitor API usage and costs
   - Consider implementing caching for common queries

## Development Tips

### Adding New Subagents

To create a new subagent:

1. Extend the `BaseSubagent` class in `subagents.py`
2. Implement the `execute` method
3. Register it in the `SubagentOrchestrator`
4. Add keyword detection in `determine_subagent` if needed

### Customizing Personalization

The personalization system can be extended by:
- Adding new preference types in the database schema
- Updating the frontend components
- Modifying the backend API endpoints

### Extending Translation

For production use, consider:
- Adding caching to reduce API calls
- Implementing fallback languages
- Adding content formatting preservation