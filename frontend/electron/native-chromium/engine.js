const { BrowserView, session, webContents } = require('electron');
const path = require('path');
const fs = require('fs');

/**
 * Native Chromium Engine - Core Browser Engine Implementation
 * Provides full Chromium capabilities beyond iframe limitations
 */
class NativeChromiumEngine {
  constructor(options = {}) {
    this.options = {
      enableExtensions: options.enableExtensions || true,
      enableDevTools: options.enableDevTools || true,
      enableFileAccess: options.enableFileAccess || true,
      enableCrossOrigin: options.enableCrossOrigin || true,
      userAgent: options.userAgent || 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) AETHER/6.0.0 Chrome/120.0.0.0 Safari/537.36',
      ...options
    };

    this.browserView = null;
    this.mainWindow = null;
    this.currentUrl = null;
    this.navigationHistory = [];
    this.currentHistoryIndex = -1;
    
    // Native capabilities
    this.extensions = new Map();
    this.devToolsOpen = false;
    
    console.log('🔥 Native Chromium Engine Initialized');
  }

  async attachToWindow(window) {
    this.mainWindow = window;
    
    // Create native browser view with full Chromium capabilities
    this.browserView = new BrowserView({
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        enableRemoteModule: false,
        
        // Enable native Chromium features
        webSecurity: false, // Allow cross-origin requests
        allowRunningInsecureContent: true,
        experimentalFeatures: true,
        
        // Enable plugins and multimedia
        plugins: true,
        javascript: true,
        webgl: true,
        webaudio: true,
        
        // File system access
        nodeIntegrationInWorker: false,
        nodeIntegrationInSubFrames: false,
        
        // Custom user agent
        userAgent: this.options.userAgent
      }
    });

    // Attach browser view to window
    this.mainWindow.setBrowserView(this.browserView);
    
    // Set initial bounds (full window minus header)
    const bounds = this.mainWindow.getBounds();
    this.browserView.setBounds({
      x: 0,
      y: 120, // Leave space for AETHER UI header
      width: bounds.width,
      height: bounds.height - 120
    });

    // Setup native browser view event handlers
    this.setupBrowserViewEvents();
    
    // Configure session for enhanced capabilities
    await this.configureSession();
    
    console.log('✅ Native Chromium Engine Attached to Window');
    return { success: true };
  }

  setupBrowserViewEvents() {
    const webContents = this.browserView.webContents;

    // Navigation events
    webContents.on('did-start-loading', () => {
      this.sendToRenderer('navigation-started', { url: this.currentUrl });
    });

    webContents.on('did-finish-load', () => {
      this.sendToRenderer('navigation-completed', { 
        url: this.currentUrl,
        title: webContents.getTitle(),
        canGoBack: webContents.canGoBack(),
        canGoForward: webContents.canGoForward()
      });
    });

    webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
      this.sendToRenderer('navigation-failed', {
        url: validatedURL,
        error: errorDescription,
        errorCode
      });
    });

    // Title and favicon updates
    webContents.on('page-title-updated', (event, title) => {
      this.sendToRenderer('title-updated', { title, url: this.currentUrl });
    });

    webContents.on('page-favicon-updated', (event, favicons) => {
      this.sendToRenderer('favicon-updated', { favicons, url: this.currentUrl });
    });

    // Security and certificate events
    webContents.on('certificate-error', (event, url, error, certificate, callback) => {
      // Allow certificate errors for enhanced compatibility
      event.preventDefault();
      callback(true);
    });

    // New window handling
    webContents.setWindowOpenHandler(({ url, frameName, features, disposition }) => {
      // Handle new windows natively
      this.sendToRenderer('new-window-requested', { url, frameName, features, disposition });
      return { action: 'allow' };
    });

    // Download handling
    webContents.session.on('will-download', (event, item, webContents) => {
      this.sendToRenderer('download-started', {
        filename: item.getFilename(),
        url: item.getURL(),
        totalBytes: item.getTotalBytes()
      });
    });

    // Console messages (for debugging)
    webContents.on('console-message', (event, level, message, line, sourceId) => {
      if (this.options.enableDevTools) {
        console.log(`[Native Browser Console] ${level}: ${message}`);
      }
    });
  }

  async configureSession() {
    const ses = this.browserView.webContents.session;

    // Enable experimental web platform features
    await ses.setPermissionRequestHandler((webContents, permission, callback) => {
      // Grant all permissions for enhanced browsing (camera, microphone, etc.)
      callback(true);
    });

    // Configure cache for better performance
    await ses.clearCache();

    // Set custom headers for better compatibility
    ses.webRequest.onBeforeSendHeaders((details, callback) => {
      details.requestHeaders['User-Agent'] = this.options.userAgent;
      callback({ requestHeaders: details.requestHeaders });
    });

    console.log('✅ Native Session Configured');
  }

  async navigate(url) {
    if (!this.browserView) {
      return { success: false, error: 'Browser view not initialized' };
    }

    try {
      // Validate and clean URL
      let cleanUrl = url;
      if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://') && !cleanUrl.startsWith('file://')) {
        cleanUrl = `https://${cleanUrl}`;
      }

      this.currentUrl = cleanUrl;
      
      // Add to navigation history
      this.addToHistory(cleanUrl);
      
      // Navigate using native Chromium
      await this.browserView.webContents.loadURL(cleanUrl);
      
      console.log(`🔗 Native Navigation: ${cleanUrl}`);
      
      return { 
        success: true, 
        url: cleanUrl,
        canGoBack: this.browserView.webContents.canGoBack(),
        canGoForward: this.browserView.webContents.canGoForward()
      };
      
    } catch (error) {
      console.error('Native navigation error:', error);
      return { success: false, error: error.message };
    }
  }

  async goBack() {
    if (!this.browserView) {
      return { success: false };
    }

    try {
      if (this.browserView.webContents.canGoBack()) {
        await this.browserView.webContents.goBack();
        this.currentUrl = this.browserView.webContents.getURL();
        return { 
          success: true, 
          url: this.currentUrl,
          canGoBack: this.browserView.webContents.canGoBack(),
          canGoForward: this.browserView.webContents.canGoForward()
        };
      }
      return { success: false, error: 'Cannot go back' };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async goForward() {
    if (!this.browserView) {
      return { success: false };
    }

    try {
      if (this.browserView.webContents.canGoForward()) {
        await this.browserView.webContents.goForward();
        this.currentUrl = this.browserView.webContents.getURL();
        return { 
          success: true, 
          url: this.currentUrl,
          canGoBack: this.browserView.webContents.canGoBack(),
          canGoForward: this.browserView.webContents.canGoForward()
        };
      }
      return { success: false, error: 'Cannot go forward' };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async refresh() {
    if (!this.browserView) {
      return { success: false };
    }

    try {
      await this.browserView.webContents.reload();
      return { 
        success: true, 
        url: this.currentUrl 
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async captureScreenshot(options = {}) {
    if (!this.browserView) {
      return { success: false, error: 'Browser view not initialized' };
    }

    try {
      const image = await this.browserView.webContents.capturePage();
      const buffer = image.toPNG();
      
      // Save to file if path provided
      if (options.savePath) {
        fs.writeFileSync(options.savePath, buffer);
      }
      
      return {
        success: true,
        buffer: buffer,
        dataUrl: `data:image/png;base64,${buffer.toString('base64')}`,
        size: { width: image.getSize().width, height: image.getSize().height }
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async executeJavaScript(code) {
    if (!this.browserView) {
      return { success: false, error: 'Browser view not initialized' };
    }

    try {
      const result = await this.browserView.webContents.executeJavaScript(code);
      return { success: true, result };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async injectCSS(css) {
    if (!this.browserView) {
      return { success: false, error: 'Browser view not initialized' };
    }

    try {
      await this.browserView.webContents.insertCSS(css);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  addToHistory(url) {
    // Remove any forward history if we're not at the end
    if (this.currentHistoryIndex < this.navigationHistory.length - 1) {
      this.navigationHistory = this.navigationHistory.slice(0, this.currentHistoryIndex + 1);
    }
    
    this.navigationHistory.push(url);
    this.currentHistoryIndex = this.navigationHistory.length - 1;
  }

  sendToRenderer(event, data) {
    if (this.mainWindow && this.mainWindow.webContents) {
      this.mainWindow.webContents.send(event, data);
    }
  }

  async cleanup() {
    if (this.browserView) {
      // Clean up browser view
      this.browserView.webContents.destroy();
      this.browserView = null;
    }
    console.log('✅ Native Chromium Engine Cleanup Complete');
  }

  // Getters for current state
  getCurrentUrl() {
    return this.currentUrl;
  }

  getNavigationHistory() {
    return {
      history: this.navigationHistory,
      currentIndex: this.currentHistoryIndex
    };
  }

  canGoBack() {
    return this.browserView ? this.browserView.webContents.canGoBack() : false;
  }

  canGoForward() {
    return this.browserView ? this.browserView.webContents.canGoForward() : false;
  }
}

module.exports = NativeChromiumEngine;