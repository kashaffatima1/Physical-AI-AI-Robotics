/**
 * Client module to inject the floating chatbot into all Docusaurus pages
 *
 * This module ensures the chatbot is available on all pages of the Physical AI textbook website.
 * It dynamically imports the FloatingChatbot component and renders it in the layout.
 */

import React from 'react';
import FloatingChatbot from '../components/FloatingChatbot/FloatingChatbot';

/**
 * ChatbotLoader Component
 *
 * A wrapper component that conditionally renders the FloatingChatbot
 * only on the client-side to avoid SSR issues
 */
const ChatbotLoader = () => {
  const [isClient, setIsClient] = React.useState(false);

  React.useEffect(() => {
    setIsClient(true);
  }, []);

  return isClient ? <FloatingChatbot /> : null;
};

export default ChatbotLoader;