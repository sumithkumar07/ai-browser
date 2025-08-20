import React, { useState, useRef, useEffect } from 'react';

const SimplifiedInterface = ({ 
  onCommand, 
  currentUrl, 
  sessionId, 
  aiLoading,
  nativeAPI 
}) => {
  const [commandInput, setCommandInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [suggestions] = useState([
    'Navigate to google.com',
    'Summarize this page',
    'Extract data from this website',
    'Create workflow automation',
    'Search for AI tools'
  ]);
  const inputRef = useRef(null);

  useEffect(() => {
    // Focus input on load
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!commandInput.trim()) return;

    const commandData = {
      command: commandInput,
      context: {
        currentUrl: currentUrl,
        sessionId: sessionId,
        timestamp: new Date().toISOString(),
        nativeEngine: !!nativeAPI
      }
    };

    await onCommand(commandData);
    setCommandInput('');
  };

  const handleSuggestionClick = (suggestion) => {
    setCommandInput(suggestion);
  };

  const handleVoiceCommand = () => {
    if (!('webkitSpeechRecognition' in window)) {
      alert('Voice recognition not supported in this browser');
      return;
    }

    const recognition = new window.webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setCommandInput(transcript);
      setIsListening(false);
    };

    recognition.onerror = () => {
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  return (
    <div className="simplified-interface">
      {/* Header */}
      <div className="simplified-header">
        <div className="aether-branding">
          <div className="logo">⚡</div>
          <div className="brand-text">
            <h1>AETHER</h1>
            <p>Express Ideas, AETHER Acts</p>
          </div>
        </div>

        <div className="engine-status">
          {nativeAPI ? (
            <span className="native-active">🔥 Native Chromium</span>
          ) : (
            <span className="web-mode">🌐 Enhanced Web</span>
          )}
        </div>
      </div>

      {/* Command Interface */}
      <div className="command-center">
        <form onSubmit={handleSubmit} className="command-form">
          <div className="command-input-container">
            <div className="command-icon">👑</div>
            
            <input
              ref={inputRef}
              type="text"
              value={commandInput}
              onChange={(e) => setCommandInput(e.target.value)}
              placeholder="Tell AETHER what you want to do..."
              className="command-input"
              disabled={aiLoading}
            />

            <button
              type="button"
              onClick={handleVoiceCommand}
              className={`voice-btn ${isListening ? 'listening' : ''}`}
              title="Voice Command"
            >
              {isListening ? '🎙️' : '🎤'}
            </button>

            <button
              type="submit"
              className="execute-btn"
              disabled={!commandInput.trim() || aiLoading}
            >
              {aiLoading ? (
                <div className="loading-spinner"></div>
              ) : (
                '⚡'
              )}
            </button>
          </div>
        </form>

        {/* Quick Suggestions */}
        <div className="quick-suggestions">
          <div className="suggestions-label">Quick Actions:</div>
          <div className="suggestions-grid">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                className="suggestion-chip"
                onClick={() => handleSuggestionClick(suggestion)}
                disabled={aiLoading}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Status Bar */}
      <div className="status-bar">
        <div className="current-context">
          {currentUrl ? (
            <span className="context-url">📍 {new URL(currentUrl).hostname}</span>
          ) : (
            <span className="context-ready">🏠 Ready for commands</span>
          )}
        </div>
        
        <div className="capabilities">
          <span className="capability">🧠 AI Assistant</span>
          <span className="capability">🔧 Automation</span>
          <span className="capability">🌐 Web Access</span>
          {nativeAPI && <span className="capability">⚡ Native Engine</span>}
        </div>
      </div>

      <style jsx>{`
        .simplified-interface {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          z-index: 1000;
          background: linear-gradient(135deg, #0a0a0f 0%, #1a1a1f 100%);
          border-bottom: 1px solid rgba(139, 92, 246, 0.2);
          backdrop-filter: blur(20px);
        }

        .simplified-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 24px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .aether-branding {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .logo {
          font-size: 28px;
          background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .brand-text h1 {
          font-size: 20px;
          font-weight: 700;
          background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          margin: 0;
        }

        .brand-text p {
          font-size: 12px;
          color: #a1a1aa;
          margin: 0;
        }

        .engine-status {
          padding: 6px 12px;
          background: rgba(139, 92, 246, 0.1);
          border: 1px solid rgba(139, 92, 246, 0.2);
          border-radius: 16px;
          font-size: 12px;
          font-weight: 600;
        }

        .native-active {
          color: #22c55e;
        }

        .web-mode {
          color: #f59e0b;
        }

        .command-center {
          padding: 24px;
        }

        .command-form {
          margin-bottom: 24px;
        }

        .command-input-container {
          display: flex;
          align-items: center;
          background: rgba(139, 92, 246, 0.1);
          border: 2px solid rgba(139, 92, 246, 0.3);
          border-radius: 24px;
          padding: 4px;
          transition: all 0.3s ease;
        }

        .command-input-container:focus-within {
          border-color: #8b5cf6;
          box-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
        }

        .command-icon {
          font-size: 20px;
          margin-left: 16px;
          margin-right: 8px;
        }

        .command-input {
          flex: 1;
          background: transparent;
          border: none;
          outline: none;
          color: #fff;
          font-size: 16px;
          padding: 16px 8px;
          placeholder-color: #71717a;
        }

        .command-input::placeholder {
          color: #71717a;
        }

        .voice-btn {
          width: 44px;
          height: 44px;
          border: none;
          background: rgba(139, 92, 246, 0.2);
          border-radius: 50%;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 18px;
          transition: all 0.3s ease;
          margin-right: 4px;
        }

        .voice-btn:hover {
          background: rgba(139, 92, 246, 0.4);
          transform: scale(1.05);
        }

        .voice-btn.listening {
          background: #ef4444;
          animation: pulse 1s infinite;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }

        .execute-btn {
          width: 44px;
          height: 44px;
          border: none;
          background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%);
          border-radius: 50%;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 18px;
          color: #fff;
          transition: all 0.3s ease;
        }

        .execute-btn:hover:not(:disabled) {
          transform: scale(1.05);
          box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4);
        }

        .execute-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .loading-spinner {
          width: 20px;
          height: 20px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-left: 2px solid #fff;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .quick-suggestions {
          text-align: center;
        }

        .suggestions-label {
          color: #a1a1aa;
          font-size: 14px;
          margin-bottom: 12px;
        }

        .suggestions-grid {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          justify-content: center;
        }

        .suggestion-chip {
          background: rgba(139, 92, 246, 0.1);
          border: 1px solid rgba(139, 92, 246, 0.2);
          border-radius: 16px;
          padding: 8px 16px;
          color: #e5e5e5;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .suggestion-chip:hover:not(:disabled) {
          background: rgba(139, 92, 246, 0.2);
          border-color: #8b5cf6;
          transform: translateY(-1px);
        }

        .suggestion-chip:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .status-bar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 24px;
          background: rgba(0, 0, 0, 0.2);
          border-top: 1px solid rgba(255, 255, 255, 0.1);
          font-size: 12px;
        }

        .current-context {
          color: #a1a1aa;
        }

        .context-url {
          color: #8b5cf6;
        }

        .context-ready {
          color: #22c55e;
        }

        .capabilities {
          display: flex;
          gap: 16px;
        }

        .capability {
          color: #71717a;
          display: flex;
          align-items: center;
          gap: 4px;
        }

        /* Mobile responsiveness */
        @media (max-width: 768px) {
          .simplified-header {
            padding: 12px 16px;
          }

          .command-center {
            padding: 16px;
          }

          .command-input {
            font-size: 14px;
          }

          .suggestions-grid {
            flex-direction: column;
          }

          .status-bar {
            flex-direction: column;
            gap: 8px;
            text-align: center;
          }

          .capabilities {
            justify-content: center;
          }
        }
      `}</style>
    </div>
  );
};

export default SimplifiedInterface;