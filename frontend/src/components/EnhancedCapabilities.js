import React, { useState, useEffect } from 'react';

const EnhancedCapabilities = ({ backendUrl, currentUrl, sessionId }) => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [shadowTasks, setShadowTasks] = useState([]);
  const [splitViewSession, setSplitViewSession] = useState(null);
  const [availablePlatforms, setAvailablePlatforms] = useState([]);

  useEffect(() => {
    checkSystemStatus();
    loadUserShadowTasks();
    loadAvailablePlatforms();
  }, []);

  const checkSystemStatus = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/enhanced/system-status`);
      const data = await response.json();
      setSystemStatus(data);
    } catch (error) {
      console.error('Failed to check system status:', error);
    }
  };

  const loadUserShadowTasks = async () => {
    if (!systemStatus?.enhanced_systems_available) return;
    
    try {
      const response = await fetch(`${backendUrl}/api/shadow/active-tasks/${sessionId}`);
      if (response.ok) {
        const data = await response.json();
        setShadowTasks(data.active_tasks || []);
      }
    } catch (error) {
      console.error('Failed to load shadow tasks:', error);
    }
  };

  const loadAvailablePlatforms = async () => {
    if (!systemStatus?.enhanced_systems_available) return;
    
    try {
      const response = await fetch(`${backendUrl}/api/platforms/available`);
      if (response.ok) {
        const data = await response.json();
        setAvailablePlatforms(data.integrations || []);
      }
    } catch (error) {
      console.error('Failed to load platforms:', error);
    }
  };

  const createShadowTask = async (command) => {
    try {
      const response = await fetch(`${backendUrl}/api/shadow/create-task`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command,
          user_session: sessionId,
          current_url: currentUrl,
          priority: 'normal',
          background_mode: true
        })
      });

      if (response.ok) {
        const result = await response.json();
        alert(`🌟 Shadow Task Created: ${result.task_id}`);
        loadUserShadowTasks();
      }
    } catch (error) {
      console.error('Failed to create shadow task:', error);
    }
  };

  const createSplitView = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/split-view/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_session: sessionId,
          layout: 'horizontal',
          initial_urls: [currentUrl, 'https://google.com']
        })
      });

      if (response.ok) {
        const result = await response.json();
        setSplitViewSession(result.session_id);
        alert(`🔲 Split View Created: ${result.session_id}`);
      }
    } catch (error) {
      console.error('Failed to create split view:', error);
    }
  };

  if (!systemStatus) {
    return (
      <div className="enhanced-capabilities loading">
        <div className="loading-spinner"></div>
        <p>Loading enhanced capabilities...</p>
      </div>
    );
  }

  return (
    <div className="enhanced-capabilities">
      <div className="capability-header">
        <h3>🚀 Enhanced AETHER Capabilities</h3>
        <div className={`status-indicator ${systemStatus.enhanced_systems_available ? 'active' : 'inactive'}`}>
          {systemStatus.enhanced_systems_available ? '✅ All Systems Active' : '⚠️ Basic Mode'}
        </div>
      </div>

      {systemStatus.enhanced_systems_available ? (
        <div className="capabilities-grid">
          {/* Shadow Workspace */}
          <div className="capability-card">
            <div className="card-header">
              <span className="card-icon">🌟</span>
              <h4>Shadow Workspace</h4>
            </div>
            <p>Background task execution without disrupting your workflow</p>
            <div className="card-actions">
              <button 
                onClick={() => createShadowTask('Analyze current page and extract key insights')}
                className="action-btn primary"
              >
                Create Shadow Task
              </button>
              {shadowTasks.length > 0 && (
                <span className="task-count">{shadowTasks.length} active tasks</span>
              )}
            </div>
          </div>

          {/* Visual Workflow Builder */}
          <div className="capability-card">
            <div className="card-header">
              <span className="card-icon">🎨</span>
              <h4>Visual Workflow Builder</h4> 
            </div>
            <p>Drag & drop interface for creating automation workflows</p>
            <div className="card-actions">
              <button 
                onClick={() => alert('Visual Workflow Builder - Ready for UI integration!')}
                className="action-btn primary"
              >
                Open Workflow Builder
              </button>
            </div>
          </div>

          {/* Split View Engine */}
          <div className="capability-card">
            <div className="card-header">
              <span className="card-icon">🔲</span>
              <h4>Split View Browsing</h4>
            </div>
            <p>Multi-website viewing in a single browser window</p>
            <div className="card-actions">
              <button 
                onClick={createSplitView}
                className="action-btn primary"
              >
                Create Split View
              </button>
              {splitViewSession && (
                <span className="session-id">Session: {splitViewSession.slice(0, 8)}...</span>
              )}
            </div>
          </div>

          {/* Platform Integrations */}
          <div className="capability-card">
            <div className="card-header">
              <span className="card-icon">🔗</span>
              <h4>Platform Integrations</h4>
            </div>
            <p>{availablePlatforms.length} platforms available for cross-platform automation</p>
            <div className="card-actions">
              <button 
                onClick={() => alert(`${availablePlatforms.length} platforms ready: Twitter, LinkedIn, GitHub, Notion, Slack and more!`)}
                className="action-btn primary"
              >
                View Platforms
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="fallback-mode">
          <p>Enhanced systems are being initialized. Basic functionality available.</p>
          <div className="basic-features">
            <span>✅ AI Chat</span>
            <span>✅ Web Browsing</span>
            <span>✅ Voice Commands</span>
            <span>✅ Page Summarization</span>
          </div>
        </div>
      )}

      <style jsx>{`
        .enhanced-capabilities {
          padding: 20px;
          background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
          border-radius: 12px;
          color: white;
          margin: 10px 0;
        }

        .loading {
          text-align: center;
          padding: 40px;
        }

        .loading-spinner {
          width: 40px;
          height: 40px;
          border: 4px solid rgba(255, 255, 255, 0.3);
          border-left: 4px solid #a855f7;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 20px;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .capability-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.2);
          padding-bottom: 16px;
        }

        .capability-header h3 {
          margin: 0;
          font-size: 1.5rem;
          font-weight: bold;
        }

        .status-indicator {
          padding: 8px 16px;
          border-radius: 20px;
          font-size: 0.9rem;
          font-weight: 600;
        }

        .status-indicator.active {
          background: rgba(34, 197, 94, 0.2);
          color: #22c55e;
          border: 1px solid rgba(34, 197, 94, 0.3);
        }

        .status-indicator.inactive {
          background: rgba(251, 191, 36, 0.2);
          color: #fbbf24;
          border: 1px solid rgba(251, 191, 36, 0.3);
        }

        .capabilities-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 20px;
        }

        .capability-card {
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 12px;
          padding: 20px;
          backdrop-filter: blur(10px);
          transition: all 0.3s ease;
        }

        .capability-card:hover {
          transform: translateY(-2px);
          background: rgba(255, 255, 255, 0.15);
          border-color: rgba(168, 85, 247, 0.5);
        }

        .card-header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 12px;
        }

        .card-icon {
          font-size: 1.5rem;
        }

        .card-header h4 {
          margin: 0;
          font-size: 1.1rem;
          font-weight: 600;
        }

        .capability-card p {
          color: rgba(255, 255, 255, 0.8);
          margin-bottom: 16px;
          line-height: 1.5;
        }

        .card-actions {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .action-btn {
          padding: 10px 20px;
          border: none;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
          font-size: 0.9rem;
        }

        .action-btn.primary {
          background: linear-gradient(135deg, #a855f7 0%, #8b5cf6 100%);
          color: white;
        }

        .action-btn.primary:hover {
          background: linear-gradient(135deg, #9333ea 0%, #7c3aed 100%);
          transform: translateY(-1px);
        }

        .task-count, .session-id {
          font-size: 0.8rem;
          color: rgba(255, 255, 255, 0.7);
          background: rgba(255, 255, 255, 0.1);
          padding: 4px 12px;
          border-radius: 12px;
        }

        .fallback-mode {
          text-align: center;
          padding: 30px;
        }

        .basic-features {
          display: flex;
          flex-wrap: wrap;
          justify-content: center;
          gap: 16px;
          margin-top: 20px;
        }

        .basic-features span {
          background: rgba(34, 197, 94, 0.2);
          color: #22c55e;
          padding: 8px 16px;
          border-radius: 20px;
          font-size: 0.9rem;
          border: 1px solid rgba(34, 197, 94, 0.3);
        }
      `}</style>
    </div>
  );
};

export default EnhancedCapabilities;