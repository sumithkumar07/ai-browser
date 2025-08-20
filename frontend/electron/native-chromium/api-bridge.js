/**
 * Native API Bridge for Electron
 * Bridges frontend requests to native Chromium capabilities
 */

const EventEmitter = require('events');

class NativeAPIBridge extends EventEmitter {
    constructor(nativeEngine) {
        super();
        
        this.nativeEngine = nativeEngine;
        this.activeSessions = new Map();
        
        // Setup event forwarding
        this.setupEventForwarding();
        
        console.log('🔗 Native API Bridge initialized');
    }

    setupEventForwarding() {
        // Forward native engine events to frontend
        this.nativeEngine.on('navigation-complete', (data) => {
            this.emit('native-event', {
                type: 'navigation-complete',
                data: data
            });
        });

        this.nativeEngine.on('page-loaded', (data) => {
            this.emit('native-event', {
                type: 'page-loaded', 
                data: data
            });
        });
    }

    async handleAPICall(method, params = {}) {
        try {
            console.log(`📞 API Call: ${method}`, params);

            switch (method) {
                case 'navigate':
                    return await this.nativeEngine.navigate(params.url, params.sessionId);

                case 'goBack':
                    return await this.nativeEngine.goBack(params.sessionId);

                case 'goForward':
                    return await this.nativeEngine.goForward(params.sessionId);

                case 'refresh':
                    return await this.nativeEngine.refresh(params.sessionId);

                case 'screenshot':
                    return await this.nativeEngine.captureScreenshot(params.options);

                case 'executeJS':
                    return await this.nativeEngine.executeJavaScript(params.script, params.sessionId);

                case 'getPageInfo':
                    return await this.nativeEngine.getPageInfo(params.sessionId);

                case 'createBrowserView':
                    return await this.nativeEngine.createBrowserView(params.options);

                case 'closeBrowserView':
                    return await this.nativeEngine.closeBrowserView(params.viewId);

                case 'getCapabilities':
                    return await this.nativeEngine.getCapabilities();

                case 'createSession':
                    return this.createSession(params);

                case 'closeSession':
                    return this.closeSession(params.sessionId);

                case 'getSessionInfo':
                    return this.getSessionInfo(params.sessionId);

                default:
                    return {
                        success: false,
                        error: `Unknown API method: ${method}`
                    };
            }

        } catch (error) {
            console.error(`❌ API call failed (${method}):`, error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }

    createSession(params) {
        try {
            const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            
            const session = {
                id: sessionId,
                userSession: params.userSession || 'default',
                userAgent: params.userAgent || 'AETHER-Native-Browser/6.0.0',
                created: new Date(),
                lastActivity: new Date(),
                capabilities: [
                    'native_navigation',
                    'screenshot_capture',
                    'javascript_execution',
                    'browser_view_management',
                    'cross_origin_access'
                ]
            };

            this.activeSessions.set(sessionId, session);

            console.log(`✅ Session created: ${sessionId}`);

            return {
                success: true,
                session_id: sessionId,
                capabilities: session.capabilities,
                user_agent: session.userAgent
            };

        } catch (error) {
            console.error(`❌ Session creation failed:`, error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }

    closeSession(sessionId) {
        try {
            const session = this.activeSessions.get(sessionId);
            if (!session) {
                return {
                    success: false,
                    error: 'Session not found'
                };
            }

            this.activeSessions.delete(sessionId);

            console.log(`✅ Session closed: ${sessionId}`);

            return {
                success: true,
                session_id: sessionId
            };

        } catch (error) {
            console.error(`❌ Session close failed:`, error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }

    getSessionInfo(sessionId) {
        try {
            const session = this.activeSessions.get(sessionId);
            if (!session) {
                return {
                    success: false,
                    error: 'Session not found'
                };
            }

            return {
                success: true,
                session: {
                    id: session.id,
                    userSession: session.userSession,
                    created: session.created.toISOString(),
                    lastActivity: session.lastActivity.toISOString(),
                    capabilities: session.capabilities
                }
            };

        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    updateSessionActivity(sessionId) {
        const session = this.activeSessions.get(sessionId);
        if (session) {
            session.lastActivity = new Date();
        }
    }

    getActiveSessionCount() {
        return this.activeSessions.size;
    }

    getAllSessions() {
        return Array.from(this.activeSessions.values()).map(session => ({
            id: session.id,
            userSession: session.userSession,
            created: session.created.toISOString(),
            lastActivity: session.lastActivity.toISOString()
        }));
    }

    async cleanup() {
        try {
            // Close all active sessions
            for (const sessionId of this.activeSessions.keys()) {
                this.closeSession(sessionId);
            }

            console.log('🧹 Native API Bridge cleaned up');
            return { success: true };

        } catch (error) {
            console.error(`❌ API Bridge cleanup failed:`, error.message);
            return { success: false, error: error.message };
        }
    }
}

module.exports = NativeAPIBridge;