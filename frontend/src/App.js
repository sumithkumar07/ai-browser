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

  // Enhanced AI Assistant with all backend integration + Fellou.ai-level automation
  const handleAiMessage = async () => {
    if (!aiInput.trim()) return;

    const userMessage = { role: 'user', content: aiInput };
    setChatMessages(prev => [...prev, userMessage]);
    setAiLoading(true);

    try {
      // Enhanced chat with automation support
      const response = await fetch(`${backendUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: aiInput,
          session_id: sessionId,
          current_url: currentUrl,
          enable_automation: true,  // Enable Fellou.ai-level automation
          background_execution: true
        })
      });

      if (response.ok) {
        const result = await response.json();
        
        // Create enhanced AI message with automation info
        let aiResponse = result.response;
        
        // If automation was triggered, enhance the response
        if (result.automation_triggered && result.task_id) {
          aiResponse += `\n\n🔗 **Task ID:** ${result.task_id}`;
          
          // Start monitoring task progress
          monitorTaskProgress(result.task_id);
        }
        
        const aiMessage = { 
          role: 'assistant', 
          content: aiResponse,
          automation_triggered: result.automation_triggered,
          task_id: result.task_id,
          suggestions: result.suggestions || []
        };
        
        setChatMessages(prev => [...prev, aiMessage]);
        
        // Show automation suggestions if available
        if (result.suggestions && result.suggestions.length > 0) {
          showAutomationSuggestions(result.suggestions);
        }
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

  // Monitor background task progress
  const monitorTaskProgress = async (taskId) => {
    const checkProgress = async () => {
      try {
        const response = await fetch(`${backendUrl}/api/automation/status/${taskId}`);
        if (response.ok) {
          const status = await response.json();
          
          // Update UI with progress if task is still running
          if (status.progress >= 0 && status.progress < 100) {
            // Show subtle progress indicator
            updateTaskProgress(taskId, status);
            
            // Check again in 3 seconds
            setTimeout(checkProgress, 3000);
          } else if (status.progress === 100) {
            // Task completed - notify user
            showTaskCompletion(taskId, status);
          }
        }
      } catch (error) {
        console.error('Error checking task progress:', error);
      }
    };
    
    // Start monitoring after 2 seconds
    setTimeout(checkProgress, 2000);
  };

  // Show automation suggestions (integrated into existing UI)
  const showAutomationSuggestions = (suggestions) => {
    // Add suggestions as quick action buttons in existing framework
    const suggestionMessages = suggestions.map(suggestion => ({
      role: 'assistant',
      content: `💡 **Quick Suggestion:** ${suggestion.text}`,
      is_suggestion: true,
      suggested_command: suggestion.command
    }));
    
    setChatMessages(prev => [...prev, ...suggestionMessages]);
  };

  // Update task progress (subtle, non-disruptive)
  const updateTaskProgress = (taskId, status) => {
    // Store progress in state for optional display
    setBackgroundTasks(prev => ({
      ...prev,
      [taskId]: {
        name: status.name || 'Background Task',
        progress: status.progress,
        status: status.status
      }
    }));
  };

  // Show task completion notification
  const showTaskCompletion = (taskId, status) => {
    // Add completion message to chat
    const completionMessage = {
      role: 'assistant',
      content: `✅ **Task Completed!** ${status.name || 'Your automation task'} has finished successfully.\n\n📊 **Results available** - Task ID: ${taskId}`,
      task_completed: true,
      task_id: taskId
    };
    
    setChatMessages(prev => [...prev, completionMessage]);
    
    // Remove from active background tasks
    setBackgroundTasks(prev => {
      const updated = {...prev};
      delete updated[taskId];
      return updated;
    });
  };

  // Enhanced state for background tasks
  const [backgroundTasks, setBackgroundTasks] = useState({});

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

  // Handle keyboard shortcuts with enhanced accessibility
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
      // Ctrl+T - New Tab
      else if (e.ctrlKey && e.key === 't') {
        e.preventDefault();
        createNewTab();
      }
      // Ctrl+W - Close Tab
      else if (e.ctrlKey && e.key === 'w') {
        e.preventDefault();
        if (tabs.length > 1) {
          closeTab(activeTab);
        }
      }
      // Ctrl+R - Refresh
      else if (e.ctrlKey && e.key === 'r') {
        e.preventDefault();
        handleRefresh();
      }
      // Alt+Left - Go Back
      else if (e.altKey && e.key === 'ArrowLeft') {
        e.preventDefault();
        if (canGoBack) handleGoBack();
      }
      // Alt+Right - Go Forward
      else if (e.altKey && e.key === 'ArrowRight') {
        e.preventDefault();
        if (canGoForward) handleGoForward();
      }
      // F12 - Show Tour
      else if (e.key === 'F12') {
        e.preventDefault();
        showTour();
      }
      // Escape - Close all panels
      else if (e.key === 'Escape') {
        setVoiceVisible(false);
        if (shouldShowTour) hideTour();
        setWorkflowBuilder({ ...workflowBuilder, visible: false });
      }
    };

    // Add event listener
    document.addEventListener('keydown', handleKeyDown);
    
    // Cleanup
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [aiVisible, workflowBuilder, canGoBack, canGoForward, activeTab, tabs.length, shouldShowTour, hideTour, showTour]);

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
          backgroundTasks={backgroundTasks}
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