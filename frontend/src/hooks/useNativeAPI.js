/**
 * Native API Hook - Complete Backend Integration
 * Seamless access to Native Chromium Engine capabilities
 * Full integration with server-side Playwright and WebSocket communication
 */

import { useState, useEffect, useCallback, useRef } from 'react';

const useNativeAPI = (backendUrl, sessionId) => {
  // Native API state
  const [nativeSessionId, setNativeSessionId] = useState(null);
  const [isNativeAvailable, setIsNativeAvailable] = useState(false);
  const [capabilities, setCapabilities] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [performanceMetrics, setPerformanceMetrics] = useState({});
  const [engineInfo, setEngineInfo] = useState({});
  
  // WebSocket connection
  const [websocket, setWebsocket] = useState(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  /**
   * Initialize Native Browser API Connection
   */
  const initializeNativeAPI = useCallback(async () => {
    try {
      setConnectionStatus('connecting');
      
      // Check native browser status first
      const statusResponse = await fetch(`${backendUrl}/api/native/status`);
      const statusData = await statusResponse.json();
      
      if (!statusData.native_available) {
        console.warn('❌ Native Chromium Engine not available');
        setIsNativeAvailable(false);
        setConnectionStatus('unavailable');
        return false;
      }

      setEngineInfo({
        engine_type: statusData.engine_type || 'playwright_chromium',
        version: statusData.version || '6.0.0',
        browser_ready: statusData.browser_ready || false,
        active_sessions: statusData.active_sessions || 0
      });

      // Create native browser session
      const sessionResponse = await fetch(`${backendUrl}/api/native/create-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_session: sessionId,
          user_agent: navigator.userAgent || 'AETHER-Native-Browser/6.0.0'
        })
      });

      if (sessionResponse.ok) {
        const sessionData = await sessionResponse.json();
        setNativeSessionId(sessionData.session_id);
        setCapabilities(sessionData.capabilities);
        setIsNativeAvailable(true);
        setConnectionStatus('connected');
        reconnectAttempts.current = 0;
        
        console.log('✅ Native API initialized:', sessionData.session_id);
        console.log('🔥 Capabilities:', sessionData.capabilities);
        return sessionData.session_id;
      } else {
        const errorData = await sessionResponse.json();
        throw new Error(errorData.detail || 'Failed to create native session');
      }
      
    } catch (error) {
      console.error('❌ Native API initialization error:', error);
      setIsNativeAvailable(false);
      setConnectionStatus('error');
      
      // Retry logic
      if (reconnectAttempts.current < maxReconnectAttempts) {
        reconnectAttempts.current++;
        console.log(`⚠️ Retrying... (${reconnectAttempts.current}/${maxReconnectAttempts})`);
        setTimeout(initializeNativeAPI, 3000);
      }
      
      return false;
    }
  }, [backendUrl, sessionId]);

  /**
   * Navigate to URL using native browser
   */
  const navigateTo = useCallback(async (url) => {
    if (!nativeSessionId) {
      console.warn('Native session not available for navigation');
      return { success: false, error: 'No native session' };
    }

    try {
      const response = await fetch(`${backendUrl}/api/native/navigate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: nativeSessionId,
          url: url,
          timeout: 30000
        })
      });

      if (response.ok) {
        const result = await response.json();
        
        // Update performance metrics
        setPerformanceMetrics(prev => ({
          ...prev,
          last_navigation: {
            url: result.url,
            load_time: result.load_time,
            timestamp: result.timestamp || new Date().toISOString(),
            status_code: result.status_code
          }
        }));

        console.log('🔥 Native navigation successful:', result.url);
        return result;
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Navigation failed');
      }
    } catch (error) {
      console.error('❌ Native navigation error:', error);
      return { success: false, error: error.message };
    }
  }, [backendUrl, nativeSessionId]);

  /**
   * Execute JavaScript in native browser
   */
  const executeScript = useCallback(async (script, args = []) => {
    if (!nativeSessionId) {
      return { success: false, error: 'No native session' };
    }

    try {
      const response = await fetch(`${backendUrl}/api/native/execute-js`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: nativeSessionId,
          script: script,
          args: args
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('📜 Script executed successfully');
        return result;
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Script execution failed');
      }
    } catch (error) {
      console.error('❌ Script execution error:', error);
      return { success: false, error: error.message };
    }
  }, [backendUrl, nativeSessionId]);

  /**
   * Capture screenshot using native browser
   */
  const captureScreenshot = useCallback(async (options = {}) => {
    if (!nativeSessionId) {
      return { success: false, error: 'No native session' };
    }

    try {
      const response = await fetch(`${backendUrl}/api/native/screenshot`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: nativeSessionId,
          full_page: options.full_page || false,
          quality: options.quality || 80
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('📷 Screenshot captured successfully');
        return result;
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Screenshot failed');
      }
    } catch (error) {
      console.error('❌ Screenshot error:', error);
      return { success: false, error: error.message };
    }
  }, [backendUrl, nativeSessionId]);

  /**
   * Click element using native browser
   */
  const clickElement = useCallback(async (selector, timeout = 5000) => {
    if (!nativeSessionId) {
      return { success: false, error: 'No native session' };
    }

    try {
      const response = await fetch(`${backendUrl}/api/native/click`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: nativeSessionId,
          selector: selector,
          timeout: timeout
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('👆 Element clicked successfully:', selector);
        return result;
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Click failed');
      }
    } catch (error) {
      console.error('❌ Click error:', error);
      return { success: false, error: error.message };
    }
  }, [backendUrl, nativeSessionId]);

  /**
   * Click at specific coordinates
   */
  const clickCoordinates = useCallback(async (x, y) => {
    if (!nativeSessionId) {
      return { success: false, error: 'No native session' };
    }

    try {
      const response = await fetch(`${backendUrl}/api/native/click`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: nativeSessionId,
          x: x,
          y: y
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('👆 Coordinate click successful:', { x, y });
        return result;
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Click failed');
      }
    } catch (error) {
      console.error('❌ Coordinate click error:', error);
      return { success: false, error: error.message };
    }
  }, [backendUrl, nativeSessionId]);

  /**
   * Type text using native browser
   */
  const typeText = useCallback(async (selector, text, clear = true) => {
    if (!nativeSessionId) {
      return { success: false, error: 'No native session' };
    }

    try {
      const response = await fetch(`${backendUrl}/api/native/type`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: nativeSessionId,
          selector: selector,
          text: text,
          clear: clear
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('⌨️ Text typed successfully:', selector);
        return result;
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Type failed');
      }
    } catch (error) {
      console.error('❌ Type error:', error);
      return { success: false, error: error.message };
    }
  }, [backendUrl, nativeSessionId]);

  /**
   * Get page content using native browser
   */
  const getPageContent = useCallback(async (includeHtml = false) => {
    if (!nativeSessionId) {
      return { success: false, error: 'No native session' };
    }

    try {
      const response = await fetch(`${backendUrl}/api/native/get-content`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: nativeSessionId,
          include_html: includeHtml
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('📄 Page content retrieved successfully');
        return result;
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Get content failed');
      }
    } catch (error) {
      console.error('❌ Get content error:', error);
      return { success: false, error: error.message };
    }
  }, [backendUrl, nativeSessionId]);

  /**
   * Get performance metrics
   */
  const getPerformanceMetrics = useCallback(async () => {
    if (!nativeSessionId) {
      return { success: false, error: 'No native session' };
    }

    try {
      const response = await fetch(`${backendUrl}/api/native/performance/${nativeSessionId}`);
      
      if (response.ok) {
        const result = await response.json();
        setPerformanceMetrics(prev => ({ ...prev, ...result.metrics }));
        return result;
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Get performance failed');
      }
    } catch (error) {
      console.error('❌ Performance metrics error:', error);
      return { success: false, error: error.message };
    }
  }, [backendUrl, nativeSessionId]);

  /**
   * Smart click using AI element detection (Computer Use API)
   */
  const smartClick = useCallback(async (description) => {
    if (!nativeSessionId) {
      return { success: false, error: 'No native session' };
    }

    try {
      const response = await fetch(`${backendUrl}/api/native/automation/smart-click`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: nativeSessionId,
          description: description
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('🎯 Smart click successful:', description);
        return result;
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Smart click failed');
      }
    } catch (error) {
      console.error('❌ Smart click error:', error);
      return { success: false, error: error.message };
    }
  }, [backendUrl, nativeSessionId]);

  /**
   * Extract structured data from page
   */
  const extractPageData = useCallback(async (dataType = 'general') => {
    if (!nativeSessionId) {
      return { success: false, error: 'No native session' };
    }

    try {
      const response = await fetch(`${backendUrl}/api/native/automation/extract-data`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: nativeSessionId,
          data_type: dataType
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('📊 Data extraction successful:', dataType);
        return result;
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Data extraction failed');
      }
    } catch (error) {
      console.error('❌ Data extraction error:', error);
      return { success: false, error: error.message };
    }
  }, [backendUrl, nativeSessionId]);

  /**
   * Browser navigation methods
   */
  const browserBack = useCallback(async () => {
    return await executeScript('window.history.back()');
  }, [executeScript]);

  const browserForward = useCallback(async () => {
    return await executeScript('window.history.forward()');
  }, [executeScript]);

  const browserRefresh = useCallback(async () => {
    return await executeScript('window.location.reload()');
  }, [executeScript]);

  /**
   * Check if native Chromium is available
   */
  const hasNativeChromium = useCallback(() => {
    return isNativeAvailable && connectionStatus === 'connected';
  }, [isNativeAvailable, connectionStatus]);

  /**
   * Get comprehensive status
   */
  const getStatus = useCallback(() => {
    return {
      isNativeAvailable,
      connectionStatus,
      nativeSessionId,
      capabilities,
      performanceMetrics,
      engineInfo,
      hasNativeChromium: hasNativeChromium()
    };
  }, [isNativeAvailable, connectionStatus, nativeSessionId, capabilities, performanceMetrics, engineInfo, hasNativeChromium]);

  /**
   * Cleanup native session
   */
  const cleanup = useCallback(async () => {
    if (nativeSessionId) {
      try {
        await fetch(`${backendUrl}/api/native/session/${nativeSessionId}`, {
          method: 'DELETE'
        });
        console.log('🧹 Native session cleaned up');
      } catch (error) {
        console.error('Cleanup error:', error);
      }
    }
    
    if (websocket) {
      websocket.close();
    }
    
    setNativeSessionId(null);
    setIsNativeAvailable(false);
    setConnectionStatus('disconnected');
  }, [backendUrl, nativeSessionId, websocket]);

  // Initialize on mount
  useEffect(() => {
    if (backendUrl && sessionId) {
      console.log('🔥 Initializing Native API...');
      initializeNativeAPI();
    }

    // Cleanup on unmount
    return () => {
      cleanup();
    };
  }, [backendUrl, sessionId, initializeNativeAPI, cleanup]);

  // Return comprehensive native API interface
  return {
    // Connection status
    isNativeAvailable,
    connectionStatus,
    nativeSessionId,
    capabilities,
    performanceMetrics,
    engineInfo,
    
    // Core browser methods
    navigateTo,
    executeScript,
    captureScreenshot,
    getPageContent,
    getPerformanceMetrics,
    
    // Interaction methods
    clickElement,
    clickCoordinates,
    typeText,
    smartClick,
    
    // Navigation methods
    browserBack,
    browserForward,
    browserRefresh,
    
    // Advanced methods
    extractPageData,
    
    // Utility methods
    hasNativeChromium,
    getStatus,
    initializeNativeAPI,
    cleanup
  };
};

export default useNativeAPI;