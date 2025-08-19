import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import './components/AdvancedFeatures.css';
import AdvancedFeatures from './components/AdvancedFeatures';
import SmartSearchBar from './components/SmartSearchBar';
import PageSummaryPanel from './components/PageSummaryPanel';
import VoiceCommandPanel from './components/VoiceCommandPanel';

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

  // AI Assistant state
  const [aiVisible, setAiVisible] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [aiInput, setAiInput] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  
  // Browser history
  const [history, setHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  
  // Advanced Features State
  const [summaryVisible, setSummaryVisible] = useState(false);
  const [voiceVisible, setVoiceVisible] = useState(false);
  const [workflowVisible, setWorkflowVisible] = useState(false);
  const [systemStatusVisible, setSystemStatusVisible] = useState(false);
  
  // Quick suggestions
  const [suggestions, setSuggestions] = useState([
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

  // AI Assistant functions
  const handleAiMessage = async () => {
    if (!aiInput.trim()) return;

    const userMessage = { role: 'user', content: aiInput };
    setChatMessages(prev => [...prev, userMessage]);
    setAiLoading(true);

    try {
      const response = await fetch(`${backendUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: aiInput,
          session_id: 'web-session-' + Date.now(),
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

  // Enhanced AI Quick Actions with backend integration
  const aiQuickActions = [
    { 
      text: "📄 Summarize Page", 
      action: () => setSummaryVisible(true)
    },
    { 
      text: "🎤 Voice Commands", 
      action: () => setVoiceVisible(true)
    },
    { 
      text: "🔧 Workflows", 
      action: () => setWorkflowVisible(true)
    },
    { 
      text: "📊 System Status", 
      action: () => setSystemStatusVisible(true)
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
      // Ctrl+Shift+S - Summarize Page  
      else if (e.ctrlKey && e.shiftKey && e.key === 'S') {
        e.preventDefault();
        if (currentUrl) setSummaryVisible(true);
      }
      // Ctrl+Shift+A - AI Assistant
      else if (e.ctrlKey && e.shiftKey && e.key === 'A') {
        e.preventDefault();
        setAiVisible(!aiVisible);
      }
      // Escape - Close all panels
      else if (e.key === 'Escape') {
        setSummaryVisible(false);
        setVoiceVisible(false);
        setWorkflowVisible(false);
        setSystemStatusVisible(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [aiVisible, currentUrl]);

  return (
    <div className="browser-app">
      {/* Tab Bar */}
      <div className="tab-bar">
        <div className="tabs-container">
          {tabs.map(tab => (
            <div 
              key={tab.id}
              className={`tab ${tab.id === activeTab ? 'active' : ''}`}
              onClick={() => switchTab(tab.id)}
            >
              <span className="tab-favicon">{tab.favicon}</span>
              <span className="tab-title">{tab.title}</span>
              {tabs.length > 1 && (
                <button 
                  className="tab-close"
                  onClick={(e) => {
                    e.stopPropagation();
                    closeTab(tab.id);
                  }}
                >
                  ×
                </button>
              )}
            </div>
          ))}
          <button className="new-tab-btn" onClick={createNewTab}>+</button>
        </div>
      </div>

      {/* Navigation Bar with Enhanced Features */}
      <div className="nav-bar">
        <div className="nav-controls">
          <button 
            className={`nav-btn ${!canGoBack ? 'disabled' : ''}`}
            onClick={handleGoBack}
            disabled={!canGoBack}
            title="Go back (Alt+←)"
          >
            ←
          </button>
          <button 
            className={`nav-btn ${!canGoForward ? 'disabled' : ''}`}
            onClick={handleGoForward}
            disabled={!canGoForward}
            title="Go forward (Alt+→)"
          >
            →
          </button>
          <button 
            className="nav-btn"
            onClick={handleRefresh}
            title="Refresh (Ctrl+R)"
          >
            {isLoading ? '⟳' : '↻'}
          </button>
        </div>

        <div className="address-bar">
          <div className="security-indicator">
            {isSecure ? (
              <span className="secure" title="Secure connection">🔒</span>
            ) : (
              <span className="insecure" title="Not secure">⚠️</span>
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
          >
            →
          </button>
        </div>

        <div className="browser-actions">
          {/* Voice Command Button */}
          <button 
            className={`nav-btn voice-btn ${advancedFeatures.voiceListening ? 'active listening' : ''}`}
            onClick={() => setVoiceVisible(true)}
            title="Voice Commands (Ctrl+Shift+P)"
          >
            🎤
          </button>
          
          {/* Summary Button */}
          <button 
            className="nav-btn summary-btn"
            onClick={() => setSummaryVisible(true)}
            title="Summarize Page (Ctrl+Shift+S)"
            disabled={!currentUrl}
          >
            📄
          </button>
          
          {/* AI Assistant Button */}
          <button 
            className={`ai-toggle ${aiVisible ? 'active' : ''}`}
            onClick={() => setAiVisible(!aiVisible)}
            title="AI Assistant (Ctrl+Shift+A)"
          >
            🤖
          </button>
          
          {/* System Status Button */}
          <button 
            className="nav-btn status-btn"
            onClick={() => setSystemStatusVisible(true)}
            title="System Status"
          >
            📊
          </button>
          
          <button className="menu-btn" title="Menu">⋮</button>
        </div>
      </div>

      {/* Main Browser Content */}
      <div className="browser-content">
        {/* Web View */}
        <div className={`web-view ${aiVisible ? 'with-ai' : ''}`}>
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
              />
            </div>
          ) : (
            <div className="start-page">
              <div className="start-content">
                <div className="aether-logo">
                  <div className="logo-icon">⚡</div>
                  <h1>AETHER</h1>
                  <p>AI-First Browser</p>
                </div>
                
                <div className="quick-access">
                  <h2>Quick Access</h2>
                  <div className="suggestions-grid">
                    {suggestions.map((site, index) => (
                      <div 
                        key={index}
                        className="suggestion-card"
                        onClick={() => handleNavigate(site.url)}
                      >
                        <div className="suggestion-favicon">{site.favicon}</div>
                        <div className="suggestion-title">{site.title}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="ai-quick-actions">
                  <h2>Advanced Features</h2>
                  <div className="actions-grid">
                    {aiQuickActions.map((action, index) => (
                      <button 
                        key={index}
                        className="action-btn"
                        onClick={() => handleQuickAction(action.action)}
                      >
                        {action.text}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* AI Assistant Panel */}
        {aiVisible && (
          <div className="ai-panel">
            <div className="ai-header">
              <div className="ai-title">
                <span className="ai-icon">🤖</span>
                <span>AETHER AI</span>
              </div>
              <button 
                className="ai-close"
                onClick={() => setAiVisible(false)}
              >
                ×
              </button>
            </div>

            <div className="ai-content">
              <div className="chat-messages">
                {chatMessages.length === 0 ? (
                  <div className="welcome-message">
                    <div className="welcome-icon">✨</div>
                    <h3>Hello! I'm your AI assistant</h3>
                    <p>I can help you browse, research, summarize content, automate tasks, and much more. What would you like me to do?</p>
                  </div>
                ) : (
                  chatMessages.map((message, index) => (
                    <div key={index} className={`message ${message.role}`}>
                      <div className="message-content">{message.content}</div>
                    </div>
                  ))
                )}
                
                {aiLoading && (
                  <div className="message assistant loading">
                    <div className="typing-indicator">
                      <span></span><span></span><span></span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              <div className="ai-input-area">
                <div className="quick-suggestions">
                  {currentUrl && (
                    <>
                      <button 
                        className="suggestion-chip"
                        onClick={() => setSummaryVisible(true)}
                      >
                        📄 Summarize
                      </button>
                      <button 
                        className="suggestion-chip"
                        onClick={() => {
                          setAiInput("Extract key information from this page");
                          handleAiMessage();
                        }}
                      >
                        📝 Extract Info
                      </button>
                      <button 
                        className="suggestion-chip"
                        onClick={() => {
                          setAiInput("Find websites similar to this one");
                          handleAiMessage();
                        }}
                      >
                        🔍 Similar Sites
                      </button>
                    </>
                  )}
                </div>
                
                <div className="ai-input-box">
                  <input
                    type="text"
                    className="ai-input"
                    value={aiInput}
                    onChange={(e) => setAiInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleAiMessage()}
                    placeholder="Ask me anything..."
                  />
                  <button 
                    className="ai-send"
                    onClick={handleAiMessage}
                    disabled={aiLoading || !aiInput.trim()}
                  >
                    {aiLoading ? '⟳' : '→'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Advanced Feature Panels */}
      <PageSummaryPanel 
        currentUrl={currentUrl}
        summary={advancedFeatures.summary}
        summaryLoading={advancedFeatures.summaryLoading}
        onGetSummary={advancedFeatures.getPageSummary}
        visible={summaryVisible}
        onClose={() => setSummaryVisible(false)}
      />
      
      <VoiceCommandPanel 
        visible={voiceVisible}
        onClose={() => setVoiceVisible(false)}
        voiceListening={advancedFeatures.voiceListening}
        setVoiceListening={advancedFeatures.setVoiceListening}
        onProcessVoiceCommand={advancedFeatures.processVoiceCommand}
        availableShortcuts={advancedFeatures.availableShortcuts}
      />

      {/* System Status Panel */}
      {systemStatusVisible && advancedFeatures.systemStatus && (
        <div className="status-panel-overlay" onClick={() => setSystemStatusVisible(false)}>
          <div className="status-panel" onClick={e => e.stopPropagation()}>
            <div className="status-header">
              <h3>📊 System Status</h3>
              <button onClick={() => setSystemStatusVisible(false)}>×</button>
            </div>
            <div className="status-content">
              <div className="status-item">
                <span>Status:</span>
                <span className="status-value">{advancedFeatures.systemStatus.status}</span>
              </div>
              <div className="status-item">
                <span>Version:</span>
                <span className="status-value">{advancedFeatures.systemStatus.version}</span>
              </div>
              <div className="status-item">
                <span>Recent Tabs:</span>
                <span className="status-value">{advancedFeatures.systemStatus.stats?.recent_tabs || 0}</span>
              </div>
              <div className="status-item">
                <span>Chat Sessions:</span>
                <span className="status-value">{advancedFeatures.systemStatus.stats?.chat_sessions || 0}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;