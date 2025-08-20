import React, { useEffect, useRef, useState } from 'react';
import './NativeBrowserEngine.css';

const NativeBrowserEngine = ({ 
  currentUrl, 
  onUrlChange, 
  onNavigationChange, 
  nativeAPI 
}) => {
  const browserRef = useRef(null);
  const [isLoading, setIsLoading] = useState(false);
  const [canGoBack, setCanGoBack] = useState(false);
  const [canGoForward, setCanGoForward] = useState(false);
  const [securityInfo, setSecurityInfo] = useState({ isSecure: true, certificate: null });
  const [performance, setPerformance] = useState({ loadTime: 0, memoryUsage: 0 });
  const [devToolsOpen, setDevToolsOpen] = useState(false);
  const [extensionsEnabled, setExtensionsEnabled] = useState(true);

  useEffect(() => {
    if (nativeAPI && browserRef.current) {
      initializeNativeBrowser();
    }
  }, [nativeAPI]);

  useEffect(() => {
    if (currentUrl && nativeAPI) {
      navigateToUrl(currentUrl);
    }
  }, [currentUrl, nativeAPI]);

  const initializeNativeBrowser = async () => {
    try {
      // Initialize native Chromium engine
      await nativeAPI.initializeBrowser(browserRef.current, {
        enableExtensions: true,
        enableDevTools: true,
        enableWebSecurity: true,
        enableJavaScript: true,
        enableImages: true,
        enablePlugins: true,
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) AETHER/6.0.0 Chrome/121.0.0.0 Safari/537.36'
      });

      // Set up event listeners
      nativeAPI.onNavigationStart((url) => {
        setIsLoading(true);
        onUrlChange(url);
      });

      nativeAPI.onNavigationComplete((data) => {
        setIsLoading(false);
        setCanGoBack(data.canGoBack);
        setCanGoForward(data.canGoForward);
        setSecurityInfo(data.securityInfo);
        setPerformance(data.performance);
        
        onNavigationChange({
          canGoBack: data.canGoBack,
          canGoForward: data.canGoForward,
          isLoading: false
        });
      });

      nativeAPI.onSecurityStateChanged((securityInfo) => {
        setSecurityInfo(securityInfo);
      });

      nativeAPI.onPerformanceUpdate((perfData) => {
        setPerformance(perfData);
      });

      console.log('✅ Native Chromium browser initialized');
    } catch (error) {
      console.error('❌ Failed to initialize native browser:', error);
    }
  };

  const navigateToUrl = async (url) => {
    if (!nativeAPI || !url) return;
    
    try {
      setIsLoading(true);
      const result = await nativeAPI.navigateTo(url);
      
      if (result.success) {
        console.log(`✅ Native navigation to ${url} successful`);
      } else {
        console.error(`❌ Native navigation failed: ${result.error}`);
      }
    } catch (error) {
      console.error('❌ Navigation error:', error);
      setIsLoading(false);
    }
  };

  const handleGoBack = async () => {
    if (nativeAPI && canGoBack) {
      await nativeAPI.browserBack();
    }
  };

  const handleGoForward = async () => {
    if (nativeAPI && canGoForward) {
      await nativeAPI.browserForward();
    }
  };

  const handleRefresh = async () => {
    if (nativeAPI) {
      await nativeAPI.browserRefresh();
    }
  };

  const toggleDevTools = async () => {
    if (nativeAPI) {
      if (devToolsOpen) {
        await nativeAPI.closeDevTools();
      } else {
        await nativeAPI.openDevTools();
      }
      setDevToolsOpen(!devToolsOpen);
    }
  };

  const captureScreenshot = async () => {
    if (nativeAPI) {
      try {
        const screenshot = await nativeAPI.captureScreenshot();
        console.log('📸 Screenshot captured:', screenshot);
        return screenshot;
      } catch (error) {
        console.error('❌ Screenshot failed:', error);
      }
    }
  };

  const executeJavaScript = async (script) => {
    if (nativeAPI) {
      try {
        const result = await nativeAPI.executeJavaScript(script);
        return result;
      } catch (error) {
        console.error('❌ JavaScript execution failed:', error);
      }
    }
  };

  const installExtension = async (extensionPath) => {
    if (nativeAPI) {
      try {
        const result = await nativeAPI.installExtension(extensionPath);
        console.log('🧩 Extension installed:', result);
        return result;
      } catch (error) {
        console.error('❌ Extension installation failed:', error);
      }
    }
  };

  return (
    <div className="native-browser-engine">
      {/* Native Browser Controls */}
      <div className="native-controls">
        <div className="navigation-controls">
          <button 
            className={`control-btn ${!canGoBack ? 'disabled' : ''}`}
            onClick={handleGoBack}
            disabled={!canGoBack}
            title="Go back"
          >
            ←
          </button>
          <button 
            className={`control-btn ${!canGoForward ? 'disabled' : ''}`}
            onClick={handleGoForward}
            disabled={!canGoForward}
            title="Go forward"
          >
            →
          </button>
          <button 
            className="control-btn"
            onClick={handleRefresh}
            title="Refresh"
          >
            {isLoading ? '⟳' : '↻'}
          </button>
        </div>

        <div className="browser-info">
          <div className={`security-badge ${securityInfo.isSecure ? 'secure' : 'insecure'}`}>
            {securityInfo.isSecure ? '🔒' : '⚠️'}
            <span>{securityInfo.isSecure ? 'Secure' : 'Not Secure'}</span>
          </div>
          
          <div className="performance-info">
            <span className="load-time">Load: {performance.loadTime}ms</span>
            <span className="memory-usage">Memory: {Math.round(performance.memoryUsage)}MB</span>
          </div>
        </div>

        <div className="developer-tools">
          <button 
            className={`control-btn ${devToolsOpen ? 'active' : ''}`}
            onClick={toggleDevTools}
            title="Toggle DevTools"
          >
            🔧
          </button>
          <button 
            className="control-btn"
            onClick={captureScreenshot}
            title="Capture Screenshot"
          >
            📸
          </button>
          <button 
            className={`control-btn ${extensionsEnabled ? 'active' : ''}`}
            onClick={() => setExtensionsEnabled(!extensionsEnabled)}
            title="Toggle Extensions"
          >
            🧩
          </button>
        </div>
      </div>

      {/* Native Browser Container */}
      <div 
        ref={browserRef}
        className="native-browser-container"
        style={{ 
          width: '100%', 
          height: 'calc(100% - 60px)',
          background: '#ffffff'
        }}
      >
        {isLoading && (
          <div className="native-loading-overlay">
            <div className="native-loading-spinner"></div>
            <div className="loading-info">
              <span>Loading with Native Chromium...</span>
              <div className="loading-progress">
                <div className="progress-bar"></div>
              </div>
            </div>
          </div>
        )}
        
        {!nativeAPI && (
          <div className="native-fallback">
            <div className="fallback-message">
              <h3>🔥 Native Chromium Engine</h3>
              <p>This feature requires the AETHER desktop application.</p>
              <p>Currently running in enhanced web mode.</p>
              <button 
                className="download-desktop-btn"
                onClick={() => window.open('https://github.com/aether-browser/desktop', '_blank')}
              >
                Download Desktop App
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Extension Management Panel */}
      {extensionsEnabled && (
        <div className="extensions-panel">
          <div className="panel-header">
            <h4>🧩 Extensions</h4>
          </div>
          <div className="extensions-list">
            <div className="extension-item">
              <span>uBlock Origin</span>
              <button className="toggle-extension">✅</button>
            </div>
            <div className="extension-item">
              <span>React DevTools</span>
              <button className="toggle-extension">✅</button>
            </div>
            <div className="extension-item">
              <span>AETHER Assistant</span>
              <button className="toggle-extension">✅</button>
            </div>
          </div>
          <button 
            className="install-extension-btn"
            onClick={() => document.getElementById('extension-input').click()}
          >
            + Install Extension
          </button>
          <input 
            id="extension-input"
            type="file" 
            accept=".crx,.zip"
            style={{ display: 'none' }}
            onChange={(e) => {
              if (e.target.files[0]) {
                installExtension(e.target.files[0].path);
              }
            }}
          />
        </div>
      )}
    </div>
  );
};

export default NativeBrowserEngine;