const { app, BrowserWindow, ipcMain, protocol, session } = require('electron');
const path = require('path');
const { NativeBrowserEngine } = require('./browser-engine/native-browser');
const { ComputerUseAPI } = require('./computer-use/computer-api');
const { WebSocketBridge } = require('./bridge/websocket-bridge');
const { SecurityManager } = require('./security/security-manager');

class AetherDesktopCompanion {
    constructor() {
        this.mainWindow = null;
        this.nativeBrowser = null;
        this.computerUse = null;
        this.bridge = null;
        this.security = null;
        this.webAppURL = 'http://localhost:3000';
    }

    async initialize() {
        // Initialize core components
        this.nativeBrowser = new NativeBrowserEngine();
        this.computerUse = new ComputerUseAPI();
        this.bridge = new WebSocketBridge(this.webAppURL);
        this.security = new SecurityManager();

        await this.setupProtocols();
        await this.createMainWindow();
        await this.setupIpcHandlers();
        
        console.log('🚀 AETHER Desktop Companion initialized successfully');
    }

    async setupProtocols() {
        // Register custom protocol for enhanced security
        protocol.registerSchemesAsPrivileged([
            {
                scheme: 'aether',
                privileges: {
                    standard: true,
                    secure: true,
                    allowServiceWorkers: true,
                    supportFetchAPI: true,
                    corsEnabled: true
                }
            }
        ]);
    }

    async createMainWindow() {
        this.mainWindow = new BrowserWindow({
            width: 1400,
            height: 900,
            minWidth: 1200,
            minHeight: 800,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                enableRemoteModule: false,
                webSecurity: false, // Disable for cross-origin access
                allowRunningInsecureContent: true,
                preload: path.join(__dirname, 'preload.js')
            },
            icon: path.join(__dirname, '../assets/icon.png'),
            titleBarStyle: 'default',
            show: false
        });

        // Load the web application
        await this.mainWindow.loadURL(this.webAppURL);

        // Show window when ready
        this.mainWindow.once('ready-to-show', () => {
            this.mainWindow.show();
            this.mainWindow.focus();
        });

        // Handle window events
        this.mainWindow.on('closed', () => {
            this.mainWindow = null;
        });

        // Enable developer tools in development
        if (process.env.NODE_ENV === 'development') {
            this.mainWindow.webContents.openDevTools();
        }
    }

    async setupIpcHandlers() {
        // Native browser operations
        ipcMain.handle('native-browser-navigate', async (event, url) => {
            return await this.nativeBrowser.navigateToUrl(url);
        });

        ipcMain.handle('native-browser-execute-script', async (event, script) => {
            return await this.nativeBrowser.executeScript(script);
        });

        ipcMain.handle('native-browser-get-content', async (event) => {
            return await this.nativeBrowser.getPageContent();
        });

        // Computer Use API
        ipcMain.handle('computer-use-screenshot', async (event) => {
            return await this.computerUse.takeScreenshot();
        });

        ipcMain.handle('computer-use-click', async (event, x, y) => {
            return await this.computerUse.clickAt(x, y);
        });

        ipcMain.handle('computer-use-type', async (event, text) => {
            return await this.computerUse.typeText(text);
        });

        // Cross-origin automation
        ipcMain.handle('cross-origin-automation', async (event, config) => {
            return await this.nativeBrowser.executeCrossOriginAutomation(config);
        });

        // Security operations
        ipcMain.handle('security-validate-operation', async (event, operation) => {
            return await this.security.validateOperation(operation);
        });

        // Bridge operations
        ipcMain.handle('bridge-send-message', async (event, message) => {
            return await this.bridge.sendMessage(message);
        });

        // Enhanced Desktop Features
        ipcMain.handle('get-system-info', async (event) => {
            return await this.computerUse.getSystemInfo();
        });

        ipcMain.handle('get-capabilities', async (event) => {
            return await this.computerUse.getCapabilities();
        });

        ipcMain.handle('computer-use-keypress', async (event, key, modifiers) => {
            return await this.computerUse.sendKeyPress(key, modifiers);
        });

        ipcMain.handle('create-persistent-session', async (event, url, sessionId) => {
            return await this.nativeBrowser.createPersistentSession(url, sessionId);
        });

        ipcMain.handle('execute-in-session', async (event, sessionId, actions) => {
            return await this.nativeBrowser.executeInSession(sessionId, actions);
        });

        ipcMain.handle('get-running-processes', async (event) => {
            return await this.computerUse.getRunningProcesses();
        });

        // Window management
        ipcMain.handle('minimize-window', async (event) => {
            this.mainWindow?.minimize();
            return { success: true };
        });

        ipcMain.handle('maximize-window', async (event) => {
            if (this.mainWindow?.isMaximized()) {
                this.mainWindow.unmaximize();
            } else {
                this.mainWindow?.maximize();
            }
            return { success: true };
        });

        ipcMain.handle('close-window', async (event) => {
            this.mainWindow?.close();
            return { success: true };
        });

        ipcMain.handle('open-dev-tools', async (event) => {
            this.mainWindow?.webContents.openDevTools();
            return { success: true };
        });
    }
}

// App event handlers
app.whenReady().then(async () => {
    const companion = new AetherDesktopCompanion();
    await companion.initialize();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        const companion = new AetherDesktopCompanion();
        companion.initialize();
    }
});

// Security: Prevent new window creation
app.on('web-contents-created', (event, contents) => {
    contents.on('new-window', (event, url) => {
        event.preventDefault();
        // Handle new window requests through native browser
    });
});

module.exports = AetherDesktopCompanion;