import React, { useState, useEffect, useCallback } from 'react';
import './SimplifiedInterface.css';

const SimplifiedInterface = ({ 
  onCommand, 
  currentUrl, 
  sessionId, 
  aiLoading, 
  nativeAPI 
}) => {
  const [commandInput, setCommandInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [recentCommands, setRecentCommands] = useState([]);

  // Fellou.ai-style intelligent suggestions
  const intelligentSuggestions = [
    'Navigate to google.com and search for AI tools',
    'Extract all links from this page',
    'Create an automation workflow',
    'Summarize the current page',
    'Find similar websites',
    'Monitor this page for changes',
    'Generate a report from page content',
    'Set up price monitoring',
    'Create shortcuts for frequent tasks',
    'Analyze page performance'
  ];

  // Voice recognition setup
  useEffect(() => {
    if ('webkitSpeechRecognition' in window) {
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

      window.speechRecognition = recognition;
    }
  }, []);

  // Smart suggestions based on input
  useEffect(() => {
    if (commandInput.length > 2) {
      const filtered = intelligentSuggestions.filter(suggestion =>
        suggestion.toLowerCase().includes(commandInput.toLowerCase())
      );
      setSuggestions(filtered.slice(0, 5));
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  }, [commandInput]);

  // Handle command execution
  const executeCommand = useCallback(async (command) => {
    if (!command.trim()) return;

    // Add to recent commands
    setRecentCommands(prev => [command, ...prev.slice(0, 4)]);
    
    // Hide suggestions
    setShowSuggestions(false);
    setCommandInput('');

    // Process command with AI
    await onCommand({
      command: command,
      context: {
        currentUrl,
        sessionId,
        timestamp: new Date().toISOString(),
        interface_mode: 'fellou'
      }
    });
  }, [onCommand, currentUrl, sessionId]);

  // Handle voice input
  const startVoiceInput = () => {
    if (window.speechRecognition) {
      window.speechRecognition.start();
    }
  };

  // Handle key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      executeCommand(commandInput);
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
      setCommandInput('');
    }
  };

  return (
    <div className="simplified-interface">
      {/* AETHER Branding - Fellou.ai Style */}
      <div className="aether-header">
        <div className="aether-logo-simplified">
          <div className="logo-gradient">⚡</div>
          <div className="brand-text">
            <h1>AETHER</h1>
            <p>Express Ideas, AETHER Acts</p>
          </div>
        </div>
        
        {/* Status Indicator */}
        <div className="status-indicator">
          <div className={`status-dot ${nativeAPI ? 'native' : 'web'}`}></div>
          <span className="status-text">
            {nativeAPI ? 'Native Chromium' : 'Enhanced Web'}
          </span>
        </div>
      </div>

      {/* Single Command Interface - Fellou.ai Style */}
      <div className="command-center">
        <div className="command-container">
          <div className="command-input-wrapper">
            <div className="command-icon">
              <div className="ai-pulse"></div>
              🤖
            </div>
            
            <input
              type="text"
              className="command-input"
              placeholder="Tell AETHER what you want to do..."
              value={commandInput}
              onChange={(e) => setCommandInput(e.target.value)}
              onKeyDown={handleKeyPress}
              disabled={aiLoading}
              autoFocus
            />
            
            <div className="command-actions">
              <button
                className={`voice-btn ${isListening ? 'listening' : ''}`}
                onClick={startVoiceInput}
                disabled={aiLoading}
                title="Voice Command"
              >
                {isListening ? (
                  <div className="listening-indicator">
                    <div className="pulse-ring"></div>
                    <div className="pulse-ring delay-1"></div>
                    <div className="pulse-ring delay-2"></div>
                    🎤
                  </div>
                ) : (
                  '🎤'
                )}
              </button>
              
              <button
                className={`execute-btn ${aiLoading ? 'loading' : ''}`}
                onClick={() => executeCommand(commandInput)}
                disabled={aiLoading || !commandInput.trim()}
                title="Execute Command"
              >
                {aiLoading ? (
                  <div className="loading-spinner"></div>
                ) : (
                  '→'
                )}
              </button>
            </div>
          </div>

          {/* Smart Suggestions Dropdown */}
          {showSuggestions && suggestions.length > 0 && (
            <div className="suggestions-dropdown">
              {suggestions.map((suggestion, index) => (
                <div
                  key={index}
                  className="suggestion-item"
                  onClick={() => executeCommand(suggestion)}
                >
                  <div className="suggestion-icon">💡</div>
                  <span className="suggestion-text">{suggestion}</span>
                </div>
              ))}
            </div>
          )}

          {/* Recent Commands */}
          {recentCommands.length > 0 && !showSuggestions && (
            <div className="recent-commands">
              <div className="recent-header">Recent</div>
              {recentCommands.slice(0, 3).map((command, index) => (
                <div
                  key={index}
                  className="recent-item"
                  onClick={() => executeCommand(command)}
                >
                  <div className="recent-icon">⏱️</div>
                  <span className="recent-text">{command}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Context Information */}
        {currentUrl && (
          <div className="context-info">
            <div className="context-icon">🌐</div>
            <span className="context-url">{currentUrl}</span>
          </div>
        )}
      </div>

      {/* Minimal Action Bar - Only Essential Controls */}
      <div className="minimal-actions">
        <div className="action-group">
          <button className="minimal-btn home" title="Home">🏠</button>
          <button className="minimal-btn back" title="Back">←</button>
          <button className="minimal-btn forward" title="Forward">→</button>
          <button className="minimal-btn refresh" title="Refresh">↻</button>
        </div>
        
        <div className="action-group">
          <button className="minimal-btn settings" title="Settings">⚙️</button>
          <button 
            className="minimal-btn traditional" 
            title="Switch to Traditional Mode"
            onClick={() => window.location.reload()}
          >
            📱
          </button>
        </div>
      </div>
    </div>
  );
};

export default SimplifiedInterface;