import React, { useEffect, useState, useRef } from 'react';
import { 
  ArrowLeft, 
  ArrowRight, 
  RotateCcw, 
  Shield, 
  ShieldAlert, 
  Settings, 
  Puzzle,
  Code2,
  Monitor
} from 'lucide-react';

const NativeBrowserEngine = ({ 
  currentUrl, 
  onUrlChange,
  onNavigationChange,
  nativeAPI = null 
}) => {
  const [navigationState, setNavigationState] = useState({
    canGoBack: false,
    canGoForward: false,
    isLoading: false,
    isSecure: false,
    title: 'New Tab'
  });
  
  const [devToolsOpen, setDevToolsOpen] = useState(false);
  const [extensions, setExtensions] = useState([]);
  const [showEngineInfo, setShowEngineInfo] = useState(false);
  const browserViewRef = useRef(null);

  // Native Chromium capabilities detection
  const hasNativeChromium = nativeAPI?.hasNativeChromium() || false;
  const hasExtensionSupport = nativeAPI?.hasExtensionSupport() || false;
  const hasCrossOriginAccess = nativeAPI?.hasCrossOriginAccess() || false;

  // Initialize native browser capabilities
  useEffect(() => {
    if (nativeAPI) {
      // Load extensions
      loadExtensions();
      
      // Set up navigation event listeners
      nativeAPI.onNavigationChange((data) => {
        setNavigationState(prev => ({
          ...prev,
          ...data
        }));
        onNavigationChange?.(data);
      });
    }
  }, [nativeAPI, onNavigationChange]);

  const loadExtensions = async () => {
    if (nativeAPI?.getExtensions) {
      try {
        const extensionList = await nativeAPI.getExtensions();
        setExtensions(extensionList);
      } catch (error) {
        console.error('Failed to load extensions:', error);
      }
    }
  };

  // Native browser controls
  const handleBack = async () => {
    if (nativeAPI?.browserBack) {
      const success = await nativeAPI.browserBack();
      if (success) {
        setNavigationState(prev => ({ ...prev, canGoBack: false }));
      }
    }
  };

  const handleForward = async () => {
    if (nativeAPI?.browserForward) {
      const success = await nativeAPI.browserForward();
      if (success) {
        setNavigationState(prev => ({ ...prev, canGoForward: false }));
      }
    }
  };

  const handleRefresh = async () => {
    if (nativeAPI?.browserRefresh) {
      setNavigationState(prev => ({ ...prev, isLoading: true }));
      await nativeAPI.browserRefresh();
      setTimeout(() => {
        setNavigationState(prev => ({ ...prev, isLoading: false }));
      }, 1000);
    }
  };

  const handleNavigate = async (url) => {
    if (nativeAPI?.navigateTo) {
      setNavigationState(prev => ({ ...prev, isLoading: true }));
      
      try {
        const result = await nativeAPI.navigateTo(url);
        if (result.success) {
          onUrlChange?.(url);
          setNavigationState(prev => ({
            ...prev,
            isSecure: url.startsWith('https://'),
            isLoading: false
          }));
        }
      } catch (error) {
        console.error('Navigation error:', error);
        setNavigationState(prev => ({ ...prev, isLoading: false }));
      }
    }
  };

  const toggleDevTools = async () => {
    if (nativeAPI?.openDevTools) {
      await nativeAPI.openDevTools();
      setDevToolsOpen(!devToolsOpen);
    }
  };

  if (!hasNativeChromium) {
    return (
      <div className="browser-engine-fallback">
        <div className="fallback-message">
          <Monitor className="w-8 h-8 text-yellow-400" />
          <h3>Enhanced Browser Mode</h3>
          <p>Running in enhanced iframe mode. For full native Chromium features, use the desktop app.</p>
        </div>
        
        <style jsx>{`
          .browser-engine-fallback {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 200px;
            background: rgba(15, 15, 20, 0.95);
            border-radius: 12px;
            border: 1px solid rgba(234, 179, 8, 0.2);
            margin: 20px;
          }

          .fallback-message {
            text-align: center;
            color: white;
          }

          .fallback-message h3 {
            margin: 12px 0 8px;
            color: #eab308;
          }

          .fallback-message p {
            margin: 0;
            color: rgba(255, 255, 255, 0.7);
            font-size: 14px;
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="native-browser-engine">
      {/* Native Browser Controls */}
      <div className="native-controls">
        <div className="navigation-controls">
          <button
            className={`nav-btn ${!navigationState.canGoBack ? 'disabled' : ''}`}
            onClick={handleBack}
            disabled={!navigationState.canGoBack}
            title="Go Back"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          
          <button
            className={`nav-btn ${!navigationState.canGoForward ? 'disabled' : ''}`}
            onClick={handleForward}
            disabled={!navigationState.canGoForward}
            title="Go Forward"
          >
            <ArrowRight className="w-4 h-4" />
          </button>
          
          <button
            className="nav-btn"
            onClick={handleRefresh}
            disabled={navigationState.isLoading}
            title="Refresh"
          >
            <RotateCcw className={`w-4 h-4 ${navigationState.isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Security Indicator */}
        <div className="security-indicator">
          {navigationState.isSecure ? (
            <Shield className="w-4 h-4 text-green-400" title="Secure Connection" />
          ) : (
            <ShieldAlert className="w-4 h-4 text-yellow-400" title="Not Secure" />
          )}
        </div>

        {/* Native Features */}
        <div className="native-features">
          {/* DevTools Access */}
          <button
            className={`feature-btn ${devToolsOpen ? 'active' : ''}`}
            onClick={toggleDevTools}
            title="Chrome Developer Tools"
          >
            <Code2 className="w-4 h-4" />
          </button>

          {/* Extensions */}
          {hasExtensionSupport && (
            <div className="extensions-panel">
              <button
                className="feature-btn"
                onClick={() => setShowEngineInfo(!showEngineInfo)}
                title={`Extensions (${extensions.length})`}
              >
                <Puzzle className="w-4 h-4" />
                {extensions.length > 0 && (
                  <span className="extension-count">{extensions.length}</span>
                )}
              </button>
            </div>
          )}

          {/* Engine Info */}
          <button
            className="feature-btn"
            onClick={() => setShowEngineInfo(!showEngineInfo)}
            title="Native Engine Info"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Engine Info Panel */}
      {showEngineInfo && (
        <div className="engine-info-panel">
          <div className="info-header">
            <h3>🔥 Native Chromium Engine</h3>
            <button onClick={() => setShowEngineInfo(false)}>×</button>
          </div>
          
          <div className="capabilities-grid">
            <div className="capability">
              <div className="capability-icon">🌐</div>
              <div>
                <h4>Native Browser Engine</h4>
                <p>Full Chromium with V8 JavaScript engine</p>
              </div>
            </div>
            
            <div className="capability">
              <div className="capability-icon">🔧</div>
              <div>
                <h4>Chrome DevTools</h4>
                <p>Complete debugging and inspection tools</p>
              </div>
            </div>
            
            {hasExtensionSupport && (
              <div className="capability">
                <div className="capability-icon">🧩</div>
                <div>
                  <h4>Extension Support</h4>
                  <p>{extensions.length} extensions loaded</p>
                </div>
              </div>
            )}
            
            {hasCrossOriginAccess && (
              <div className="capability">
                <div className="capability-icon">🔓</div>
                <div>
                  <h4>Cross-Origin Access</h4>
                  <p>No CORS restrictions (like Fellou.ai)</p>
                </div>
              </div>
            )}
          </div>

          {extensions.length > 0 && (
            <div className="extensions-list">
              <h4>Loaded Extensions:</h4>
              <div className="extension-items">
                {extensions.map((ext) => (
                  <div key={ext.id} className="extension-item">
                    <span className="extension-name">{ext.name}</span>
                    <span className="extension-version">v{ext.version}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Native Browser View Container */}
      <div 
        ref={browserViewRef}
        className="native-browser-view"
        style={{
          position: 'absolute',
          top: '60px',
          left: 0,
          right: 0,
          bottom: 0,
          background: '#1a1a1a'
        }}
      >
        {navigationState.isLoading && (
          <div className="loading-overlay">
            <div className="loading-indicator">
              <div className="loading-spinner"></div>
              <span>Loading with native Chromium...</span>
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        .native-browser-engine {
          position: relative;
          width: 100%;
          height: 100vh;
          background: #0a0a0f;
        }

        .native-controls {
          display: flex;
          align-items: center;
          padding: 12px 16px;
          background: rgba(15, 15, 20, 0.95);
          border-bottom: 1px solid rgba(147, 51, 234, 0.1);
          gap: 16px;
          height: 60px;
          backdrop-filter: blur(10px);
        }

        .navigation-controls {
          display: flex;
          gap: 8px;
        }

        .nav-btn, .feature-btn {
          padding: 8px;
          border-radius: 8px;
          border: none;
          background: rgba(147, 51, 234, 0.1);
          color: white;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .nav-btn:hover, .feature-btn:hover {
          background: rgba(147, 51, 234, 0.2);
          transform: scale(1.05);
        }

        .nav-btn.disabled {
          opacity: 0.3;
          cursor: not-allowed;
          transform: none;
        }

        .feature-btn.active {
          background: rgba(147, 51, 234, 0.3);
        }

        .security-indicator {
          margin-left: 8px;
        }

        .native-features {
          display: flex;
          gap: 8px;
          margin-left: auto;
        }

        .extensions-panel {
          position: relative;
        }

        .extension-count {
          position: absolute;
          top: -4px;
          right: -4px;
          background: #ef4444;
          color: white;
          font-size: 10px;
          border-radius: 50%;
          width: 16px;
          height: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
        }

        .engine-info-panel {
          position: absolute;
          top: 60px;
          right: 20px;
          width: 400px;
          background: rgba(15, 15, 20, 0.95);
          border: 1px solid rgba(147, 51, 234, 0.2);
          border-radius: 12px;
          padding: 20px;
          backdrop-filter: blur(20px);
          z-index: 1000;
          animation: slideIn 0.3s ease-out;
        }

        .info-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .info-header h3 {
          margin: 0;
          color: white;
          font-size: 16px;
        }

        .info-header button {
          background: none;
          border: none;
          color: white;
          font-size: 20px;
          cursor: pointer;
          padding: 4px;
          border-radius: 4px;
        }

        .info-header button:hover {
          background: rgba(255, 255, 255, 0.1);
        }

        .capabilities-grid {
          display: grid;
          gap: 12px;
          margin-bottom: 16px;
        }

        .capability {
          display: flex;
          gap: 12px;
          align-items: center;
          padding: 12px;
          background: rgba(147, 51, 234, 0.05);
          border: 1px solid rgba(147, 51, 234, 0.1);
          border-radius: 8px;
        }

        .capability-icon {
          font-size: 24px;
          flex-shrink: 0;
        }

        .capability h4 {
          margin: 0 0 4px 0;
          color: white;
          font-size: 14px;
        }

        .capability p {
          margin: 0;
          color: rgba(255, 255, 255, 0.6);
          font-size: 12px;
        }

        .extensions-list {
          border-top: 1px solid rgba(147, 51, 234, 0.1);
          padding-top: 16px;
        }

        .extensions-list h4 {
          margin: 0 0 12px 0;
          color: white;
          font-size: 14px;
        }

        .extension-items {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .extension-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 12px;
          background: rgba(34, 197, 94, 0.05);
          border: 1px solid rgba(34, 197, 94, 0.1);
          border-radius: 6px;
        }

        .extension-name {
          color: #22c55e;
          font-size: 13px;
          font-weight: 500;
        }

        .extension-version {
          color: rgba(34, 197, 94, 0.7);
          font-size: 11px;
        }

        .loading-overlay {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(10, 10, 15, 0.8);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 100;
        }

        .loading-indicator {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 16px;
          color: white;
        }

        .loading-spinner {
          width: 40px;
          height: 40px;
          border: 4px solid rgba(147, 51, 234, 0.3);
          border-top: 4px solid rgb(147, 51, 234);
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateX(20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        /* Mobile responsiveness */
        @media (max-width: 768px) {
          .engine-info-panel {
            width: 90%;
            right: 5%;
          }

          .native-controls {
            padding: 10px 12px;
            gap: 12px;
          }

          .capability {
            padding: 10px;
          }

          .capability-icon {
            font-size: 20px;
          }
        }
      `}</style>
    </div>
  );
};

export default NativeBrowserEngine;