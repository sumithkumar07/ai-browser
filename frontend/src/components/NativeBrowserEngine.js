import React, { useEffect, useState, useCallback, useRef } from 'react';

/**
 * Native Browser Engine Component
 * Provides native Chromium browser integration when running in Electron
 */
const NativeBrowserEngine = ({ 
  currentUrl, 
  onUrlChange, 
  onNavigationChange, 
  nativeAPI 
}) => {
  const [isNativeSupported, setIsNativeSupported] = useState(false);
  const [browserState, setBrowserState] = useState({
    url: '',
    title: 'New Tab',
    canGoBack: false,
    canGoForward: false,
    isLoading: false,
    isSecure: false
  });
  const [capabilities, setCapabilities] = useState(null);
  const [devToolsOpen, setDevToolsOpen] = useState(false);
  const [extensions, setExtensions] = useState([]);
  
  const containerRef = useRef(null);

  // Initialize native browser engine
  useEffect(() => {
    const initializeNativeEngine = async () => {
      if (nativeAPI && nativeAPI.hasNativeChromium()) {
        console.log('🔥 Initializing Native Chromium Engine...');
        
        try {
          // Get native capabilities
          const caps = await nativeAPI.getCapabilities();
          setCapabilities(caps);
          setIsNativeSupported(true);
          
          console.log('✅ Native Chromium Engine Ready:', caps);
          
          // Setup event listeners
          setupNativeEventListeners();
          
        } catch (error) {
          console.error('Failed to initialize native engine:', error);
          setIsNativeSupported(false);
        }
      } else {
        setIsNativeSupported(false);
      }
    };

    initializeNativeEngine();
    
    return () => {
      // Cleanup event listeners
      if (nativeAPI && nativeAPI.removeAllListeners) {
        nativeAPI.removeAllListeners('navigation-updated');
        nativeAPI.removeAllListeners('title-updated');
        nativeAPI.removeAllListeners('loading-state-changed');
      }
    };
  }, [nativeAPI]);

  // Setup native event listeners
  const setupNativeEventListeners = useCallback(() => {
    if (!nativeAPI) return;

    // Navigation events
    nativeAPI.onNavigationUpdate && nativeAPI.onNavigationUpdate((event, data) => {
      setBrowserState(prev => ({
        ...prev,
        url: data.url,
        title: data.title || prev.title,
        canGoBack: data.canGoBack,
        canGoForward: data.canGoForward,
        isLoading: data.isLoading,
        isSecure: data.url?.startsWith('https://')
      }));

      if (onUrlChange && data.url !== currentUrl) {
        onUrlChange(data.url);
      }

      if (onNavigationChange) {
        onNavigationChange({
          canGoBack: data.canGoBack,
          canGoForward: data.canGoForward,
          isLoading: data.isLoading
        });
      }
    });

    // New tab requests
    nativeAPI.onNewTab && nativeAPI.onNewTab((event) => {
      handleNewTab();
    });

    // Native commands
    nativeAPI.onNativeCommand && nativeAPI.onNativeCommand((event, command) => {
      handleNativeCommand(command);
    });

  }, [nativeAPI, currentUrl, onUrlChange, onNavigationChange]);

  // Navigate using native engine
  const handleNavigate = useCallback(async (url) => {
    if (!isNativeSupported || !nativeAPI) {
      console.warn('Native navigation not supported');
      return;
    }

    try {
      setBrowserState(prev => ({ ...prev, isLoading: true }));
      
      const result = await nativeAPI.navigateTo(url);
      
      if (result.success) {
        setBrowserState(prev => ({
          ...prev,
          url: result.url || url,
          isLoading: false,
          canGoBack: result.canGoBack || false,
          canGoForward: result.canGoForward || false,
          isSecure: url.startsWith('https://')
        }));
        
        if (onUrlChange) {
          onUrlChange(result.url || url);
        }
      } else {
        console.error('Native navigation failed:', result.error);
        setBrowserState(prev => ({ ...prev, isLoading: false }));
      }
    } catch (error) {
      console.error('Navigation error:', error);
      setBrowserState(prev => ({ ...prev, isLoading: false }));
    }
  }, [isNativeSupported, nativeAPI, onUrlChange]);

  // Native browser controls
  const handleGoBack = useCallback(async () => {
    if (isNativeSupported && nativeAPI) {
      const result = await nativeAPI.goBack();
      if (result.success && onUrlChange) {
        onUrlChange(result.url);
      }
    }
  }, [isNativeSupported, nativeAPI, onUrlChange]);

  const handleGoForward = useCallback(async () => {
    if (isNativeSupported && nativeAPI) {
      const result = await nativeAPI.goForward();
      if (result.success && onUrlChange) {
        onUrlChange(result.url);
      }
    }
  }, [isNativeSupported, nativeAPI, onUrlChange]);

  const handleRefresh = useCallback(async () => {
    if (isNativeSupported && nativeAPI) {
      await nativeAPI.refresh();
    }
  }, [isNativeSupported, nativeAPI]);

  // DevTools management
  const handleToggleDevTools = useCallback(async () => {
    if (isNativeSupported && nativeAPI) {
      try {
        if (devToolsOpen) {
          // Close DevTools (if API supports it)
          setDevToolsOpen(false);
        } else {
          const result = await nativeAPI.openDevTools();
          if (result.success) {
            setDevToolsOpen(true);
          }
        }
      } catch (error) {
        console.error('DevTools toggle error:', error);
      }
    }
  }, [isNativeSupported, nativeAPI, devToolsOpen]);

  // Screenshot capture
  const handleCaptureScreenshot = useCallback(async () => {
    if (isNativeSupported && nativeAPI) {
      try {
        const result = await nativeAPI.captureScreenshot({
          format: 'png',
          quality: 90
        });
        
        if (result.success) {
          // Download or display screenshot
          const link = document.createElement('a');
          link.href = result.dataUrl;
          link.download = `aether-screenshot-${Date.now()}.png`;
          link.click();
        }
      } catch (error) {
        console.error('Screenshot capture error:', error);
      }
    }
  }, [isNativeSupported, nativeAPI]);

  // Extension management
  const loadExtensions = useCallback(async () => {
    if (isNativeSupported && nativeAPI) {
      try {
        const result = await nativeAPI.getExtensions();
        if (result.success) {
          setExtensions(result.extensions || []);
        }
      } catch (error) {
        console.error('Extension loading error:', error);
      }
    }
  }, [isNativeSupported, nativeAPI]);

  // Load extension from directory
  const handleLoadExtension = useCallback(async () => {
    if (isNativeSupported && nativeAPI) {
      try {
        const result = await nativeAPI.showOpenDialog({
          properties: ['openDirectory'],
          title: 'Select Chrome Extension Directory'
        });
        
        if (!result.canceled && result.filePaths.length > 0) {
          const extensionPath = result.filePaths[0];
          const loadResult = await nativeAPI.loadExtension(extensionPath);
          
          if (loadResult.success) {
            console.log('Extension loaded:', loadResult.extension);
            await loadExtensions(); // Refresh extensions list
          } else {
            console.error('Extension load failed:', loadResult.error);
          }
        }
      } catch (error) {
        console.error('Extension selection error:', error);
      }
    }
  }, [isNativeSupported, nativeAPI, loadExtensions]);

  // Handle new tab
  const handleNewTab = useCallback(() => {
    // This would be handled by the parent component
    console.log('New tab requested via native menu');
  }, []);

  // Handle native commands from menu
  const handleNativeCommand = useCallback((command) => {
    switch (command.type) {
      case 'navigate':
        if (command.url) {
          handleNavigate(command.url);
        }
        break;
      case 'refresh':
        handleRefresh();
        break;
      case 'devtools':
        handleToggleDevTools();
        break;
      case 'screenshot':
        handleCaptureScreenshot();
        break;
      default:
        console.log('Unknown native command:', command);
    }
  }, [handleNavigate, handleRefresh, handleToggleDevTools, handleCaptureScreenshot]);

  // Navigate when currentUrl changes
  useEffect(() => {
    if (currentUrl && currentUrl !== browserState.url) {
      handleNavigate(currentUrl);
    }
  }, [currentUrl, browserState.url, handleNavigate]);

  // Load extensions on mount
  useEffect(() => {
    if (isNativeSupported) {
      loadExtensions();
    }
  }, [isNativeSupported, loadExtensions]);

  if (!isNativeSupported) {
    return (
      <div className="native-browser-fallback">
        <div className="fallback-message">
          <h3>🌐 Web Version Mode</h3>
          <p>Native Chromium engine is available in the desktop app.</p>
          <p>Currently running enhanced iframe browser engine.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="native-browser-engine" ref={containerRef}>
      {/* Native Browser Status */}
      <div className="native-status-bar">
        <div className="native-status-info">
          <span className="native-indicator">🔥</span>
          <span className="native-text">Native Chromium Engine</span>
          {capabilities && (
            <span className="chromium-version">
              v{capabilities.chromiumVersion}
            </span>
          )}
        </div>
        
        <div className="native-controls">
          <button
            className="native-control-btn"
            onClick={handleToggleDevTools}
            title="Toggle DevTools (F12)"
          >
            🔧
          </button>
          
          <button
            className="native-control-btn"
            onClick={handleCaptureScreenshot}
            title="Capture Screenshot"
          >
            📸
          </button>
          
          <button
            className="native-control-btn"
            onClick={handleLoadExtension}
            title="Load Extension"
          >
            🧩
          </button>
          
          {extensions.length > 0 && (
            <div className="extensions-indicator">
              <span className="extensions-count">{extensions.length}</span>
              <span className="extensions-text">Extensions</span>
            </div>
          )}
        </div>
      </div>

      {/* Native Browser View Container */}
      <div className="native-browser-container">
        {/* The actual browser view is managed by Electron BrowserView */}
        {/* This div serves as a placeholder and reference point */}
        <div className="native-browser-placeholder">
          {browserState.isLoading && (
            <div className="native-loading-overlay">
              <div className="native-loading-spinner"></div>
              <div className="native-loading-text">
                Loading with Native Chromium Engine...
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Native Features Showcase */}
      {capabilities && (
        <div className="native-capabilities">
          <div className="capability-item">
            <span className="capability-icon">✅</span>
            <span>Native Navigation</span>
          </div>
          <div className="capability-item">
            <span className="capability-icon">🔧</span>
            <span>DevTools Access</span>
          </div>
          <div className="capability-item">
            <span className="capability-icon">🧩</span>
            <span>Extension Support</span>
          </div>
          <div className="capability-item">
            <span className="capability-icon">🌐</span>
            <span>Cross-Origin Access</span>
          </div>
        </div>
      )}

      <style jsx>{`
        .native-browser-engine {
          width: 100%;
          height: 100%;
          display: flex;
          flex-direction: column;
        }

        .native-status-bar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 16px;
          background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
          border-bottom: 1px solid #4c1d95;
          color: white;
          font-size: 12px;
        }

        .native-status-info {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .native-indicator {
          font-size: 14px;
        }

        .native-text {
          font-weight: 600;
        }

        .chromium-version {
          background: rgba(147, 51, 234, 0.3);
          padding: 2px 6px;
          border-radius: 10px;
          font-size: 10px;
        }

        .native-controls {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .native-control-btn {
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.2);
          color: white;
          padding: 4px 8px;
          border-radius: 4px;
          cursor: pointer;
          font-size: 12px;
          transition: all 0.2s ease;
        }

        .native-control-btn:hover {
          background: rgba(255, 255, 255, 0.2);
          transform: translateY(-1px);
        }

        .extensions-indicator {
          display: flex;
          align-items: center;
          gap: 4px;
          background: rgba(34, 197, 94, 0.2);
          padding: 4px 8px;
          border-radius: 10px;
        }

        .extensions-count {
          background: rgba(34, 197, 94, 0.8);
          color: white;
          padding: 2px 6px;
          border-radius: 8px;
          font-size: 10px;
          font-weight: bold;
        }

        .native-browser-container {
          flex: 1;
          position: relative;
          background: #1f1f1f;
        }

        .native-browser-placeholder {
          width: 100%;
          height: 100%;
          position: relative;
        }

        .native-loading-overlay {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.8);
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          color: white;
        }

        .native-loading-spinner {
          width: 32px;
          height: 32px;
          border: 3px solid rgba(147, 51, 234, 0.3);
          border-top: 3px solid #9333ea;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-bottom: 16px;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .native-loading-text {
          font-size: 14px;
          color: #e5e7eb;
        }

        .native-capabilities {
          display: flex;
          justify-content: center;
          gap: 20px;
          padding: 12px;
          background: rgba(30, 27, 75, 0.5);
          border-top: 1px solid #4c1d95;
        }

        .capability-item {
          display: flex;
          align-items: center;
          gap: 6px;
          color: #e5e7eb;
          font-size: 12px;
        }

        .capability-icon {
          font-size: 14px;
        }

        .native-browser-fallback {
          display: flex;
          justify-content: center;
          align-items: center;
          height: 300px;
          background: rgba(30, 27, 75, 0.1);
          border: 2px dashed #4c1d95;
          border-radius: 8px;
          margin: 20px;
        }

        .fallback-message {
          text-align: center;
          color: #6b7280;
        }

        .fallback-message h3 {
          color: #374151;
          margin-bottom: 12px;
        }

        .fallback-message p {
          margin: 4px 0;
          font-size: 14px;
        }
      `}</style>
    </div>
  );
};

export default NativeBrowserEngine;