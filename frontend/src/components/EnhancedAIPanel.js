import React, { useState, useRef, useEffect } from 'react';
import './EnhancedAIPanel.css';

const EnhancedAIPanel = ({ 
  isVisible, 
  onClose, 
  chatMessages, 
  setChatMessages, 
  aiInput, 
  setAiInput, 
  aiLoading, 
  onSendMessage,
  currentUrl,
  sessionId,
  backgroundTasks = {}  // Add background tasks support
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState('chat');
  const [suggestions, setSuggestions] = useState([]);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const [isTyping, setIsTyping] = useState(false);

  // Calculate active background tasks
  const activeTaskCount = Object.keys(backgroundTasks).length;

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Auto-focus input when panel opens
  useEffect(() => {
    if (isVisible && inputRef.current) {
      setTimeout(() => inputRef.current.focus(), 100);
    }
  }, [isVisible]);

  // Generate smart suggestions based on current context
  useEffect(() => {
    const generateSuggestions = () => {
      const baseSuggestions = [
        '💡 What can you help me with?',
        '📊 Show system status',
        '🔧 Create a workflow'
      ];

      if (currentUrl) {
        return [
          '📄 Summarize this page',
          '🔍 Extract key information',
          '🚀 Automate this task',
          ...baseSuggestions
        ];
      }

      return baseSuggestions;
    };

    setSuggestions(generateSuggestions());
  }, [currentUrl]);

  const handleInputChange = (e) => {
    setAiInput(e.target.value);
    setIsTyping(true);
    setTimeout(() => setIsTyping(false), 1000);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    if (aiInput.trim() && !aiLoading) {
      onSendMessage();
      setSuggestions([]); // Clear suggestions after first message
    }
  };

  const handleSuggestionClick = (suggestion) => {
    const cleanText = suggestion.replace(/[^\w\s]/gi, '').trim();
    setAiInput(cleanText);
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
  };

  const formatMessage = (content) => {
    // Enhanced message formatting with better parsing
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br/>')
      .replace(/- (.*?)(?=\n|$)/g, '<li>$1</li>')
      .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
  };

  if (!isVisible) return null;

  return (
    <div className={`ai-panel enhanced ${isExpanded ? 'expanded' : ''}`}>
      {/* Header */}
      <div className="ai-header">
        <div className="ai-title-section">
          <div className="ai-avatar">
            <div className="avatar-glow"></div>
            🤖
          </div>
          <div className="ai-info">
            <h3>AETHER Assistant</h3>
            <p className="ai-status">
              {aiLoading ? 'Thinking...' : `Ready • ${chatMessages.length} messages`}
            </p>
          </div>
        </div>
        <div className="ai-controls">
          <button 
            className={`expand-btn ${isExpanded ? 'expanded' : ''}`}
            onClick={() => setIsExpanded(!isExpanded)}
            title={isExpanded ? 'Minimize' : 'Expand'}
            aria-label={isExpanded ? 'Minimize AI panel' : 'Expand AI panel'}
          >
            {isExpanded ? '⤓' : '⤢'}
          </button>
          <button 
            className="close-btn"
            onClick={onClose}
            title="Close AI Assistant"
            aria-label="Close AI Assistant"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="ai-tabs">
        <button 
          className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          💬 Chat
        </button>
        <button 
          className={`tab-btn ${activeTab === 'actions' ? 'active' : ''}`}
          onClick={() => setActiveTab('actions')}
        >
          ⚡ Actions
        </button>
        <button 
          className={`tab-btn ${activeTab === 'insights' ? 'active' : ''}`}
          onClick={() => setActiveTab('insights')}
        >
          📊 Insights
        </button>
      </div>

      {/* Content */}
      <div className="ai-content">
        {activeTab === 'chat' && (
          <div className="chat-container">
            <div className="chat-messages">
              {chatMessages.length === 0 ? (
                <div className="welcome-screen">
                  <div className="welcome-animation">
                    <div className="pulse-ring"></div>
                    <div className="ai-icon">🧠</div>
                  </div>
                  <h3>Hello! I'm your AI assistant</h3>
                  <p>I can help you browse smarter, automate tasks, and get insights from web content.</p>
                  
                  <div className="capabilities-preview">
                    <div className="capability-item">
                      <span className="capability-icon">📄</span>
                      <span>Summarize web pages</span>
                    </div>
                    <div className="capability-item">
                      <span className="capability-icon">🔧</span>
                      <span>Create automations</span>
                    </div>
                    <div className="capability-item">
                      <span className="capability-icon">💡</span>
                      <span>Extract insights</span>
                    </div>
                    <div className="capability-item">
                      <span className="capability-icon">🚀</span>
                      <span>Boost productivity</span>
                    </div>
                  </div>
                </div>
              ) : (
                chatMessages.map((message, index) => (
                  <div key={index} className={`message ${message.role}`}>
                    <div className="message-avatar">
                      {message.role === 'user' ? '👤' : '🤖'}
                    </div>
                    <div className="message-content">
                      <div 
                        className="message-text"
                        dangerouslySetInnerHTML={{ 
                          __html: formatMessage(message.content) 
                        }} 
                      />
                      <div className="message-time">
                        {new Date().toLocaleTimeString([], { 
                          hour: '2-digit', 
                          minute: '2-digit' 
                        })}
                      </div>
                    </div>
                  </div>
                ))
              )}
              
              {aiLoading && (
                <div className="message assistant loading">
                  <div className="message-avatar">🤖</div>
                  <div className="message-content">
                    <div className="typing-animation">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Smart Suggestions */}
            {suggestions.length > 0 && chatMessages.length === 0 && (
              <div className="smart-suggestions">
                <p className="suggestions-title">Try asking me:</p>
                <div className="suggestions-grid">
                  {suggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      className="suggestion-chip"
                      onClick={() => handleSuggestionClick(suggestion)}
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Input Area */}
            <div className="chat-input-container">
              <div className={`input-wrapper ${isTyping ? 'typing' : ''}`}>
                <textarea
                  ref={inputRef}
                  className="chat-input"
                  value={aiInput}
                  onChange={handleInputChange}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me anything... (Shift+Enter for new line)"
                  disabled={aiLoading}
                  rows={1}
                  style={{ 
                    height: 'auto',
                    minHeight: '44px',
                    maxHeight: '120px'
                  }}
                  onInput={(e) => {
                    e.target.style.height = 'auto';
                    e.target.style.height = e.target.scrollHeight + 'px';
                  }}
                />
                <button
                  className={`send-btn ${aiInput.trim() ? 'ready' : ''}`}
                  onClick={handleSend}
                  disabled={!aiInput.trim() || aiLoading}
                  title="Send message"
                  aria-label="Send message"
                >
                  {aiLoading ? '⏳' : '→'}
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'actions' && (
          <div className="actions-container">
            <h4>Quick Actions</h4>
            <div className="action-buttons">
              <button 
                className="action-button"
                onClick={() => handleSuggestionClick('Summarize this page')}
              >
                <span className="action-icon">📄</span>
                <span>Summarize Page</span>
              </button>
              <button 
                className="action-button"
                onClick={() => handleSuggestionClick('Show system status')}
              >
                <span className="action-icon">📊</span>
                <span>System Status</span>
              </button>
              <button 
                className="action-button"
                onClick={() => handleSuggestionClick('Create workflow')}
              >
                <span className="action-icon">🔧</span>
                <span>Create Workflow</span>
              </button>
              <button 
                className="action-button"
                onClick={() => handleSuggestionClick('Extract key information')}
              >
                <span className="action-icon">🔍</span>
                <span>Extract Info</span>
              </button>
            </div>
          </div>
        )}

        {activeTab === 'insights' && (
          <div className="insights-container">
            <h4>Page Insights</h4>
            {currentUrl ? (
              <div className="page-analysis">
                <div className="insight-item">
                  <span className="insight-label">Current Page:</span>
                  <span className="insight-value">{new URL(currentUrl).hostname}</span>
                </div>
                <div className="insight-item">
                  <span className="insight-label">Security:</span>
                  <span className={`insight-value ${currentUrl.startsWith('https') ? 'secure' : 'insecure'}`}>
                    {currentUrl.startsWith('https') ? '🔒 Secure' : '⚠️ Not Secure'}
                  </span>
                </div>
                <div className="insight-item">
                  <span className="insight-label">Session:</span>
                  <span className="insight-value">{sessionId?.slice(-8)}</span>
                </div>
              </div>
            ) : (
              <p className="no-insights">Navigate to a website to see insights</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedAIPanel;