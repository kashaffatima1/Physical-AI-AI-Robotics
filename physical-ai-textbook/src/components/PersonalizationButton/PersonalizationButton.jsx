import React, { useState, useEffect } from 'react';

const PersonalizationButton = ({ chapterId }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [user, setUser] = useState(null);
  const [preferences, setPreferences] = useState({
    language: 'en',
    difficulty: 2,
    hide_advanced: false,
    hide_code: false
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Check if user is logged in
  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Check if we have user data in localStorage or session
        const userData = localStorage.getItem('better-auth-user');
        if (userData) {
          const parsed = JSON.parse(userData);
          setUser(parsed);
          // Get current preferences for this chapter
          await loadPreferences(parsed.id, chapterId);
        }
      } catch (error) {
        console.error('Auth check error:', error);
      }
    };

    checkAuth();
  }, [chapterId]);

  const loadPreferences = async (userId, chapterId) => {
    if (!userId || !chapterId) return;

    try {
      const response = await fetch('/api/auth/get-personalize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'user-id': userId,
          'chapter-id': chapterId
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPreferences({
          language: data.language || 'en',
          difficulty: data.difficulty || 2,
          hide_advanced: data.hide_advanced || false,
          hide_code: data.hide_code || false
        });
      }
    } catch (error) {
      console.error('Error loading preferences:', error);
    }
  };

  const handleSavePreferences = async () => {
    if (!user || !chapterId) return;

    setIsSaving(true);
    try {
      const response = await fetch('/api/auth/personalize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'user-id': user.id,
          'chapter-id': chapterId
        },
        body: JSON.stringify(preferences)
      });

      if (response.ok) {
        alert('Personalization settings saved successfully!');
        setIsModalOpen(false);
      } else {
        alert('Failed to save preferences');
      }
    } catch (error) {
      console.error('Error saving preferences:', error);
      alert('Error saving preferences');
    } finally {
      setIsSaving(false);
    }
  };

  if (!user) {
    return (
      <div className="personalization-notice">
        <p>Sign in to personalize this chapter's content to your experience level.</p>
      </div>
    );
  }

  return (
    <>
      <button
        className="personalize-button"
        onClick={() => setIsModalOpen(true)}
        title="Personalize this chapter"
      >
        🎯 Personalize
      </button>

      {isModalOpen && (
        <div className="personalization-modal-overlay">
          <div className="personalization-modal">
            <div className="modal-header">
              <h3>Personalize Chapter Content</h3>
              <button className="close-button" onClick={() => setIsModalOpen(false)}>
                ×
              </button>
            </div>

            <div className="modal-content">
              <div className="preference-group">
                <label>
                  <input
                    type="checkbox"
                    checked={preferences.hide_advanced}
                    onChange={(e) => setPreferences({...preferences, hide_advanced: e.target.checked})}
                  />
                  Hide advanced examples
                </label>
              </div>

              <div className="preference-group">
                <label>
                  <input
                    type="checkbox"
                    checked={preferences.hide_code}
                    onChange={(e) => setPreferences({...preferences, hide_code: e.target.checked})}
                  />
                  Hide code examples
                </label>
              </div>

              <div className="preference-group">
                <label>Difficulty Level:</label>
                <div className="difficulty-options">
                  <label>
                    <input
                      type="radio"
                      name="difficulty"
                      value={1}
                      checked={preferences.difficulty === 1}
                      onChange={() => setPreferences({...preferences, difficulty: 1})}
                    />
                    Beginner
                  </label>
                  <label>
                    <input
                      type="radio"
                      name="difficulty"
                      value={2}
                      checked={preferences.difficulty === 2}
                      onChange={() => setPreferences({...preferences, difficulty: 2})}
                    />
                    Intermediate
                  </label>
                  <label>
                    <input
                      type="radio"
                      name="difficulty"
                      value={3}
                      checked={preferences.difficulty === 3}
                      onChange={() => setPreferences({...preferences, difficulty: 3})}
                    />
                    Advanced
                  </label>
                </div>
              </div>
            </div>

            <div className="modal-actions">
              <button
                className="save-button"
                onClick={handleSavePreferences}
                disabled={isSaving}
              >
                {isSaving ? 'Saving...' : 'Save Preferences'}
              </button>
              <button
                className="cancel-button"
                onClick={() => setIsModalOpen(false)}
                disabled={isSaving}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default PersonalizationButton;