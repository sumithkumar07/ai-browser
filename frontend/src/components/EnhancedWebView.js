import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  RefreshCw, 
  Shield, 
  AlertTriangle, 
  ExternalLink,
  Lock,
  Globe,
  Zap
} from 'lucide-react';

/**
 * Enhanced WebView Component - Phase 2: Browser Engine Enhancement
 * 
 * This component provides enhanced browsing capabilities beyond basic iframe,
 * approaching native browser functionality while working within web constraints.
 * 
 * Features:
 * - Enhanced security and error handling
 * - Better performance monitoring
 * - Advanced navigation controls  
 * - Real browser-like experience
 * - Security indicators and warnings
 */

const EnhancedWebView = ({ 
  url, 
  title, 
  onNavigate, 
  onTitleChange, 
  onSecurityChange,
  onPerformanceUpdate,
  isLoading,
  className = ""
}) => {
  const iframeRef = useRef(null);
  const [securityStatus, setSecurityStatus] = useState('unknown');
  const [performanceMetrics, setPerformanceMetrics] = useState({});
  const [errorState, setErrorState] = useState(null);
  const [loadStartTime, setLoadStartTime] = useState(null);
  const [canGoBack, setCanGoBack] = useState(false);
  const [canGoForward, setCanGoForward] = useState(false);
  
  // Enhanced security checking
  const checkSecurity = useCallback((targetUrl) => {
    if (!targetUrl) return 'unknown';
    
    try {
      const parsedUrl = new URL(targetUrl);
      
      // HTTPS check
      if (parsedUrl.protocol === 'https:') {
        setSecurityStatus('secure');
        return 'secure';
      } else if (parsedUrl.protocol === 'http:') {
        setSecurityStatus('warning');
        return 'warning';
      } else {
        setSecurityStatus('insecure');
        return 'insecure';
      }
    } catch (error) {
      setSecurityStatus('error');
      return 'error';
    }
  }, []);

  // Performance monitoring
  const measurePerformance = useCallback(() => {
    if (loadStartTime) {
      const loadTime = Date.now() - loadStartTime;
      const metrics = {
        loadTime,
        timestamp: new Date().toISOString(),
        url: url
      };
      
      setPerformanceMetrics(metrics);
      onPerformanceUpdate?.(metrics);
    }
  }, [loadStartTime, url, onPerformanceUpdate]);

  // Enhanced iframe event handlers
  useEffect(() => {
    const iframe = iframeRef.current;
    if (!iframe) return;

    const handleLoad = () => {
      measurePerformance();
      setErrorState(null);
      
      try {
        // Try to access iframe content for enhanced features
        // Note: This will be limited by CORS, but we can still get some info
        const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document;
        
        if (iframeDoc) {
          const actualTitle = iframeDoc.title;
          if (actualTitle && actualTitle !== title) {
            onTitleChange?.(actualTitle);
          }
        }
      } catch (error) {
        // CORS restriction - expected for external sites
        console.debug('Cross-origin content - limited access');
      }
    };

    const handleError = () => {
      setErrorState({
        type: 'load_error',
        message: 'Failed to load the requested page',
        url: url
      });
    };

    // Add event listeners
    iframe.addEventListener('load', handleLoad);
    iframe.addEventListener('error', handleError);

    return () => {
      iframe.removeEventListener('load', handleLoad);
      iframe.removeEventListener('error', handleError);
    };
  }, [url, title, onTitleChange, measurePerformance]);

  // URL change effect
  useEffect(() => {
    if (url) {
      setLoadStartTime(Date.now());
      const security = checkSecurity(url);
      onSecurityChange?.(security);
    }
  }, [url, checkSecurity, onSecurityChange]);

  // Enhanced navigation functions
  const refresh = useCallback(() => {
    if (iframeRef.current) {
      setLoadStartTime(Date.now());
      setErrorState(null);
      iframeRef.current.src = iframeRef.current.src; // Force reload
    }
  }, []);

  const openInNewTab = useCallback(() => {
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  }, [url]);

  // Security status component
  const SecurityIndicator = () => {
    const getSecurityConfig = () => {
      switch (securityStatus) {
        case 'secure':
          return {
            icon: Lock,
            color: 'text-green-600',
            bg: 'bg-green-50',
            border: 'border-green-200',
            text: 'Secure Connection'
          };
        case 'warning':
          return {
            icon: AlertTriangle,
            color: 'text-yellow-600',
            bg: 'bg-yellow-50',
            border: 'border-yellow-200',
            text: 'Insecure Connection'
          };
        case 'insecure':
          return {
            icon: AlertTriangle,
            color: 'text-red-600',
            bg: 'bg-red-50',
            border: 'border-red-200',
            text: 'Not Secure'
          };
        default:
          return {
            icon: Globe,
            color: 'text-gray-500',
            bg: 'bg-gray-50',
            border: 'border-gray-200',
            text: 'Loading...'
          };
      }
    };

    const config = getSecurityConfig();
    const Icon = config.icon;

    return (
      <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-medium border ${config.bg} ${config.border} ${config.color}`}>
        <Icon size={12} />
        <span>{config.text}</span>
      </div>
    );
  };

  // Performance indicator
  const PerformanceIndicator = () => {
    if (!performanceMetrics.loadTime) return null;

    const getPerformanceColor = (time) => {
      if (time < 1000) return 'text-green-600';
      if (time < 3000) return 'text-yellow-600';
      return 'text-red-600';
    };

    return (
      <div className={`flex items-center space-x-1 text-xs ${getPerformanceColor(performanceMetrics.loadTime)}`}>
        <Zap size={12} />
        <span>{performanceMetrics.loadTime}ms</span>
      </div>
    );
  };

  // Error state component
  if (errorState) {
    return (
      <div className={`enhanced-webview-error ${className}`}>
        <div className="flex flex-col items-center justify-center h-full bg-gray-50 rounded-lg">
          <AlertTriangle size={48} className="text-red-500 mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Unable to Load Page</h3>
          <p className="text-gray-600 mb-4 max-w-md text-center">{errorState.message}</p>
          <div className="flex space-x-3">
            <button 
              onClick={refresh}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              Try Again
            </button>
            <button 
              onClick={openInNewTab}
              className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
            >
              Open in New Tab
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`enhanced-webview-container ${className}`}>
      {/* Enhanced Controls Bar */}
      <div className="enhanced-webview-controls flex items-center justify-between p-3 bg-white border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <SecurityIndicator />
          <PerformanceIndicator />
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={refresh}
            disabled={isLoading}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            title="Refresh page"
          >
            <RefreshCw size={16} className={isLoading ? 'animate-spin' : ''} />
          </button>
          <button
            onClick={openInNewTab}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            title="Open in new tab"
          >
            <ExternalLink size={16} />
          </button>
        </div>
      </div>

      {/* Enhanced iframe with better attributes */}
      <div className="enhanced-webview-content relative flex-1">
        {isLoading && (
          <div className="absolute inset-0 bg-white bg-opacity-90 flex items-center justify-center z-10 backdrop-blur-sm">
            <div className="text-center">
              <div className="loading-dots mb-3">
                <div className="loading-dot"></div>
                <div className="loading-dot"></div>
                <div className="loading-dot"></div>
              </div>
              <p className="text-gray-600 font-medium">Loading enhanced browser content...</p>
              <div className="text-xs text-gray-500 mt-1">
                Enhanced WebView • Secure Rendering
              </div>
            </div>
          </div>
        )}
        
        <iframe
          ref={iframeRef}
          src={url}
          className="w-full h-full border-0"
          title={title}
          // Enhanced sandbox attributes for better security and functionality
          sandbox="allow-same-origin allow-scripts allow-forms allow-navigation allow-popups allow-popups-to-escape-sandbox allow-storage-access-by-user-activation"
          // Additional attributes for better compatibility
          loading="lazy"
          referrerPolicy="strict-origin-when-cross-origin"
          // Enhanced iframe attributes
          allow="camera; microphone; geolocation; encrypted-media; autoplay; clipboard-read; clipboard-write"
          // Security headers
          credentialless="true"
        />
      </div>
    </div>
  );
};

export default EnhancedWebView;