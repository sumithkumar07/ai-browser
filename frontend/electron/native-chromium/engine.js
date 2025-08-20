/**
 * Native Chromium Engine for Electron
 * Provides direct Chromium access through Electron's renderer process
 */

const { BrowserView, session, webContents } = require('electron');
const EventEmitter = require('events');

class NativeChromiumEngine extends EventEmitter {
    constructor(options = {}) {
        super();
        
        this.options = {
            enableExtensions: options.enableExtensions || false,
            enableDevTools: options.enableDevTools || true,
            enableFileAccess: options.enableFileAccess || true,
            enableCrossOrigin: options.enableCrossOrigin || true,
            ...options
        };
        
        this.browserViews = new Map();
        this.mainWindow = null;
        this.isInitialized = false;
        
        console.log('🔥 NativeChromiumEngine initialized with options:', this.options);
    }

    async attachToWindow(mainWindow) {
        this.mainWindow = mainWindow;
        this.isInitialized = true;
        
        // Setup session permissions
        await this.setupSessionPermissions();
        
        console.log('✅ Native Chromium Engine attached to window');
        return true;
    }

    async setupSessionPermissions() {
        const ses = session.defaultSession;
        
        // Permission handling for enhanced capabilities
        ses.setPermissionRequestHandler((webContents, permission, callback) => {
            console.log(`Permission requested: ${permission}`);
            
            // Allow all permissions for native browsing
            const allowedPermissions = [
                'camera',
                'microphone',
                'notifications',
                'geolocation',
                'midi',
                'midiSysex',
                'pointerLock',
                'fullscreen'
            ];
            
            if (allowedPermissions.includes(permission)) {
                callback(true);
            } else {
                callback(false);
            }
        });

        // Setup preload script for enhanced capabilities
        ses.setPreloads([]);
        
        console.log('✅ Session permissions configured for native browsing');
    }

    async navigate(url, sessionId = 'main') {
        try {
            if (!this.mainWindow) {
                throw new Error('Main window not available');
            }

            // Navigate using main window's webContents
            await this.mainWindow.webContents.loadURL(url);
            
            const result = {
                success: true,
                url: this.mainWindow.webContents.getURL(),
                title: this.mainWindow.webContents.getTitle()
            };

            this.emit('navigation-complete', { sessionId, ...result });
            
            console.log(`🔥 Native navigation successful: ${url}`);
            return result;

        } catch (error) {
            console.error(`❌ Navigation failed: ${error.message}`);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async goBack(sessionId = 'main') {
        try {
            if (this.mainWindow && this.mainWindow.webContents.canGoBack()) {
                this.mainWindow.webContents.goBack();
                
                return {
                    success: true,
                    url: this.mainWindow.webContents.getURL()
                };
            }
            
            return { success: false, error: 'Cannot go back' };
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async goForward(sessionId = 'main') {
        try {
            if (this.mainWindow && this.mainWindow.webContents.canGoForward()) {
                this.mainWindow.webContents.goForward();
                
                return {
                    success: true,
                    url: this.mainWindow.webContents.getURL()
                };
            }
            
            return { success: false, error: 'Cannot go forward' };
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async refresh(sessionId = 'main') {
        try {
            if (this.mainWindow) {
                this.mainWindow.webContents.reload();
                
                return {
                    success: true,
                    url: this.mainWindow.webContents.getURL()
                };
            }
            
            return { success: false, error: 'Window not available' };
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async captureScreenshot(options = {}) {
        try {
            if (!this.mainWindow) {
                throw new Error('Main window not available');
            }

            const image = await this.mainWindow.webContents.capturePage();
            const buffer = image.toPNG();
            
            return {
                success: true,
                screenshot: buffer.toString('base64'),
                format: 'png',
                size: buffer.length
            };

        } catch (error) {
            console.error(`❌ Screenshot failed: ${error.message}`);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async executeJavaScript(script, sessionId = 'main') {
        try {
            if (!this.mainWindow) {
                throw new Error('Main window not available');
            }

            const result = await this.mainWindow.webContents.executeJavaScript(script);
            
            return {
                success: true,
                result: result
            };

        } catch (error) {
            console.error(`❌ JavaScript execution failed: ${error.message}`);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async getPageInfo(sessionId = 'main') {
        try {
            if (!this.mainWindow) {
                throw new Error('Main window not available');
            }

            const webContents = this.mainWindow.webContents;
            
            return {
                success: true,
                url: webContents.getURL(),
                title: webContents.getTitle(),
                canGoBack: webContents.canGoBack(),
                canGoForward: webContents.canGoForward(),
                isLoading: webContents.isLoading(),
                zoomLevel: webContents.getZoomLevel()
            };

        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    async createBrowserView(options = {}) {
        try {
            const browserView = new BrowserView({
                webPreferences: {
                    nodeIntegration: false,
                    contextIsolation: true,
                    enableRemoteModule: false,
                    webSecurity: !this.options.enableCrossOrigin,
                    allowRunningInsecureContent: true,
                    ...options.webPreferences
                }
            });

            const viewId = Date.now().toString();
            this.browserViews.set(viewId, browserView);

            if (this.mainWindow) {
                this.mainWindow.setBrowserView(browserView);
                browserView.setBounds({ x: 0, y: 80, width: 1920, height: 1000 });
            }

            console.log(`✅ BrowserView created: ${viewId}`);
            return {
                success: true,
                viewId: viewId,
                view: browserView
            };

        } catch (error) {
            console.error(`❌ BrowserView creation failed: ${error.message}`);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async closeBrowserView(viewId) {
        try {
            const browserView = this.browserViews.get(viewId);
            if (!browserView) {
                throw new Error('BrowserView not found');
            }

            if (this.mainWindow) {
                this.mainWindow.removeBrowserView(browserView);
            }

            browserView.webContents.destroy();
            this.browserViews.delete(viewId);

            console.log(`✅ BrowserView closed: ${viewId}`);
            return { success: true };

        } catch (error) {
            console.error(`❌ BrowserView close failed: ${error.message}`);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async getCapabilities() {
        return {
            hasNativeChromium: true,
            hasExtensionSupport: this.options.enableExtensions,
            hasDevTools: this.options.enableDevTools,
            hasFileSystemAccess: this.options.enableFileAccess,
            hasCrossOriginAccess: this.options.enableCrossOrigin,
            hasScreenshotCapture: true,
            hasJavaScriptExecution: true,
            hasBrowserViewSupport: true,
            version: '6.0.0',
            chromiumVersion: process.versions.chrome,
            electronVersion: process.versions.electron
        };
    }

    async cleanup() {
        try {
            // Close all browser views
            for (const [viewId, browserView] of this.browserViews) {
                if (this.mainWindow) {
                    this.mainWindow.removeBrowserView(browserView);
                }
                browserView.webContents.destroy();
            }
            
            this.browserViews.clear();
            this.isInitialized = false;
            
            console.log('🧹 Native Chromium Engine cleaned up');
            return { success: true };

        } catch (error) {
            console.error(`❌ Cleanup failed: ${error.message}`);
            return { success: false, error: error.message };
        }
    }
}

module.exports = NativeChromiumEngine;