import React, { useState, useEffect, useRef } from 'react';
import './FloatingChatbot.css';

/**
 * Floating RAG Chatbot Component for Docusaurus
 *
 * This component integrates with the backend RAG system to provide:
 * - Query functionality via /query endpoint
 * - Selected text queries via /query_selected_text endpoint
 * - Session management with UUIDs
 * - Source citations with title, URL, and score
 * - Error handling and loading states
 * - Authentication integration with Better Auth
 * - Personalization based on user preferences
 * - Urdu translation capabilities
 *
 * Integration with:
 * - main.py backend: Uses FastAPI endpoints for RAG queries
 * - auth.py: Handles user authentication and preferences
 * - Qdrant: Vector database for document similarity search
 * - Cohere: Embeddings and text generation
 */
const FloatingChatbot = () => {
  // Add auth state
  const [user, setUser] = useState(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState('signin'); // 'signin' or 'signup'
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [selectedText, setSelectedText] = useState('');
  const [error, setError] = useState(null);

  // Ensure this only runs on the client side
  const [isClient, setIsClient] = useState(false);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const chatContainerRef = useRef(null);

  // Check authentication status on component mount
  useEffect(() => {
    setIsClient(true);
    checkAuthStatus();
  }, []);

  // Check if user is authenticated
  const checkAuthStatus = async () => {
    try {
      const userData = localStorage.getItem('better-auth-user');
      if (userData) {
        const parsed = JSON.parse(userData);
        setUser(parsed);
      }
    } catch (error) {
      console.error('Auth check error:', error);
    }
  };

  // Handle text selection on the page
  useEffect(() => {
    if (!isClient) return;

    const handleSelection = () => {
      const selection = window.getSelection();
      if (selection.toString().trim() !== '') {
        setSelectedText(selection.toString().trim());
      }
    };

    document.addEventListener('mouseup', handleSelection);
    return () => {
      document.removeEventListener('mouseup', handleSelection);
    };
  }, [isClient]);

  // Auth functions
  const signup = async (email, password, softwareExperience, hardwareExperience) => {
    try {
      const response = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
          software_experience: softwareExperience,
          hardware_experience: hardwareExperience
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Signup failed');
      }

      const data = await response.json();
      const userData = {
        id: data.user_id,
        email: data.email,
        session_token: data.session_token
      };

      localStorage.setItem('better-auth-user', JSON.stringify(userData));
      setUser(userData);
      setAuthModalOpen(false);

      return { success: true, data };
    } catch (error) {
      console.error('Signup error:', error);
      return { success: false, error: error.message };
    }
  };

  const signin = async (email, password) => {
    try {
      const response = await fetch('/api/auth/signin', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Signin failed');
      }

      const data = await response.json();
      const userData = {
        id: data.user_id,
        email: data.email,
        session_token: data.session_token
      };

      localStorage.setItem('better-auth-user', JSON.stringify(userData));
      setUser(userData);
      setAuthModalOpen(false);

      return { success: true, data };
    } catch (error) {
      console.error('Signin error:', error);
      return { success: false, error: error.message };
    }
  };

  const signout = () => {
    localStorage.removeItem('better-auth-user');
    setUser(null);
  };

  // Scroll to bottom of messages
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Generate a new session ID if one doesn't exist
  useEffect(() => {
    if (!sessionId) {
      setSessionId(generateSessionId());
    }
  }, [sessionId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const generateSessionId = () => {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  };

  const sendMessage = async (message, isQuerySelectedText = false) => {
    if ((!message.trim() && !selectedText.trim()) || isLoading || !isClient) return;

    const userMessage = {
      id: Date.now(),
      text: isQuerySelectedText && selectedText ?
        `Query: ${message}\nSelected: ${selectedText}` : message,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      let response;
      const backendUrl = process.env.NODE_ENV === 'development'
        ? 'http://127.0.0.1:8000'
        : 'https://your-backend-deployment-url.vercel.app'; // Update with your actual backend URL

      if (isQuerySelectedText && selectedText.trim()) {
        response = await fetch(`${backendUrl}/query_selected_text`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: message || 'Explain this selected text',
            selected_text: selectedText,
            session_id: sessionId
          })
        });
      } else {
        response = await fetch(`${backendUrl}/query`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: message,
            session_id: sessionId
          })
        });
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Update session ID if new one was generated
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
      }

      const botMessage = {
        id: Date.now() + 1,
        text: data.answer,
        sender: 'bot',
        sources: data.sources || [],
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);
      setSelectedText(''); // Clear selected text after sending
    } catch (err) {
      console.error('Error sending message:', err);
      setError('Failed to get response. Please try again.');

      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error. Please try again.',
        sender: 'bot',
        error: true,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim() || (selectedText.trim() && !isOpen)) {
      sendMessage(inputValue || 'Explain this', selectedText.trim() !== '' && !inputValue.trim());
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (inputValue.trim() || (selectedText.trim() && !isOpen)) {
        sendMessage(inputValue || 'Explain this', selectedText.trim() !== '' && !inputValue.trim());
      }
    }
  };

  const toggleChat = () => {
    setIsOpen(!isOpen);
    if (!isOpen && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const closeChat = () => {
    setIsOpen(false);
  };

  // Don't render anything on the server side
  if (!isClient) {
    return null;
  }

  return (
    <div className="floating-chatbot">
      {isOpen ? (
        <div className="chatbot-window" ref={chatContainerRef}>
          <div className="chatbot-header">
            <div className="chatbot-title">Physical AI Assistant</div>
            <div className="chatbot-auth">
              {user ? (
                <div className="user-info">
                  <span>Hi, {user.email.split('@')[0]}!</span>
                  <button onClick={signout} className="signout-button">Sign Out</button>
                </div>
              ) : (
                <button onClick={() => setAuthModalOpen(true)} className="auth-button">Sign In</button>
              )}
            </div>
            <button className="chatbot-close" onClick={closeChat}>
              ×
            </button>
          </div>

          <div className="chatbot-messages">
            {messages.length === 0 ? (
              <div className="welcome-message">
                <h3>Hello! 👋</h3>
                <p>Ask me anything about Physical AI, robotics, or the textbook content.</p>
                {selectedText && (
                  <div className="selected-text-preview">
                    <p><strong>Selected text:</strong> "{selectedText.substring(0, 100)}{selectedText.length > 100 ? '...' : ''}"</p>
                    <button
                      onClick={() => sendMessage('Explain this', true)}
                      className="query-selected-btn"
                    >
                      Ask about selected text
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="messages-list">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`message ${message.sender}-message`}
                  >
                    <div className="message-content">
                      <div className="message-text">
                        {message.text}
                      </div>

                      {message.sender === 'bot' && message.sources && message.sources.length > 0 && (
                        <div className="sources">
                          <h4>Sources:</h4>
                          <ul>
                            {message.sources.map((source, index) => (
                              <li key={index} className="source-item">
                                <a
                                  href={source.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="source-link"
                                >
                                  {source.title}
                                </a>
                                <span className="source-score">Score: {source.score.toFixed(3)}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {message.error && (
                        <div className="error-message">
                          An error occurred. Please try again.
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="message bot-message">
                    <div className="message-content">
                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {selectedText && messages.length > 0 && (
            <div className="selected-text-notice">
              <strong>Selected:</strong> "{selectedText.substring(0, 100)}{selectedText.length > 100 ? '...' : ''}"
              <button
                onClick={() => sendMessage(inputValue || 'Explain this', true)}
                disabled={isLoading}
                className="query-selected-btn-small"
              >
                Ask
              </button>
            </div>
          )}

          <form className="chatbot-input-form" onSubmit={handleSubmit}>
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={selectedText ? "Ask about selected text or type a question..." : "Ask a question about Physical AI..."}
              className="chatbot-input"
              rows="1"
              disabled={isLoading}
            />
            <button
              type="submit"
              className="chatbot-send-btn"
              disabled={!inputValue.trim() && !selectedText.trim() || isLoading}
            >
              {isLoading ? 'Sending...' : '→'}
            </button>
          </form>

          {error && (
            <div className="chatbot-error">
              {error}
            </div>
          )}
        </div>
      ) : null}

      <button
        className={`chatbot-button ${isOpen ? 'open' : ''}`}
        onClick={toggleChat}
        aria-label={isOpen ? "Close chat" : "Open chat"}
      >
        <div className="chatbot-icon">
          💬
        </div>
        {selectedText && !isOpen && (
          <div className="quick-ask-badge" onClick={(e) => {
            e.stopPropagation();
            setIsOpen(true);
            setTimeout(() => {
              sendMessage('Explain this', true);
            }, 300);
          }}>
            Ask
          </div>
        )}
      </button>
    </div>
  );

  // Auth modal component
  const AuthModal = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [softwareExperience, setSoftwareExperience] = useState('');
    const [hardwareExperience, setHardwareExperience] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
      e.preventDefault();
      setError('');

      if (authMode === 'signup') {
        const result = await signup(email, password, softwareExperience, hardwareExperience);
        if (!result.success) {
          setError(result.error);
        }
      } else {
        const result = await signin(email, password);
        if (!result.success) {
          setError(result.error);
        }
      }
    };

    return (
      <div className="auth-modal-overlay">
        <div className="auth-modal">
          <div className="auth-modal-header">
            <h3>{authMode === 'signup' ? 'Create Account' : 'Sign In'}</h3>
            <button className="close-button" onClick={() => setAuthModalOpen(false)}>
              ×
            </button>
          </div>

          {error && <div className="error-message">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="email">Email:</label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password:</label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {authMode === 'signup' && (
              <>
                <div className="form-group">
                  <label htmlFor="softwareExperience">Software Background:</label>
                  <textarea
                    id="softwareExperience"
                    value={softwareExperience}
                    onChange={(e) => setSoftwareExperience(e.target.value)}
                    placeholder="Describe your software experience (e.g., programming languages, frameworks, etc.)"
                    rows="3"
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="hardwareExperience">Hardware Background:</label>
                  <textarea
                    id="hardwareExperience"
                    value={hardwareExperience}
                    onChange={(e) => setHardwareExperience(e.target.value)}
                    placeholder="Describe your hardware experience (e.g., electronics, robotics, etc.)"
                    rows="3"
                    required
                  />
                </div>
              </>
            )}

            <button type="submit" className="auth-button">
              {authMode === 'signup' ? 'Sign Up' : 'Sign In'}
            </button>
          </form>

          <div className="auth-switch">
            <p>
              {authMode === 'signup'
                ? 'Already have an account? '
                : "Don't have an account? "}
              <button
                type="button"
                className="switch-mode-button"
                onClick={() => setAuthMode(authMode === 'signup' ? 'signin' : 'signup')}
              >
                {authMode === 'signup' ? 'Sign In' : 'Sign Up'}
              </button>
            </p>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="floating-chatbot">
      {isOpen ? (
        <div className="chatbot-window" ref={chatContainerRef}>
          <div className="chatbot-header">
            <div className="chatbot-title">Physical AI Assistant</div>
            <div className="chatbot-auth">
              {user ? (
                <div className="user-info">
                  <span>Hi, {user.email.split('@')[0]}!</span>
                  <button onClick={signout} className="signout-button">Sign Out</button>
                </div>
              ) : (
                <button onClick={() => setAuthModalOpen(true)} className="auth-button">Sign In</button>
              )}
            </div>
            <button className="chatbot-close" onClick={closeChat}>
              ×
            </button>
          </div>

          <div className="chatbot-messages">
            {messages.length === 0 ? (
              <div className="welcome-message">
                <h3>Hello! 👋</h3>
                <p>Ask me anything about Physical AI, robotics, or the textbook content.</p>
                {selectedText && (
                  <div className="selected-text-preview">
                    <p><strong>Selected text:</strong> "{selectedText.substring(0, 100)}{selectedText.length > 100 ? '...' : ''}"</p>
                    <button
                      onClick={() => sendMessage('Explain this', true)}
                      className="query-selected-btn"
                    >
                      Ask about selected text
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="messages-list">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`message ${message.sender}-message`}
                  >
                    <div className="message-content">
                      <div className="message-text">
                        {message.text}
                      </div>

                      {message.sender === 'bot' && message.sources && message.sources.length > 0 && (
                        <div className="sources">
                          <h4>Sources:</h4>
                          <ul>
                            {message.sources.map((source, index) => (
                              <li key={index} className="source-item">
                                <a
                                  href={source.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="source-link"
                                >
                                  {source.title}
                                </a>
                                <span className="source-score">Score: {source.score.toFixed(3)}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {message.error && (
                        <div className="error-message">
                          An error occurred. Please try again.
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="message bot-message">
                    <div className="message-content">
                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {selectedText && messages.length > 0 && (
            <div className="selected-text-notice">
              <strong>Selected:</strong> "{selectedText.substring(0, 100)}{selectedText.length > 100 ? '...' : ''}"
              <button
                onClick={() => sendMessage(inputValue || 'Explain this', true)}
                disabled={isLoading}
                className="query-selected-btn-small"
              >
                Ask
              </button>
            </div>
          )}

          <form className="chatbot-input-form" onSubmit={handleSubmit}>
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={selectedText ? "Ask about selected text or type a question..." : "Ask a question about Physical AI..."}
              className="chatbot-input"
              rows="1"
              disabled={isLoading}
            />
            <button
              type="submit"
              className="chatbot-send-btn"
              disabled={!inputValue.trim() && !selectedText.trim() || isLoading}
            >
              {isLoading ? 'Sending...' : '→'}
            </button>
          </form>

          {error && (
            <div className="chatbot-error">
              {error}
            </div>
          )}
        </div>
      ) : null}

      <button
        className={`chatbot-button ${isOpen ? 'open' : ''}`}
        onClick={toggleChat}
        aria-label={isOpen ? "Close chat" : "Open chat"}
      >
        <div className="chatbot-icon">
          💬
        </div>
        {selectedText && !isOpen && (
          <div className="quick-ask-badge" onClick={(e) => {
            e.stopPropagation();
            setIsOpen(true);
            setTimeout(() => {
              sendMessage('Explain this', true);
            }, 300);
          }}>
            Ask
          </div>
        )}
      </button>

      {authModalOpen && <AuthModal />}
    </div>
  );
};

export default FloatingChatbot;