/**
 * Ultimate Simplicity Interface - Single Natural Language Input
 * Complete implementation of the ultimate simplicity concept from the comprehensive plan
 * Features:
 * - Single natural language input for all actions
 * - AI-powered command interpretation and execution
 * - Predictive interface with context awareness
 * - Memory-based suggestions and automation
 * - Real-time feedback and execution status
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import './UltimateSimplicityInterface.css';

const UltimateSimplicityInterface = ({ 
  sessionId, 
  backendUrl, 
  onCommandExecuted,
  onWorkflowCreated,
  currentContext = {}
}) => {
  // Core state
  const [command, setCommand] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionHistory, setExecutionHistory] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [contextAwareness, setContextAwareness] = useState({});
  const [performanceMode, setPerformanceMode] = useState('balanced');
  
  // UI state
  const [showPredictions, setShowPredictions] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [confidence, setConfidence] = useState(0);
  
  // Refs
  const inputRef = useRef(null);
  const historyRef = useRef(null);
  const predictionTimeoutRef = useRef(null);
  
  // Voice recognition (if supported)
  const [speechRecognition, setSpeechRecognition] = useState(null);

  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';
      
      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setCommand(transcript);
        setIsListening(false);
        
        // Auto-execute if confidence is high
        if (event.results[0][0].confidence > 0.8) {
          setTimeout(() => executeCommand(transcript), 500);
        }
      };
      
      recognition.onerror = () => {
        setIsListening(false);
      };
      
      recognition.onend = () => {
        setIsListening(false);
      };
      
      setSpeechRecognition(recognition);
    }
  }, []);

  // Get predictions and context awareness
  const updatePredictions = useCallback(async () => {
    if (!command.trim() || command.length < 3) {
      setPredictions([]);
      return;
    }

    try {
      const response = await fetch(`${backendUrl}/api/enhanced/memory-query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: sessionId,
          query_type: 'predictions',
          context: {
            current_command: command,
            ...currentContext
          },
          session_id: sessionId
        })
      });

      const data = await response.json();
      
      if (data.success && data.predictions?.predictions) {
        setPredictions(data.predictions.predictions);
        
        // Calculate overall confidence
        const avgConfidence = data.predictions.predictions.reduce(
          (sum, pred) => sum + (pred.confidence || 0), 0
        ) / data.predictions.predictions.length;
        
        setConfidence(avgConfidence || 0);
      }
    } catch (error) {
      console.error('Prediction update error:', error);
    }
  }, [command, backendUrl, sessionId, currentContext]);

  // Debounced prediction updates
  useEffect(() => {
    if (predictionTimeoutRef.current) {
      clearTimeout(predictionTimeoutRef.current);
    }

    predictionTimeoutRef.current = setTimeout(() => {
      updatePredictions();
    }, 300);

    return () => {
      if (predictionTimeoutRef.current) {
        clearTimeout(predictionTimeoutRef.current);
      }
    };
  }, [command, updatePredictions]);

  // Execute command using Ultimate Simplicity API
  const executeCommand = async (commandText = command) => {
    if (!commandText.trim()) return;

    setIsExecuting(true);
    const startTime = Date.now();

    try {
      const response = await fetch(`${backendUrl}/api/enhanced/ultimate-command`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command: commandText,
          session_id: sessionId,
          user_id: sessionId,
          context: currentContext,
          auto_remember: true,
          performance_mode: performanceMode
        })
      });

      const result = await response.json();
      const executionTime = Date.now() - startTime;

      // Create execution record
      const execution = {
        id: Date.now().toString(),
        command: commandText,
        timestamp: new Date().toISOString(),
        success: result.success,
        result: result,
        execution_time: executionTime,
        strategy: result.execution_strategy
      };

      // Update history
      setExecutionHistory(prev => [execution, ...prev.slice(0, 9)]); // Keep last 10

      // Show result feedback
      if (result.success) {
        showSuccessFeedback(result);
      } else {
        showErrorFeedback(result);
      }

      // Clear command after successful execution
      if (result.success) {
        setCommand('');
        setPredictions([]);
      }

      // Notify parent components
      if (onCommandExecuted) {
        onCommandExecuted(execution);
      }

      // If workflow was created, notify
      if (result.workflow_id && onWorkflowCreated) {
        onWorkflowCreated({
          workflow_id: result.workflow_id,
          workflow_name: result.workflow_name
        });
      }

    } catch (error) {
      const execution = {
        id: Date.now().toString(),
        command: commandText,
        timestamp: new Date().toISOString(),
        success: false,
        result: { error: error.message },
        execution_time: Date.now() - startTime,
        strategy: 'error'
      };

      setExecutionHistory(prev => [execution, ...prev.slice(0, 9)]);
      showErrorFeedback({ error: error.message });
    } finally {
      setIsExecuting(false);
    }
  };

  // Create workflow from command
  const createWorkflow = async () => {
    if (!command.trim()) return;

    setIsExecuting(true);

    try {
      const response = await fetch(`${backendUrl}/api/enhanced/create-workflow`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          instruction: command,
          user_id: sessionId,
          session_id: sessionId,
          auto_execute: false,
          context: currentContext
        })
      });

      const result = await response.json();

      if (result.success && onWorkflowCreated) {
        onWorkflowCreated(result.workflow);
        showSuccessFeedback({ message: `Workflow "${result.workflow.name}" created successfully` });
        setCommand('');
      } else {
        showErrorFeedback(result);
      }

    } catch (error) {
      showErrorFeedback({ error: error.message });
    } finally {
      setIsExecuting(false);
    }
  };

  // Voice input toggle
  const toggleVoiceInput = () => {
    if (!speechRecognition) return;

    if (isListening) {
      speechRecognition.stop();
      setIsListening(false);
    } else {
      speechRecognition.start();
      setIsListening(true);
    }
  };

  // Handle prediction selection
  const selectPrediction = (prediction) => {
    if (prediction.type === 'automation' && prediction.procedure) {
      // Execute automation directly
      executeCommand(`Execute workflow: ${prediction.procedure.name}`);
    } else if (prediction.suggested_actions && prediction.suggested_actions.length > 0) {
      // Use suggested action
      setCommand(prediction.suggested_actions[0]);
    } else {
      // Use prediction description as command
      setCommand(prediction.description);
    }
    setShowPredictions(false);
  };

  // Keyboard handlers
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (e.ctrlKey) {
        createWorkflow();
      } else {
        executeCommand();
      }
    } else if (e.key === 'Escape') {
      setCommand('');
      setPredictions([]);
      setShowPredictions(false);
    } else if (e.key === 'ArrowUp' && executionHistory.length > 0) {
      e.preventDefault();
      setCommand(executionHistory[0].command);
    }
  };

  // Feedback functions
  const showSuccessFeedback = (result) => {
    // Create success notification
    const notification = document.createElement('div');
    notification.className = 'ultimate-success-notification';
    notification.textContent = result.message || 'Command executed successfully!';
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.remove();
    }, 3000);
  };

  const showErrorFeedback = (result) => {
    // Create error notification
    const notification = document.createElement('div');
    notification.className = 'ultimate-error-notification';
    notification.textContent = result.error || 'Command failed';
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.remove();
    }, 5000);
  };

  // Auto-focus input
  useEffect(() => {
    if (inputRef.current && !isExecuting) {
      inputRef.current.focus();
    }
  }, [isExecuting]);

  return (
    <div className="ultimate-simplicity-interface">
      {/* Context Awareness Display */}
      {Object.keys(currentContext).length > 0 && (
        <div className="context-awareness">
          <div className="context-indicator">
            🧠 Context: {currentContext.url ? new URL(currentContext.url).hostname : 'Active'}
          </div>
          {confidence > 0.6 && (
            <div className="confidence-meter">
              <div className="confidence-bar">
                <div 
                  className="confidence-fill" 
                  style={{ width: `${confidence * 100}%` }}
                ></div>
              </div>
              <span className="confidence-text">
                {Math.round(confidence * 100)}% confident
              </span>
            </div>
          )}
        </div>
      )}

      {/* Main Input Area */}
      <div className="ultimate-input-container">
        <div className="input-wrapper">
          {/* Voice Input Button */}
          {speechRecognition && (
            <button
              className={`voice-input-btn ${isListening ? 'listening' : ''}`}
              onClick={toggleVoiceInput}
              title="Voice input (click to start/stop)"
            >
              {isListening ? '🔴' : '🎤'}
            </button>
          )}

          {/* Main Input */}
          <textarea
            ref={inputRef}
            className="ultimate-input"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Express your idea, AETHER acts..."
            disabled={isExecuting}
            rows={1}
            style={{
              height: 'auto',
              minHeight: '60px',
              resize: 'none'
            }}
          />

          {/* Action Buttons */}
          <div className="action-buttons">
            <button
              className="execute-btn primary"
              onClick={() => executeCommand()}
              disabled={!command.trim() || isExecuting}
              title="Execute command (Enter)"
            >
              {isExecuting ? (
                <span className="loading-spinner">⚡</span>
              ) : (
                '🚀 Execute'
              )}
            </button>

            <button
              className="workflow-btn secondary"
              onClick={createWorkflow}
              disabled={!command.trim() || isExecuting}
              title="Create workflow (Ctrl+Enter)"
            >
              🧠 Create Workflow
            </button>

            {predictions.length > 0 && (
              <button
                className="predictions-btn"
                onClick={() => setShowPredictions(!showPredictions)}
                title="Show AI predictions"
              >
                🔮 Predictions ({predictions.length})
              </button>
            )}
          </div>
        </div>

        {/* Performance Mode Selector */}
        <div className="performance-mode">
          <label>Mode:</label>
          <select
            value={performanceMode}
            onChange={(e) => setPerformanceMode(e.target.value)}
            disabled={isExecuting}
          >
            <option value="fast">⚡ Fast</option>
            <option value="balanced">⚖️ Balanced</option>
            <option value="thorough">🔍 Thorough</option>
          </select>
        </div>
      </div>

      {/* AI Predictions Panel */}
      {showPredictions && predictions.length > 0 && (
        <div className="predictions-panel">
          <div className="predictions-header">
            <h3>🤖 AI Predictions & Suggestions</h3>
            <button 
              className="close-btn"
              onClick={() => setShowPredictions(false)}
            >
              ✕
            </button>
          </div>
          <div className="predictions-list">
            {predictions.map((prediction, index) => (
              <div
                key={index}
                className={`prediction-item ${prediction.type}`}
                onClick={() => selectPrediction(prediction)}
              >
                <div className="prediction-header">
                  <span className="prediction-type">
                    {prediction.type === 'automation' ? '🤖' :
                     prediction.type === 'pattern_based' ? '🔄' :
                     prediction.type === 'context_based' ? '🧠' : '💡'}
                  </span>
                  <span className="prediction-confidence">
                    {Math.round((prediction.confidence || 0) * 100)}%
                  </span>
                </div>
                <div className="prediction-description">
                  {prediction.description}
                </div>
                {prediction.reasoning && (
                  <div className="prediction-reasoning">
                    {prediction.reasoning}
                  </div>
                )}
                {prediction.suggested_actions && (
                  <div className="prediction-actions">
                    {prediction.suggested_actions.slice(0, 2).map((action, actionIndex) => (
                      <span key={actionIndex} className="suggested-action">
                        {action}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Execution History */}
      {executionHistory.length > 0 && (
        <div className="execution-history-toggle">
          <button
            className="history-toggle-btn"
            onClick={() => setShowHistory(!showHistory)}
          >
            📜 History ({executionHistory.length})
          </button>
        </div>
      )}

      {showHistory && (
        <div className="execution-history" ref={historyRef}>
          <div className="history-header">
            <h3>🕐 Recent Commands</h3>
            <button 
              className="close-btn"
              onClick={() => setShowHistory(false)}
            >
              ✕
            </button>
          </div>
          <div className="history-list">
            {executionHistory.map((execution) => (
              <div
                key={execution.id}
                className={`history-item ${execution.success ? 'success' : 'error'}`}
                onClick={() => setCommand(execution.command)}
              >
                <div className="history-header">
                  <span className="history-status">
                    {execution.success ? '✅' : '❌'}
                  </span>
                  <span className="history-time">
                    {new Date(execution.timestamp).toLocaleTimeString()}
                  </span>
                  <span className="history-strategy">
                    {execution.strategy}
                  </span>
                </div>
                <div className="history-command">
                  {execution.command}
                </div>
                {execution.result?.error && (
                  <div className="history-error">
                    {execution.result.error}
                  </div>
                )}
                <div className="history-timing">
                  {execution.execution_time}ms
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Status Indicators */}
      <div className="status-indicators">
        {isExecuting && (
          <div className="executing-indicator">
            <span className="loading-spinner">⚡</span>
            Executing command...
          </div>
        )}
        
        {isListening && (
          <div className="listening-indicator">
            <span className="pulse">🔴</span>
            Listening...
          </div>
        )}
      </div>

      {/* Help Text */}
      <div className="help-text">
        <div className="help-shortcuts">
          <span><kbd>Enter</kbd> Execute</span>
          <span><kbd>Ctrl+Enter</kbd> Create Workflow</span>
          <span><kbd>↑</kbd> Previous Command</span>
          <span><kbd>Esc</kbd> Clear</span>
        </div>
      </div>
    </div>
  );
};

export default UltimateSimplicityInterface;