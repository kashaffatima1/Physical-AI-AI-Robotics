/**
 * Custom Layout Component for Docusaurus
 *
 * This component wraps the default Docusaurus layout and adds the floating chatbot
 * and other components to all pages of the Physical AI textbook website.
 */

import React, { useEffect, useState, useCallback } from 'react';
import DefaultLayout from '@theme-original/Layout';
import FloatingChatbot from '../../components/FloatingChatbot/FloatingChatbot';
import PersonalizationButton from '../../components/PersonalizationButton/PersonalizationButton';
import UrduTranslationButton from '../../components/UrduTranslationButton/UrduTranslationButton';
import '../../css/components.css';

/**
 * Layout Component
 *
 * Extends the default Docusaurus layout to include the floating RAG chatbot
 * and other interactive components
 */
export default function Layout(props) {
  const [currentPath, setCurrentPath] = useState('');
  const [chapterContent, setChapterContent] = useState('');

  // Get current path to determine if we're on a document page
  useEffect(() => {
    setCurrentPath(typeof window !== 'undefined' ? window.location.pathname : '');
  }, []);

  // Extract chapter content when path changes
  useEffect(() => {
    if (typeof window !== 'undefined') {
      // Wait for the page to load completely
      const timer = setTimeout(() => {
        const content = extractChapterContent();
        setChapterContent(content);
      }, 100);

      return () => clearTimeout(timer);
    }
  }, [currentPath]);

  // Function to extract content from the page
  const extractChapterContent = useCallback(() => {
    if (typeof window === 'undefined') return '';

    // Try multiple selectors to find the main content area
    const selectors = [
      '.markdown',           // Docusaurus markdown content
      'article',             // Main article content
      '.theme-doc-markdown', // Docusaurus theme markdown
      '.main-wrapper',       // Main content wrapper
      'main',                // Main content area
      '.container',          // Container with content
      '[role="main"]'        // Main role
    ];

    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element) {
        // Get text content but try to preserve some structure
        return element.innerText || element.textContent || '';
      }
    }

    // Fallback to body content if no specific content found
    return document.body?.innerText || '';
  }, []);

  // Determine if we're on a document page (not on homepage)
  const isDocumentPage = currentPath && !currentPath.includes('/index') && currentPath !== '/';

  // Generate chapter ID from current path
  const getChapterId = () => {
    if (typeof window !== 'undefined') {
      const path = window.location.pathname;
      // Remove leading slash and replace other slashes with underscores
      return path.replace(/^\//, '').replace(/\//g, '_') || 'home';
    }
    return 'home';
  };

  return (
    <>
      <DefaultLayout {...props} />
      <FloatingChatbot />
      {isDocumentPage && (
        <div className="document-components">
          <PersonalizationButton chapterId={getChapterId()} />
          <UrduTranslationButton chapterContent={chapterContent} />
        </div>
      )}
    </>
  );
}