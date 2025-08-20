const { app, BrowserWindow, ipcMain, session, webContents } = require('electron');
const path = require('path');
const isDev = require('electron-is-dev');
const { autoUpdater } = require('electron-updater');

// Native Chromium Engine - Main Process
class NativeChromiumEngine {
  constructor() {
    this.mainWindow = null;
    this.browserViews = new Map();
    this.currentViewId = null;
    this.sessions = new Map();
    
    // Initialize native capabilities
    this.setupNativeCapabilities();
  }

  setupNativeCapabilities() {
    // Enable chrome extensions support
    app.commandLine.appendSwitch('--enable-chrome-browser-cloud-management');
    app.commandLine.appendSwitch('--enable-features', 'ElectronSerialChooser');
    
    // Enhanced security and compatibility
    app.commandLine.appendSwitch('--disable-web-security');
    app.commandLine.appendSwitch('--disable-features', 'OutOfBlinkCors');
    app.commandLine.appendSwitch('--allow-running-insecure-content');
    app.commandLine.appendSwitch('--ignore-certificate-errors');
  }

  async createMainWindow() {
    this.mainWindow = new BrowserWindow({
      width: 1400,
      height: 900,
      minWidth: 800,
      minHeight: 600,
      webPreferences: {
        nodeIntegration: true,
        contextIsolation: false,
        enableRemoteModule: true,
        webSecurity: false,
        allowRunningInsecureContent: true,
        experimentalFeatures: true
      },
      titleBarStyle: 'hidden',
      titleBarOverlay: {
        color: '#1a1a1a',
        symbolColor: '#8b5cf6'
      },
      icon: path.join(__dirname, 'assets', 'icon.png')
    });

    // Load AETHER interface
    const startUrl = isDev 
      ? 'http://localhost:3000' 
      : `file://${path.join(__dirname, '../frontend/build/index.html')}`;
    
    await this.mainWindow.loadURL(startUrl);

    // Setup IPC handlers
    this.setupIpcHandlers();
    
    // Inject native API
    await this.injectNativeAPI();

    if (isDev) {
      this.mainWindow.webContents.openDevTools({ mode: 'detach' });
    }

    return this.mainWindow;
  }

  async injectNativeAPI() {
    // Inject the native API into the renderer process
    await this.mainWindow.webContents.executeJavaScript(`
      window.nativeAPI = {
        // Core browser methods
        navigateTo: async (url) => {
          return new Promise((resolve) => {
            window.electronAPI.navigateTo(url).then(resolve);
          });
        },
        
        browserBack: async () => {
          return new Promise((resolve) => {
            window.electronAPI.browserBack().then(resolve);
          });
        },
        
        browserForward: async () => {
          return new Promise((resolve) => {
            window.electronAPI.browserForward().then(resolve);
          });
        },
        
        browserRefresh: async () => {
          return new Promise((resolve) => {
            window.electronAPI.browserRefresh().then(resolve);
          });
        },

        // Enhanced capabilities
        hasNativeChromium: () => true,
        
        executeJavaScript: async (code) => {
          return window.electronAPI.executeJavaScript(code);
        },
        
        captureScreenshot: async () => {
          return window.electronAPI.captureScreenshot();
        },
        
        openDevTools: () => {
          window.electronAPI.openDevTools();
        },
        
        installExtension: async (extensionPath) => {
          return window.electronAPI.installExtension(extensionPath);
        },
        
        // Platform integrations
        accessLocalFiles: async (path) => {
          return window.electronAPI.accessLocalFiles(path);
        },
        
        systemNotification: (title, body) => {
          window.electronAPI.systemNotification(title, body);
        }
      };

      // Expose electron API
      window.electronAPI = {
        navigateTo: (url) => window.electronIPC.invoke('navigate-to', url),
        browserBack: () => window.electronIPC.invoke('browser-back'),
        browserForward: () => window.electronIPC.invoke('browser-forward'), 
        browserRefresh: () => window.electronIPC.invoke('browser-refresh'),
        executeJavaScript: (code) => window.electronIPC.invoke('execute-js', code),
        captureScreenshot: () => window.electronIPC.invoke('capture-screenshot'),
        openDevTools: () => window.electronIPC.invoke('open-devtools'),
        installExtension: (path) => window.electronIPC.invoke('install-extension', path),
        accessLocalFiles: (path) => window.electronIPC.invoke('access-local-files', path),
        systemNotification: (title, body) => window.electronIPC.invoke('system-notification', title, body)
      };

      window.electronIPC = {
        invoke: (channel, ...args) => {
          return new Promise((resolve, reject) => {
            const callbackId = 'callback_' + Date.now() + '_' + Math.random();
            
            window.addEventListener(callbackId, (event) => {
              if (event.detail.error) {
                reject(new Error(event.detail.error));
              } else {
                resolve(event.detail.result);
              }
            }, { once: true });
            
            window.postMessage({
              type: 'ipc-invoke',
              channel: channel,
              args: args,
              callbackId: callbackId
            }, '*');
          });
        }
      };

      console.log('🔥 Native Chromium API injected successfully');
    `);
  }

  setupIpcHandlers() {
    // Navigation handlers
    ipcMain.handle('navigate-to', async (event, url) => {
      try {
        await this.navigateToUrl(url);
        return { success: true, url: url };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    ipcMain.handle('browser-back', async (event) => {
      try {
        const view = this.getCurrentBrowserView();
        if (view && view.webContents.canGoBack()) {
          view.webContents.goBack();
          return true;
        }
        return false;
      } catch (error) {
        return false;
      }
    });

    ipcMain.handle('browser-forward', async (event) => {
      try {
        const view = this.getCurrentBrowserView();
        if (view && view.webContents.canGoForward()) {
          view.webContents.goForward();
          return true;
        }
        return false;
      } catch (error) {
        return false;
      }
    });

    ipcMain.handle('browser-refresh', async (event) => {
      try {
        const view = this.getCurrentBrowserView();
        if (view) {
          view.webContents.reload();
          return true;
        }
        return false;
      } catch (error) {
        return false;
      }
    });

    // Enhanced capabilities handlers
    ipcMain.handle('execute-js', async (event, code) => {
      try {
        const view = this.getCurrentBrowserView();
        if (view) {
          const result = await view.webContents.executeJavaScript(code);
          return { success: true, result: result };
        }
        return { success: false, error: 'No active browser view' };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    ipcMain.handle('capture-screenshot', async (event) => {
      try {
        const view = this.getCurrentBrowserView();
        if (view) {
          const image = await view.webContents.capturePage();
          return { success: true, screenshot: image.toDataURL() };
        }
        return { success: false, error: 'No active browser view' };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    ipcMain.handle('open-devtools', async (event) => {
      try {
        const view = this.getCurrentBrowserView();
        if (view) {
          view.webContents.openDevTools({ mode: 'detach' });
          return { success: true };
        }
        return { success: false, error: 'No active browser view' };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    // System integration handlers
    ipcMain.handle('system-notification', async (event, title, body) => {
      try {
        const { Notification } = require('electron');
        new Notification({ title, body }).show();
        return { success: true };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    ipcMain.handle('install-extension', async (event, extensionPath) => {
      try {
        // Extension installation capability
        const extensionId = await session.defaultSession.loadExtension(extensionPath);
        return { success: true, extensionId: extensionId };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });
  }

  async navigateToUrl(url) {
    const { BrowserView } = require('electron');
    
    // Create or reuse browser view
    if (!this.currentViewId || !this.browserViews.has(this.currentViewId)) {
      const viewId = 'view_' + Date.now();
      const browserView = new BrowserView({
        webPreferences: {
          nodeIntegration: false,
          contextIsolation: true,
          enableRemoteModule: false,
          webSecurity: false,
          allowRunningInsecureContent: true,
          plugins: true,
          experimentalFeatures: true
        }
      });

      this.browserViews.set(viewId, browserView);
      this.currentViewId = viewId;
      this.mainWindow.setBrowserView(browserView);
      
      // Position the browser view (leave space for AETHER UI)
      const { width, height } = this.mainWindow.getBounds();
      browserView.setBounds({ x: 0, y: 120, width: width, height: height - 120 });
    }

    const browserView = this.browserViews.get(this.currentViewId);
    await browserView.webContents.loadURL(url);
    
    return browserView;
  }

  getCurrentBrowserView() {
    if (this.currentViewId && this.browserViews.has(this.currentViewId)) {
      return this.browserViews.get(this.currentViewId);
    }
    return null;
  }

  setupAutoUpdater() {
    if (!isDev) {
      autoUpdater.checkForUpdatesAndNotify();
      
      autoUpdater.on('update-available', () => {
        console.log('Update available');
      });

      autoUpdater.on('update-downloaded', () => {
        console.log('Update downloaded');
        autoUpdater.quitAndInstall();
      });
    }
  }
}

// Initialize native engine
const nativeEngine = new NativeChromiumEngine();

// App event handlers
app.whenReady().then(async () => {
  await nativeEngine.createMainWindow();
  nativeEngine.setupAutoUpdater();
  
  console.log('🚀 AETHER Native Chromium Engine started');
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', async () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    await nativeEngine.createMainWindow();
  }
});

// Enhanced session management
app.on('ready', () => {
  // Enable chrome extensions
  const extensions = [
    // Popular extensions can be loaded here
  ];
  
  // Setup enhanced session
  const ses = session.defaultSession;
  
  // Enable additional protocols
  ses.protocol.registerFileProtocol('aether', (request, callback) => {
    const url = request.url.substr(8);
    callback({ path: path.normalize(`${__dirname}/${url}`) });
  });
});

module.exports = nativeEngine;