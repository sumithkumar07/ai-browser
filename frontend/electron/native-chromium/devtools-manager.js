/**
 * DevTools Manager for Native Chromium
 * Manages Chrome DevTools integration
 */

class DevToolsManager {
    constructor() {
        this.devToolsWindows = new Map();
        this.isEnabled = true;
        
        console.log('🔧 DevTools Manager initialized');
    }

    async openDevTools(webContentsId = null, options = {}) {
        try {
            const { webContents } = require('electron');
            
            let targetWebContents;
            
            if (webContentsId) {
                targetWebContents = webContents.fromId(webContentsId);
            } else {
                // Use the focused web contents
                const focusedWindow = require('electron').BrowserWindow.getFocusedWindow();
                if (focusedWindow) {
                    targetWebContents = focusedWindow.webContents;
                }
            }

            if (!targetWebContents) {
                throw new Error('No web contents available for DevTools');
            }

            // Open DevTools
            targetWebContents.openDevTools({
                mode: options.mode || 'detach',
                activate: options.activate !== false
            });

            const devToolsId = `devtools_${Date.now()}`;
            this.devToolsWindows.set(devToolsId, {
                id: devToolsId,
                webContentsId: targetWebContents.id,
                opened: new Date(),
                options: options
            });

            console.log(`✅ DevTools opened: ${devToolsId}`);

            return {
                success: true,
                devtools_id: devToolsId,
                webcontents_id: targetWebContents.id
            };

        } catch (error) {
            console.error(`❌ DevTools open failed:`, error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async closeDevTools(devToolsId = null) {
        try {
            const { webContents } = require('electron');

            if (devToolsId) {
                const devToolsInfo = this.devToolsWindows.get(devToolsId);
                if (!devToolsInfo) {
                    throw new Error('DevTools session not found');
                }

                const targetWebContents = webContents.fromId(devToolsInfo.webContentsId);
                if (targetWebContents) {
                    targetWebContents.closeDevTools();
                }

                this.devToolsWindows.delete(devToolsId);

                console.log(`✅ DevTools closed: ${devToolsId}`);

            } else {
                // Close all DevTools
                const focusedWindow = require('electron').BrowserWindow.getFocusedWindow();
                if (focusedWindow) {
                    focusedWindow.webContents.closeDevTools();
                }

                console.log('✅ All DevTools closed');
            }

            return { success: true };

        } catch (error) {
            console.error(`❌ DevTools close failed:`, error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async toggleDevTools(webContentsId = null) {
        try {
            const { webContents } = require('electron');
            
            let targetWebContents;
            
            if (webContentsId) {
                targetWebContents = webContents.fromId(webContentsId);
            } else {
                const focusedWindow = require('electron').BrowserWindow.getFocusedWindow();
                if (focusedWindow) {
                    targetWebContents = focusedWindow.webContents;
                }
            }

            if (!targetWebContents) {
                throw new Error('No web contents available');
            }

            if (targetWebContents.isDevToolsOpened()) {
                targetWebContents.closeDevTools();
                return { success: true, action: 'closed' };
            } else {
                targetWebContents.openDevTools({ mode: 'detach' });
                return { success: true, action: 'opened' };
            }

        } catch (error) {
            console.error(`❌ DevTools toggle failed:`, error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async executeInDevTools(devToolsId, expression) {
        try {
            const devToolsInfo = this.devToolsWindows.get(devToolsId);
            if (!devToolsInfo) {
                throw new Error('DevTools session not found');
            }

            const { webContents } = require('electron');
            const targetWebContents = webContents.fromId(devToolsInfo.webContentsId);
            
            if (!targetWebContents) {
                throw new Error('Target web contents not found');
            }

            // Execute in DevTools context
            const result = await targetWebContents.devToolsWebContents.executeJavaScript(expression);

            console.log(`🔧 DevTools expression executed: ${devToolsId}`);

            return {
                success: true,
                result: result
            };

        } catch (error) {
            console.error(`❌ DevTools execution failed:`, error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }

    getDevToolsInfo(devToolsId) {
        const devToolsInfo = this.devToolsWindows.get(devToolsId);
        if (!devToolsInfo) {
            return {
                success: false,
                error: 'DevTools session not found'
            };
        }

        return {
            success: true,
            devtools: {
                id: devToolsInfo.id,
                webContentsId: devToolsInfo.webContentsId,
                opened: devToolsInfo.opened.toISOString(),
                options: devToolsInfo.options
            }
        };
    }

    getAllDevToolsSessions() {
        const sessions = Array.from(this.devToolsWindows.values()).map(session => ({
            id: session.id,
            webContentsId: session.webContentsId,
            opened: session.opened.toISOString(),
            options: session.options
        }));

        return {
            success: true,
            sessions: sessions,
            total: sessions.length
        };
    }

    enable() {
        this.isEnabled = true;
        console.log('✅ DevTools Manager enabled');
        return { success: true, enabled: true };
    }

    disable() {
        this.isEnabled = false;
        console.log('⚠️ DevTools Manager disabled');
        return { success: true, enabled: false };
    }

    async cleanup() {
        try {
            // Close all DevTools sessions
            for (const devToolsId of this.devToolsWindows.keys()) {
                await this.closeDevTools(devToolsId);
            }

            console.log('🧹 DevTools Manager cleaned up');
            return { success: true };

        } catch (error) {
            console.error(`❌ DevTools cleanup failed:`, error.message);
            return { success: false, error: error.message };
        }
    }
}

module.exports = DevToolsManager;