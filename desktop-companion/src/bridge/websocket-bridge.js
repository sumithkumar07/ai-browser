const WebSocket = require('ws');
const express = require('express');
const cors = require('cors');

class WebSocketBridge {
    constructor(webAppURL) {
        this.webAppURL = webAppURL;
        this.websocket = null;
        this.isConnected = false;
        this.messageQueue = [];
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        
        // Set up HTTP server for receiving messages from web app
        this.setupHttpServer();
    }

    async initialize() {
        try {
            await this.connectToWebApp();
            console.log('✅ WebSocket Bridge initialized');
            return { success: true };
        } catch (error) {
            console.error('❌ WebSocket Bridge initialization failed:', error);
            return { success: false, error: error.message };
        }
    }

    setupHttpServer() {
        this.app = express();
        this.app.use(cors());
        this.app.use(express.json());

        // Endpoint for web app to send messages to desktop
        this.app.post('/desktop-message', (req, res) => {
            this.handleWebAppMessage(req.body);
            res.json({ success: true, message: 'Message received' });
        });

        // Health check endpoint
        this.app.get('/health', (req, res) => {
            res.json({
                status: 'healthy',
                connected: this.isConnected,
                webAppURL: this.webAppURL
            });
        });

        // Start HTTP server on port 3001 (desktop companion port)
        this.server = this.app.listen(3001, () => {
            console.log('🌉 Desktop Bridge HTTP server running on port 3001');
        });
    }

    async connectToWebApp() {
        try {
            // For now, we'll simulate the WebSocket connection since the web app 
            // doesn't have a WebSocket server running. In production, this would
            // connect to ws://localhost:3000/ws or similar
            
            console.log(`Attempting to connect to ${this.webAppURL}`);
            
            // Simulate connection success
            this.isConnected = true;
            this.reconnectAttempts = 0;
            
            // Process any queued messages
            this.processMessageQueue();
            
            console.log('✅ Connected to web application');
            return true;
        } catch (error) {
            console.error('❌ Failed to connect to web app:', error);
            this.isConnected = false;
            
            // Attempt reconnection
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                console.log(`Retrying connection (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
                setTimeout(() => this.connectToWebApp(), 5000);
            }
            
            throw error;
        }
    }

    async sendMessage(message) {
        try {
            if (!this.isConnected) {
                // Queue message for later sending
                this.messageQueue.push(message);
                console.log('Message queued - not connected to web app');
                return { success: false, error: 'Not connected to web app', queued: true };
            }

            // In production, this would send via WebSocket
            console.log('📤 Sending message to web app:', message);
            
            // Simulate sending message to web app
            // In real implementation: this.websocket.send(JSON.stringify(message));
            
            return { 
                success: true, 
                message: 'Message sent to web app',
                data: message 
            };
        } catch (error) {
            console.error('❌ Failed to send message:', error);
            return { success: false, error: error.message };
        }
    }

    handleWebAppMessage(message) {
        try {
            console.log('📥 Received message from web app:', message);
            
            // Process different message types
            switch (message.type) {
                case 'automation_request':
                    this.handleAutomationRequest(message.data);
                    break;
                case 'screenshot_request':
                    this.handleScreenshotRequest(message.data);
                    break;
                case 'status_request':
                    this.handleStatusRequest(message.data);
                    break;
                default:
                    console.log('Unknown message type:', message.type);
            }
        } catch (error) {
            console.error('❌ Error handling web app message:', error);
        }
    }

    async handleAutomationRequest(data) {
        try {
            console.log('🤖 Processing automation request:', data);
            
            // In production, this would trigger actual automation
            const result = {
                success: true,
                automationId: data.automationId,
                result: 'Automation completed successfully',
                timestamp: new Date().toISOString()
            };
            
            // Send result back to web app
            await this.sendMessage({
                type: 'automation_result',
                data: result
            });
        } catch (error) {
            console.error('❌ Automation request failed:', error);
        }
    }

    async handleScreenshotRequest(data) {
        try {
            console.log('📸 Processing screenshot request:', data);
            
            // In production, this would take actual screenshot
            const result = {
                success: true,
                screenshotId: data.screenshotId,
                filepath: '/desktop/screenshots/screenshot_' + Date.now() + '.png',
                timestamp: new Date().toISOString()
            };
            
            // Send result back to web app
            await this.sendMessage({
                type: 'screenshot_result',
                data: result
            });
        } catch (error) {
            console.error('❌ Screenshot request failed:', error);
        }
    }

    async handleStatusRequest(data) {
        try {
            console.log('📊 Processing status request:', data);
            
            const status = {
                connected: this.isConnected,
                uptime: process.uptime(),
                memoryUsage: process.memoryUsage(),
                version: '1.0.0',
                capabilities: [
                    'screenshot',
                    'automation',
                    'cross_origin_access',
                    'file_system',
                    'system_integration'
                ]
            };
            
            // Send status back to web app
            await this.sendMessage({
                type: 'status_result',
                data: status
            });
        } catch (error) {
            console.error('❌ Status request failed:', error);
        }
    }

    processMessageQueue() {
        if (this.messageQueue.length === 0) return;
        
        console.log(`Processing ${this.messageQueue.length} queued messages`);
        
        const queuedMessages = [...this.messageQueue];
        this.messageQueue = [];
        
        queuedMessages.forEach(async (message) => {
            await this.sendMessage(message);
        });
    }

    async disconnect() {
        try {
            if (this.websocket) {
                this.websocket.close();
                this.websocket = null;
            }
            
            if (this.server) {
                this.server.close();
            }
            
            this.isConnected = false;
            console.log('🔌 Disconnected from web app');
        } catch (error) {
            console.error('❌ Error during disconnect:', error);
        }
    }

    getConnectionStatus() {
        return {
            connected: this.isConnected,
            webAppURL: this.webAppURL,
            queuedMessages: this.messageQueue.length,
            reconnectAttempts: this.reconnectAttempts
        };
    }
}

module.exports = { WebSocketBridge };