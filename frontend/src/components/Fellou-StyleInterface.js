import React, { useState, useEffect, useRef, useCallback } from 'react';
import './FellowStyleInterface.css';

const FellowStyleInterface = ({ 
  onNavigate, 
  onAICommand,
  currentUrl,
  sessionId,
  backendUrl 
}) => {
  const [commandInput, setCommandInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [aiProcessing, setAiProcessing] = useState(false);
  const [contextMode, setContextMode] = useState('browser'); // browser, automation, workflow
  
  const inputRef = useRef(null);

  // Proactive AI suggestions based on context
  const proactiveSuggestions = [
    "Navigate to google.com",
    "Summarize this page", 
    "Extract data from current page",
    "Create workflow for this task",
    "Monitor this page for changes",
    "Find similar websites",
    "Generate report from content",
    "Set up automation"
  ];

  // Context-sensitive command examples
  const getContextExamples = () => {
    switch(contextMode) {
      case 'automation':
        return [
          "Extract all links from this page",
          "Monitor price changes on this product",
          "Auto-fill forms with my data",
          "Create recurring task for this action"
        ];
      case 'workflow':
        return [
          "Create workflow: research → analyze → report",
          "Set up daily automation for this task",
          "Build multi-step process for data collection",
          "Generate template from current page"
        ];
      default:
        return [
          "Go to github.com",
          "Search for AI tools 2025", 
          "Summarize current page",
          "Find related articles"
        ];
    }
  };

  // Enhanced command processing with NLP
  const processCommand = useCallback(async (command) => {
    if (!command.trim()) return;
    
    setAiProcessing(true);
    setShowSuggestions(false);
    
    try {
      // Advanced command interpretation
      const response = await fetch(`${backendUrl}/api/enhanced/command-processor`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command: command,
          context: {
            current_url: currentUrl,
            session_id: sessionId,
            context_mode: contextMode,
            enable_proactive: true,
            multi_step_parsing: true
          }
        })
      });

      if (response.ok) {
        const result = await response.json();
        
        // Handle different command types
        switch (result.command_type) {
          case 'navigation':
            if (result.url) {
              onNavigate(result.url);
            }
            break;
            
          case 'automation':
            // Trigger automation workflow
            await handleAutomationCommand(result);
            break;
            
          case 'ai_query':
            // Process through AI assistant
            if (onAICommand) {
              onAICommand(command, result);
            }
            break;
            
          case 'multi_step':
            // Handle complex multi-step commands
            await handleMultiStepCommand(result);
            break;
            
          default:
            // Fallback to AI processing
            if (onAICommand) {
              onAICommand(command);
            }
        }
        
        // Update context based on command
        if (result.suggested_context) {
          setContextMode(result.suggested_context);
        }
        
      } else {
        // Fallback to basic AI processing
        if (onAICommand) {
          onAICommand(command);
        }
      }
    } catch (error) {
      console.error('Command processing error:', error);
      // Fallback to AI assistant
      if (onAICommand) {
        onAICommand(command);
      }
    } finally {
      setAiProcessing(false);
      setCommandInput('');
    }
  }, [backendUrl, currentUrl, sessionId, contextMode, onNavigate, onAICommand]);

  // Handle automation commands
  const handleAutomationCommand = async (result) => {
    try {
      const automationResponse = await fetch(`${backendUrl}/api/automation/execute-smart`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          automation_config: result.automation_config,
          session_id: sessionId,
          background: true
        })
      });
      
      if (automationResponse.ok) {
        const automationResult = await automationResponse.json();
        // Show subtle confirmation
        showAutomationFeedback(automationResult);
      }
    } catch (error) {
      console.error('Automation execution error:', error);
    }
  };

  // Handle multi-step commands (Fellou.ai-style)
  const handleMultiStepCommand = async (result) => {
    for (const step of result.steps || []) {
      try {
        await fetch(`${backendUrl}/api/automation/execute-step`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            step: step,
            session_id: sessionId,
            sequence_id: result.sequence_id
          })
        });
      } catch (error) {
        console.error('Multi-step execution error:', error);
        break; // Stop on error
      }
    }
  };

  // Show automation feedback
  const showAutomationFeedback = (result) => {
    // Could integrate with notification system
    console.log('Automation started:', result);
  };

  // Voice command integration
  const handleVoiceCommand = useCallback(() => {
    if (!('webkitSpeechRecognition' in window)) {
      alert('Speech recognition not supported');
      return;
    }

    const recognition = new window.webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    setIsListening(true);

    recognition.onresult = (event) => {
      const command = event.results[0][0].transcript;
      setCommandInput(command);
      processCommand(command);
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  }, [processCommand]);

  // Get intelligent suggestions
  const getIntelligentSuggestions = useCallback(async (input) => {
    if (!input.trim() || input.length < 2) {
      setSuggestions(proactiveSuggestions.slice(0, 5));
      return;
    }

    try {
      const response = await fetch(`${backendUrl}/api/enhanced/command-suggestions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          partial_command: input,
          context: {
            current_url: currentUrl,
            context_mode: contextMode
          }
        })
      });

      if (response.ok) {
        const result = await response.json();
        setSuggestions(result.suggestions || proactiveSuggestions.slice(0, 5));
      }
    } catch (error) {
      // Fallback to static suggestions
      const filtered = proactiveSuggestions.filter(s => 
        s.toLowerCase().includes(input.toLowerCase())
      );
      setSuggestions(filtered.slice(0, 5));
    }
  }, [backendUrl, currentUrl, contextMode, proactiveSuggestions]);

  // Handle input changes
  const handleInputChange = (e) => {
    const value = e.target.value;
    setCommandInput(value);
    
    if (value.trim()) {
      getIntelligentSuggestions(value);
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  };

  // Handle key presses
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      processCommand(commandInput);
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
      setCommandInput('');
    }
  };

  // Focus input on mount
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  return (
    <div className="fellou-interface">
      {/* Minimalist Command Interface */}
      <div className="command-interface">
        <div className="command-input-container">
          <div className="command-icon">
            {aiProcessing ? (
              <div className="processing-indicator">
                <div className="pulse"></div>
              </div>
            ) : (
              <span className="ai-icon">🤖</span>
            )}
          </div>
          
          <input
            ref={inputRef}
            type="text"
            value={commandInput}
            onChange={handleInputChange}
            onKeyDown={handleKeyPress}
            placeholder="Tell AETHER what you want to do..."
            className="command-input"
            disabled={aiProcessing}
          />
          
          <div className="command-actions">
            <button
              className={`voice-btn ${isListening ? 'listening' : ''}`}
              onClick={handleVoiceCommand}
              disabled={aiProcessing}
              title="Voice command"
            >
              🎤
            </button>
          </div>
        </div>

        {/* Context Mode Indicator */}
        <div className="context-mode">
          <div className="mode-indicators">
            <button 
              className={`mode-btn ${contextMode === 'browser' ? 'active' : ''}`}
              onClick={() => setContextMode('browser')}
            >
              Browse
            </button>
            <button 
              className={`mode-btn ${contextMode === 'automation' ? 'active' : ''}`}
              onClick={() => setContextMode('automation')}
            >
              Automate
            </button>
            <button 
              className={`mode-btn ${contextMode === 'workflow' ? 'active' : ''}`}
              onClick={() => setContextMode('workflow')}
            >
              Workflow
            </button>
          </div>
        </div>

        {/* Intelligent Suggestions */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="suggestions-dropdown">
            <div className="suggestions-header">
              <span>Smart Suggestions</span>
            </div>
            {suggestions.map((suggestion, index) => (
              <div
                key={index}
                className="suggestion-item"
                onClick={() => {
                  setCommandInput(suggestion);
                  setShowSuggestions(false);
                  setTimeout(() => processCommand(suggestion), 100);
                }}
              >
                <span className="suggestion-icon">💡</span>
                <span className="suggestion-text">{suggestion}</span>
              </div>
            ))}
          </div>
        )}

        {/* Context Examples */}
        <div className="context-examples">
          <div className="examples-grid">
            {getContextExamples().slice(0, 4).map((example, index) => (
              <button
                key={index}
                className="example-chip"
                onClick={() => {
                  setCommandInput(example);
                  setTimeout(() => processCommand(example), 100);
                }}
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FellowStyleInterface;