import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';
import FellowStyleInterface from './components/Fellou-StyleInterface';
import EnhancedAIPanel from './components/EnhancedAIPanel';
import ShadowWorkspaceManager from './components/ShadowWorkspaceManager';

// Enhanced AETHER with Fellou.ai-style simplicity
function EnhancedAetherApp() {
  // Core browser state
  const [currentUrl, setCurrentUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [browserTabs, setBrowserTabs] = useState([
    { id: 1, title: 'New Tab', url: '', active: true, favicon: '🌐' }
  ]);
  const [activeTab, setActiveTab] = useState(1);

  // Simplified AI state
  const [aiVisible, setAiVisible] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [sessionId] = useState('enhanced-session-' + Date.now());
  
  // Enhanced features state
  const [chromiumSessions, setChromiumSessions] = useState([]);
  const [behaviorLearning, setBehaviorLearning] = useState(true);
  const [proactiveMode, setProactiveMode] = useState(true);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  const iframeRef = useRef(null);

  // Track user behavior for learning
  const trackBehavior = useCallback(async (action) => {
    if (!behaviorLearning) return;
    
    try {
      await fetch(`${backendUrl}/api/enhanced/behavioral-tracking`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          action: {
            type: action.type,
            command: action.command,
            current_url: currentUrl,
            context: action.context || {},
            success: action.success !== false
          }
        })
      });
    } catch (error) {
      console.error('Behavior tracking error:', error);
    }
  }, [behaviorLearning, sessionId, currentUrl, backendUrl]);

  // Enhanced navigation with native Chromium support
  const handleNavigate = useCallback(async (url) => {
    if (!url) return;
    
    // Add protocol if missing
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'https://' + url;
    }
    
    setIsLoading(true);
    setCurrentUrl(url);
    
    try {
      // Try native Chromium first, fallback to iframe
      const nativeResult = await tryNativeNavigation(url);
      if (!nativeResult.success) {
        // Fallback to iframe navigation
        await fallbackIframeNavigation(url);
      }
      
      // Track behavior
      await trackBehavior({
        type: 'navigation',
        command: `navigate to ${url}`,
        context: { method: nativeResult.success ? 'chromium' : 'iframe' }
      });
      
      // Update tab
      updateActiveTab(url);
      
    } catch (error) {
      console.error('Navigation error:', error);
    } finally {
      setIsLoading(false);
    }
  }, [trackBehavior]);

  // Try native Chromium navigation
  const tryNativeNavigation = async (url) => {
    try {
      // Check if we have an active Chromium session
      let sessionId = chromiumSessions[0]?.session_id;
      
      if (!sessionId) {
        // Create new Chromium session
        const createResponse = await fetch(`${backendUrl}/api/chromium/create-session`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_session: sessionId,
            width: 1920,
            height: 1080,
            enable_devtools: true
          })
        });
        
        if (createResponse.ok) {
          const createResult = await createResponse.json();
          if (createResult.success) {
            sessionId = createResult.session_id;
            setChromiumSessions(prev => [...prev, createResult]);
          } else {
            return { success: false, error: 'Failed to create Chromium session' };
          }
        }
      }
      
      // Navigate using Chromium
      if (sessionId) {
        const navResponse = await fetch(`${backendUrl}/api/chromium/navigate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sessionId,
            url: url
          })
        });
        
        if (navResponse.ok) {
          const navResult = await navResponse.json();
          return navResult;
        }
      }
      
      return { success: false, error: 'Chromium navigation failed' };
      
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  // Fallback iframe navigation
  const fallbackIframeNavigation = async (url) => {
    // Standard iframe navigation
    if (iframeRef.current) {
      iframeRef.current.src = url;
    }
    
    // Store in browsing history
    try {
      await fetch(`${backendUrl}/api/browse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url })
      });
    } catch (error) {
      console.error('Error storing browse history:', error);
    }
  };

  // Update active tab
  const updateActiveTab = (url) => {
    setBrowserTabs(prev => prev.map(tab => 
      tab.id === activeTab 
        ? { ...tab, url: url, title: getDomainFromUrl(url) }
        : tab
    ));
  };

  const getDomainFromUrl = (url) => {
    try {
      const domain = new URL(url).hostname;
      return domain.replace('www.', '');
    } catch {
      return 'New Tab';
    }
  };

  // Enhanced AI command processing
  const handleAICommand = useCallback(async (command, context = {}) => {
    try {
      const userMessage = { role: 'user', content: command };
      setChatMessages(prev => [...prev, userMessage]);
      
      // Process with enhanced AI
      const response = await fetch(`${backendUrl}/api/enhanced/command-processor`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command: command,
          context: {
            current_url: currentUrl,
            session_id: sessionId,
            context_mode: context.mode || 'browser',
            ...context
          }
        })
      });

      if (response.ok) {
        const result = await response.json();
        
        if (result.success) {
          // Handle different command types
          await handleCommandResult(result, command);
        } else {
          // Fallback to basic chat
          await handleBasicChat(command);
        }
      }
      
    } catch (error) {
      console.error('AI command error:', error);
      await handleBasicChat(command);
    }
  }, [currentUrl, sessionId, backendUrl]);

  // Handle command result
  const handleCommandResult = async (result, originalCommand) => {
    let aiResponse = '';
    
    switch (result.command_type) {
      case 'navigation':
        if (result.url) {
          await handleNavigate(result.url);
          aiResponse = `✅ Navigating to ${result.url}`;
        }
        break;
        
      case 'automation':
        aiResponse = `🔧 Starting automation: ${originalCommand}`;
        // Trigger automation
        break;
        
      case 'multi_step':
        aiResponse = `⚡ Executing multi-step command:\n${result.steps?.map((s, i) => `${i+1}. ${s.command}`).join('\n')}`;
        break;
        
      default:
        aiResponse = `🤖 Processing: ${originalCommand}`;
        break;
    }
    
    const aiMessage = { 
      role: 'assistant', 
      content: aiResponse,
      command_type: result.command_type,
      confidence: result.confidence
    };
    
    setChatMessages(prev => [...prev, aiMessage]);
    
    // Track successful AI interaction
    await trackBehavior({
      type: 'ai_command',
      command: originalCommand,
      context: { command_type: result.command_type, confidence: result.confidence }
    });
  };

  // Basic chat fallback
  const handleBasicChat = async (command) => {
    try {
      const response = await fetch(`${backendUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: command,
          session_id: sessionId,
          current_url: currentUrl
        })
      });

      if (response.ok) {
        const result = await response.json();
        const aiMessage = { role: 'assistant', content: result.response };
        setChatMessages(prev => [...prev, aiMessage]);
      }
    } catch (error) {
      console.error('Basic chat error:', error);
      const errorMessage = { 
        role: 'assistant', 
        content: 'I apologize, but I encountered an error. Please try again.' 
      };
      setChatMessages(prev => [...prev, errorMessage]);
    }
  };

  // Get proactive suggestions periodically
  useEffect(() => {
    if (!proactiveMode) return;
    
    const getProactiveSuggestions = async () => {
      try {
        const response = await fetch(`${backendUrl}/api/enhanced/proactive-suggestions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sessionId,
            current_context: {
              current_url: currentUrl,
              active_for: Date.now() - (sessionId.split('-').pop() || 0)
            }
          })
        });

        if (response.ok) {
          const result = await response.json();
          if (result.success && result.suggestions?.length > 0) {
            // Add proactive suggestions to chat (subtle)
            const proactiveMessage = {
              role: 'assistant',
              content: `💡 **Proactive Suggestion**: ${result.suggestions[0].description}`,
              is_proactive: true,
              suggestions: result.suggestions
            };
            setChatMessages(prev => [...prev, proactiveMessage]);
          }
        }
      } catch (error) {
        console.error('Proactive suggestions error:', error);
      }
    };

    // Check for proactive suggestions every 30 seconds
    const interval = setInterval(getProactiveSuggestions, 30000);
    return () => clearInterval(interval);
  }, [proactiveMode, currentUrl, sessionId, backendUrl]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl+K - Focus command interface
      if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        // Focus would be handled by FellowStyleInterface
      }
      // Ctrl+Shift+A - Toggle AI
      else if (e.ctrlKey && e.shiftKey && e.key === 'A') {
        e.preventDefault();
        setAiVisible(!aiVisible);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [aiVisible]);

  return (
    <div className="enhanced-aether-app">
      {/* Fellou.ai-Style Command Interface - Main Interface */}
      <FellowStyleInterface
        onNavigate={handleNavigate}
        onAICommand={handleAICommand}
        currentUrl={currentUrl}
        sessionId={sessionId}
        backendUrl={backendUrl}
      />

      {/* Main Browser Content */}
      <div className="enhanced-browser-content" style={{ marginTop: '120px' }}>
        {currentUrl ? (
          <div className="iframe-container">
            {isLoading && (
              <div className="loading-overlay">
                <div className="loading-spinner"></div>
                <div className="loading-text">Loading {getDomainFromUrl(currentUrl)}...</div>
              </div>
            )}
            <iframe
              ref={iframeRef}
              src={currentUrl}
              className="web-iframe"
              title="Web Content"
              sandbox="allow-same-origin allow-scripts allow-forms allow-navigation allow-popups allow-popups-to-escape-sandbox"
              onLoad={() => setIsLoading(false)}
              style={{ 
                width: '100%', 
                height: 'calc(100vh - 120px)',
                border: 'none' 
              }}
            />
          </div>
        ) : (
          <div className="enhanced-start-page">
            <div className="start-content">
              <div className="aether-logo enhanced">
                <div className="logo-icon">⚡</div>
                <h1>AETHER</h1>
                <p>AI-First Browser with Native Engine</p>
              </div>
              
              <div className="capabilities-showcase">
                <div className="capability-card">
                  <div className="capability-icon">🧠</div>
                  <h3>Proactive AI</h3>
                  <p>AI that learns and suggests actions</p>
                </div>
                <div className="capability-card">
                  <div className="capability-icon">🔗</div>
                  <h3>Native Engine</h3>
                  <p>Full Chromium with extensions</p>
                </div>
                <div className="capability-card">
                  <div className="capability-icon">💬</div>
                  <h3>Natural Commands</h3>
                  <p>Tell AETHER what you want to do</p>
                </div>
                <div className="capability-card">
                  <div className="capability-icon">⚡</div>
                  <h3>Instant Action</h3>
                  <p>Multi-step automation in one command</p>
                </div>
              </div>
              
              <div className="enhanced-features-status">
                <div className="status-indicators">
                  <div className="status-item">
                    <span className="status-dot active"></span>
                    <span>Behavioral Learning</span>
                  </div>
                  <div className="status-item">
                    <span className="status-dot active"></span>
                    <span>Proactive Suggestions</span>
                  </div>
                  <div className="status-item">
                    <span className="status-dot active"></span>
                    <span>Native Chromium</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* AI Assistant Panel - Minimal, context-aware */}
      {aiVisible && (
        <EnhancedAIPanel
          isVisible={aiVisible}
          onClose={() => setAiVisible(false)}
          chatMessages={chatMessages}
          setChatMessages={setChatMessages}
          currentUrl={currentUrl}
          sessionId={sessionId}
          onSendMessage={handleAICommand}
          proactiveMode={proactiveMode}
        />
      )}

      {/* Shadow Workspace Manager - Background task execution */}
      <ShadowWorkspaceManager 
        backendUrl={backendUrl}
        userSession={sessionId}
      />

      {/* Settings Panel - Minimal controls */}
      <div className="enhanced-settings">
        <button
          className={`settings-toggle ${aiVisible ? 'active' : ''}`}
          onClick={() => setAiVisible(!aiVisible)}
          title="AI Assistant"
        >
          🤖
        </button>
        
        <div className="settings-indicators">
          <div 
            className={`indicator ${behaviorLearning ? 'active' : ''}`}
            onClick={() => setBehaviorLearning(!behaviorLearning)}
            title="Behavioral Learning"
          >
            🧠
          </div>
          <div 
            className={`indicator ${proactiveMode ? 'active' : ''}`}
            onClick={() => setProactiveMode(!proactiveMode)}
            title="Proactive Mode"
          >
            💡
          </div>
        </div>
      </div>
    </div>
  );
}

export default EnhancedAetherApp;