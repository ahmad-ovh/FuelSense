import React, { useState, useRef, useEffect } from 'react';

const AIChat = ({ apiBaseUrl }) => {
  const [messages, setMessages] = useState([
    { sender: 'assistant', text: 'Welcome to your FuelSense Copilot. Ask me how to optimize your driving style, project your monthly budget, or check the best time to refuel.' }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || loading) return;

    const userText = inputValue;
    setInputValue('');
    
    // Add user message to state
    setMessages((prev) => [...prev, { sender: 'user', text: userText }]);
    setLoading(true);

    try {
      const response = await fetch(`${apiBaseUrl}/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 1, message: userText }),
      });

      if (!response.ok) {
        throw new Error('Chat API failed');
      }

      const data = await response.json();
      setMessages((prev) => [...prev, { sender: 'assistant', text: data.response }]);
    } catch (error) {
      console.error(error);
      setMessages((prev) => [...prev, { sender: 'assistant', text: 'Sorry, I am having trouble connecting to my engine right now. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ai-chat-container">
      <h3 className="section-title">Interactive AI Copilot</h3>
      
      <div className="chat-history">
        {messages.map((msg, index) => (
          <div key={index} className={`chat-bubble-wrapper ${msg.sender === 'user' ? 'bubble-user' : 'bubble-assistant'}`}>
            <div className="chat-bubble">
              {msg.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="chat-bubble-wrapper bubble-assistant">
            <div className="chat-bubble bubble-loading">
              <span className="dot-blink">.</span>
              <span className="dot-blink">.</span>
              <span className="dot-blink">.</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSendMessage} className="chat-input-form">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Ask copilot about score, costs, or emissions..."
          className="chat-input"
          disabled={loading}
        />
        <button type="submit" className="chat-send-btn" disabled={loading || !inputValue.trim()}>
          <svg viewBox="0 0 24 24" width="18" height="18">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" fill="currentColor"/>
          </svg>
        </button>
      </form>
    </div>
  );
};

export default AIChat;
