/**
 * Native Browser Engine Component
 * Replaces iframe with WebSocket-connected native Chromium engine
 * Provides Fellou.ai-level capabilities through enhanced backend bridge
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
  
  // Refs
  const canvasRef = useRef(null);
  const reconnectTimerRef = useRef(null);

  // Initialize native browser session
  const initializeNativeSession = useCallback(async () => {
    try {
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
        
        console.log('✅ Native browser session initialized:', result.session_id);
        return result.session_id;
      } else {
        throw new Error('Failed to create native session');
      }
    } catch (error) {
      console.error('Native session initialization error:', error);
      return null;
    }
  }, [backendUrl, sessionId]);

  // Initialize WebSocket connection for real-time control
  const initializeWebSocket = useCallback((sessionId) => {
    try {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${wsProtocol}//${window.location.host}/ws/native/${sessionId}`;
      
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('🔥 Native browser WebSocket connected');
        setIsConnected(true);
        setWebsocket(ws);
        
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
        
        // Attempt reconnection
        reconnectTimerRef.current = setTimeout(() => {
          if (nativeSessionId) {
            initializeWebSocket(nativeSessionId);
          }
        }, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

    } catch (error) {
      console.error('WebSocket initialization error:', error);
    }
  }, [nativeSessionId]);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((data) => {
    switch (data.type) {
      case 'connection_established':
        console.log('Native browser ready:', data.session_id);
        break;
        
      case 'navigation_complete':
        setIsLoading(false);
        onUrlChange(data.url);
        onNavigationChange({
          canGoBack: true, // TODO: Get from session state
          canGoForward: false, // TODO: Get from session state
          isLoading: false,
          title: data.title,
          securityInfo: data.security
        });
        
        // Request screenshot update
        requestScreenshot();
        break;
        
      case 'page_loaded':
        setIsLoading(false);
        onUrlChange(data.url);
        
        // Auto-capture screenshot on page load
        requestScreenshot();
        break;
        
      case 'screenshot_captured':
        if (data.success && data.screenshot) {
          setScreenshot(`data:image/jpeg;base64,${data.screenshot}`);
          renderScreenshotToCanvas(data.screenshot);
        }
        break;
        
      case 'performance_update':
        setPerformanceMetrics(data.metrics);
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
    
    try {
      websocket.send(JSON.stringify({
        action: 'navigate',
        url: url
      }));
      
      return true;
    } catch (error) {
      console.error('Navigation error:', error);
      setIsLoading(false);
      return false;
    }
  }, [websocket, isConnected]);

  // Request screenshot from native engine
  const requestScreenshot = useCallback(() => {
    if (websocket && isConnected) {
      websocket.send(JSON.stringify({
        action: 'screenshot',
        full_page: false,
        quality: 80
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
        if (data.messageId === messageId) {
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
      selector: selector
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
      text: text
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
        y: Math.round(y)
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

  // Auto-refresh screenshot every 5 seconds when idle
  useEffect(() => {
    const interval = setInterval(() => {
      if (isConnected && !isLoading) {
        requestScreenshot();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [isConnected, isLoading, requestScreenshot]);

  // Expose native browser API for parent components
  React.useImperativeHandle(React.forwardRef(), () => ({
    navigateToUrl,
    executeJavaScript,
    clickElement,
    typeText,
    requestScreenshot,
    capabilities,
    performanceMetrics,
    isConnected
  }), [navigateToUrl, executeJavaScript, clickElement, typeText, requestScreenshot, capabilities, performanceMetrics, isConnected]);

  return (
    <div className="native-browser-engine">
      {/* Connection Status */}
      <div className={`native-status ${isConnected ? 'connected' : 'disconnected'}`}>
        <div className="status-indicator">
          {isConnected ? '🔥' : '⚠️'}
        </div>
        <span className="status-text">
          {isConnected 
            ? `Native Chromium (${capabilities.length} capabilities)` 
            : 'Connecting to Native Engine...'
          }
        </span>
        {performanceMetrics.load_time && (
          <span className="performance-info">
            Load: {Math.round(performanceMetrics.load_time)}ms
          </span>
        )}
      </div>

      {/* Loading Overlay */}
      {isLoading && (
        <div className="native-loading-overlay">
          <div className="loading-spinner"></div>
          <div className="loading-text">Loading with Native Chromium...</div>
        </div>
      )}

      {/* Native Browser Canvas */}
      <div className="native-browser-canvas">
        {screenshot ? (
          <canvas
            ref={canvasRef}
            className="browser-canvas"
            onClick={handleCanvasClick}
            style={{
              width: '100%',
              height: 'auto',
              cursor: 'pointer',
              border: isConnected ? '2px solid #4CAF50' : '2px solid #ff9800'
            }}
            title="Native Chromium Browser - Click to interact"
          />
        ) : (
          <div className="canvas-placeholder">
            <div className="placeholder-icon">🌐</div>
            <div className="placeholder-text">
              {isConnected 
                ? 'Capturing browser view...' 
                : 'Connecting to Native Chromium Engine...'
              }
            </div>
          </div>
        )}
      </div>

      {/* Native Browser Controls */}
      {isConnected && (
        <div className="native-controls">
          <button 
            className="native-control-btn"
            onClick={() => executeJavaScript('window.history.back()')}
            title="Go Back"
          >
            ←
          </button>
          <button 
            className="native-control-btn"
            onClick={() => executeJavaScript('window.history.forward()')}
            title="Go Forward"
          >
            →
          </button>
          <button 
            className="native-control-btn"
            onClick={() => executeJavaScript('window.location.reload()')}
            title="Refresh"
          >
            ↻
          </button>
          <button 
            className="native-control-btn"
            onClick={requestScreenshot}
            title="Refresh View"
          >
            📷
          </button>
          <button 
            className="native-control-btn"
            onClick={() => executeJavaScript('window.scrollTo(0, 0)')}
            title="Scroll to Top"
          >
            ⬆️
          </button>
        </div>
      )}

      {/* Development Info */}
      {process.env.NODE_ENV === 'development' && isConnected && (
        <div className="dev-info">
          <div>Session: {nativeSessionId}</div>
          <div>Capabilities: {capabilities.join(', ')}</div>
          <div>WebSocket: {isConnected ? 'Connected' : 'Disconnected'}</div>
        </div>
      )}
    </div>
  );
};

export default NativeBrowserEngine;