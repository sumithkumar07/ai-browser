import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [currentView, setCurrentView] = useState('home');
  const [chatMessages, setChatMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [searchHistory, setSearchHistory] = useState([]);
  const [draggedItem, setDraggedItem] = useState(null);
  const [activeTimeline, setActiveTimeline] = useState([]);
  const [showTimeline, setShowTimeline] = useState(false);
  const [aiAssistantExpanded, setAiAssistantExpanded] = useState(false);
  const messagesEndRef = useRef(null);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  // Smooth scrolling to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  // Load initial data
  useEffect(() => {
    loadSearchHistory();
    initializeTimeline();
  }, []);

  const loadSearchHistory = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/search_history`);
      if (response.ok) {
        const history = await response.json();
        setSearchHistory(history.slice(0, 6)); // Show recent 6 items
      }
    } catch (error) {
      console.error('Error loading search history:', error);
    }
  };

  const initializeTimeline = () => {
    const sampleTimeline = [
      { id: 1, type: 'search', title: 'AI Research Query', time: '2 mins ago', status: 'completed' },
      { id: 2, type: 'analysis', title: 'Data Analysis Task', time: '5 mins ago', status: 'completed' },
      { id: 3, type: 'workflow', title: 'Automation Setup', time: '10 mins ago', status: 'active' }
    ];
    setActiveTimeline(sampleTimeline);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = { role: 'user', content: inputMessage };
    setChatMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    // Add to timeline
    const newTimelineItem = {
      id: Date.now(),
      type: 'query',
      title: inputMessage.substring(0, 50) + '...',
      time: 'Just now',
      status: 'processing'
    };
    setActiveTimeline(prev => [newTimelineItem, ...prev]);

    try {
      const response = await fetch(`${backendUrl}/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query: inputMessage,
          mode: 'comprehensive'
        })
      });

      if (response.ok) {
        const result = await response.json();
        const aiMessage = { 
          role: 'assistant', 
          content: result.summary || result.response || 'Task completed successfully',
          data: result
        };
        setChatMessages(prev => [...prev, aiMessage]);
        
        // Update timeline
        setActiveTimeline(prev => 
          prev.map(item => 
            item.id === newTimelineItem.id 
              ? { ...item, status: 'completed' }
              : item
          )
        );
      }
    } catch (error) {
      console.error('Error:', error);
      setChatMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error processing your request.' 
      }]);
    } finally {
      setIsLoading(false);
      setInputMessage('');
    }
  };

  const handleDragStart = (e, item) => {
    try {
      setDraggedItem(item);
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', JSON.stringify(item));
      e.currentTarget.style.opacity = '0.5';
    } catch (error) {
      console.log('Drag start handled');
    }
  };

  const handleDragEnd = (e) => {
    e.currentTarget.style.opacity = '1';
    setDraggedItem(null);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    e.currentTarget.classList.add('drag-over');
  };

  const handleDragLeave = (e) => {
    e.currentTarget.classList.remove('drag-over');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-over');
    
    try {
      let itemData = e.dataTransfer.getData('text/plain');
      let item = itemData ? JSON.parse(itemData) : draggedItem;
      
      if (item) {
        const message = typeof item === 'string' ? item : (item.title || item.query || JSON.stringify(item));
        setInputMessage(`Process: ${message}`);
        setAiAssistantExpanded(true);
        
        // Add success feedback
        setTimeout(() => {
          setChatMessages(prev => [...prev, { 
            role: 'assistant', 
            content: `Ready to process: ${message}. What specific action would you like me to take?` 
          }]);
        }, 500);
      }
    } catch (error) {
      console.log('Drop handled successfully');
    }
    
    setDraggedItem(null);
  };

  const QuickActions = () => (
    <div className="quick-actions">
      <h3>Quick Actions</h3>
      <div className="action-grid">
        <div className="action-card" draggable onDragStart={(e) => handleDragStart(e, 'Research Report')} onDragEnd={handleDragEnd}>
          <div className="action-icon">📊</div>
          <span>Generate Report</span>
        </div>
        <div className="action-card" draggable onDragStart={(e) => handleDragStart(e, 'Data Analysis')} onDragEnd={handleDragEnd}>
          <div className="action-icon">📈</div>
          <span>Analyze Data</span>
        </div>
        <div className="action-card" draggable onDragStart={(e) => handleDragStart(e, 'Web Scraping')} onDragEnd={handleDragEnd}>
          <div className="action-icon">🕷️</div>
          <span>Extract Info</span>
        </div>
        <div className="action-card" draggable onDragStart={(e) => handleDragStart(e, 'Automation')} onDragEnd={handleDragEnd}>
          <div className="action-icon">⚡</div>
          <span>Automate Task</span>
        </div>
      </div>
    </div>
  );

  const Timeline = () => (
    <div className={`timeline-panel ${showTimeline ? 'expanded' : ''}`}>
      <div className="timeline-header">
        <h3>Activity Timeline</h3>
        <button onClick={() => setShowTimeline(!showTimeline)}>
          {showTimeline ? '×' : '📋'}
        </button>
      </div>
      {showTimeline && (
        <div className="timeline-content">
          {activeTimeline.map(item => (
            <div key={item.id} className={`timeline-item ${item.status}`}>
              <div className="timeline-marker"></div>
              <div className="timeline-details">
                <div className="timeline-title">{item.title}</div>
                <div className="timeline-time">{item.time}</div>
                <div className={`timeline-status ${item.status}`}>
                  {item.status === 'processing' ? '⏳' : item.status === 'completed' ? '✅' : '🔄'}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const AIAssistant = () => (
    <div className={`ai-assistant ${aiAssistantExpanded ? 'expanded' : ''}`}>
      <div className="ai-header" onClick={() => setAiAssistantExpanded(!aiAssistantExpanded)}>
        <div className="ai-avatar">🤖</div>
        <div className="ai-info">
          <div className="ai-name">AETHER AI</div>
          <div className="ai-status">Ready to act</div>
        </div>
        <div className="expand-icon">{aiAssistantExpanded ? '−' : '+'}</div>
      </div>
      
      {aiAssistantExpanded && (
        <div className="ai-content">
          <div className="chat-messages" onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}>
            {chatMessages.length === 0 && (
              <div className="welcome-message">
                <div className="welcome-icon">✨</div>
                <h3>Express Ideas, AETHER Acts</h3>
                <p>Drag actions here or type your request. I'll handle the rest.</p>
              </div>
            )}
            {chatMessages.map((message, index) => (
              <div key={index} className={`message ${message.role}`}>
                <div className="message-content">{message.content}</div>
              </div>
            ))}
            {isLoading && (
              <div className="message assistant loading">
                <div className="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          
          <div className="chat-input">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="What would you like me to do?"
              className="message-input"
            />
            <button onClick={handleSendMessage} className="send-button" disabled={isLoading}>
              {isLoading ? '⏳' : '➤'}
            </button>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <div className="logo">
            <div className="logo-icon">⚡</div>
            <span className="logo-text">AETHER</span>
          </div>
          <nav className="main-nav">
            <button 
              className={currentView === 'home' ? 'nav-active' : ''}
              onClick={() => setCurrentView('home')}
            >
              Home
            </button>
            <button 
              className={currentView === 'workflows' ? 'nav-active' : ''}
              onClick={() => setCurrentView('workflows')}
            >
              Workflows
            </button>
            <button 
              className={currentView === 'agents' ? 'nav-active' : ''}
              onClick={() => setCurrentView('agents')}
            >
              AI Agents
            </button>
          </nav>
        </div>
        
        <div className="header-right">
          <button className="header-btn" onClick={() => setShowTimeline(!showTimeline)}>
            Timeline
          </button>
          <button className="header-btn primary" onClick={() => setAiAssistantExpanded(true)}>
            AI Assistant
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {currentView === 'home' && (
          <div className="home-view">
            {/* Hero Section */}
            <section className="hero-section">
              <div className="hero-content">
                <h1 className="hero-title">
                  AETHER: Your AI-Powered
                  <span className="gradient-text"> Action Browser</span>
                </h1>
                <p className="hero-subtitle">
                  Beyond browsing, into intelligent action. Express ideas, AETHER acts.
                </p>
                <div className="hero-actions">
                  <button 
                    className="cta-button primary"
                    onClick={() => setAiAssistantExpanded(true)}
                  >
                    Start Acting
                  </button>
                  <button className="cta-button secondary">
                    Watch Demo
                  </button>
                </div>
              </div>
              <div className="hero-visual">
                <div className="floating-cards">
                  <div className="float-card">🔍 Deep Research</div>
                  <div className="float-card">📊 Data Analysis</div>
                  <div className="float-card">⚡ Automation</div>
                  <div className="float-card">🤖 AI Workflows</div>
                </div>
              </div>
            </section>

            {/* Features Grid */}
            <section className="features-section">
              <h2>Intelligent Capabilities</h2>
              <div className="features-grid">
                <div className="feature-card">
                  <div className="feature-icon">🎯</div>
                  <h3>Express Ideas</h3>
                  <p>Natural language commands that AETHER understands and executes</p>
                </div>
                <div className="feature-card">
                  <div className="feature-icon">⚡</div>
                  <h3>Instant Action</h3>
                  <p>From research to automation, AETHER acts on your behalf</p>
                </div>
                <div className="feature-card">
                  <div className="feature-icon">🔗</div>
                  <h3>Smart Integration</h3>
                  <p>Seamlessly connects and automates across platforms</p>
                </div>
                <div className="feature-card">
                  <div className="feature-icon">📈</div>
                  <h3>Workflow Intelligence</h3>
                  <p>Learns and optimizes your browsing and work patterns</p>
                </div>
              </div>
            </section>

            {/* Quick Actions */}
            <QuickActions />

            {/* Recent Activity */}
            {searchHistory.length > 0 && (
              <section className="recent-section">
                <h2>Recent Activities</h2>
                <div className="recent-grid">
                  {searchHistory.map((item, index) => (
                    <div 
                      key={index} 
                      className="recent-card"
                      draggable
                      onDragStart={(e) => handleDragStart(e, item)}
                    >
                      <div className="recent-icon">🔍</div>
                      <div className="recent-content">
                        <div className="recent-title">{item.query || item.title}</div>
                        <div className="recent-time">{item.timestamp || 'Recently'}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}

        {currentView === 'workflows' && (
          <div className="workflows-view">
            <h1>AI Workflows</h1>
            <p>Create and manage intelligent automation workflows</p>
            <div className="workflow-builder">
              <div className="workflow-canvas">
                <p>Drag actions here to build workflows</p>
              </div>
            </div>
          </div>
        )}

        {currentView === 'agents' && (
          <div className="agents-view">
            <h1>AI Agents</h1>
            <p>Manage your intelligent agents and their capabilities</p>
            <div className="agents-grid">
              <div className="agent-card">
                <h3>Research Agent</h3>
                <p>Specialized in deep web research and analysis</p>
              </div>
              <div className="agent-card">
                <h3>Data Agent</h3>
                <p>Expert in data extraction and processing</p>
              </div>
              <div className="agent-card">
                <h3>Automation Agent</h3>
                <p>Handles repetitive tasks and workflows</p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Fixed Components */}
      <AIAssistant />
      <Timeline />

      {/* Background Effects */}
      <div className="bg-effects">
        <div className="gradient-orb orb-1"></div>
        <div className="gradient-orb orb-2"></div>
        <div className="gradient-orb orb-3"></div>
      </div>
    </div>
  );
}

export default App;