import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Send, Mic, Bot, Brain, Sparkles, Zap } from 'lucide-react';

const FellouCommandInterface = ({ 
  onCommand, 
  currentUrl, 
  sessionId, 
  aiLoading = false,
  proactiveSuggestions = [],
  behavioralInsights = null
}) => {
  const [command, setCommand] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [showProactive, setShowProactive] = useState(false);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);

  // Fellou.ai-style proactive suggestions
  const defaultSuggestions = [
    "Navigate to linkedin.com and find AI professionals",
    "Extract all links from this page and save to spreadsheet", 
    "Monitor this page for price changes and notify me",
    "Summarize the key points from this article",
    "Find similar websites to the current one",
    "Create a workflow to automate this task"
  ];

  // Enhanced command processing with context awareness
  const processCommand = useCallback(async () => {
    if (!command.trim()) return;

    // Add to behavioral learning
    const commandData = {
      command: command,
      context: {
        url: currentUrl,
        timestamp: Date.now(),
        sessionId: sessionId
      }
    };

    // Process via enhanced backend
    try {
      await onCommand(commandData);
      
      // Clear command and update suggestions based on success
      setCommand('');
      updateSmartSuggestions(command);
      
    } catch (error) {
      console.error('Command processing error:', error);
    }
  }, [command, currentUrl, sessionId, onCommand]);

  // Smart suggestion updates based on command patterns
  const updateSmartSuggestions = (executedCommand) => {
    const commandLower = executedCommand.toLowerCase();
    
    if (commandLower.includes('extract') || commandLower.includes('data')) {
      setSuggestions([
        "Export extracted data to CSV",
        "Set up monitoring for data changes",
        "Create automation for data extraction"
      ]);
    } else if (commandLower.includes('navigate') || commandLower.includes('go to')) {
      setSuggestions([
        "Bookmark this site for quick access",
        "Monitor this site for updates",
        "Extract key information from this page"
      ]);
    } else {
      setSuggestions(defaultSuggestions.slice(0, 3));
    }
  };

  // Voice recognition setup
  useEffect(() => {
    if (typeof window !== 'undefined' && 'webkitSpeechRecognition' in window) {
      recognitionRef.current = new window.webkitSpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setCommand(transcript);
        setIsListening(false);
      };

      recognitionRef.current.onerror = () => {
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }
  }, []);

  // Start voice recognition
  const startListening = () => {
    if (recognitionRef.current) {
      setIsListening(true);
      recognitionRef.current.start();
    }
  };

  // Enhanced keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e) => {
      // Ctrl+K or Cmd+K to focus command input (like Fellou.ai)
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
      }
      
      // Enter to execute command
      if (e.key === 'Enter' && document.activeElement === inputRef.current) {
        e.preventDefault();
        processCommand();
      }

      // Escape to clear command
      if (e.key === 'Escape' && document.activeElement === inputRef.current) {
        setCommand('');
        setShowProactive(false);
      }
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, [processCommand]);

  // Proactive suggestions from AI
  useEffect(() => {
    if (proactiveSuggestions.length > 0) {
      setSuggestions(proactiveSuggestions);
      setShowProactive(true);
    }
  }, [proactiveSuggestions]);

  // Auto-focus command input
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  return (
    <div className="fellou-command-interface">
      {/* Proactive AI Indicator */}
      {showProactive && (
        <div className="proactive-indicator">
          <div className="proactive-pulse">
            <Brain className="w-4 h-4 text-purple-400" />
            <span className="text-sm text-purple-300">AI suggests actions for this page</span>
          </div>
        </div>
      )}

      {/* Main Command Interface */}
      <div className="command-container">
        <div className="command-input-wrapper">
          {/* AI Status Indicator */}
          <div className="ai-status">
            {aiLoading ? (
              <div className="ai-thinking">
                <Sparkles className="w-5 h-5 text-purple-400 animate-pulse" />
              </div>
            ) : (
              <Bot className="w-5 h-5 text-purple-400" />
            )}
          </div>

          {/* Command Input */}
          <input
            ref={inputRef}
            type="text"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            placeholder="Express ideas, AETHER acts... (Ctrl+K to focus)"
            className="command-input"
            disabled={aiLoading}
          />

          {/* Voice Input */}
          <button
            onClick={startListening}
            className={`voice-btn ${isListening ? 'listening' : ''}`}
            disabled={aiLoading}
            title="Voice input"
          >
            <Mic className={`w-5 h-5 ${isListening ? 'text-red-400' : 'text-gray-400'}`} />
          </button>

          {/* Send Button */}
          <button
            onClick={processCommand}
            className="send-btn"
            disabled={!command.trim() || aiLoading}
            title="Execute command"
          >
            {aiLoading ? (
              <div className="loading-spinner"></div>
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Smart Suggestions */}
        {suggestions.length > 0 && (
          <div className="suggestions-panel">
            <div className="suggestions-header">
              <Zap className="w-4 h-4 text-yellow-400" />
              <span className="text-sm text-gray-300">Smart Suggestions</span>
            </div>
            <div className="suggestions-list">
              {suggestions.slice(0, 3).map((suggestion, index) => (
                <button
                  key={index}
                  className="suggestion-chip"
                  onClick={() => {
                    setCommand(suggestion);
                    inputRef.current?.focus();
                  }}
                >
                  <span className="suggestion-text">{suggestion}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Behavioral Insights */}
        {behavioralInsights && (
          <div className="behavioral-insights">
            <div className="insights-indicator">
              <Brain className="w-4 h-4 text-blue-400" />
              <span className="text-xs text-blue-300">
                Pattern detected: {behavioralInsights.pattern} 
                ({behavioralInsights.confidence}% confidence)
              </span>
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        .fellou-command-interface {
          position: relative;
          z-index: 1000;
        }

        .proactive-indicator {
          position: fixed;
          top: 20px;
          right: 20px;
          background: rgba(139, 69, 19, 0.1);
          border: 1px solid rgba(147, 51, 234, 0.3);
          border-radius: 12px;
          padding: 8px 12px;
          backdrop-filter: blur(10px);
          animation: slideIn 0.3s ease-out;
        }

        .proactive-pulse {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .command-container {
          position: fixed;
          bottom: 30px;
          left: 50%;
          transform: translateX(-50%);
          width: 90%;
          max-width: 800px;
          background: rgba(15, 15, 20, 0.95);
          border: 2px solid rgba(147, 51, 234, 0.3);
          border-radius: 20px;
          padding: 16px;
          backdrop-filter: blur(20px);
          box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.05);
        }

        .command-input-wrapper {
          display: flex;
          align-items: center;
          gap: 12px;
          background: rgba(30, 30, 35, 0.8);
          border-radius: 16px;
          padding: 12px 16px;
          border: 1px solid rgba(147, 51, 234, 0.2);
        }

        .ai-status {
          flex-shrink: 0;
        }

        .ai-thinking {
          animation: pulse 2s infinite;
        }

        .command-input {
          flex: 1;
          background: transparent;
          border: none;
          outline: none;
          color: white;
          font-size: 16px;
          font-weight: 400;
          line-height: 1.5;
        }

        .command-input::placeholder {
          color: rgba(156, 163, 175, 0.6);
          font-style: italic;
        }

        .voice-btn, .send-btn {
          flex-shrink: 0;
          padding: 8px;
          border-radius: 12px;
          border: none;
          background: rgba(147, 51, 234, 0.1);
          color: white;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .voice-btn:hover, .send-btn:hover {
          background: rgba(147, 51, 234, 0.2);
          transform: scale(1.05);
        }

        .voice-btn.listening {
          background: rgba(239, 68, 68, 0.2);
          animation: pulse 1s infinite;
        }

        .send-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
          transform: none;
        }

        .loading-spinner {
          width: 20px;
          height: 20px;
          border: 2px solid rgba(147, 51, 234, 0.3);
          border-top: 2px solid rgb(147, 51, 234);
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        .suggestions-panel {
          margin-top: 16px;
          border-top: 1px solid rgba(147, 51, 234, 0.1);
          padding-top: 16px;
        }

        .suggestions-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 12px;
        }

        .suggestions-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .suggestion-chip {
          background: rgba(147, 51, 234, 0.05);
          border: 1px solid rgba(147, 51, 234, 0.1);
          border-radius: 12px;
          padding: 10px 16px;
          color: rgba(255, 255, 255, 0.8);
          cursor: pointer;
          transition: all 0.2s ease;
          text-align: left;
          font-size: 14px;
          line-height: 1.4;
        }

        .suggestion-chip:hover {
          background: rgba(147, 51, 234, 0.1);
          border-color: rgba(147, 51, 234, 0.3);
          transform: translateY(-1px);
        }

        .behavioral-insights {
          margin-top: 12px;
          padding: 8px 12px;
          background: rgba(59, 130, 246, 0.05);
          border: 1px solid rgba(59, 130, 246, 0.1);
          border-radius: 8px;
        }

        .insights-indicator {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }

        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        /* Mobile responsiveness */
        @media (max-width: 768px) {
          .command-container {
            width: 95%;
            bottom: 20px;
            padding: 12px;
          }

          .command-input-wrapper {
            padding: 10px 12px;
          }

          .command-input {
            font-size: 14px;
          }

          .suggestions-list {
            display: grid;
            grid-template-columns: 1fr;
            gap: 6px;
          }

          .suggestion-chip {
            padding: 8px 12px;
            font-size: 13px;
          }
        }
      `}</style>
    </div>
  );
};

export default FellouCommandInterface;