/**
 * Native Browser Engine Component - Complete Native Implementation
 * Full integration with backend Native Chromium Engine via WebSocket
 * NO IFRAME FALLBACK - Pure Native Chromium Only
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import './NativeBrowserEngine.css';

const NativeBrowserEngine = ({ 
  currentUrl, 
  onUrlChange, 
  onNavigationChange, 
  sessionId,
  backendUrl 
}) => {
  // Native browser state
  const [nativeSessionId, setNativeSessionId] = useState(null);
  const [websocket, setWebsocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [screenshot, setScreenshot] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [capabilities, setCapabilities] = useState([]);
  const [performanceMetrics, setPerformanceMetrics] = useState({});
  const [engineStatus, setEngineStatus] = useState('disconnected');
  const [errorMessage, setErrorMessage] = useState(null);
  
  // Refs
  const canvasRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  // Initialize native browser session
  const initializeNativeSession = useCallback(async () => {
    try {
      setEngineStatus('initializing');
      setErrorMessage(null);
      
      const response = await fetch(`${backendUrl}/api/native/create-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_session: sessionId,
          user_agent: navigator.userAgent
        })
      });

      if (response.ok) {
        const result = await response.json();
        setNativeSessionId(result.session_id);
        setCapabilities(result.capabilities);
        
        // Initialize WebSocket connection
        initializeWebSocket(result.session_id);
        
        setEngineStatus('connected');
        console.log('✅ Native browser session initialized:', result.session_id);
        return result.session_id;
      } else {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }
    } catch (error) {
      console.error('Native session initialization error:', error);
      setEngineStatus('error');
      setErrorMessage(error.message);
      
      // Retry initialization
      if (reconnectAttempts.current < maxReconnectAttempts) {
        reconnectAttempts.current++;
        console.log(`Retrying initialization... (${reconnectAttempts.current}/${maxReconnectAttempts})`);
        setTimeout(initializeNativeSession, 3000);
      }
      
      return null;
    }
  }, [backendUrl, sessionId]);

  // Initialize WebSocket connection for real-time control
  const initializeWebSocket = useCallback((sessionId) => {
    try {
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.close();
      }
      
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = new URL(backendUrl).host;
      const wsUrl = `${wsProtocol}//${wsHost}/ws/native/${sessionId}`;
      
      console.log('🔗 Connecting to WebSocket:', wsUrl);
      
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('🔥 Native browser WebSocket connected');
        setIsConnected(true);
        setWebsocket(ws);
        setEngineStatus('operational');
        reconnectAttempts.current = 0;
        
        // Send initial status request
        ws.send(JSON.stringify({
          action: 'get_status'
        }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('WebSocket message parse error:', error);
        }
      };

      ws.onclose = () => {
        console.log('Native browser WebSocket disconnected');
        setIsConnected(false);
        setWebsocket(null);
        setEngineStatus('disconnected');
        
        // Attempt reconnection if not max attempts
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectTimerRef.current = setTimeout(() => {
            if (nativeSessionId) {
              reconnectAttempts.current++;
              initializeWebSocket(nativeSessionId);
            }
          }, 3000);
        } else {
          setEngineStatus('error');
          setErrorMessage('Maximum reconnection attempts reached');
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setEngineStatus('error');
        setErrorMessage('WebSocket connection failed');
      };

    } catch (error) {
      console.error('WebSocket initialization error:', error);
      setEngineStatus('error');
      setErrorMessage('Failed to initialize WebSocket');
    }
  }, [backendUrl, nativeSessionId, websocket]);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((data) => {
    console.log('📨 WebSocket message:', data.type);
    
    switch (data.type) {
      case 'connection_established':
        console.log('✅ Native browser ready:', data.session_id);
        setIsConnected(true);
        setEngineStatus('operational');
        break;
        
      case 'navigation_complete':
      case 'navigation_result':
        if (data.result?.success || data.success) {
          setIsLoading(false);
          const url = data.url || data.result?.url;
          const title = data.title || data.result?.title;
          
          if (url) onUrlChange(url);
          
          onNavigationChange({
            canGoBack: true,
            canGoForward: false,
            isLoading: false,
            title: title,
            securityInfo: data.security
          });
          
          // Request screenshot update
          requestScreenshot();
        }
        break;
        
      case 'page_loaded':
        setIsLoading(false);
        if (data.url) onUrlChange(data.url);
        requestScreenshot();
        break;
        
      case 'screenshot_captured':
        if (data.success && data.screenshot) {
          setScreenshot(`data:image/jpeg;base64,${data.screenshot}`);
          renderScreenshotToCanvas(data.screenshot);
        }
        break;
        
      case 'performance_result':
      case 'performance_update':
        const metrics = data.result?.metrics || data.metrics;
        if (metrics) {
          setPerformanceMetrics(metrics);
        }
        break;
        
      case 'status_response':
        if (data.status) {
          console.log('Native browser status:', data.status);
        }
        break;
        
      case 'error':
        console.error('Native browser error:', data.error || data.message);
        setErrorMessage(data.error || data.message);
        break;
        
      default:
        console.log('Unknown WebSocket message:', data);
    }
  }, [onUrlChange, onNavigationChange]);

  // Navigate to URL using native engine
  const navigateToUrl = useCallback(async (url) => {
    if (!websocket || !isConnected) {
      console.error('Native browser not connected');
      return false;
    }

    setIsLoading(true);
    setErrorMessage(null);
    
    try {
      websocket.send(JSON.stringify({
        action: 'navigate',
        url: url,
        messageId: `nav_${Date.now()}`
      }));
      
      return true;
    } catch (error) {
      console.error('Navigation error:', error);
      setIsLoading(false);
      setErrorMessage('Navigation failed');
      return false;
    }
  }, [websocket, isConnected]);

  // Request screenshot from native engine
  const requestScreenshot = useCallback(() => {
    if (websocket && isConnected) {
      websocket.send(JSON.stringify({
        action: 'screenshot',
        full_page: false,
        quality: 80,
        messageId: `screenshot_${Date.now()}`
      }));
    }
  }, [websocket, isConnected]);

  // Execute JavaScript in native browser
  const executeJavaScript = useCallback(async (script, args = []) => {
    if (!websocket || !isConnected) {
      return { success: false, error: 'Not connected' };
    }

    return new Promise((resolve) => {
      const messageId = `js_${Date.now()}`;
      
      const handleResponse = (event) => {
        const data = JSON.parse(event.data);
        if (data.messageId === messageId && data.type === 'js_result') {
          websocket.removeEventListener('message', handleResponse);
          resolve(data);
        }
      };

      websocket.addEventListener('message', handleResponse);
      
      websocket.send(JSON.stringify({
        action: 'execute_js',
        messageId: messageId,
        script: script,
        args: args
      }));
      
      // Timeout after 10 seconds
      setTimeout(() => {
        websocket.removeEventListener('message', handleResponse);
        resolve({ success: false, error: 'Timeout' });
      }, 10000);
    });
  }, [websocket, isConnected]);

  // Click element in native browser
  const clickElement = useCallback(async (selector) => {
    if (!websocket || !isConnected) {
      return { success: false, error: 'Not connected' };
    }

    websocket.send(JSON.stringify({
      action: 'click',
      selector: selector,
      messageId: `click_${Date.now()}`
    }));

    // Request updated screenshot after click
    setTimeout(requestScreenshot, 1000);
    
    return { success: true };
  }, [websocket, isConnected, requestScreenshot]);

  // Type text in native browser
  const typeText = useCallback(async (selector, text) => {
    if (!websocket || !isConnected) {
      return { success: false, error: 'Not connected' };
    }

    websocket.send(JSON.stringify({
      action: 'type',
      selector: selector,
      text: text,
      messageId: `type_${Date.now()}`
    }));

    // Request updated screenshot after typing
    setTimeout(requestScreenshot, 1000);
    
    return { success: true };
  }, [websocket, isConnected, requestScreenshot]);

  // Render screenshot to canvas with click handling
  const renderScreenshotToCanvas = useCallback((screenshotBase64) => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const img = new Image();

    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);
    };

    img.src = `data:image/jpeg;base64,${screenshotBase64}`;
  }, []);

  // Handle canvas clicks (convert to browser coordinates)
  const handleCanvasClick = useCallback(async (event) => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    
    // Calculate click coordinates relative to canvas
    const x = ((event.clientX - rect.left) / rect.width) * canvas.width;
    const y = ((event.clientY - rect.top) / rect.height) * canvas.height;

    // Send click coordinates to native browser
    if (websocket && isConnected) {
      websocket.send(JSON.stringify({
        action: 'click_coordinates',
        x: Math.round(x),
        y: Math.round(y),
        messageId: `click_coords_${Date.now()}`
      }));

      // Request updated screenshot
      setTimeout(requestScreenshot, 1000);
    }
  }, [websocket, isConnected, requestScreenshot]);

  // Initialize when component mounts
  useEffect(() => {
    initializeNativeSession();
    
    return () => {
      // Cleanup
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      if (websocket) {
        websocket.close();
      }
    };
  }, [initializeNativeSession]);

  // Navigate when currentUrl changes
  useEffect(() => {
    if (currentUrl && isConnected) {
      navigateToUrl(currentUrl);
    }
  }, [currentUrl, isConnected, navigateToUrl]);

  // Auto-refresh screenshot every 10 seconds when idle
  useEffect(() => {
    if (!isConnected || isLoading) return;
    
    const interval = setInterval(() => {
      requestScreenshot();
    }, 10000);

    return () => clearInterval(interval);
  }, [isConnected, isLoading, requestScreenshot]);

  // Get status indicator color
  const getStatusColor = () => {
    switch (engineStatus) {
      case 'operational': return '#4CAF50';
      case 'connected': return '#2196F3';
      case 'initializing': return '#FF9800';
      case 'disconnected': return '#757575';
      case 'error': return '#f44336';
      default: return '#757575';
    }
  };

  // Expose native browser API for parent components
  React.useImperativeHandle(React.forwardRef(), () => ({
    navigateToUrl,
    executeJavaScript,
    clickElement,
    typeText,
    requestScreenshot,
    capabilities,
    performanceMetrics,
    isConnected,
    engineStatus
  }), [navigateToUrl, executeJavaScript, clickElement, typeText, requestScreenshot, capabilities, performanceMetrics, isConnected, engineStatus]);

  return (
    <div className="native-browser-engine">
      {/* Connection Status */}
      <div className={`native-status status-${engineStatus}`} style={{ borderLeft: `4px solid ${getStatusColor()}` }}>
        <div className="status-indicator">
          {engineStatus === 'operational' ? '🔥' : 
           engineStatus === 'connected' ? '🔗' :
           engineStatus === 'initializing' ? '⏳' :
           engineStatus === 'error' ? '❌' : '⚠️'}
        </div>
        <span className="status-text">
          {engineStatus === 'operational' 
            ? `Native Chromium Engine (${capabilities.length} capabilities)` 
            : engineStatus === 'connected'
            ? 'Native Engine Connected'
            : engineStatus === 'initializing'
            ? 'Initializing Native Chromium...'
            : engineStatus === 'error'
            ? `Error: ${errorMessage || 'Unknown error'}`
            : 'Connecting to Native Engine...'}
        </span>
        {performanceMetrics.load_time && (
          <span className="performance-info">
            Load: {Math.round(performanceMetrics.load_time)}ms
          </span>
        )}
        {nativeSessionId && (
          <span className="session-info">
            Session: {nativeSessionId.slice(-8)}
          </span>
        )}
      </div>

      {/* Loading Overlay */}
      {isLoading && (
        <div className="native-loading-overlay">
          <div className="loading-spinner"></div>
          <div className="loading-text">Loading with Native Chromium Engine...</div>
          <div className="loading-subtext">Playwright-powered browsing</div>
        </div>
      )}

      {/* Error Display */}
      {engineStatus === 'error' && (
        <div className="native-error-display">
          <div className="error-icon">⚠️</div>
          <div className="error-title">Native Engine Error</div>
          <div className="error-message">{errorMessage}</div>
          <button 
            className="error-retry-btn"
            onClick={() => {
              reconnectAttempts.current = 0;
              initializeNativeSession();
            }}
          >
            Retry Connection
          </button>
        </div>
      )}

      {/* Native Browser Canvas */}
      <div className="native-browser-canvas">
        {screenshot && engineStatus === 'operational' ? (
          <div className="canvas-container">
            <canvas
              ref={canvasRef}
              className="browser-canvas"
              onClick={handleCanvasClick}
              style={{
                width: '100%',
                height: 'auto',
                cursor: 'pointer',
                border: `2px solid ${getStatusColor()}`,
                borderRadius: '4px'
              }}
              title="Native Chromium Browser - Click to interact"
            />
            <div className="canvas-overlay">
              <div className="canvas-info">
                🔥 Live Native Chromium View
              </div>
            </div>
          </div>
        ) : (
          <div className="canvas-placeholder">
            <div className="placeholder-icon">
              {engineStatus === 'operational' ? '🌐' : 
               engineStatus === 'initializing' ? '⚙️' : '🔧'}
            </div>
            <div className="placeholder-text">
              {engineStatus === 'operational' 
                ? 'Capturing native browser view...' 
                : engineStatus === 'initializing'
                ? 'Starting Native Chromium Engine...'
                : engineStatus === 'error'
                ? 'Native Engine Unavailable'
                : 'Connecting to Native Chromium...'}
            </div>
            {engineStatus === 'operational' && (
              <button 
                className="capture-btn"
                onClick={requestScreenshot}
              >
                📷 Capture View
              </button>
            )}
          </div>
        )}
      </div>

      {/* Native Browser Controls */}
      {isConnected && engineStatus === 'operational' && (
        <div className="native-controls">
          <button 
            className="native-control-btn"
            onClick={() => executeJavaScript('window.history.back()')}
            title="Go Back"
            disabled={isLoading}
          >
            ← Back
          </button>
          <button 
            className="native-control-btn"
            onClick={() => executeJavaScript('window.history.forward()')}
            title="Go Forward"
            disabled={isLoading}
          >
            Forward →
          </button>
          <button 
            className="native-control-btn"
            onClick={() => executeJavaScript('window.location.reload()')}
            title="Refresh"
            disabled={isLoading}
          >
            ↻ Refresh
          </button>
          <button 
            className="native-control-btn"
            onClick={requestScreenshot}
            title="Update View"
          >
            📷 Capture
          </button>
          <button 
            className="native-control-btn"
            onClick={() => executeJavaScript('window.scrollTo(0, 0)')}
            title="Scroll to Top"
            disabled={isLoading}
          >
            ⬆️ Top
          </button>
        </div>
      )}

      {/* Development Info */}
      {process.env.NODE_ENV === 'development' && isConnected && (
        <div className="dev-info">
          <div><strong>Session:</strong> {nativeSessionId}</div>
          <div><strong>Status:</strong> {engineStatus}</div>
          <div><strong>Capabilities:</strong> {capabilities.join(', ')}</div>
          <div><strong>WebSocket:</strong> {isConnected ? 'Connected' : 'Disconnected'}</div>
          <div><strong>Screenshot:</strong> {screenshot ? 'Available' : 'None'}</div>
        </div>
      )}
    </div>
  );
};

export default NativeBrowserEngine;