import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';
import './components/AdvancedFeatures.css';
import './components/SmartSearchSuggestions.css';
import AdvancedFeatures from './components/AdvancedFeatures';
import SmartSearchBar from './components/SmartSearchBar';
import VoiceCommandPanel from './components/VoiceCommandPanel';
import EnhancedAIPanel from './components/EnhancedAIPanel';
import OnboardingTour, { useOnboardingTour } from './components/OnboardingTour';

function App() {
  // Browser state
  const [currentUrl, setCurrentUrl] = useState('');
  const [urlInput, setUrlInput] = useState('https://example.com');
  const [isLoading, setIsLoading] = useState(false);
  const [canGoBack, setCanGoBack] = useState(false);
  const [canGoForward, setCanGoForward] = useState(false);
  const [isSecure, setIsSecure] = useState(true);
  const [tabs, setTabs] = useState([
    { id: 1, title: 'New Tab', url: '', active: true, favicon: '🌐' }
  ]);
  const [activeTab, setActiveTab] = useState(1);

  // AI Assistant state - Enhanced with all capabilities
  const [aiVisible, setAiVisible] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [aiInput, setAiInput] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [sessionId] = useState('web-session-' + Date.now());
  
  // Browser history
  const [history, setHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  
  // Advanced Features State - Simplified
  const [voiceVisible, setVoiceVisible] = useState(false);
  const [workflowBuilder, setWorkflowBuilder] = useState({ visible: false, workflows: [] });
  const [automationSuggestions, setAutomationSuggestions] = useState([]);

  // Onboarding Tour
  const { shouldShowTour, showTour, hideTour } = useOnboardingTour();
  
  const [suggestions] = useState([
    { title: 'Google', url: 'https://google.com', favicon: '🔍' },
    { title: 'GitHub', url: 'https://github.com', favicon: '🐙' },
    { title: 'Stack Overflow', url: 'https://stackoverflow.com', favicon: '📚' },
    { title: 'ChatGPT', url: 'https://chat.openai.com', favicon: '🤖' }
  ]);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  const iframeRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Initialize advanced features
  const advancedFeatures = AdvancedFeatures({ 
    backendUrl, 
    currentUrl, 
    onNavigate: handleNavigate 
  });

  // Scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  // Load automation suggestions when URL changes
  useEffect(() => {
    if (currentUrl) {
      loadAutomationSuggestions();
    }
  }, [currentUrl]);

  // Load context-aware automation suggestions
  const loadAutomationSuggestions = useCallback(async () => {
    try {
      const response = await fetch(`${backendUrl}/api/automation-suggestions`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const result = await response.json();
        setAutomationSuggestions(result.suggestions || []);
      }
    } catch (error) {
      console.error('Failed to load automation suggestions:', error);
    }
  }, [backendUrl]);

  // Handle URL navigation
  async function handleNavigate(url) {
    if (!url) return;
    
    // Add protocol if missing
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'https://' + url;
    }
    
    setIsLoading(true);
    setCurrentUrl(url);
    setUrlInput(url);
    setIsSecure(url.startsWith('https://'));
    
    // Update tab
    const updatedTabs = tabs.map(tab => 
      tab.id === activeTab 
        ? { ...tab, url: url, title: getDomainFromUrl(url) }
        : tab
    );
    setTabs(updatedTabs);
    
    // Update history
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(url);
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
    setCanGoBack(newHistory.length > 1);
    setCanGoForward(false);
    
    // Simulate loading time
    setTimeout(() => {
      setIsLoading(false);
    }, 1000);

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
  }

  const getDomainFromUrl = (url) => {
    try {
      const domain = new URL(url).hostname;
      return domain.replace('www.', '');
    } catch {
      return 'New Tab';
    }
  };

  const handleGoBack = () => {
    if (canGoBack && historyIndex > 0) {
      const newIndex = historyIndex - 1;
      setHistoryIndex(newIndex);
      const url = history[newIndex];
      setCurrentUrl(url);
      setUrlInput(url);
      setCanGoForward(true);
      setCanGoBack(newIndex > 0);
    }
  };

  const handleGoForward = () => {
    if (canGoForward && historyIndex < history.length - 1) {
      const newIndex = historyIndex + 1;
      setHistoryIndex(newIndex);
      const url = history[newIndex];
      setCurrentUrl(url);
      setUrlInput(url);
      setCanGoBack(true);
      setCanGoForward(newIndex < history.length - 1);
    }
  };

  const handleRefresh = () => {
    if (currentUrl) {
      setIsLoading(true);
      setTimeout(() => setIsLoading(false), 800);
    }
  };

  const createNewTab = () => {
    const newTab = {
      id: Date.now(),
      title: 'New Tab',
      url: '',
      active: false,
      favicon: '🌐'
    };
    setTabs([...tabs, newTab]);
    setActiveTab(newTab.id);
    setCurrentUrl('');
    setUrlInput('');
  };

  const closeTab = (tabId) => {
    if (tabs.length === 1) return; // Don't close last tab
    
    const updatedTabs = tabs.filter(tab => tab.id !== tabId);
    setTabs(updatedTabs);
    
    if (activeTab === tabId) {
      const newActiveTab = updatedTabs[0];
      setActiveTab(newActiveTab.id);
      setCurrentUrl(newActiveTab.url);
      setUrlInput(newActiveTab.url);
    }
  };

  const switchTab = (tabId) => {
    setActiveTab(tabId);
    const tab = tabs.find(t => t.id === tabId);
    if (tab) {
      setCurrentUrl(tab.url);
      setUrlInput(tab.url || '');
    }
  };

  // Enhanced AI Assistant with all backend integration
  const handleAiMessage = async () => {
    if (!aiInput.trim()) return;

    const userMessage = { role: 'user', content: aiInput };
    setChatMessages(prev => [...prev, userMessage]);
    setAiLoading(true);

    // Process special AI commands for direct feature access
    const command = aiInput.toLowerCase();
    
    try {
      // Handle summarization directly
      if (command.includes('summarize') && currentUrl) {
        const summaryResponse = await fetch(`${backendUrl}/api/summarize`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            url: currentUrl, 
            length: command.includes('short') ? 'short' : command.includes('long') ? 'long' : 'medium' 
          })
        });
        
        if (summaryResponse.ok) {
          const summaryResult = await summaryResponse.json();
          const aiMessage = { 
            role: 'assistant', 
            content: `📄 **Page Summary:**\n\n**${summaryResult.title}**\n\n${summaryResult.summary}\n\n*Word count: ${summaryResult.word_count} | Summary type: ${summaryResult.length}*`
          };
          setChatMessages(prev => [...prev, aiMessage]);
          setAiLoading(false);
          setAiInput('');
          return;
        }
      }
      
      // Handle system status directly
      if (command.includes('system status') || command.includes('system info')) {
        const statusResponse = await fetch(`${backendUrl}/api/enhanced/system/overview`);
        
        if (statusResponse.ok) {
          const statusResult = await statusResponse.json();
          const aiMessage = { 
            role: 'assistant', 
            content: `📊 **System Status:**\n\n• Status: ${statusResult.status}\n• Version: ${statusResult.version}\n• Recent Tabs: ${statusResult.stats?.recent_tabs || 0}\n• Chat Sessions: ${statusResult.stats?.chat_sessions || 0}\n• Workflows: ${statusResult.stats?.workflows || 0}\n\n✅ All systems operational!`
          };
          setChatMessages(prev => [...prev, aiMessage]);
          setAiLoading(false);
          setAiInput('');
          return;
        }
      }
      
      // Handle workflow creation directly
      if (command.includes('create workflow') || command.includes('automate')) {
        const workflowData = {
          name: `Auto Workflow ${Date.now()}`,
          description: `Workflow created from: "${aiInput}"`,
          steps: [
            { action: 'navigate', url: currentUrl || 'https://example.com' },
            { action: 'extract', selector: 'title' }
          ]
        };
        
        const workflowResponse = await fetch(`${backendUrl}/api/create-workflow`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(workflowData)
        });
        
        if (workflowResponse.ok) {
          const workflowResult = await workflowResponse.json();
          const aiMessage = { 
            role: 'assistant', 
            content: `🔧 **Workflow Created Successfully!**\n\n**ID:** ${workflowResult.workflow_id}\n**Name:** ${workflowResult.name}\n\nYour automation workflow is ready to use. You can now execute it or modify it as needed.`
          };
          setChatMessages(prev => [...prev, aiMessage]);
          setAiLoading(false);
          setAiInput('');
          return;
        }
      }

      // Regular AI chat with context
      const response = await fetch(`${backendUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: aiInput,
          session_id: sessionId,
          current_url: currentUrl
        })
      });

      if (response.ok) {
        const result = await response.json();
        const aiMessage = { 
          role: 'assistant', 
          content: result.response || 'I can help you with that!'
        };
        setChatMessages(prev => [...prev, aiMessage]);
      }
    } catch (error) {
      console.error('Error:', error);
      setChatMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again.' 
      }]);
    } finally {
      setAiLoading(false);
      setAiInput('');
    }
  };

  // Enhanced AI Quick Actions - All capabilities in one place
  const aiQuickActions = [
    { 
      text: "📄 Summarize Page", 
      action: () => {
        setAiInput("Summarize this page");
        setAiVisible(true);
        setTimeout(() => handleAiMessage(), 100);
      }
    },
    { 
      text: "📊 System Status", 
      action: () => {
        setAiInput("Show system status");
        setAiVisible(true);
        setTimeout(() => handleAiMessage(), 100);
      }
    },
    { 
      text: "🔧 Create Workflow", 
      action: () => {
        setAiInput("Create an automation workflow for this page");
        setAiVisible(true);
        setTimeout(() => handleAiMessage(), 100);
      }
    },
    { 
      text: "🎤 Voice Commands", 
      action: () => setVoiceVisible(true)
    }
  ];

  const handleQuickAction = (action) => {
    action();
  };

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl+Shift+P - Voice Commands
      if (e.ctrlKey && e.shiftKey && e.key === 'P') {
        e.preventDefault();
        setVoiceVisible(true);
      }
      // Ctrl+Shift+A - AI Assistant
      else if (e.ctrlKey && e.shiftKey && e.key === 'A') {
        e.preventDefault();
        setAiVisible(!aiVisible);
      }
      // Escape - Close all panels
      else if (e.key === 'Escape') {
        setVoiceVisible(false);
        setWorkflowBuilder({ ...workflowBuilder, visible: false });
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [aiVisible, workflowBuilder]);

  return (
    <div className="browser-app">
      {/* Onboarding Tour */}
      <OnboardingTour 
        isVisible={shouldShowTour}
        onComplete={hideTour}
      />

      {/* Tab Bar */}
      <div className="tab-bar">
        <div className="tabs-container">
          {tabs.map(tab => (
            <div 
              key={tab.id}
              className={`tab ${tab.id === activeTab ? 'active' : ''}`}
              onClick={() => switchTab(tab.id)}
              role="tab"
              aria-selected={tab.id === activeTab}
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  switchTab(tab.id);
                }
              }}
            >
              <span className="tab-favicon" role="img" aria-label="Tab icon">{tab.favicon}</span>
              <span className="tab-title">{tab.title}</span>
              {tabs.length > 1 && (
                <button 
                  className="tab-close"
                  onClick={(e) => {
                    e.stopPropagation();
                    closeTab(tab.id);
                  }}
                  title={`Close ${tab.title}`}
                  aria-label={`Close ${tab.title} tab`}
                >
                  ×
                </button>
              )}
            </div>
          ))}
          <button 
            className="new-tab-btn" 
            onClick={createNewTab}
            title="Open new tab (Ctrl+T)"
            aria-label="Open new tab"
          >
            +
          </button>
        </div>
      </div>

      {/* Navigation Bar - Enhanced with accessibility */}
      <div className="nav-bar">
        <div className="nav-controls">
          <button 
            className={`nav-btn ${!canGoBack ? 'disabled' : ''}`}
            onClick={handleGoBack}
            disabled={!canGoBack}
            title="Go back (Alt+←)"
            aria-label="Navigate back"
          >
            ←
          </button>
          <button 
            className={`nav-btn ${!canGoForward ? 'disabled' : ''}`}
            onClick={handleGoForward}
            disabled={!canGoForward}
            title="Go forward (Alt+→)"
            aria-label="Navigate forward"
          >
            →
          </button>
          <button 
            className="nav-btn"
            onClick={handleRefresh}
            title="Refresh (Ctrl+R)"
            aria-label="Refresh page"
          >
            {isLoading ? '⟳' : '↻'}
          </button>
        </div>

        <div className="address-bar">
          <div className="security-indicator" title={isSecure ? 'Secure connection' : 'Not secure'}>
            {isSecure ? (
              <span className="secure" role="img" aria-label="Secure connection">🔒</span>
            ) : (
              <span className="insecure" role="img" aria-label="Not secure">⚠️</span>
            )}
          </div>
          
          {/* Enhanced Smart Search Bar */}
          <SmartSearchBar 
            urlInput={urlInput}
            setUrlInput={setUrlInput}
            onNavigate={handleNavigate}
            searchSuggestions={advancedFeatures.searchSuggestions}
            showSuggestions={advancedFeatures.showSuggestions}
            onGetSuggestions={advancedFeatures.getSearchSuggestions}
            setShowSuggestions={advancedFeatures.setShowSuggestions}
          />
          
          <button 
            className="nav-btn go-btn"
            onClick={() => handleNavigate(urlInput)}
            title="Go"
            aria-label="Navigate to URL"
          >
            →
          </button>
        </div>

        <div className="browser-actions">
          {/* Voice Command Button - Enhanced with accessibility */}
          <button 
            className={`nav-btn voice-btn ${advancedFeatures.voiceListening ? 'active listening' : ''}`}
            onClick={() => setVoiceVisible(true)}
            title="Voice Commands (Ctrl+Shift+P)"
            aria-label="Open voice commands"
            aria-pressed={voiceVisible}
          >
            🎤
          </button>
          
          {/* AI Assistant Button - Enhanced with accessibility */}
          <button 
            className={`ai-toggle ${aiVisible ? 'active' : ''}`}
            onClick={() => setAiVisible(!aiVisible)}
            title="AI Assistant - All Features (Ctrl+Shift+A)"
            aria-label="Toggle AI Assistant"
            aria-pressed={aiVisible}
          >
            🤖
          </button>
          
          <button 
            className="menu-btn" 
            title="Menu"
            aria-label="Open menu"
            onClick={showTour}
          >
            ⋮
          </button>
        </div>
      </div>

      {/* Main Browser Content */}
      <div className="browser-content">
        {/* Web View */}
        <div className={`web-view ${aiVisible ? 'with-ai' : ''}`}>
          {currentUrl ? (
            <div className="iframe-container">
              {isLoading && (
                <div className="loading-overlay" role="progressbar" aria-label="Loading page">
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
                aria-label={`Web content for ${getDomainFromUrl(currentUrl)}`}
              />
            </div>
          ) : (
            <div className="start-page">
              <div className="start-content">
                <div className="aether-logo">
                  <div className="logo-icon" role="img" aria-label="AETHER logo">⚡</div>
                  <h1>AETHER</h1>
                  <p>AI-First Browser</p>
                </div>
                
                <div className="quick-access">
                  <h2>Quick Access</h2>
                  <div className="suggestions-grid" role="grid" aria-label="Quick access websites">
                    {suggestions.map((site, index) => (
                      <div 
                        key={index}
                        className="suggestion-card"
                        onClick={() => handleNavigate(site.url)}
                        role="gridcell"
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            handleNavigate(site.url);
                          }
                        }}
                        aria-label={`Navigate to ${site.title}`}
                      >
                        <div className="suggestion-favicon" role="img" aria-label={`${site.title} icon`}>
                          {site.favicon}
                        </div>
                        <div className="suggestion-title">{site.title}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="ai-quick-actions">
                  <h2>AI-Powered Features</h2>
                  <div className="actions-grid" role="grid" aria-label="AI-powered features">
                    {aiQuickActions.map((action, index) => (
                      <button 
                        key={index}
                        className="action-btn"
                        onClick={() => handleQuickAction(action.action)}
                        role="gridcell"
                        aria-label={action.text.replace(/[^\w\s]/gi, '')}
                      >
                        {action.text}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Show automation suggestions if available */}
                {automationSuggestions.length > 0 && (
                  <div className="automation-suggestions">
                    <h2>Smart Automation</h2>
                    <div className="suggestions-list" role="list" aria-label="Automation suggestions">
                      {automationSuggestions.slice(0, 3).map((suggestion, index) => (
                        <div key={index} className="suggestion-item" role="listitem">
                          <span className="suggestion-icon" role="img" aria-label="Automation">🔧</span>
                          <span className="suggestion-text">{suggestion}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Enhanced AI Assistant Panel */}
        <EnhancedAIPanel
          isVisible={aiVisible}
          onClose={() => setAiVisible(false)}
          chatMessages={chatMessages}
          setChatMessages={setChatMessages}
          aiInput={aiInput}
          setAiInput={setAiInput}
          aiLoading={aiLoading}
          onSendMessage={handleAiMessage}
          currentUrl={currentUrl}
          sessionId={sessionId}
        />
      </div>

      {/* Voice Command Panel - Enhanced interface */}
      <VoiceCommandPanel 
        visible={voiceVisible}
        onClose={() => setVoiceVisible(false)}
        voiceListening={advancedFeatures.voiceListening}
        setVoiceListening={advancedFeatures.setVoiceListening}
        onProcessVoiceCommand={advancedFeatures.processVoiceCommand}
        availableShortcuts={advancedFeatures.availableShortcuts}
      />
    </div>
  );
}

export default App;