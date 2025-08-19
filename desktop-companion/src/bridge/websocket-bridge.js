/**
 * WebSocket Bridge for AETHER Desktop Companion
 * Connects desktop app with web interface
 */

const WebSocket = require('ws');
const axios = require('axios');

class WebSocketBridge {
    constructor(webAppURL) {
        this.webAppURL = webAppURL;
        this.wsServer = null;
        this.connections = new Map();
        this.backendURL = webAppURL.replace(':3000', ':8001'); // Assuming backend on 8001
        this.isConnected = false;
        this.messageQueue = [];
        this.syncData = {
            recentTabs: [],
            activeAutomations: [],
            chatSessions: [],
            userPreferences: {}
        };
    }

    async initialize() {
        try {
            // Start WebSocket server for desktop-web communication
            this.wsServer = new WebSocket.Server({ port: 8080 });
            
            this.wsServer.on('connection', (ws) => {
                const connectionId = `conn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
                this.connections.set(connectionId, ws);
                
                console.log(`🔗 Desktop Bridge: New connection ${connectionId}`);
                
                ws.on('message', (data) => {
                    this.handleWebMessage(JSON.parse(data.toString()), connectionId);
                });
                
                ws.on('close', () => {
                    this.connections.delete(connectionId);
                    console.log(`🔗 Desktop Bridge: Connection ${connectionId} closed`);
                });
                
                // Send initial sync data
                this.sendSyncData(ws);
            });
            
            // Connect to backend API
            await this.connectToBackend();
            
            console.log('✅ WebSocket Bridge initialized on port 8080');
            return { success: true, port: 8080 };
        } catch (error) {
            console.error('❌ Failed to initialize WebSocket Bridge:', error);
            return { success: false, error: error.message };
        }
    }

    async connectToBackend() {
        try {
            // Test backend connection
            const response = await axios.get(`${this.backendURL}/api/health`);
            this.isConnected = response.status === 200;
            
            if (this.isConnected) {
                console.log('✅ Connected to AETHER backend');
                
                // Process queued messages
                while (this.messageQueue.length > 0) {
                    const message = this.messageQueue.shift();
                    await this.sendToBackend(message);
                }
            }
            
            return { success: this.isConnected };
        } catch (error) {
            console.log('⚠️ Backend not available, queuing messages');
            this.isConnected = false;
            return { success: false, error: error.message };
        }
    }

    async handleWebMessage(message, connectionId) {
        try {
            const { type, data } = message;
            
            switch (type) {
                case 'desktop_navigate':
                    // Handle navigation request from web interface
                    return await this.handleDesktopNavigation(data);
                    
                case 'cross_origin_request':
                    // Handle cross-origin automation request
                    return await this.handleCrossOriginRequest(data);
                    
                case 'computer_use_request':
                    // Handle computer use API request
                    return await this.handleComputerUseRequest(data);
                    
                case 'sync_request':
                    // Handle data synchronization request
                    return await this.handleSyncRequest(data, connectionId);
                    
                case 'automation_command':
                    // Handle automation commands
                    return await this.handleAutomationCommand(data);
                    
                default:
                    console.log(`Unknown message type: ${type}`);
                    return { success: false, error: 'Unknown message type' };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async handleDesktopNavigation(data) {
        try {
            const { url, options = {} } = data;
            
            // Send to native browser
            const result = await window.aetherDesktop?.navigateTo(url);
            
            // Sync with backend
            if (this.isConnected) {
                await this.sendToBackend({
                    endpoint: '/api/browse',
                    method: 'POST',
                    data: { url, source: 'desktop' }
                });
            }
            
            // Broadcast to all connections
            this.broadcast({
                type: 'navigation_update',
                data: { url, result }
            });
            
            return { success: true, result };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async handleCrossOriginRequest(data) {
        try {
            const { sites, actions, coordination } = data;
            
            // Execute cross-origin automation
            const result = await window.aetherDesktop?.executeCrossOriginAutomation({
                sites,
                actions,
                coordination
            });
            
            // Log to backend for analytics
            if (this.isConnected) {
                await this.sendToBackend({
                    endpoint: '/api/automation-analytics',
                    method: 'POST',
                    data: {
                        type: 'cross_origin',
                        sites: sites.length,
                        actions: actions.length,
                        success: result.success,
                        source: 'desktop'
                    }
                });
            }
            
            // Broadcast result
            this.broadcast({
                type: 'cross_origin_result',
                data: result
            });
            
            return result;
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async handleComputerUseRequest(data) {
        try {
            const { action, params } = data;
            let result;
            
            switch (action) {
                case 'screenshot':
                    result = await window.aetherDesktop?.takeScreenshot();
                    break;
                case 'click':
                    result = await window.aetherDesktop?.clickAt(params.x, params.y);
                    break;
                case 'type':
                    result = await window.aetherDesktop?.typeText(params.text);
                    break;
                case 'keypress':
                    result = await window.aetherDesktop?.sendKeyPress(params.key, params.modifiers);
                    break;
                default:
                    throw new Error(`Unknown computer use action: ${action}`);
            }
            
            // Log action to backend
            if (this.isConnected) {
                await this.sendToBackend({
                    endpoint: '/api/computer-use-log',
                    method: 'POST',
                    data: {
                        action,
                        params,
                        result: result.success,
                        timestamp: new Date().toISOString()
                    }
                });
            }
            
            return result;
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async handleSyncRequest(data, connectionId) {
        try {
            const { syncType } = data;
            
            switch (syncType) {
                case 'full_sync':
                    await this.performFullSync();
                    break;
                case 'tabs_sync':
                    await this.syncTabs();
                    break;
                case 'automations_sync':
                    await this.syncAutomations();
                    break;
                case 'chat_sync':
                    await this.syncChatSessions();
                    break;
            }
            
            // Send updated data to requester
            const connection = this.connections.get(connectionId);
            if (connection) {
                this.sendSyncData(connection);
            }
            
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async performFullSync() {
        try {
            if (!this.isConnected) {
                await this.connectToBackend();
            }
            
            if (this.isConnected) {
                // Sync recent tabs
                const tabsResponse = await axios.get(`${this.backendURL}/api/recent-tabs`);
                this.syncData.recentTabs = tabsResponse.data.tabs || [];
                
                // Sync active automations
                const automationsResponse = await axios.get(`${this.backendURL}/api/active-automations`);
                this.syncData.activeAutomations = automationsResponse.data.active_tasks || [];
                
                // Sync chat sessions (if available)
                try {
                    const chatResponse = await axios.get(`${this.backendURL}/api/chat-sessions`);
                    this.syncData.chatSessions = chatResponse.data.sessions || [];
                } catch (e) {
                    // Chat sessions endpoint might not exist
                    this.syncData.chatSessions = [];
                }
            }
            
            return { success: true };
        } catch (error) {
            console.error('Full sync failed:', error);
            return { success: false, error: error.message };
        }
    }

    async sendToBackend(message) {
        try {
            if (!this.isConnected) {
                this.messageQueue.push(message);
                return { success: false, queued: true };
            }
            
            const { endpoint, method = 'GET', data } = message;
            const config = {
                method,
                url: `${this.backendURL}${endpoint}`,
                headers: { 'Content-Type': 'application/json' }
            };
            
            if (data && (method === 'POST' || method === 'PUT')) {
                config.data = data;
            }
            
            const response = await axios(config);
            return { success: true, data: response.data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    broadcast(message) {
        const messageString = JSON.stringify(message);
        for (const connection of this.connections.values()) {
            if (connection.readyState === WebSocket.OPEN) {
                connection.send(messageString);
            }
        }
    }

    sendSyncData(connection) {
        if (connection.readyState === WebSocket.OPEN) {
            connection.send(JSON.stringify({
                type: 'sync_data',
                data: this.syncData
            }));
        }
    }

    async sendMessage(message) {
        // Main interface for external message sending
        try {
            this.broadcast({
                type: 'external_message',
                data: message
            });
            
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
}

module.exports = { WebSocketBridge };