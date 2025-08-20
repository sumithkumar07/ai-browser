const { app, BrowserWindow, ipcMain, webContents, Menu, shell, dialog, session } = require('electron');
const path = require('path');
const isDev = require('electron-is-dev');
const { autoUpdater } = require('electron-updater');
const windowStateKeeper = require('electron-window-state');

// Native Chromium Integration - Core Components
const NativeChromiumEngine = require('./native-chromium/engine');
const NativeAPIBridge = require('./native-chromium/api-bridge');
const DevToolsManager = require('./native-chromium/devtools-manager');
const ExtensionManager = require('./native-chromium/extension-manager');

class AETHERNativeApp {
  constructor() {
    this.mainWindow = null;
    this.nativeEngine = null;
    this.apiBridge = null;
    this.devToolsManager = null;
    this.extensionManager = null;
    this.isAppReady = false;
    
    // Initialize native components
    this.initializeNativeComponents();
    
    // Setup app event listeners
    this.setupAppEvents();
  }

  async initializeNativeComponents() {
    console.log('🔥 Initializing Native Chromium Components...');
    
    try {
      // Initialize Native Chromium Engine
      this.nativeEngine = new NativeChromiumEngine({
        enableExtensions: true,
        enableDevTools: true,
        enableFileAccess: true,
        enableCrossOrigin: true
      });
      
      // Initialize API Bridge for frontend communication
      this.apiBridge = new NativeAPIBridge(this.nativeEngine);
      
      // Initialize DevTools Manager
      this.devToolsManager = new DevToolsManager();
      
      // Initialize Extension Manager
      this.extensionManager = new ExtensionManager();
      
      console.log('✅ Native Chromium Components Initialized');
    } catch (error) {
      console.error('❌ Failed to initialize native components:', error);
    }
  }

  setupAppEvents() {
    // App ready event
    app.whenReady().then(() => {
      this.createMainWindow();
      this.setupNativeMenus();
      this.setupIpcHandlers();
      this.isAppReady = true;
    });

    // Window management
    app.on('window-all-closed', () => {
      if (process.platform !== 'darwin') {
        app.quit();
      }
    });

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        this.createMainWindow();
      }
    });

    // Security: Prevent new window creation
    app.on('web-contents-created', (event, contents) => {
      contents.on('new-window', (event, navigationUrl) => {
        event.preventDefault();
        shell.openExternal(navigationUrl);
      });
    });
  }

  async createMainWindow() {
    // Load window state
    let mainWindowState = windowStateKeeper({
      defaultWidth: 1920,
      defaultHeight: 1080
    });

    // Create the browser window with native Chromium capabilities
    this.mainWindow = new BrowserWindow({
      x: mainWindowState.x,
      y: mainWindowState.y,
      width: mainWindowState.width,
      height: mainWindowState.height,
      minWidth: 1200,
      minHeight: 800,
      webPreferences: {
        // Enable native capabilities
        nodeIntegration: true,
        contextIsolation: false,
        enableRemoteModule: true,
        webSecurity: false, // Allow cross-origin for native browsing
        allowRunningInsecureContent: true,
        experimentalFeatures: true,
        
        // Native Chromium features
        plugins: true,
        javascript: true,
        webgl: true,
        webaudio: true,
        
        // Enhanced sandbox with native access
        sandbox: false,
        
        // Preload script for native API injection
        preload: path.join(__dirname, 'preload.js')
      },
      show: false,
      frame: true,
      titleBarStyle: 'default',
      icon: path.join(__dirname, '../public/icon.png'),
      
      // Native window features
      transparent: false,
      hasShadow: true,
      vibrancy: 'dark'
    });

    // Let windowStateKeeper manage the main window
    mainWindowState.manage(this.mainWindow);

    // Load the app
    const startUrl = isDev 
      ? 'http://localhost:3000' 
      : `file://${path.join(__dirname, '../build/index.html')}`;
    
    await this.mainWindow.loadURL(startUrl);

    // Show window when ready
    this.mainWindow.once('ready-to-show', () => {
      this.mainWindow.show();
      
      // Focus for better UX
      if (isDev) {
        this.mainWindow.webContents.openDevTools();
      }
    });

    // Setup native engine with main window
    if (this.nativeEngine) {
      await this.nativeEngine.attachToWindow(this.mainWindow);
    }

    console.log('✅ AETHER Native Window Created');
  }

  setupNativeMenus() {
    const template = [
      {
        label: 'AETHER',
        submenu: [
          {
            label: 'About AETHER',
            click: () => {
              dialog.showMessageBox(this.mainWindow, {
                type: 'info',
                title: 'About AETHER',
                message: 'AETHER v6.0 - Native Chromium Browser',
                detail: 'AI-First Browser with Full Native Capabilities'
              });
            }
          },
          { type: 'separator' },
          { role: 'quit' }
        ]
      },
      {
        label: 'File',
        submenu: [
          {
            label: 'New Tab',
            accelerator: 'CmdOrCtrl+T',
            click: () => {
              this.mainWindow.webContents.send('native-new-tab');
            }
          },
          {
            label: 'New Window',
            accelerator: 'CmdOrCtrl+N',
            click: () => {
              this.createMainWindow();
            }
          },
          { type: 'separator' },
          {
            label: 'Open File',
            accelerator: 'CmdOrCtrl+O',
            click: async () => {
              const result = await dialog.showOpenDialog(this.mainWindow, {
                properties: ['openFile'],
                filters: [
                  { name: 'Web Files', extensions: ['html', 'htm'] },
                  { name: 'All Files', extensions: ['*'] }
                ]
              });
              
              if (!result.canceled && result.filePaths.length > 0) {
                const filePath = result.filePaths[0];
                this.mainWindow.webContents.send('native-navigate', `file://${filePath}`);
              }
            }
          }
        ]
      },
      {
        label: 'Edit',
        submenu: [
          { role: 'undo' },
          { role: 'redo' },
          { type: 'separator' },
          { role: 'cut' },
          { role: 'copy' },
          { role: 'paste' }
        ]
      },
      {
        label: 'View',
        submenu: [
          { role: 'reload' },
          { role: 'forceReload' },
          {
            label: 'Developer Tools',
            accelerator: 'F12',
            click: () => {
              this.mainWindow.webContents.toggleDevTools();
            }
          },
          { type: 'separator' },
          { role: 'resetzoom' },
          { role: 'zoomin' },
          { role: 'zoomout' },
          { type: 'separator' },
          { role: 'togglefullscreen' }
        ]
      },
      {
        label: 'Navigate',
        submenu: [
          {
            label: 'Back',
            accelerator: 'Alt+Left',
            click: () => {
              this.mainWindow.webContents.send('native-go-back');
            }
          },
          {
            label: 'Forward',
            accelerator: 'Alt+Right',
            click: () => {
              this.mainWindow.webContents.send('native-go-forward');
            }
          },
          {
            label: 'Refresh',
            accelerator: 'CmdOrCtrl+R',
            click: () => {
              this.mainWindow.webContents.send('native-refresh');
            }
          },
          { type: 'separator' },
          {
            label: 'Home',
            accelerator: 'Alt+Home',
            click: () => {
              this.mainWindow.webContents.send('native-navigate', 'aether://home');
            }
          }
        ]
      },
      {
        label: 'Extensions',
        submenu: [
          {
            label: 'Manage Extensions',
            click: () => {
              this.mainWindow.webContents.send('open-extensions-manager');
            }
          },
          {
            label: 'Install Extension',
            click: async () => {
              const result = await dialog.showOpenDialog(this.mainWindow, {
                properties: ['openDirectory'],
                title: 'Select Extension Directory'
              });
              
              if (!result.canceled && result.filePaths.length > 0) {
                const extensionPath = result.filePaths[0];
                await this.extensionManager.loadExtension(extensionPath);
              }
            }
          }
        ]
      },
      {
        label: 'Window',
        submenu: [
          { role: 'minimize' },
          { role: 'close' }
        ]
      }
    ];

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
  }

  setupIpcHandlers() {
    console.log('🔗 Setting up Native IPC Handlers...');

    // Native navigation
    ipcMain.handle('native-navigate', async (event, url) => {
      if (this.nativeEngine) {
        return await this.nativeEngine.navigate(url);
      }
      return { success: false, error: 'Native engine not available' };
    });

    // Native browser controls
    ipcMain.handle('native-go-back', async (event) => {
      if (this.nativeEngine) {
        return await this.nativeEngine.goBack();
      }
      return { success: false };
    });

    ipcMain.handle('native-go-forward', async (event) => {
      if (this.nativeEngine) {
        return await this.nativeEngine.goForward();
      }
      return { success: false };
    });

    ipcMain.handle('native-refresh', async (event) => {
      if (this.nativeEngine) {
        return await this.nativeEngine.refresh();
      }
      return { success: false };
    });

    // Native screenshot
    ipcMain.handle('native-screenshot', async (event, options = {}) => {
      if (this.nativeEngine) {
        return await this.nativeEngine.captureScreenshot(options);
      }
      return { success: false, error: 'Native engine not available' };
    });

    // DevTools management
    ipcMain.handle('native-open-devtools', async (event) => {
      if (this.devToolsManager) {
        return await this.devToolsManager.openDevTools();
      }
      return { success: false };
    });

    // Extension management
    ipcMain.handle('native-load-extension', async (event, extensionPath) => {
      if (this.extensionManager) {
        return await this.extensionManager.loadExtension(extensionPath);
      }
      return { success: false, error: 'Extension manager not available' };
    });

    ipcMain.handle('native-get-extensions', async (event) => {
      if (this.extensionManager) {
        return await this.extensionManager.getLoadedExtensions();
      }
      return { success: false, extensions: [] };
    });

    // File system access
    ipcMain.handle('native-show-open-dialog', async (event, options) => {
      return await dialog.showOpenDialog(this.mainWindow, options);
    });

    ipcMain.handle('native-show-save-dialog', async (event, options) => {
      return await dialog.showSaveDialog(this.mainWindow, options);
    });

    // Native capabilities check
    ipcMain.handle('native-get-capabilities', async (event) => {
      return {
        hasNativeChromium: true,
        hasExtensionSupport: true,
        hasDevTools: true,
        hasFileSystemAccess: true,
        hasCrossOriginAccess: true,
        version: '6.0.0',
        chromiumVersion: process.versions.chrome,
        electronVersion: process.versions.electron
      };
    });

    console.log('✅ Native IPC Handlers Ready');
  }

  // Cleanup on app quit
  async cleanup() {
    if (this.nativeEngine) {
      await this.nativeEngine.cleanup();
    }
    if (this.extensionManager) {
      await this.extensionManager.cleanup();
    }
  }
}

// Initialize AETHER Native App
const aetherApp = new AETHERNativeApp();

// Cleanup on quit
app.on('before-quit', async () => {
  await aetherApp.cleanup();
});

// Handle certificate errors for development
app.on('certificate-error', (event, webContents, url, error, certificate, callback) => {
  if (isDev) {
    // In development, ignore certificate errors
    event.preventDefault();
    callback(true);
  } else {
    callback(false);
  }
});

// Auto updater (for production)
if (!isDev) {
  autoUpdater.checkForUpdatesAndNotify();
}

console.log('🚀 AETHER Native Chromium App Starting...');