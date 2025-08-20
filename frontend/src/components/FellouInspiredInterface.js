import React, { useState, useEffect, useRef } from 'react';
import './FellouInspiredInterface.css';

const FellouInspiredInterface = ({ 
  onNavigate, 
  currentUrl, 
  urlInput, 
  setUrlInput,
  tabs,
  activeTab,
  onTabSwitch,
  onTabClose,
  onNewTab,
  canGoBack,
  canGoForward,
  onGoBack,
  onGoForward,
  onRefresh,
  isLoading,
  isSecure,
  aiVisible,
  setAiVisible,
  chatMessages,
  setChatMessages,
  aiInput,
  setAiInput,
  aiLoading,
  onSendMessage,
  sessionId,
  backgroundTasks 
}) => {
  const [timelineVisible, setTimelineVisible] = useState(false);
  const [workspaceVisible, setWorkspaceVisible] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [draggedItem, setDraggedItem] = useState(null);
  const iframeRef = useRef(null);

  // Fellou.ai-style quick actions
  const quickActions = [
    { id: 'research', icon: '🔍', title: 'Deep Research', description: 'Multi-source research' },
    { id: 'automate', icon: '⚡', title: 'Automate Task', description: 'Create automation' },
    { id: 'extract', icon: '📊', title: 'Extract Data', description: 'Get structured data' },
    { id: 'monitor', icon: '👁️', title: 'Monitor Page', description: 'Track changes' }
  ];

  // Timeline entries (Fellou.ai-style activity feed)
  const [timelineEntries, setTimelineEntries] = useState([
    { id: 1, type: 'navigation', title: 'Navigated to Google', time: '2 min ago', status: 'completed' },
    { id: 2, type: 'automation', title: 'Data extraction task', time: '5 min ago', status: 'running' },
    { id: 3, type: 'research', title: 'Deep search completed', time: '10 min ago', status: 'completed' }
  ]);

  // Workspace items (Fellou.ai-style drag-drop elements)
  const [workspaceItems, setWorkspaceItems] = useState([
    { id: 'item1', type: 'url', content: 'https://github.com', title: 'GitHub Repository' },
    { id: 'item2', type: 'data', content: 'User research data', title: 'Research Results' },
    { id: 'item3', type: 'task', content: 'Automate login process', title: 'Automation Task' }
  ]);

  const handleDragStart = (e, item) => {
    setDraggedItem(item);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (draggedItem && draggedItem.type === 'url') {
      onNavigate(draggedItem.content);
    }
    setDraggedItem(null);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  return (
    <div className="fellou-interface">
      {/* Fellou.ai-style Header Bar */}
      <div className="fellou-header">
        <div className="fellou-brand">
          <div className="brand-icon">⚡</div>
          <div className="brand-text">
            <h1>AETHER</h1>
            <span>AI-Powered Browser</span>
          </div>
        </div>
        
        <div className="fellou-nav-controls">
          <button 
            className={`nav-btn ${!canGoBack ? 'disabled' : ''}`}
            onClick={onGoBack}
            disabled={!canGoBack}
            title="Go back"
          >
            ←
          </button>
          <button 
            className={`nav-btn ${!canGoForward ? 'disabled' : ''}`}
            onClick={onGoForward}
            disabled={!canGoForward}
            title="Go forward"
          >
            →
          </button>
          <button className="nav-btn" onClick={onRefresh} title="Refresh">
            {isLoading ? '⟳' : '↻'}
          </button>
        </div>

        <div className="fellou-address-bar">
          <div className="security-indicator">
            {isSecure ? '🔒' : '⚠️'}
          </div>
          <input
            type="text"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && onNavigate(urlInput)}
            placeholder="Enter URL or tell AETHER what to do..."
            className="address-input"
          />
          <button 
            className="go-btn"
            onClick={() => onNavigate(urlInput)}
            title="Navigate"
          >
            →
          </button>
        </div>

        <div className="fellou-controls">
          <button 
            className={`control-btn ${timelineVisible ? 'active' : ''}`}
            onClick={() => setTimelineVisible(!timelineVisible)}
            title="Timeline"
          >
            📋
          </button>
          <button 
            className={`control-btn ${workspaceVisible ? 'active' : ''}`}
            onClick={() => setWorkspaceVisible(!workspaceVisible)}
            title="Workspace"
          >
            🗂️
          </button>
          <button 
            className={`control-btn ${aiVisible ? 'active' : ''}`}
            onClick={() => setAiVisible(!aiVisible)}
            title="AI Assistant"
          >
            🤖
          </button>
          <button 
            className="control-btn"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            title="Toggle sidebar"
          >
            ⋮
          </button>
        </div>
      </div>

      {/* Fellou.ai-style Tab Bar */}
      <div className="fellou-tab-bar">
        <div className="tab-container">
          {tabs.map(tab => (
            <div 
              key={tab.id}
              className={`fellou-tab ${tab.id === activeTab ? 'active' : ''}`}
              onClick={() => onTabSwitch(tab.id)}
            >
              <span className="tab-favicon">{tab.favicon}</span>
              <span className="tab-title">{tab.title}</span>
              {tabs.length > 1 && (
                <button 
                  className="tab-close"
                  onClick={(e) => {
                    e.stopPropagation();
                    onTabClose(tab.id);
                  }}
                >
                  ×
                </button>
              )}
            </div>
          ))}
          <button className="new-tab-btn" onClick={onNewTab} title="New Tab">
            +
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="fellou-content">
        {/* Left Sidebar - Fellou.ai-style Tools */}
        {!sidebarCollapsed && (
          <div className="fellou-sidebar">
            <div className="sidebar-section">
              <h3>Quick Actions</h3>
              <div className="quick-actions-grid">
                {quickActions.map(action => (
                  <div key={action.id} className="quick-action-card">
                    <div className="action-icon">{action.icon}</div>
                    <div className="action-content">
                      <div className="action-title">{action.title}</div>
                      <div className="action-description">{action.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Background Tasks (Shadow Workspace) */}
            {Object.keys(backgroundTasks).length > 0 && (
              <div className="sidebar-section">
                <h3>Background Tasks</h3>
                <div className="background-tasks">
                  {Object.entries(backgroundTasks).map(([taskId, task]) => (
                    <div key={taskId} className="task-item">
                      <div className="task-name">{task.name}</div>
                      <div className="task-progress">
                        <div className="progress-bar">
                          <div 
                            className="progress-fill"
                            style={{ width: `${task.progress}%` }}
                          ></div>
                        </div>
                        <span>{task.progress}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Workspace Items */}
            {workspaceVisible && (
              <div className="sidebar-section">
                <h3>Workspace</h3>
                <div className="workspace-items">
                  {workspaceItems.map(item => (
                    <div 
                      key={item.id}
                      className="workspace-item"
                      draggable
                      onDragStart={(e) => handleDragStart(e, item)}
                    >
                      <div className="item-icon">
                        {item.type === 'url' ? '🔗' : item.type === 'data' ? '📊' : '⚡'}
                      </div>
                      <div className="item-content">
                        <div className="item-title">{item.title}</div>
                        <div className="item-description">{item.content}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Central Browser Area */}
        <div className="fellou-browser-area">
          {currentUrl ? (
            <div 
              className="browser-frame-container"
              onDrop={handleDrop}
              onDragOver={handleDragOver}
            >
              {isLoading && (
                <div className="fellou-loading">
                  <div className="loading-spinner"></div>
                  <div className="loading-text">Loading with AETHER...</div>
                </div>
              )}
              <iframe
                ref={iframeRef}
                src={currentUrl}
                className="fellou-browser-frame"
                title="Web Content"
                sandbox="allow-same-origin allow-scripts allow-forms allow-navigation allow-popups allow-popups-to-escape-sandbox"
                onLoad={() => {/* handle load */}}
              />
            </div>
          ) : (
            <div className="fellou-home-screen">
              <div className="home-content">
                <div className="welcome-section">
                  <h2>Welcome to AETHER</h2>
                  <p>Your AI-powered browser with Fellou.ai-inspired interface</p>
                </div>
                
                <div className="home-actions">
                  <div className="action-categories">
                    <div className="category">
                      <h3>🔍 Research</h3>
                      <p>Deep multi-source research with AI analysis</p>
                    </div>
                    <div className="category">
                      <h3>⚡ Automate</h3>
                      <p>Create workflows and automate repetitive tasks</p>
                    </div>
                    <div className="category">
                      <h3>📊 Extract</h3>
                      <p>Extract and analyze data from any website</p>
                    </div>
                    <div className="category">
                      <h3>👁️ Monitor</h3>
                      <p>Monitor websites for changes and updates</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Panel - AI Assistant & Timeline */}
        <div className={`fellou-right-panel ${aiVisible || timelineVisible ? 'visible' : ''}`}>
          {/* AI Assistant Panel */}
          {aiVisible && (
            <div className="ai-panel">
              <div className="panel-header">
                <h3>AI Assistant</h3>
                <button onClick={() => setAiVisible(false)}>✕</button>
              </div>
              
              {/* AI Status */}
              <div className="ai-status">
                <div className="ai-status-dot"></div>
                <span>AETHER AI is online and ready</span>
              </div>
              
              {/* Quick Actions */}
              <div className="ai-quick-actions">
                <h4>Quick Actions</h4>
                <div className="ai-quick-buttons">
                  <button className="ai-quick-button" onClick={() => setAiInput("Summarize this page")}>
                    📄 Summarize
                  </button>
                  <button className="ai-quick-button" onClick={() => setAiInput("Extract key information")}>
                    📊 Extract
                  </button>
                  <button className="ai-quick-button" onClick={() => setAiInput("Create automation workflow")}>
                    ⚡ Automate
                  </button>
                  <button className="ai-quick-button" onClick={() => setAiInput("Analyze this content")}>
                    🔍 Analyze
                  </button>
                </div>
              </div>
              
              <div className="chat-messages">
                {chatMessages.map((message, index) => (
                  <div key={index} className={`message ${message.role}`}>
                    <div className="message-header">
                      <div className="message-avatar">
                        {message.role === 'user' ? 'You' : '🤖'}
                      </div>
                      <span>{message.role === 'user' ? 'You' : 'AETHER AI'}</span>
                    </div>
                    <div className="message-content">
                      {message.content}
                    </div>
                    {message.suggestions && (
                      <div className="message-suggestions">
                        {message.suggestions.map((suggestion, i) => (
                          <button 
                            key={i} 
                            className="suggestion-chip"
                            onClick={() => setAiInput(suggestion.text)}
                          >
                            {suggestion.text}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                {aiLoading && (
                  <div className="message assistant">
                    <div className="message-header">
                      <div className="message-avatar">🤖</div>
                      <span>AETHER AI</span>
                    </div>
                    <div className="typing-indicator">
                      <div className="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="chat-input">
                <div className="chat-input-container">
                  <input
                    type="text"
                    value={aiInput}
                    onChange={(e) => setAiInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && !aiLoading && aiInput.trim() && onSendMessage()}
                    placeholder="Ask AETHER anything..."
                    disabled={aiLoading}
                  />
                  <button 
                    className="chat-send-button"
                    onClick={onSendMessage} 
                    disabled={aiLoading || !aiInput.trim()}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Timeline Panel */}
          {timelineVisible && (
            <div className="timeline-panel">
              <div className="panel-header">
                <h3>📋 Activity Timeline</h3>
                <button onClick={() => setTimelineVisible(false)}>×</button>
              </div>
              
              <div className="timeline-entries">
                {timelineEntries.map(entry => (
                  <div key={entry.id} className="timeline-entry">
                    <div className={`entry-status ${entry.status}`}></div>
                    <div className="entry-content">
                      <div className="entry-title">{entry.title}</div>
                      <div className="entry-time">{entry.time}</div>
                      <div className={`entry-badge ${entry.status}`}>
                        {entry.status}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FellouInspiredInterface;