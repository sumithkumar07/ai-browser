// 🎨 WORKSTREAM B: ULTIMATE SIMPLICITY INTERFACE
// Fellou.ai-level simplicity - "Express Ideas, AETHER Acts"

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './UltimateInterface.css';

const UltimateInterface = ({ 
  onCommand, 
  currentUrl, 
  sessionId, 
  aiLoading, 
  nativeAPI 
}) => {
  // Core state
  const [command, setCommand] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [aiResponse, setAiResponse] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [intent, setIntent] = useState('');
  const [confidenceLevel, setConfidenceLevel] = useState(0);
  
  // Advanced features
  const [voiceListening, setVoiceListening] = useState(false);
  const [contextualMode, setContextualMode] = useState('general');
  const [smartPreview, setSmartPreview] = useState(null);
  const [executionPlan, setExecutionPlan] = useState([]);
  
  // UI state
  const [interfaceTheme, setInterfaceTheme] = useState('cosmic');
  const [focusMode, setFocusMode] = useState(false);
  const [adaptiveLayout, setAdaptiveLayout] = useState('centered');
  
  // Refs
  const inputRef = useRef(null);
  const voiceRecognition = useRef(null);
  const commandHistory = useRef([]);
  
  // Initialize interface
  useEffect(() => {
    // Focus on input when component mounts
    if (inputRef.current) {
      inputRef.current.focus();
    }
    
    // Initialize voice recognition if available
    initializeVoiceRecognition();
    
    // Analyze current context
    analyzeCurrentContext();
    
    // Set up adaptive interface
    setupAdaptiveInterface();
  }, []);
  
  // Voice Recognition Setup
  const initializeVoiceRecognition = useCallback(() => {
    if ('webkitSpeechRecognition' in window) {
      voiceRecognition.current = new window.webkitSpeechRecognition();
      voiceRecognition.current.continuous = false;
      voiceRecognition.current.interimResults = false;
      voiceRecognition.current.lang = 'en-US';
      
      voiceRecognition.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setCommand(transcript);
        setVoiceListening(false);
        // Auto-execute voice commands
        setTimeout(() => handleCommand(transcript), 500);
      };
      
      voiceRecognition.current.onerror = () => {
        setVoiceListening(false);
      };
      
      voiceRecognition.current.onend = () => {
        setVoiceListening(false);
      };
    }
  }, []);
  
  // Context Analysis
  const analyzeCurrentContext = useCallback(async () => {
    try {
      if (currentUrl) {
        // Determine contextual mode based on current page
        const domain = new URL(currentUrl).hostname;
        
        if (domain.includes('linkedin')) {
          setContextualMode('professional');
        } else if (domain.includes('twitter') || domain.includes('instagram')) {
          setContextualMode('social');
        } else if (domain.includes('github')) {
          setContextualMode('development');
        } else if (domain.includes('google') || domain.includes('search')) {
          setContextualMode('research');
        } else {
          setContextualMode('general');
        }
        
        // Generate contextual suggestions
        await generateContextualSuggestions(domain);
      }
    } catch (error) {
      console.error('Context analysis failed:', error);
    }
  }, [currentUrl]);
  
  // Adaptive Interface Setup
  const setupAdaptiveInterface = useCallback(() => {
    // Analyze screen size and adjust layout
    const screenWidth = window.innerWidth;
    const screenHeight = window.innerHeight;
    
    if (screenWidth < 768) {
      setAdaptiveLayout('mobile');
    } else if (screenWidth < 1200) {
      setAdaptiveLayout('tablet');
    } else {
      setAdaptiveLayout('desktop');
    }
    
    // Set theme based on time of day
    const hour = new Date().getHours();
    if (hour >= 6 && hour < 18) {
      setInterfaceTheme('daylight');
    } else {
      setInterfaceTheme('cosmic');
    }
  }, []);
  
  // Generate Contextual Suggestions
  const generateContextualSuggestions = async (domain) => {
    const contextualSuggestions = {
      'linkedin.com': [
        "Find AI engineers with 5+ years experience",
        "Post about latest tech trends",
        "Connect with people from my company",
        "Update my profile with new skills"
      ],
      'github.com': [
        "Create a new repository for my project",
        "Review pull requests in my repos",
        "Find trending repositories in JavaScript",
        "Update README files across projects"
      ],
      'twitter.com': [
        "Tweet about my latest project",
        "Find tweets about AI developments",
        "Schedule a thread about productivity",
        "Analyze engagement on my recent posts"
      ],
      'google.com': [
        "Research latest developments in AI",
        "Find the best practices for React",
        "Compare different programming languages",
        "Search for tutorials on machine learning"
      ]
    };
    
    const domainSuggestions = contextualSuggestions[domain] || [
      "Navigate to a specific page",
      "Extract information from this page",
      "Take a screenshot for reference",
      "Summarize the main content"
    ];
    
    setSuggestions(domainSuggestions);
  };
  
  // Command Processing with AI Intent Analysis
  const analyzeCommandIntent = useCallback(async (commandText) => {
    try {
      // Simple intent detection (can be enhanced with actual AI)
      const intents = {
        navigation: ['go to', 'visit', 'navigate', 'open'],
        automation: ['automate', 'create workflow', 'set up', 'batch'],
        extraction: ['extract', 'scrape', 'get data', 'collect'],
        social: ['post', 'tweet', 'share', 'follow', 'like'],
        research: ['research', 'find', 'search', 'analyze'],
        productivity: ['schedule', 'remind', 'organize', 'manage']
      };
      
      let detectedIntent = 'general';
      let maxScore = 0;
      
      for (const [intentType, keywords] of Object.entries(intents)) {
        const score = keywords.reduce((acc, keyword) => {
          return acc + (commandText.toLowerCase().includes(keyword) ? 1 : 0);
        }, 0);
        
        if (score > maxScore) {
          maxScore = score;
          detectedIntent = intentType;
        }
      }
      
      setIntent(detectedIntent);
      setConfidenceLevel(Math.min(0.9, maxScore * 0.3 + 0.4));
      
      // Generate execution plan preview
      await generateExecutionPlan(commandText, detectedIntent);
      
    } catch (error) {
      console.error('Intent analysis failed:', error);
    }
  }, []);
  
  // Generate Execution Plan Preview
  const generateExecutionPlan = async (commandText, intentType) => {
    const planTemplates = {
      navigation: [
        { step: 1, action: 'Navigate to target URL', icon: '🌐' },
        { step: 2, action: 'Wait for page load', icon: '⏳' },
        { step: 3, action: 'Capture final state', icon: '📸' }
      ],
      automation: [
        { step: 1, action: 'Analyze current page structure', icon: '🔍' },
        { step: 2, action: 'Create automation sequence', icon: '⚙️' },
        { step: 3, action: 'Execute workflow steps', icon: '🚀' },
        { step: 4, action: 'Verify completion', icon: '✅' }
      ],
      extraction: [
        { step: 1, action: 'Identify data sources', icon: '🎯' },
        { step: 2, action: 'Extract information', icon: '📊' },
        { step: 3, action: 'Process and format data', icon: '🔧' },
        { step: 4, action: 'Present results', icon: '📋' }
      ],
      social: [
        { step: 1, action: 'Navigate to social platform', icon: '🌐' },
        { step: 2, action: 'Compose content', icon: '✍️' },
        { step: 3, action: 'Publish and monitor', icon: '🚀' }
      ],
      research: [
        { step: 1, action: 'Search multiple sources', icon: '🔍' },
        { step: 2, action: 'Analyze and synthesize', icon: '🧠' },
        { step: 3, action: 'Generate comprehensive report', icon: '📑' }
      ]
    };
    
    const plan = planTemplates[intentType] || planTemplates.navigation;
    setExecutionPlan(plan);
  };
  
  // Main Command Handler
  const handleCommand = async (commandText = command) => {
    if (!commandText.trim()) return;
    
    setIsProcessing(true);
    setAiResponse('');
    setSmartPreview(null);
    
    try {
      // Add to command history
      commandHistory.current.unshift(commandText);
      if (commandHistory.current.length > 10) {
        commandHistory.current = commandHistory.current.slice(0, 10);
      }
      
      // Analyze intent before execution
      await analyzeCommandIntent(commandText);
      
      // Show smart preview of what will happen
      setSmartPreview({
        command: commandText,
        intent: intent,
        confidence: confidenceLevel,
        estimatedDuration: executionPlan.length * 2,
        steps: executionPlan.length
      });
      
      // Execute command through parent component
      if (onCommand) {
        const result = await onCommand({
          command: commandText,
          context: {
            current_url: currentUrl,
            contextual_mode: contextualMode,
            interface_mode: 'ultimate_simplicity',
            session_id: sessionId,
            intent: intent,
            confidence: confidenceLevel
          }
        });
        
        if (result && result.ai_response) {
          setAiResponse(result.ai_response);
          
          // Update suggestions based on response
          if (result.proactive_suggestions) {
            setSuggestions(result.proactive_suggestions.map(s => s.text || s));
          }
        }
      }
      
    } catch (error) {
      console.error('Command execution failed:', error);
      setAiResponse('I encountered an issue processing your request. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };
  
  // Voice Command Toggle
  const toggleVoiceListening = () => {
    if (voiceRecognition.current) {
      if (voiceListening) {
        voiceRecognition.current.stop();
        setVoiceListening(false);
      } else {
        voiceRecognition.current.start();
        setVoiceListening(true);
      }
    }
  };
  
  // Keyboard Shortcuts
  useEffect(() => {
    const handleKeydown = (e) => {
      // Enter to execute
      if (e.key === 'Enter' && !e.shiftKey && command.trim()) {
        e.preventDefault();
        handleCommand();
      }
      
      // Ctrl+Space for voice
      if (e.ctrlKey && e.code === 'Space') {
        e.preventDefault();
        toggleVoiceListening();
      }
      
      // Escape to clear
      if (e.key === 'Escape') {
        setCommand('');
        setAiResponse('');
        setSmartPreview(null);
        setExecutionPlan([]);
      }
      
      // Up arrow for command history
      if (e.key === 'ArrowUp' && commandHistory.current.length > 0) {
        e.preventDefault();
        setCommand(commandHistory.current[0]);
      }
    };
    
    document.addEventListener('keydown', handleKeydown);
    return () => document.removeEventListener('keydown', handleKeydown);
  }, [command, handleCommand, toggleVoiceListening]);
  
  // Auto-resize textarea
  const adjustTextareaHeight = (textarea) => {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
  };
  
  return (
    <div className={`ultimate-interface ${interfaceTheme} ${adaptiveLayout} ${focusMode ? 'focus-mode' : ''}`}>
      {/* Ambient Background */}
      <div className="ambient-background">
        <motion.div 
          className="cosmic-particle"
          animate={{ 
            x: [0, 100, 0], 
            y: [0, -50, 0],
            opacity: [0.3, 0.7, 0.3] 
          }}
          transition={{ 
            duration: 8, 
            repeat: Infinity,
            ease: "easeInOut" 
          }}
        />
        <motion.div 
          className="cosmic-particle particle-2"
          animate={{ 
            x: [0, -80, 0], 
            y: [0, 60, 0],
            opacity: [0.2, 0.6, 0.2] 
          }}
          transition={{ 
            duration: 12, 
            repeat: Infinity,
            ease: "easeInOut",
            delay: 2 
          }}
        />
      </div>
      
      {/* Main Interface Container */}
      <motion.div 
        className="interface-container"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
      >
        {/* Context Indicator */}
        <AnimatePresence>
          {contextualMode !== 'general' && (
            <motion.div 
              className="context-indicator"
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <span className="context-icon">
                {contextualMode === 'professional' && '💼'}
                {contextualMode === 'social' && '🌟'}
                {contextualMode === 'development' && '⚡'}
                {contextualMode === 'research' && '🔍'}
              </span>
              <span className="context-label">
                {contextualMode.charAt(0).toUpperCase() + contextualMode.slice(1)} Mode
              </span>
            </motion.div>
          )}
        </AnimatePresence>
        
        {/* Central Command Interface */}
        <div className="central-command">
          {/* Command Input */}
          <div className="command-input-container">
            <motion.div 
              className="input-wrapper"
              whileFocus={{ scale: 1.02 }}
              transition={{ duration: 0.2 }}
            >
              <textarea
                ref={inputRef}
                value={command}
                onChange={(e) => {
                  setCommand(e.target.value);
                  adjustTextareaHeight(e.target);
                  // Real-time intent analysis for long commands
                  if (e.target.value.length > 20) {
                    analyzeCommandIntent(e.target.value);
                  }
                }}
                placeholder={
                  contextualMode === 'professional' 
                    ? "Find LinkedIn profiles, automate networking, manage connections..."
                    : contextualMode === 'social'
                    ? "Post content, analyze engagement, schedule posts..."
                    : contextualMode === 'development'
                    ? "Create repos, review code, manage issues..."
                    : contextualMode === 'research'
                    ? "Research topics, gather data, create reports..."
                    : "Express your idea, AETHER acts..."
                }
                className="command-input"
                disabled={isProcessing}
                rows={1}
                style={{ resize: 'none', overflow: 'hidden' }}
              />
              
              {/* Input Enhancements */}
              <div className="input-enhancements">
                {/* Voice Button */}
                <motion.button
                  className={`voice-btn ${voiceListening ? 'listening' : ''}`}
                  onClick={toggleVoiceListening}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  title="Voice Command (Ctrl+Space)"
                >
                  {voiceListening ? '🎙️' : '🎤'}
                </motion.button>
                
                {/* Execute Button */}
                <motion.button
                  className={`execute-btn ${command.trim() ? 'ready' : ''}`}
                  onClick={() => handleCommand()}
                  disabled={!command.trim() || isProcessing}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  title="Execute Command (Enter)"
                >
                  {isProcessing ? '⚡' : '🚀'}
                </motion.button>
              </div>
            </motion.div>
            
            {/* Intent Analysis Display */}
            <AnimatePresence>
              {intent && confidenceLevel > 0.5 && (
                <motion.div 
                  className="intent-analysis"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                >
                  <div className="intent-info">
                    <span className="intent-type">{intent}</span>
                    <div className="confidence-bar">
                      <motion.div 
                        className="confidence-fill"
                        initial={{ width: 0 }}
                        animate={{ width: `${confidenceLevel * 100}%` }}
                      />
                    </div>
                    <span className="confidence-value">
                      {Math.round(confidenceLevel * 100)}%
                    </span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          
          {/* Smart Preview */}
          <AnimatePresence>
            {smartPreview && (
              <motion.div 
                className="smart-preview"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
              >
                <div className="preview-header">
                  <span className="preview-icon">👁️</span>
                  <span className="preview-title">Execution Preview</span>
                </div>
                <div className="preview-content">
                  <div className="preview-stats">
                    <div className="stat">
                      <span className="stat-label">Steps:</span>
                      <span className="stat-value">{smartPreview.steps}</span>
                    </div>
                    <div className="stat">
                      <span className="stat-label">Duration:</span>
                      <span className="stat-value">~{smartPreview.estimatedDuration}s</span>
                    </div>
                    <div className="stat">
                      <span className="stat-label">Intent:</span>
                      <span className="stat-value">{smartPreview.intent}</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          
          {/* Execution Plan */}
          <AnimatePresence>
            {executionPlan.length > 0 && (
              <motion.div 
                className="execution-plan"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
              >
                <div className="plan-header">
                  <span className="plan-icon">📋</span>
                  <span className="plan-title">Execution Steps</span>
                </div>
                <div className="plan-steps">
                  {executionPlan.map((step, index) => (
                    <motion.div 
                      key={step.step}
                      className="plan-step"
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                    >
                      <span className="step-icon">{step.icon}</span>
                      <span className="step-number">{step.step}</span>
                      <span className="step-action">{step.action}</span>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          
          {/* AI Response */}
          <AnimatePresence>
            {aiResponse && (
              <motion.div 
                className="ai-response"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
              >
                <div className="response-header">
                  <span className="response-icon">🤖</span>
                  <span className="response-title">AETHER Response</span>
                </div>
                <div className="response-content">
                  {aiResponse}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          
          {/* Processing Indicator */}
          <AnimatePresence>
            {isProcessing && (
              <motion.div 
                className="processing-indicator"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <motion.div 
                  className="processing-spinner"
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                >
                  ⚡
                </motion.div>
                <span className="processing-text">AETHER is thinking...</span>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        
        {/* Contextual Suggestions */}
        <AnimatePresence>
          {suggestions.length > 0 && !isProcessing && (
            <motion.div 
              className="contextual-suggestions"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
            >
              <div className="suggestions-header">
                <span className="suggestions-icon">💡</span>
                <span className="suggestions-title">Quick Actions</span>
              </div>
              <div className="suggestions-grid">
                {suggestions.slice(0, 4).map((suggestion, index) => (
                  <motion.button
                    key={index}
                    className="suggestion-btn"
                    onClick={() => {
                      setCommand(suggestion);
                      setTimeout(() => handleCommand(suggestion), 100);
                    }}
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    {suggestion}
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        
        {/* Keyboard Shortcuts Help */}
        <motion.div 
          className="shortcuts-help"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
        >
          <div className="shortcut">
            <kbd>Enter</kbd> Execute
          </div>
          <div className="shortcut">
            <kbd>Ctrl</kbd> + <kbd>Space</kbd> Voice
          </div>
          <div className="shortcut">
            <kbd>Esc</kbd> Clear
          </div>
          <div className="shortcut">
            <kbd>↑</kbd> History
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
};

export default UltimateInterface;