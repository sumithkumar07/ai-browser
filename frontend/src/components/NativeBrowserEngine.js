import React, { useEffect, useRef, useState } from 'react';

const NativeBrowserEngine = ({ 
  currentUrl, 
  onUrlChange, 
  onNavigationChange, 
  nativeAPI 
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [canGoBack, setCanGoBack] = useState(false);
  const [canGoForward, setCanGoForward] = useState(false);
  const [currentDomain, setCurrentDomain] = useState('');
  const [isSecure, setIsSecure] = useState(true);
  const containerRef = useRef(null);

  useEffect(() => {
    if (currentUrl && nativeAPI) {
      handleNavigation(currentUrl);
    }
  }, [currentUrl, nativeAPI]);

  const handleNavigation = async (url) => {
    if (!nativeAPI || !url) return;

    setIsLoading(true);
    
    try {
      const result = await nativeAPI.navigateTo(url);
      
      if (result.success) {
        // Update domain and security indicators
        const urlObj = new URL(url);
        setCurrentDomain(urlObj.hostname);
        setIsSecure(url.startsWith('https://'));
        
        // Update navigation state
        await updateNavigationState();
        
        // Notify parent component
        onUrlChange(url);
      }
    } catch (error) {
      console.error('Native navigation error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const updateNavigationState = async () => {
    if (!nativeAPI) return;

    try {
      // Note: In a real implementation, you'd get these from the native API
      // For now, we'll simulate the state
      const navigationState = {
        canGoBack: canGoBack,
        canGoForward: canGoForward,
        isLoading: isLoading
      };
      
      onNavigationChange(navigationState);
    } catch (error) {
      console.error('Navigation state update error:', error);
    }
  };

  const handleBack = async () => {
    if (!nativeAPI) return;
    
    const success = await nativeAPI.browserBack();
    if (success) {
      setCanGoBack(false); // Will be updated by navigation state
      await updateNavigationState();
    }
  };

  const handleForward = async () => {
    if (!nativeAPI) return;
    
    const success = await nativeAPI.browserForward();
    if (success) {
      setCanGoForward(false); // Will be updated by navigation state
      await updateNavigationState();
    }
  };

  const handleRefresh = async () => {
    if (!nativeAPI) return;
    
    await nativeAPI.browserRefresh();
    setIsLoading(true);
    setTimeout(() => setIsLoading(false), 1000); // Simulate loading
  };

  const handleDevTools = async () => {
    if (!nativeAPI) return;
    await nativeAPI.openDevTools();
  };

  const handleScreenshot = async () => {
    if (!nativeAPI) return;
    
    try {
      const result = await nativeAPI.captureScreenshot();
      if (result.success) {
        // Create download link for screenshot
        const link = document.createElement('a');
        link.href = result.screenshot;
        link.download = `aether-screenshot-${Date.now()}.png`;
        link.click();
      }
    } catch (error) {
      console.error('Screenshot error:', error);
    }
  };

  const executeScript = async (script) => {
    if (!nativeAPI) return;
    
    try {
      const result = await nativeAPI.executeJavaScript(script);
      return result;
    } catch (error) {
      console.error('Script execution error:', error);
      return { success: false, error: error.message };
    }
  };

  return (
    <div className="native-browser-engine">
      {/* Native Browser Controls */}
      <div className="native-controls">
        <div className="navigation-controls">
          <button 
            className={`nav-btn ${!canGoBack ? 'disabled' : ''}`}
            onClick={handleBack}
            disabled={!canGoBack}
            title="Go back"
          >
            ←
          </button>
          <button 
            className={`nav-btn ${!canGoForward ? 'disabled' : ''}`}
            onClick={handleForward}
            disabled={!canGoForward}
            title="Go forward"
          >
            →
          </button>
          <button 
            className="nav-btn"
            onClick={handleRefresh}
            title="Refresh"
          >
            {isLoading ? '⟳' : '↻'}
          </button>
        </div>

        <div className="url-display">
          <div className="security-indicator">
            {isSecure ? (
              <span className="secure" title="Secure connection">🔒</span>
            ) : (
              <span className="insecure" title="Not secure">⚠️</span>
            )}
          </div>
          <div className="current-url">
            {currentDomain || 'No page loaded'}
          </div>
        </div>

        <div className="native-features">
          <button 
            className="feature-btn"
            onClick={handleDevTools}
            title="Open Developer Tools"
          >
            🔧
          </button>
          <button 
            className="feature-btn"
            onClick={handleScreenshot}
            title="Take Screenshot"
          >
            📸
          </button>
        </div>
      </div>

      {/* Native Browser Container */}
      <div 
        ref={containerRef}
        className="native-browser-container"
        style={{
          width: '100%',
          height: 'calc(100vh - 200px)',
          backgroundColor: '#1a1a1a',
          border: '1px solid #333',
          borderRadius: '8px',
          overflow: 'hidden',
          position: 'relative'
        }}
      >
        {/* Loading Overlay */}
        {isLoading && (
          <div className="native-loading-overlay">
            <div className="loading-spinner"></div>
            <div className="loading-text">
              Loading with Native Chromium Engine...
            </div>
          </div>
        )}

        {/* Native Browser View Area */}
        <div className="native-browser-view">
          {/* The actual browser content is rendered by Electron BrowserView */}
          {!currentUrl && (
            <div className="native-welcome">
              <div className="welcome-content">
                <h2>🔥 Native Chromium Engine</h2>
                <p>Full browser capabilities with no restrictions</p>
                <ul className="features-list">
                  <li>✅ Cross-origin access</li>
                  <li>✅ Browser extensions support</li>
                  <li>✅ Native DevTools</li>
                  <li>✅ Hardware acceleration</li>
                  <li>✅ Full JavaScript API access</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Native API Status */}
      <div className="native-status">
        <span className="status-indicator">
          {nativeAPI ? '🟢 Native Chromium Active' : '🟡 Web Mode'}
        </span>
      </div>

      <style jsx>{`
        .native-browser-engine {
          display: flex;
          flex-direction: column;
          height: 100%;
          background: #0a0a0f;
        }

        .native-controls {
          display: flex;
          align-items: center;
          padding: 12px 16px;
          background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
          border-bottom: 1px solid #333;
          gap: 16px;
        }

        .navigation-controls {
          display: flex;
          gap: 8px;
        }

        .nav-btn {
          width: 36px;
          height: 36px;
          border: none;
          background: #333;
          color: #fff;
          border-radius: 6px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.3s ease;
        }

        .nav-btn:hover:not(.disabled) {
          background: #8b5cf6;
          transform: translateY(-1px);
        }

        .nav-btn.disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .url-display {
          flex: 1;
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 8px 16px;
          background: #1a1a1a;
          border-radius: 24px;
          border: 1px solid #333;
        }

        .security-indicator {
          font-size: 14px;
        }

        .current-url {
          flex: 1;
          color: #e5e5e5;
          font-family: 'Monaco', monospace;
          font-size: 14px;
        }

        .native-features {
          display: flex;
          gap: 8px;
        }

        .feature-btn {
          width: 36px;
          height: 36px;
          border: none;
          background: #8b5cf6;
          color: #fff;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .feature-btn:hover {
          background: #7c3aed;
          transform: scale(1.05);
        }

        .native-browser-container {
          position: relative;
          flex: 1;
        }

        .native-loading-overlay {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(26, 26, 26, 0.9);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .loading-spinner {
          width: 40px;
          height: 40px;
          border: 4px solid #333;
          border-left: 4px solid #8b5cf6;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-bottom: 16px;
        }

        .loading-text {
          color: #8b5cf6;
          font-size: 16px;
          font-weight: 600;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .native-welcome {
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #0a0a0f 0%, #1a1a1f 100%);
        }

        .welcome-content {
          text-align: center;
          padding: 40px;
          border-radius: 16px;
          background: rgba(139, 92, 246, 0.1);
          border: 1px solid rgba(139, 92, 246, 0.2);
        }

        .welcome-content h2 {
          color: #8b5cf6;
          margin-bottom: 16px;
          font-size: 24px;
        }

        .welcome-content p {
          color: #e5e5e5;
          margin-bottom: 24px;
          font-size: 16px;
        }

        .features-list {
          list-style: none;
          padding: 0;
          text-align: left;
        }

        .features-list li {
          color: #a1a1aa;
          padding: 4px 0;
          font-size: 14px;
        }

        .native-status {
          padding: 8px 16px;
          background: #1a1a1a;
          border-top: 1px solid #333;
          display: flex;
          justify-content: center;
        }

        .status-indicator {
          font-size: 12px;
          color: #22c55e;
          font-weight: 600;
        }
      `}</style>
    </div>
  );
};

export default NativeBrowserEngine;