import React, { useState, useCallback, useRef, useEffect } from 'react';

/**
 * Simplified Interface Component - Fellou.ai-style minimalist interface
 * Provides command-first interaction with hidden complexity
 */
const SimplifiedInterface = ({ 
  onCommand, 
  currentUrl, 
  sessionId, 
  aiLoading, 
  nativeAPI 
}) => {
  const [commandInput, setCommandInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [lastCommand, setLastCommand] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  const inputRef = useRef(null);
  const commandHistoryRef = useRef([]);

  // Focus command input on mount
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  // Process enhanced command
  const handleCommand = useCallback(async (command) => {
    if (!command.trim()) return;

    setIsProcessing(true);
    setLastCommand(command);
    
    // Add to command history
    commandHistoryRef.current.unshift(command);
    if (commandHistoryRef.current.length > 10) {
      commandHistoryRef.current = commandHistoryRef.current.slice(0, 10);
    }

    try {
      const commandData = {
        command: command,
        context: {
          current_url: currentUrl,
          interface_mode: 'fellou',
          session_id: sessionId,
          native_available: nativeAPI?.hasNativeChromium() || false
        }
      };

      // Call parent command processor
      const result = await onCommand(commandData);
      
      // Handle suggestions from result
      if (result?.proactive_suggestions) {
        setSuggestions(result.proactive_suggestions);
      }

      console.log('🔥 Fellou-style command processed:', result);

    } catch (error) {
      console.error('Command processing error:', error);
    } finally {
      setIsProcessing(false);
      setCommandInput('');
    }
  }, [currentUrl, sessionId, nativeAPI, onCommand]);

  // Handle input submission
  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    handleCommand(commandInput);
  }, [commandInput, handleCommand]);

  // Handle suggestion click
  const handleSuggestionClick = useCallback((suggestion) => {
    handleCommand(suggestion.action || suggestion.title);
  }, [handleCommand]);

  // Keyboard shortcuts
  const handleKeyDown = useCallback((e) => {
    // Arrow up for command history
    if (e.key === 'ArrowUp' && commandHistoryRef.current.length > 0) {
      e.preventDefault();
      const lastCmd = commandHistoryRef.current[0];
      setCommandInput(lastCmd);
    }
    
    // Escape to clear
    if (e.key === 'Escape') {
      setCommandInput('');
      setSuggestions([]);
    }
  }, []);

  // Quick command shortcuts
  const quickCommands = [
    {
      label: 'Navigate',
      icon: '🌐',
      placeholder: 'go to example.com',
      example: 'navigate to github.com'
    },
    {
      label: 'Search',
      icon: '🔍',
      placeholder: 'search for AI tools',
      example: 'search for React tutorials'
    },
    {
      label: 'Automate',
      icon: '🤖',
      placeholder: 'automate login process',
      example: 'fill out contact form'
    },
    {
      label: 'Screenshot',
      icon: '📸',
      placeholder: 'take screenshot',
      example: 'capture full page screenshot'
    }
  ];

  return (
    <div className="simplified-interface">
      {/* Main Command Interface */}
      <div className="command-section">
        <div className="aether-branding">
          <div className="brand-logo">⚡</div>
          <div className="brand-text">
            <h1>AETHER</h1>
            <p>Express Ideas, AETHER Acts</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="command-form">
          <div className="command-input-container">
            <input
              ref={inputRef}
              type="text"
              value={commandInput}
              onChange={(e) => setCommandInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Tell AETHER what you want to do..."
              className="command-input"
              disabled={isProcessing || aiLoading}
            />
            
            <button
              type="submit"
              className="command-submit"
              disabled={!commandInput.trim() || isProcessing || aiLoading}
            >
              {isProcessing || aiLoading ? (
                <div className="processing-spinner"></div>
              ) : (
                '→'
              )}
            </button>
          </div>
          
          {lastCommand && (isProcessing || aiLoading) && (
            <div className="processing-status">
              <span className="processing-icon">🔄</span>
              <span className="processing-text">Processing: "{lastCommand}"</span>
            </div>
          )}
        </form>

        {/* Quick Command Hints */}
        <div className="quick-commands">
          {quickCommands.map((cmd, index) => (
            <div
              key={index}
              className="quick-command"
              onClick={() => setCommandInput(cmd.example)}
            >
              <span className="quick-icon">{cmd.icon}</span>
              <span className="quick-label">{cmd.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Proactive Suggestions */}
      {suggestions.length > 0 && (
        <div className="suggestions-section">
          <h3>💡 Smart Suggestions</h3>
          <div className="suggestions-grid">
            {suggestions.map((suggestion, index) => (
              <div
                key={index}
                className="suggestion-card"
                onClick={() => handleSuggestionClick(suggestion)}
              >
                <div className="suggestion-title">{suggestion.title}</div>
                <div className="suggestion-description">{suggestion.description}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Advanced Toggle */}
      <div className="interface-controls">
        <button
          className="advanced-toggle"
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          {showAdvanced ? '🔒 Hide Advanced' : '🔧 Show Advanced'}
        </button>
        
        {nativeAPI?.hasNativeChromium() && (
          <div className="native-badge">
            <span className="native-icon">🔥</span>
            <span>Native Engine</span>
          </div>
        )}
      </div>

      {/* Advanced Controls (Hidden by Default) */}
      {showAdvanced && (
        <div className="advanced-section">
          <div className="advanced-grid">
            <div className="advanced-card">
              <h4>🌐 Navigation</h4>
              <div className="advanced-actions">
                <button onClick={() => handleCommand('go back')}>← Back</button>
                <button onClick={() => handleCommand('go forward')}>Forward →</button>
                <button onClick={() => handleCommand('refresh page')}>↻ Refresh</button>
              </div>
            </div>
            
            <div className="advanced-card">
              <h4>📸 Capture</h4>
              <div className="advanced-actions">
                <button onClick={() => handleCommand('take screenshot')}>Screenshot</button>
                <button onClick={() => handleCommand('save page as PDF')}>Save PDF</button>
              </div>
            </div>
            
            <div className="advanced-card">
              <h4>🔧 DevTools</h4>
              <div className="advanced-actions">
                <button onClick={() => handleCommand('open devtools')}>DevTools</button>
                <button onClick={() => handleCommand('inspect element')}>Inspect</button>
              </div>
            </div>
            
            <div className="advanced-card">
              <h4>🤖 Automation</h4>
              <div className="advanced-actions">
                <button onClick={() => handleCommand('create workflow')}>Create Workflow</button>
                <button onClick={() => handleCommand('run automation')}>Run Automation</button>
              </div>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .simplified-interface {
          width: 100%;
          min-height: 100vh;
          background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #16213e 100%);
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 40px 20px;
        }

        .command-section {
          width: 100%;
          max-width: 800px;
          text-align: center;
        }

        .aether-branding {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 20px;
          margin-bottom: 50px;
        }

        .brand-logo {
          font-size: 60px;
          background: linear-gradient(135deg, #9333ea, #f59e0b);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          animation: pulse 2s ease-in-out infinite alternate;
        }

        @keyframes pulse {
          from { transform: scale(1); }
          to { transform: scale(1.05); }
        }

        .brand-text h1 {
          font-size: 48px;
          font-weight: 800;
          background: linear-gradient(135deg, #9333ea, #f59e0b);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          margin: 0;
          letter-spacing: -2px;
        }

        .brand-text p {
          font-size: 18px;
          color: #94a3b8;
          margin: 8px 0 0 0;
          font-weight: 300;
        }

        .command-form {
          margin-bottom: 40px;
        }

        .command-input-container {
          position: relative;
          display: flex;
          align-items: center;
          background: rgba(255, 255, 255, 0.05);
          border: 2px solid rgba(147, 51, 234, 0.3);
          border-radius: 24px;
          padding: 8px;
          backdrop-filter: blur(10px);
          transition: all 0.3s ease;
        }

        .command-input-container:focus-within {
          border-color: #9333ea;
          box-shadow: 0 0 30px rgba(147, 51, 234, 0.3);
        }

        .command-input {
          flex: 1;
          background: transparent;
          border: none;
          padding: 16px 24px;
          font-size: 18px;
          color: white;
          outline: none;
        }

        .command-input::placeholder {
          color: rgba(148, 163, 184, 0.7);
        }

        .command-submit {
          background: linear-gradient(135deg, #9333ea, #7c3aed);
          border: none;
          width: 48px;
          height: 48px;
          border-radius: 20px;
          color: white;
          font-size: 20px;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .command-submit:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 8px 25px rgba(147, 51, 234, 0.4);
        }

        .command-submit:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .processing-spinner {
          width: 20px;
          height: 20px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top: 2px solid white;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .processing-status {
          margin-top: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          color: #94a3b8;
          font-size: 14px;
        }

        .processing-icon {
          animation: spin 2s linear infinite;
        }

        .quick-commands {
          display: flex;
          justify-content: center;
          gap: 20px;
          flex-wrap: wrap;
        }

        .quick-command {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          padding: 16px;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.3s ease;
          min-width: 80px;
        }

        .quick-command:hover {
          background: rgba(147, 51, 234, 0.1);
          border-color: rgba(147, 51, 234, 0.3);
          transform: translateY(-2px);
        }

        .quick-icon {
          font-size: 24px;
        }

        .quick-label {
          font-size: 12px;
          color: #94a3b8;
          font-weight: 500;
        }

        .suggestions-section {
          margin-top: 40px;
          width: 100%;
          max-width: 800px;
        }

        .suggestions-section h3 {
          color: #e2e8f0;
          text-align: center;
          margin-bottom: 20px;
          font-weight: 600;
        }

        .suggestions-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 16px;
        }

        .suggestion-card {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 20px;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .suggestion-card:hover {
          background: rgba(147, 51, 234, 0.1);
          border-color: rgba(147, 51, 234, 0.3);
          transform: translateY(-2px);
        }

        .suggestion-title {
          font-weight: 600;
          color: white;
          margin-bottom: 8px;
        }

        .suggestion-description {
          font-size: 14px;
          color: #94a3b8;
          line-height: 1.4;
        }

        .interface-controls {
          margin-top: 40px;
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .advanced-toggle {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.2);
          color: #94a3b8;
          padding: 8px 16px;
          border-radius: 20px;
          cursor: pointer;
          font-size: 14px;
          transition: all 0.2s ease;
        }

        .advanced-toggle:hover {
          background: rgba(255, 255, 255, 0.1);
          color: white;
        }

        .native-badge {
          display: flex;
          align-items: center;
          gap: 6px;
          background: rgba(34, 197, 94, 0.1);
          border: 1px solid rgba(34, 197, 94, 0.3);
          color: #22c55e;
          padding: 6px 12px;
          border-radius: 16px;
          font-size: 12px;
          font-weight: 600;
        }

        .advanced-section {
          margin-top: 30px;
          width: 100%;
          max-width: 800px;
        }

        .advanced-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 16px;
        }

        .advanced-card {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 16px;
        }

        .advanced-card h4 {
          color: white;
          margin: 0 0 12px 0;
          font-size: 14px;
          font-weight: 600;
        }

        .advanced-actions {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .advanced-actions button {
          background: rgba(147, 51, 234, 0.1);
          border: 1px solid rgba(147, 51, 234, 0.3);
          color: #c4b5fd;
          padding: 8px 12px;
          border-radius: 6px;
          cursor: pointer;
          font-size: 12px;
          transition: all 0.2s ease;
        }

        .advanced-actions button:hover {
          background: rgba(147, 51, 234, 0.2);
          color: white;
        }

        @media (max-width: 768px) {
          .aether-branding {
            flex-direction: column;
            gap: 10px;
          }
          
          .brand-logo {
            font-size: 40px;
          }
          
          .brand-text h1 {
            font-size: 36px;
          }
          
          .command-input {
            font-size: 16px;
            padding: 14px 20px;
          }
          
          .quick-commands {
            gap: 12px;
          }
          
          .advanced-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default SimplifiedInterface;