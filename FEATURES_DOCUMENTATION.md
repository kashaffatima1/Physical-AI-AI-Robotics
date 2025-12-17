# Physical AI Book - Enhanced Features Documentation

This project extends the Physical AI book with advanced features including authentication, personalization, translation, and reusable intelligence subagents.

## Features Implemented

### 1. Reusable Intelligence (Claude Subagents & Agent Skills)

The system includes a subagent architecture that handles different types of queries:

- **Knowledge Retrieval Subagent**: Retrieves relevant information from Physical AI documentation using vector search
- **Explanation Subagent**: Explains complex Physical AI concepts in simple, understandable terms
- **Example Generator Subagent**: Generates practical examples for Physical AI concepts
- **Code Generator Subagent**: Generates code examples for Physical AI implementations

The subagent orchestrator automatically determines the appropriate subagent based on query keywords and context.

**API Endpoint**: `POST /api/subagents/query`

### 2. Signup and Signin via Better Auth

A complete authentication system with:

- User registration with background information (software and hardware experience)
- Secure password hashing
- Session management
- User profile storage and retrieval

**API Endpoints**:
- `POST /api/auth/signup` - Create new user account
- `POST /api/auth/signin` - Authenticate user
- `POST /api/auth/profile` - Get user profile
- `POST /api/auth/update-background` - Update user background

### 3. Chapter Personalization

Users can customize content per chapter:

- Difficulty level selection (Beginner, Intermediate, Advanced)
- Option to hide advanced examples
- Option to hide code examples
- Personalization settings persist across sessions

**API Endpoints**:
- `POST /api/auth/personalize` - Set personalization preferences
- `POST /api/auth/get-personalize` - Get personalization preferences

### 4. Urdu Translation

Real-time translation of content to Urdu:

- Uses Google Translate API via googletrans library
- Maintains formatting and structure
- Toggle between original and translated content

**API Endpoint**: `POST /api/auth/translate-to-urdu`

## Frontend Components

### Floating Chatbot Integration
The enhanced floating chatbot now includes:
- Authentication UI with sign-in/sign-up modals
- User profile display when logged in
- Session management
- Integration with all new backend features

### Personalization Button Component
Reusable component for chapter personalization:
- Located at `physical-ai-textbook/src/components/PersonalizationButton/PersonalizationButton.jsx`
- Allows users to customize chapter content based on preferences

### Urdu Translation Button Component
Component for translating chapter content:
- Located at `physical-ai-textbook/src/components/UrduTranslationButton/UrduTranslationButton.jsx`
- Provides toggle between original and Urdu content

## Backend Architecture

### Database Schema
The system extends the existing database with:
- `users` table: Stores user authentication data
- `user_profiles` table: Stores user background information
- `user_preferences` table: Stores personalization settings per chapter

### API Structure
```
/api/
├── /auth/          # Authentication endpoints
│   ├── /signup
│   ├── /signin
│   ├── /profile
│   ├── /translate-to-urdu
│   └── /personalize
├── /subagents/     # Subagent endpoints
│   └── /query
└── /query          # Original RAG endpoints
```

## Integration Points

### RAG Chatbot & Qdrant
- All new features integrate seamlessly with existing RAG system
- User preferences can influence search results and response generation
- Session IDs are maintained across authentication states

### Cohere Integration
- Subagents leverage Cohere's Command-R-Plus for intelligent responses
- Translation functionality can be enhanced with Cohere's multilingual capabilities

## Files Added

### Backend
- `backend/auth.py` - Authentication and user management
- `backend/subagents.py` - Subagent architecture and implementations
- Updated `backend/main.py` - New API endpoints

### Frontend
- `frontend/src/App.jsx` - Authentication UI in main chat app
- `physical-ai-textbook/src/components/FloatingChatbot/FloatingChatbot.jsx` - Enhanced chatbot with auth
- `physical-ai-textbook/src/components/PersonalizationButton/PersonalizationButton.jsx` - Personalization component
- `physical-ai-textbook/src/components/UrduTranslationButton/UrduTranslationButton.jsx` - Translation component

### Configuration
- Updated `backend/requirements.txt` - Added dependencies
- `test_features.py` - Test script for all features

## Dependencies Added

- `better-==0.0.15` - Authentication framework
- `googletrans==4.0.0-rc1` - Translation functionality

## Testing

Run the test script to verify all features work correctly:
```bash
python test_features.py
```

This will test:
- Authentication system
- Personalization features
- Urdu translation
- Subagents functionality

## Deployment

The system is configured for Vercel deployment with dual backend/frontend setup:
- Backend: Python FastAPI application
- Frontend: React/Docusaurus application

All new features are fully compatible with the existing deployment configuration.