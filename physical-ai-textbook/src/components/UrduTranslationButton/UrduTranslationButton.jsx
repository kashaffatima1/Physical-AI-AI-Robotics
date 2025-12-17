import React, { useState } from 'react';

const UrduTranslationButton = ({ chapterContent }) => {
  const [isTranslating, setIsTranslating] = useState(false);
  const [isTranslated, setIsTranslated] = useState(false);
  const [translatedContent, setTranslatedContent] = useState('');
  const [showTranslation, setShowTranslation] = useState(false);

  const translateToUrdu = async () => {
    if (!chapterContent) return;

    setIsTranslating(true);
    try {
      const response = await fetch('/api/auth/translate-to-urdu', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: chapterContent })
      });

      if (response.ok) {
        const data = await response.json();
        setTranslatedContent(data.translated_text);
        setIsTranslated(true);
        setShowTranslation(true);
      } else {
        alert('Translation failed');
      }
    } catch (error) {
      console.error('Translation error:', error);
      alert('Error during translation');
    } finally {
      setIsTranslating(false);
    }
  };

  const toggleTranslation = () => {
    if (!isTranslated) {
      translateToUrdu();
    } else {
      setShowTranslation(!showTranslation);
    }
  };

  return (
    <div className="translation-section">
      <button
        className="translate-button"
        onClick={toggleTranslation}
        disabled={isTranslating}
        title="Translate to Urdu"
      >
        {isTranslating ? 'Translating...' : showTranslation ? 'Show Original' : '.Translate to Urdu'}
      </button>

      {showTranslation && (
        <div className="translation-content">
          <div className="translation-header">
            <h4>Urdu Translation</h4>
            <button
              className="close-translation"
              onClick={() => setShowTranslation(false)}
            >
              ×
            </button>
          </div>
          <div className="urdu-text" dir="rtl">
            {translatedContent}
          </div>
        </div>
      )}
    </div>
  );
};

export default UrduTranslationButton;