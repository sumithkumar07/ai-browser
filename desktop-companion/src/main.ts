import { app, BrowserWindow, ipcMain, session, webContents } from 'electron';
import { join } from 'path';
import { ChromiumBrowserEngine } from './browser-engine/chromium-wrapper';
import { ComputerUseAPI } from './computer-use/computer-use-api';
import { WebSocketBridge } from './bridge/websocket-bridge';
import { CrossOriginHandler } from './browser-engine/cross-origin-handler';
import { SystemIntegration } from './browser-engine/system-integration';

class AetherDesktopApp {
  private mainWindow: BrowserWindow | null = null;
  private browserEngine: ChromiumBrowserEngine;
  private computerUse: ComputerUseAPI;
  private webSocketBridge: WebSocketBridge;
  private crossOriginHandler: CrossOriginHandler;
  private systemIntegration: SystemIntegration;

  constructor() {
    this.browserEngine = new ChromiumBrowserEngine();
    this.computerUse = new ComputerUseAPI();
    this.webSocketBridge = new WebSocketBridge();
    this.crossOriginHandler = new CrossOriginHandler();
    this.systemIntegration = new SystemIntegration();
  }

  async initialize(): Promise<void> {
    await app.whenReady();
    
    // Create main window with enhanced capabilities
    this.createMainWindow();
    
    // Initialize all subsystems
    await this.initializeSubsystems();
    
    // Set up IPC handlers
    this.setupIpcHandlers();
    
    console.log('🚀 AETHER Desktop Companion initialized with native browser capabilities');
  }

  private createMainWindow(): void {
    this.mainWindow = new BrowserWindow({
      width: 1920,
      height: 1080,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        enableRemoteModule: false,
        preload: join(__dirname, 'preload.js'),
        webSecurity: false, // For cross-origin access
        allowRunningInsecureContent: true,
        experimentalFeatures: true
      },
      title: 'AETHER - Desktop Companion',
      icon: join(__dirname, '../assets/icon.png')
    });

    // Load the web application
    const webAppUrl = process.env.WEB_APP_URL || 'http://localhost:3000';
    this.mainWindow.loadURL(webAppUrl);

    // Enhanced browser session with unlimited access
    const ses = this.mainWindow.webContents.session;
    
    // Disable web security for cross-origin requests
    ses.webRequest.onHeadersReceived((details, callback) => {
      callback({
        responseHeaders: {
          ...details.responseHeaders,
          'Access-Control-Allow-Origin': ['*'],
          'Access-Control-Allow-Methods': ['GET, POST, PUT, DELETE, OPTIONS'],
          'Access-Control-Allow-Headers': ['*'],
        },
      });
    });

    this.mainWindow.on('closed', () => {
      this.mainWindow = null;
    });
  }

  private async initializeSubsystems(): Promise<void> {
    try {
      await this.browserEngine.initialize();
      await this.computerUse.initialize();
      await this.webSocketBridge.initialize();
      await this.crossOriginHandler.initialize();
      await this.systemIntegration.initialize();
      
      console.log('✅ All desktop companion subsystems initialized');
    } catch (error) {
      console.error('❌ Failed to initialize subsystems:', error);
    }
  }

  private setupIpcHandlers(): void {
    // Native browsing capabilities
    ipcMain.handle('navigate-to-url', async (event, url: string) => {
      return await this.browserEngine.navigateToUrl(url);
    });

    ipcMain.handle('execute-javascript', async (event, script: string) => {
      return await this.browserEngine.executeJavaScript(script);
    });

    ipcMain.handle('get-page-content', async (event) => {
      return await this.browserEngine.getPageContent();
    });

    // Cross-origin automation
    ipcMain.handle('cross-origin-request', async (event, requestConfig) => {
      return await this.crossOriginHandler.makeRequest(requestConfig);
    });

    ipcMain.handle('bypass-cors', async (event, url: string) => {
      return await this.crossOriginHandler.bypassCors(url);
    });

    // Computer use API
    ipcMain.handle('take-screenshot', async (event) => {
      return await this.computerUse.takeScreenshot();
    });

    ipcMain.handle('click-at-position', async (event, x: number, y: number) => {
      return await this.computerUse.clickAtPosition(x, y);
    });

    ipcMain.handle('type-text', async (event, text: string) => {
      return await this.computerUse.typeText(text);
    });

    ipcMain.handle('get-system-info', async (event) => {
      return await this.systemIntegration.getSystemInfo();
    });

    // File system access
    ipcMain.handle('read-file', async (event, filePath: string) => {
      return await this.systemIntegration.readFile(filePath);
    });

    ipcMain.handle('write-file', async (event, filePath: string, content: string) => {
      return await this.systemIntegration.writeFile(filePath, content);
    });

    // WebSocket bridge for communication with web app
    ipcMain.handle('send-to-webapp', async (event, message: any) => {
      return await this.webSocketBridge.sendToWebApp(message);
    });

    console.log('🔗 IPC handlers set up for desktop companion');
  }

  async shutdown(): Promise<void> {
    try {
      await this.webSocketBridge.shutdown();
      await this.browserEngine.shutdown();
      await this.computerUse.shutdown();
      console.log('✅ Desktop companion shut down cleanly');
    } catch (error) {
      console.error('❌ Error during shutdown:', error);
    }
  }
}

// Initialize the desktop application
const aetherApp = new AetherDesktopApp();

app.whenReady().then(() => {
  aetherApp.initialize();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    aetherApp.initialize();
  }
});

app.on('before-quit', async () => {
  await aetherApp.shutdown();
});

export { AetherDesktopApp };