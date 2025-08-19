const { app, BrowserWindow, ipcMain, session, webContents } = require('electron');
const path = require('path');
const isDev = require('electron-is-dev');
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');

// Keep a global reference of the window object
let mainWindow;
let backendProcess;

// Enhanced Chromium configuration
const CHROMIUM_FLAGS = [
  '--enable-features=NetworkService,NetworkServiceInProcess',
  '--disable-extensions-except=' + path.join(__dirname, '../extensions'),
  '--load-extension=' + path.join(__dirname, '../extensions'),
  '--enable-automation',
  '--enable-devtools-experiments',
  '--allow-running-insecure-content',
  '--disable-web-security',
  '--disable-features=VizDisplayCompositor',
  '--enable-experimental-web-platform-features'
];

// Apply Chromium flags
app.commandLine.appendArgument('--enable-features=NetworkService');
CHROMIUM_FLAGS.forEach(flag => {
  app.commandLine.appendSwitch(flag.replace('--', ''));
});

function createWindow() {
  // Create the browser window with enhanced capabilities
  mainWindow = new BrowserWindow({
    width: 1920,
    height: 1080,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      webSecurity: false, // For cross-origin requests
      allowRunningInsecureContent: true,
      experimentalFeatures: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'assets/icon.png'),
    titleBarStyle: 'hiddenInset',
    show: false,
    frame: true,
    backgroundColor: '#0a0a0f'
  });

  // Enhanced window styling
  mainWindow.setMenuBarVisibility(false);
  
  // Load the app
  const startUrl = isDev 
    ? 'http://localhost:3000' 
    : `file://${path.join(__dirname, '../frontend/build/index.html')}`;
  
  mainWindow.loadURL(startUrl);

  // Show window when ready to prevent visual flash
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // Open DevTools in development
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Enhanced session configuration
  configureSession();
  
  // Setup native integrations
  setupNativeIntegrations();
}

function configureSession() {
  const ses = session.defaultSession;
  
  // Configure permissions
  ses.setPermissionRequestHandler((webContents, permission, callback) => {
    const allowedPermissions = [
      'microphone',
      'camera', 
      'notifications',
      'geolocation',
      'clipboard-read',
      'clipboard-write'
    ];
    
    callback(allowedPermissions.includes(permission));
  });

  // Configure user agent
  ses.setUserAgent('AETHER/6.0.0 (Native Chromium) Chrome/120.0.0.0');

  // Enable extensions
  if (!isDev) {
    loadExtensions();
  }
}

async function loadExtensions() {
  try {
    const extensionsPath = path.join(__dirname, '../extensions');
    
    if (fs.existsSync(extensionsPath)) {
      const extensions = fs.readdirSync(extensionsPath);
      
      for (const extension of extensions) {
        const extensionPath = path.join(extensionsPath, extension);
        
        if (fs.statSync(extensionPath).isDirectory()) {
          try {
            await session.defaultSession.loadExtension(extensionPath);
            console.log(`Loaded extension: ${extension}`);
          } catch (error) {
            console.error(`Failed to load extension ${extension}:`, error);
          }
        }
      }
    }
  } catch (error) {
    console.error('Error loading extensions:', error);
  }
}

function setupNativeIntegrations() {
  // Handle native browser creation requests
  ipcMain.handle('create-native-browser', async (event, config) => {
    try {
      const browserWindow = new BrowserWindow({
        width: config.width || 1200,
        height: config.height || 800,
        webPreferences: {
          nodeIntegration: false,
          contextIsolation: true,
          webSecurity: false,
          allowRunningInsecureContent: true
        },
        parent: mainWindow,
        modal: false
      });

      if (config.url) {
        browserWindow.loadURL(config.url);
      }

      return {
        success: true,
        windowId: browserWindow.id
      };
      
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  });

  // Handle DevTools requests
  ipcMain.handle('open-devtools', async (event, windowId) => {
    try {
      const window = windowId 
        ? BrowserWindow.fromId(windowId)
        : mainWindow;
        
      if (window) {
        window.webContents.openDevTools({ mode: 'detach' });
        return { success: true };
      }
      
      return { success: false, error: 'Window not found' };
      
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  // Handle native navigation
  ipcMain.handle('native-navigate', async (event, { windowId, url }) => {
    try {
      const window = windowId 
        ? BrowserWindow.fromId(windowId)
        : mainWindow;
        
      if (window) {
        await window.loadURL(url);
        return { success: true };
      }
      
      return { success: false, error: 'Window not found' };
      
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  // Handle script execution
  ipcMain.handle('execute-native-script', async (event, { windowId, script }) => {
    try {
      const window = windowId 
        ? BrowserWindow.fromId(windowId)
        : mainWindow;
        
      if (window) {
        const result = await window.webContents.executeJavaScript(script);
        return { success: true, result };
      }
      
      return { success: false, error: 'Window not found' };
      
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  // Handle screenshot requests
  ipcMain.handle('take-native-screenshot', async (event, { windowId, options = {} }) => {
    try {
      const window = windowId 
        ? BrowserWindow.fromId(windowId)
        : mainWindow;
        
      if (window) {
        const image = await window.capturePage();
        const buffer = options.format === 'jpeg' 
          ? image.toJPEG(options.quality || 80)
          : image.toPNG();
          
        return {
          success: true,
          data: buffer.toString('base64'),
          format: options.format || 'png'
        };
      }
      
      return { success: false, error: 'Window not found' };
      
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  // Handle extension management
  ipcMain.handle('manage-extension', async (event, { action, extensionId, extensionPath }) => {
    try {
      const ses = session.defaultSession;
      
      switch (action) {
        case 'load':
          if (extensionPath && fs.existsSync(extensionPath)) {
            const extension = await ses.loadExtension(extensionPath);
            return {
              success: true,
              extension: {
                id: extension.id,
                name: extension.name,
                version: extension.version
              }
            };
          }
          break;
          
        case 'remove':
          if (extensionId) {
            await ses.removeExtension(extensionId);
            return { success: true };
          }
          break;
          
        case 'list':
          const extensions = ses.getAllExtensions();
          return {
            success: true,
            extensions: extensions.map(ext => ({
              id: ext.id,
              name: ext.name,
              version: ext.version,
              enabled: true
            }))
          };
          
        default:
          return { success: false, error: 'Unknown action' };
      }
      
    } catch (error) {
      return { success: false, error: error.message };
    }
  });
}

function startBackend() {
  if (isDev) {
    console.log('Backend should be started manually in development mode');
    return;
  }

  try {
    const backendPath = path.join(__dirname, '../backend');
    const pythonPath = process.platform === 'win32' ? 'python' : 'python3';
    
    backendProcess = spawn(pythonPath, ['server.py'], {
      cwd: backendPath,
      stdio: ['pipe', 'pipe', 'pipe']
    });

    backendProcess.stdout.on('data', (data) => {
      console.log(`Backend: ${data}`);
    });

    backendProcess.stderr.on('data', (data) => {
      console.error(`Backend Error: ${data}`);
    });

    backendProcess.on('close', (code) => {
      console.log(`Backend process exited with code ${code}`);
    });

    console.log('Backend started successfully');
    
  } catch (error) {
    console.error('Failed to start backend:', error);
  }
}

// App event handlers
app.whenReady().then(() => {
  createWindow();
  
  // Start backend in production
  if (!isDev) {
    startBackend();
  }
  
  // macOS app re-activation
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  // Kill backend process
  if (backendProcess) {
    backendProcess.kill();
  }
  
  // Quit app except on macOS
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  // Clean shutdown
  if (backendProcess) {
    backendProcess.kill();
  }
});

// Security: Prevent new window creation from renderer
app.on('web-contents-created', (event, contents) => {
  contents.on('new-window', (event, navigationUrl) => {
    event.preventDefault();
    
    // Allow same-origin navigation
    try {
      const parsedUrl = new URL(navigationUrl);
      const currentUrl = contents.getURL();
      const parsedCurrent = new URL(currentUrl);
      
      if (parsedUrl.origin === parsedCurrent.origin) {
        contents.loadURL(navigationUrl);
      }
    } catch (error) {
      console.error('Navigation blocked:', error);
    }
  });
});

// Handle certificate errors
app.on('certificate-error', (event, webContents, url, error, certificate, callback) => {
  // Allow self-signed certificates in development
  if (isDev) {
    event.preventDefault();
    callback(true);
  } else {
    callback(false);
  }
});

console.log('AETHER Native Browser initialized with enhanced Chromium integration');