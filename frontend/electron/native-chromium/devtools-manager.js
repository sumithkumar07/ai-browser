const { BrowserWindow } = require('electron');

/**
 * DevTools Manager - Native Chrome DevTools Integration
 * Provides full Chrome DevTools access for debugging and development
 */
class DevToolsManager {
  constructor() {
    this.devToolsWindows = new Map();
    this.protocolClients = new Map();
    
    console.log('🔧 DevTools Manager Initialized');
  }

  async openDevTools(webContentsId, options = {}) {
    try {
      const { webContents } = require('electron');
      const targetWebContents = webContents.fromId(webContentsId) || 
                                webContents.getAllWebContents()[0];

      if (!targetWebContents) {
        return { success: false, error: 'No web contents found' };
      }

      // Configure DevTools options
      const devToolsOptions = {
        mode: options.mode || 'detach', // 'detach', 'right', 'bottom', 'undocked'
        activate: options.activate !== false
      };

      // Open DevTools
      targetWebContents.openDevTools(devToolsOptions);

      // Store reference
      this.devToolsWindows.set(webContentsId, {
        webContents: targetWebContents,
        options: devToolsOptions,
        opened: Date.now()
      });

      console.log(`🔧 DevTools opened for WebContents ID: ${webContentsId}`);

      return {
        success: true,
        webContentsId,
        mode: devToolsOptions.mode
      };

    } catch (error) {
      console.error('DevTools open error:', error);
      return { success: false, error: error.message };
    }
  }

  async closeDevTools(webContentsId) {
    try {
      const devToolsInfo = this.devToolsWindows.get(webContentsId);
      
      if (devToolsInfo && devToolsInfo.webContents) {
        devToolsInfo.webContents.closeDevTools();
        this.devToolsWindows.delete(webContentsId);
        
        return { success: true };
      }
      
      return { success: false, error: 'DevTools not open for this WebContents' };
      
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async executeDevToolsCommand(webContentsId, command, params = {}) {
    try {
      const devToolsInfo = this.devToolsWindows.get(webContentsId);
      
      if (!devToolsInfo || !devToolsInfo.webContents) {
        return { success: false, error: 'DevTools not open' };
      }

      // Enable Chrome DevTools Protocol
      const debugger = devToolsInfo.webContents.debugger;
      
      if (!debugger.isAttached()) {
        try {
          debugger.attach('1.3');
        } catch (error) {
          console.warn('Debugger already attached or failed to attach');
        }
      }

      // Execute DevTools Protocol command
      const result = await debugger.sendCommand(command, params);
      
      return {
        success: true,
        command,
        result
      };

    } catch (error) {
      console.error('DevTools command error:', error);
      return { success: false, error: error.message };
    }
  }

  // Advanced DevTools Features

  async enableNetworkDomain(webContentsId) {
    return await this.executeDevToolsCommand(webContentsId, 'Network.enable');
  }

  async enableRuntimeDomain(webContentsId) {
    return await this.executeDevToolsCommand(webContentsId, 'Runtime.enable');
  }

  async enablePageDomain(webContentsId) {
    return await this.executeDevToolsCommand(webContentsId, 'Page.enable');
  }

  async getNetworkRequests(webContentsId) {
    try {
      // Enable network domain first
      await this.enableNetworkDomain(webContentsId);
      
      // Get network requests (this would need to be tracked over time)
      return {
        success: true,
        message: 'Network monitoring enabled. Use DevTools to view requests.'
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async captureScreenshot(webContentsId, options = {}) {
    try {
      const screenshotOptions = {
        format: options.format || 'png',
        quality: options.quality || 100,
        clip: options.clip || undefined,
        fromSurface: options.fromSurface || true
      };

      const result = await this.executeDevToolsCommand(
        webContentsId, 
        'Page.captureScreenshot', 
        screenshotOptions
      );

      if (result.success) {
        return {
          success: true,
          data: result.result.data,
          format: screenshotOptions.format
        };
      }

      return result;
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async evaluateJavaScript(webContentsId, expression, options = {}) {
    try {
      const evalOptions = {
        expression,
        returnByValue: options.returnByValue !== false,
        awaitPromise: options.awaitPromise || false,
        userGesture: options.userGesture || false
      };

      const result = await this.executeDevToolsCommand(
        webContentsId,
        'Runtime.evaluate',
        evalOptions
      );

      if (result.success) {
        return {
          success: true,
          result: result.result.result.value,
          type: result.result.result.type
        };
      }

      return result;
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async getPageSource(webContentsId) {
    try {
      const result = await this.executeDevToolsCommand(
        webContentsId,
        'Runtime.evaluate',
        { expression: 'document.documentElement.outerHTML', returnByValue: true }
      );

      if (result.success) {
        return {
          success: true,
          source: result.result.result.value
        };
      }

      return result;
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async getCookies(webContentsId, urls = []) {
    try {
      const result = await this.executeDevToolsCommand(
        webContentsId,
        'Network.getCookies',
        urls.length > 0 ? { urls } : {}
      );

      if (result.success) {
        return {
          success: true,
          cookies: result.result.cookies
        };
      }

      return result;
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async clearCache(webContentsId) {
    try {
      const result = await this.executeDevToolsCommand(
        webContentsId,
        'Network.clearBrowserCache'
      );

      return result;
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async emulateDevice(webContentsId, device = {}) {
    try {
      const deviceOptions = {
        width: device.width || 1920,
        height: device.height || 1080,
        deviceScaleFactor: device.deviceScaleFactor || 1,
        mobile: device.mobile || false,
        fitWindow: device.fitWindow || false
      };

      const result = await this.executeDevToolsCommand(
        webContentsId,
        'Emulation.setDeviceMetricsOverride',
        deviceOptions
      );

      return result;
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Performance Monitoring
  async enablePerformanceMonitoring(webContentsId) {
    try {
      await this.executeDevToolsCommand(webContentsId, 'Performance.enable');
      const result = await this.executeDevToolsCommand(webContentsId, 'Performance.getMetrics');
      
      return {
        success: true,
        message: 'Performance monitoring enabled',
        metrics: result.success ? result.result.metrics : []
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Console API
  async getConsoleMessages(webContentsId) {
    try {
      await this.executeDevToolsCommand(webContentsId, 'Console.enable');
      
      return {
        success: true,
        message: 'Console monitoring enabled. Messages will be logged.'
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Status and Management
  isDevToolsOpen(webContentsId) {
    return this.devToolsWindows.has(webContentsId);
  }

  getOpenDevTools() {
    return Array.from(this.devToolsWindows.keys());
  }

  async closeAllDevTools() {
    const promises = Array.from(this.devToolsWindows.keys()).map(id => 
      this.closeDevTools(id)
    );
    
    const results = await Promise.all(promises);
    
    return {
      success: true,
      closed: results.filter(r => r.success).length,
      total: results.length
    };
  }

  cleanup() {
    // Close all DevTools windows
    this.devToolsWindows.forEach((info, webContentsId) => {
      try {
        if (info.webContents && !info.webContents.isDestroyed()) {
          info.webContents.closeDevTools();
        }
      } catch (error) {
        console.error('Error closing DevTools during cleanup:', error);
      }
    });

    this.devToolsWindows.clear();
    this.protocolClients.clear();
    
    console.log('✅ DevTools Manager Cleanup Complete');
  }
}

module.exports = DevToolsManager;