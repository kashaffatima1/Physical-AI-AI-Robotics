import React, { useState, useRef, useEffect } from 'react';
import './Chat.css';

// Auth context state
const useAuth = () => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const signup = async (email, password, softwareExperience, hardwareExperience) => {
    setIsLoading(true);
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
      setUser({
        id: data.user_id,
        email: data.email,
        session_token: data.session_token
      });

      return { success: true, data };
    } catch (error) {
      console.error('Signup error:', error);
      return { success: false, error: error.message };
    } finally {
      setIsLoading(false);
    }
  };

  const signin = async (email, password) => {
    setIsLoading(true);
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
      setUser({
        id: data.user_id,
        email: data.email,
        session_token: data.session_token
      });

      return { success: true, data };
    } catch (error) {
      console.error('Signin error:', error);
      return { success: false, error: error.message };
    } finally {
      setIsLoading(false);
    }
  };

  const signout = () => {
    setUser(null);
  };

  const getProfile = async () => {
    if (!user) return null;

    try {
      const response = await fetch('/api/auth/profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'user-id': user.id
        }
      });

      if (!response.ok) {
        throw new Error('Failed to get profile');
      }

      return await response.json();
    } catch (error) {
      console.error('Get profile error:', error);
      return null;
    }
  };

  return { user, isLoading, signup, signin, signout, getProfile };
};

const App = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [selectedText, setSelectedText] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSelectingText, setIsSelectingText] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState('signin'); // 'signin' or 'signup'
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  const { user, isLoading: isAuthLoading, signup, signin, signout, getProfile } = useAuth();

  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle text selection
  useEffect(() => {
    const handleSelection = () => {
      const selection = window.getSelection();
      if (selection.toString().trim() !== '') {
        setSelectedText(selection.toString());
      }
    };

    document.addEventListener('mouseup', handleSelection);
    return () => {
      document.removeEventListener('mouseup', handleSelection);
    };
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = async (message, isQuerySelectedText = false) => {
    if (!message.trim() && !selectedText.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: isQuerySelectedText ? `Query: ${message}\nSelected: ${selectedText}` : message,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      let response;
      if (isQuerySelectedText && selectedText.trim()) {
        response = await fetch('/api/query_selected_text', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: message,
            selected_text: selectedText,
            session_id: sessionId
          })
        });
      } else {
        response = await fetch('/api/query', {
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

      // Update session ID if new
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
      }

      const botMessage = {
        id: Date.now() + 1,
        text: data.answer,
        sender: 'bot',
        sources: data.sources,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
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
      setSelectedText(''); // Clear selected text after sending
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim() || selectedText.trim()) {
      sendMessage(inputValue || 'Related to selected text', selectedText.trim() !== '' && inputValue.trim() !== '');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (inputValue.trim() || selectedText.trim()) {
        sendMessage(inputValue || 'Related to selected text', selectedText.trim() !== '' && inputValue.trim() !== '');
      }
    }
  };

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
        } else {
          setShowAuthModal(false);
        }
      } else {
        const result = await signin(email, password);
        if (!result.success) {
          setError(result.error);
        } else {
          setShowAuthModal(false);
        }
      }
    };

    return (
      <div className="auth-modal-overlay">
        <div className="auth-modal">
          <div className="auth-modal-header">
            <h2>{authMode === 'signup' ? 'Create Account' : 'Sign In'}</h2>
            <button className="close-button" onClick={() => setShowAuthModal(false)}>
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
                disabled={isAuthLoading}
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
                disabled={isAuthLoading}
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
                    disabled={isAuthLoading}
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
                    disabled={isAuthLoading}
                  />
                </div>
              </>
            )}

            <button type="submit" className="auth-button" disabled={isAuthLoading}>
              {isAuthLoading ? 'Processing...' : (authMode === 'signup' ? 'Sign Up' : 'Sign In')}
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
                disabled={isAuthLoading}
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
    <div className="chat-app">
      <div className="chat-header">
        <h1>Physical AI Chatbot</h1>
        <p>Ask questions about Physical AI concepts and research</p>

        <div className="auth-section">
          {user ? (
            <div className="user-info">
              <span>Welcome, {user.email}!</span>
              <button onClick={signout} className="signout-button">Sign Out</button>
            </div>
          ) : (
            <button onClick={() => setShowAuthModal(true)} className="auth-button">Sign In/Up</button>
          )}
        </div>
      </div>

      <div className="chat-container" ref={chatContainerRef}>
        {messages.length === 0 ? (
          <div className="welcome-message">
            <h2>Welcome to the Physical AI Chatbot!</h2>
            <p>Ask me anything about Physical AI, robotics, or related topics.</p>
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
          <div className="messages">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`message ${message.sender === 'user' ? 'user-message' : 'bot-message'}`}
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
                            <a href={source.url} target="_blank" rel="noopener noreferrer">
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
            className="query-selected-btn"
          >
            Ask about selected text
          </button>
        </div>
      )}

      <form className="input-form" onSubmit={handleSubmit}>
        <div className="input-container">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={selectedText ? "Ask about the selected text or type a general question..." : "Ask a question about Physical AI..."}
            className="message-input"
            rows="3"
            disabled={isLoading}
          />
          <button
            type="submit"
            className="send-button"
            disabled={!inputValue.trim() && !selectedText.trim() || isLoading}
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </div>
        <div className="input-hints">
          <small>Press Enter to send, Shift+Enter for new line</small>
        </div>
      </form>

      {showAuthModal && <AuthModal />}
    </div>
  );
};

export default App;