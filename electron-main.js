const { app, BrowserWindow, BrowserView, ipcMain, Menu, dialog, shell } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const isDev = process.env.ELECTRON_IS_DEV === '1';
const Store = require('electron-store');

// Enhanced Store for native Chromium features
const store = new Store({
  defaults: {
    windowBounds: { width: 1400, height: 900 },
    browserSettings: {
      enableExtensions: true,
      enableDevTools: true,
      enableWebSecurity: false, // For cross-origin access
      enableNodeIntegration: false
    },
    aiSettings: {
      proactiveMode: true,
      behavioralLearning: true,
      commandMode: 'single-box'
    }
  }
});

class AetherNativeBrowser {
  constructor() {
    this.mainWindow = null;
    this.browserView = null;
    this.backendProcess = null;
    this.isReady = false;
    
    // Native Chromium session management
    this.sessions = new Map();
    this.extensions = new Map();
  }

  async initialize() {
    await app.whenReady();
    this.createMainWindow();
    this.setupNativeChromium();
    this.startBackendProcess();
    this.setupIPC();
    this.setupMenu();
    
    console.log('🔥 AETHER Native Browser initialized with Chromium engine');
  }

  createMainWindow() {
    const bounds = store.get('windowBounds');
    
    this.mainWindow = new BrowserWindow({
      ...bounds,
      minWidth: 1200,
      minHeight: 800,
      show: false,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        enableRemoteModule: false,
        preload: path.join(__dirname, 'electron-preload.js'),
        webSecurity: false, // Enable cross-origin access like Fellou.ai
        allowRunningInsecureContent: true
      },
      titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
      icon: path.join(__dirname, 'assets', 'icon.png')
    });

    // Load the React frontend
    const frontendUrl = isDev ? 'http://localhost:3000' : `file://${path.join(__dirname, 'frontend/build/index.html')}`;
    this.mainWindow.loadURL(frontendUrl);

    // Show window when ready
    this.mainWindow.once('ready-to-show', () => {
      this.mainWindow.show();
      if (isDev) {
        this.mainWindow.webContents.openDevTools();
      }
      this.isReady = true;
    });

    // Save window bounds
    this.mainWindow.on('close', () => {
      store.set('windowBounds', this.mainWindow.getBounds());
    });

    return this.mainWindow;
  }

  setupNativeChromium() {
    const { session } = require('electron');
    
    // Create enhanced browsing session with Chromium features
    const browserSession = session.fromPartition('persist:main-browser', {
      cache: true
    });

    // Enable Chrome extensions support
    if (store.get('browserSettings.enableExtensions')) {
      this.enableExtensionsSupport(browserSession);
    }

    // Configure session for cross-origin access (like Fellou.ai)
    browserSession.webRequest.onBeforeSendHeaders((details, callback) => {
      details.requestHeaders['User-Agent'] = 'AETHER-Native-Browser/6.0.0 Chrome/120.0.0.0';
      callback({ requestHeaders: details.requestHeaders });
    });

    // Native BrowserView for true Chromium engine
    this.browserView = new BrowserView({
      webPreferences: {
        session: browserSession,
        nodeIntegration: false,
        contextIsolation: true,
        webSecurity: false, // Fellou.ai-level access
        allowRunningInsecureContent: true,
        plugins: true,
        experimentalFeatures: true
      }
    });

    // Add browser view to main window
    this.mainWindow.setBrowserView(this.browserView);
    
    // Dynamic browser view resizing
    this.mainWindow.on('resize', () => {
      if (this.browserView) {
        const bounds = this.mainWindow.getBounds();
        this.browserView.setBounds({ 
          x: 0, 
          y: 120, // Leave space for UI controls
          width: bounds.width, 
          height: bounds.height - 120 
        });
      }
    });

    console.log('🌐 Native Chromium engine initialized with extension support');
  }

  enableExtensionsSupport(session) {
    // Enable Chrome extension support
    const extensionsDir = path.join(__dirname, 'extensions');
    
    try {
      // Load common extensions
      const commonExtensions = [
        // Add paths to Chrome extensions here
        // e.g., './extensions/react-devtools'
      ];

      commonExtensions.forEach(async (extensionPath) => {
        try {
          const extension = await session.loadExtension(extensionPath);
          this.extensions.set(extension.id, extension);
          console.log(`📦 Loaded extension: ${extension.name}`);
        } catch (error) {
          console.log(`⚠️ Could not load extension: ${extensionPath}`);
        }
      });
    } catch (error) {
      console.log('⚠️ Extensions directory not found, skipping extension loading');
    }
  }

  startBackendProcess() {
    if (isDev) {
      // In development, backend runs via supervisor
      console.log('📡 Using supervisor backend in development');
      return;
    }

    // In production, start backend process
    const backendScript = path.join(__dirname, 'backend', 'server.py');
    this.backendProcess = spawn('python', [backendScript], {
      cwd: path.join(__dirname, 'backend'),
      stdio: 'pipe'
    });

    this.backendProcess.stdout.on('data', (data) => {
      console.log(`Backend: ${data}`);
    });

    this.backendProcess.stderr.on('data', (data) => {
      console.error(`Backend Error: ${data}`);
    });

    console.log('🚀 Backend process started');
  }

  setupIPC() {
    // Native browser navigation
    ipcMain.handle('navigate-to', async (event, url) => {
      if (this.browserView) {
        try {
          await this.browserView.webContents.loadURL(url);
          return { success: true, url };
        } catch (error) {
          return { success: false, error: error.message };
        }
      }
    });

    // Native browser controls
    ipcMain.handle('browser-back', () => {
      if (this.browserView && this.browserView.webContents.canGoBack()) {
        this.browserView.webContents.goBack();
        return true;
      }
      return false;
    });

    ipcMain.handle('browser-forward', () => {
      if (this.browserView && this.browserView.webContents.canGoForward()) {
        this.browserView.webContents.goForward();
        return true;
      }
      return false;
    });

    ipcMain.handle('browser-refresh', () => {
      if (this.browserView) {
        this.browserView.webContents.reload();
        return true;
      }
      return false;
    });

    // Native DevTools access
    ipcMain.handle('open-devtools', () => {
      if (this.browserView && store.get('browserSettings.enableDevTools')) {
        this.browserView.webContents.openDevTools();
        return true;
      }
      return false;
    });

    // Extension management
    ipcMain.handle('get-extensions', () => {
      return Array.from(this.extensions.values()).map(ext => ({
        id: ext.id,
        name: ext.name,
        version: ext.version
      }));
    });

    // Fellou.ai-style command processing
    ipcMain.handle('process-command', async (event, command) => {
      return this.processNaturalLanguageCommand(command);
    });

    // Native session management
    ipcMain.handle('create-session', async (event, options) => {
      const sessionId = `session-${Date.now()}`;
      const newSession = session.fromPartition(`persist:${sessionId}`, options);
      this.sessions.set(sessionId, newSession);
      return sessionId;
    });

    console.log('🔌 IPC handlers registered for native Chromium features');
  }

  async processNaturalLanguageCommand(command) {
    // Enhanced NLP command processing (Fellou.ai-style)
    const commandLower = command.toLowerCase();
    
    if (commandLower.includes('navigate to') || commandLower.includes('go to')) {
      const urlMatch = command.match(/(?:navigate to|go to)\s+(.+)/i);
      if (urlMatch) {
        const url = urlMatch[1].trim();
        const fullUrl = url.startsWith('http') ? url : `https://${url}`;
        return await this.ipcMain.emit('navigate-to', null, fullUrl);
      }
    }
    
    if (commandLower.includes('open devtools') || commandLower.includes('developer tools')) {
      return await this.ipcMain.emit('open-devtools');
    }
    
    if (commandLower.includes('back') || commandLower === 'go back') {
      return await this.ipcMain.emit('browser-back');
    }
    
    if (commandLower.includes('forward') || commandLower === 'go forward') {
      return await this.ipcMain.emit('browser-forward');
    }
    
    if (commandLower.includes('refresh') || commandLower.includes('reload')) {
      return await this.ipcMain.emit('browser-refresh');
    }

    // Advanced AI command processing via backend
    try {
      const response = await fetch('http://localhost:8001/api/process-command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command, context: 'native-browser' })
      });
      
      if (response.ok) {
        const result = await response.json();
        return result;
      }
    } catch (error) {
      console.error('Error processing command:', error);
    }
    
    return { 
      success: false, 
      message: `Command not recognized: ${command}` 
    };
  }

  setupMenu() {
    const template = [
      {
        label: 'AETHER',
        submenu: [
          { role: 'about' },
          { type: 'separator' },
          { 
            label: 'Preferences',
            accelerator: 'CmdOrCtrl+,',
            click: () => {
              this.showPreferences();
            }
          },
          { type: 'separator' },
          { role: 'quit' }
        ]
      },
      {
        label: 'Browser',
        submenu: [
          { 
            label: 'Back',
            accelerator: 'CmdOrCtrl+Left',
            click: () => this.browserView?.webContents.goBack()
          },
          { 
            label: 'Forward',
            accelerator: 'CmdOrCtrl+Right',
            click: () => this.browserView?.webContents.goForward()
          },
          { 
            label: 'Refresh',
            accelerator: 'CmdOrCtrl+R',
            click: () => this.browserView?.webContents.reload()
          },
          { type: 'separator' },
          {
            label: 'Developer Tools',
            accelerator: 'F12',
            click: () => this.browserView?.webContents.openDevTools()
          }
        ]
      },
      {
        label: 'AI Assistant',
        submenu: [
          {
            label: 'Toggle AI Panel',
            accelerator: 'CmdOrCtrl+Shift+A',
            click: () => {
              this.mainWindow.webContents.send('toggle-ai-panel');
            }
          },
          {
            label: 'Voice Commands',
            accelerator: 'CmdOrCtrl+Shift+P',
            click: () => {
              this.mainWindow.webContents.send('toggle-voice-commands');
            }
          }
        ]
      }
    ];

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
  }

  showPreferences() {
    // Create preferences window
    const prefsWindow = new BrowserWindow({
      width: 600,
      height: 400,
      parent: this.mainWindow,
      modal: true,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true
      }
    });

    prefsWindow.loadURL(`data:text/html,
      <html>
        <head><title>AETHER Preferences</title></head>
        <body style="font-family: system-ui; padding: 20px;">
          <h2>🔥 AETHER Native Browser Settings</h2>
          <h3>🌐 Chromium Engine</h3>
          <label><input type="checkbox" ${store.get('browserSettings.enableExtensions') ? 'checked' : ''}> Enable Chrome Extensions</label><br>
          <label><input type="checkbox" ${store.get('browserSettings.enableDevTools') ? 'checked' : ''}> Enable Developer Tools</label><br>
          <label><input type="checkbox" ${!store.get('browserSettings.enableWebSecurity') ? 'checked' : ''}> Disable Web Security (Cross-Origin Access)</label><br>
          
          <h3>🤖 AI Settings</h3>
          <label><input type="checkbox" ${store.get('aiSettings.proactiveMode') ? 'checked' : ''}> Proactive AI Suggestions</label><br>
          <label><input type="checkbox" ${store.get('aiSettings.behavioralLearning') ? 'checked' : ''}> Behavioral Learning</label><br>
          
          <h3>🎯 Interface Mode</h3>
          <label><input type="radio" name="commandMode" value="single-box" ${store.get('aiSettings.commandMode') === 'single-box' ? 'checked' : ''}> Single Command Box (Fellou.ai Style)</label><br>
          <label><input type="radio" name="commandMode" value="traditional" ${store.get('aiSettings.commandMode') === 'traditional' ? 'checked' : ''}> Traditional Interface</label><br>
          
          <br><button onclick="window.close()">Close</button>
        </body>
      </html>
    `);
  }
}

// Initialize AETHER Native Browser
const aetherBrowser = new AetherNativeBrowser();

app.on('ready', () => {
  aetherBrowser.initialize();
});

app.on('window-all-closed', () => {
  if (aetherBrowser.backendProcess) {
    aetherBrowser.backendProcess.kill();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    aetherBrowser.createMainWindow();
  }
});

// Handle certificate errors for cross-origin access
app.on('certificate-error', (event, webContents, url, error, certificate, callback) => {
  event.preventDefault();
  callback(true);
});

console.log('🔥 AETHER Native Browser v6.0.0 - Chromium Engine with Fellou.ai capabilities');