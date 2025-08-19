import WebSocket from 'ws';
import { EventEmitter } from 'events';

export interface BridgeMessage {
  id: string;
  type: 'request' | 'response' | 'event';
  action: string;
  payload: any;
  timestamp: number;
}

export class WebSocketBridge extends EventEmitter {
  private server: WebSocket.Server | null = null;
  private clients: Set<WebSocket> = new Set();
  private port: number = 8080;
  private isRunning: boolean = false;

  async initialize(): Promise<void> {
    console.log('🌉 Initializing WebSocket bridge...');
    
    try {
      // Create WebSocket server
      this.server = new WebSocket.Server({ 
        port: this.port,
        perMessageDeflate: false
      });

      // Set up server event handlers
      this.setupServerHandlers();
      
      this.isRunning = true;
      console.log(`✅ WebSocket bridge running on port ${this.port}`);
    } catch (error) {
      console.error('❌ Failed to initialize WebSocket bridge:', error);
      throw error;
    }
  }

  private setupServerHandlers(): void {
    if (!this.server) return;

    this.server.on('connection', (ws: WebSocket) => {
      console.log('🔗 New WebSocket client connected');
      
      // Add client to set
      this.clients.add(ws);
      
      // Set up client handlers
      this.setupClientHandlers(ws);
      
      // Send welcome message
      this.sendToClient(ws, {
        id: this.generateId(),
        type: 'event',
        action: 'connected',
        payload: { message: 'Connected to AETHER Desktop Companion' },
        timestamp: Date.now()
      });
    });

    this.server.on('error', (error) => {
      console.error('WebSocket server error:', error);
      this.emit('error', error);
    });
  }

  private setupClientHandlers(ws: WebSocket): void {
    ws.on('message', (data: WebSocket.Data) => {
      try {
        const message: BridgeMessage = JSON.parse(data.toString());
        this.handleMessage(ws, message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
        this.sendError(ws, 'Invalid message format');
      }
    });

    ws.on('close', () => {
      console.log('🔌 WebSocket client disconnected');
      this.clients.delete(ws);
    });

    ws.on('error', (error) => {
      console.error('WebSocket client error:', error);
      this.clients.delete(ws);
    });
  }

  private async handleMessage(ws: WebSocket, message: BridgeMessage): Promise<void> {
    try {
      console.log(`📨 Received message: ${message.action}`);

      switch (message.action) {
        case 'ping':
          this.sendToClient(ws, {
            id: message.id,
            type: 'response',
            action: 'pong',
            payload: { timestamp: Date.now() },
            timestamp: Date.now()
          });
          break;

        case 'desktop-navigate':
          // Forward navigation request to desktop browser
          const navigationResult = await this.handleDesktopNavigation(message.payload);
          this.sendToClient(ws, {
            id: message.id,
            type: 'response',
            action: 'navigation-result',
            payload: navigationResult,
            timestamp: Date.now()
          });
          break;

        case 'desktop-execute-js':
          // Execute JavaScript in desktop browser
          const jsResult = await this.handleJavaScriptExecution(message.payload);
          this.sendToClient(ws, {
            id: message.id,
            type: 'response',
            action: 'js-result',
            payload: jsResult,
            timestamp: Date.now()
          });
          break;

        case 'computer-use':
          // Handle computer use API calls
          const computerResult = await this.handleComputerUse(message.payload);
          this.sendToClient(ws, {
            id: message.id,
            type: 'response',
            action: 'computer-result',
            payload: computerResult,
            timestamp: Date.now()
          });
          break;

        case 'cross-origin-request':
          // Handle cross-origin requests
          const corsResult = await this.handleCrossOriginRequest(message.payload);
          this.sendToClient(ws, {
            id: message.id,
            type: 'response',
            action: 'cors-result',
            payload: corsResult,
            timestamp: Date.now()
          });
          break;

        default:
          console.warn(`Unknown message action: ${message.action}`);
          this.sendError(ws, 'Unknown action', message.id);
      }
    } catch (error) {
      console.error('Error handling message:', error);
      this.sendError(ws, error instanceof Error ? error.message : 'Unknown error', message.id);
    }
  }

  private async handleDesktopNavigation(payload: any): Promise<any> {
    // This would integrate with the browser engine
    const { url } = payload;
    
    // Emit event for main process to handle
    this.emit('desktop-navigate', { url });
    
    return {
      success: true,
      url,
      message: 'Navigation request sent to desktop browser'
    };
  }

  private async handleJavaScriptExecution(payload: any): Promise<any> {
    // This would integrate with the browser engine
    const { script } = payload;
    
    // Emit event for main process to handle
    this.emit('desktop-execute-js', { script });
    
    return {
      success: true,
      script,
      message: 'JavaScript execution request sent to desktop browser'
    };
  }

  private async handleComputerUse(payload: any): Promise<any> {
    // This would integrate with the computer use API
    const { action, params } = payload;
    
    // Emit event for main process to handle
    this.emit('computer-use', { action, params });
    
    return {
      success: true,
      action,
      params,
      message: 'Computer use request processed'
    };
  }

  private async handleCrossOriginRequest(payload: any): Promise<any> {
    // This would handle cross-origin requests
    const { url, method, headers, body } = payload;
    
    // Emit event for main process to handle
    this.emit('cross-origin-request', { url, method, headers, body });
    
    return {
      success: true,
      url,
      method,
      message: 'Cross-origin request processed'
    };
  }

  sendToClient(ws: WebSocket, message: BridgeMessage): void {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    }
  }

  sendToAllClients(message: BridgeMessage): void {
    this.clients.forEach(client => {
      this.sendToClient(client, message);
    });
  }

  async sendToWebApp(message: any): Promise<any> {
    // Send message to all connected web app clients
    const bridgeMessage: BridgeMessage = {
      id: this.generateId(),
      type: 'event',
      action: 'desktop-message',
      payload: message,
      timestamp: Date.now()
    };

    this.sendToAllClients(bridgeMessage);
    
    return { success: true, message: 'Message sent to web app' };
  }

  private sendError(ws: WebSocket, error: string, messageId?: string): void {
    this.sendToClient(ws, {
      id: messageId || this.generateId(),
      type: 'response',
      action: 'error',
      payload: { error },
      timestamp: Date.now()
    });
  }

  private generateId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  broadcastEvent(action: string, payload: any): void {
    const message: BridgeMessage = {
      id: this.generateId(),
      type: 'event',
      action,
      payload,
      timestamp: Date.now()
    };

    this.sendToAllClients(message);
  }

  getConnectedClients(): number {
    return this.clients.size;
  }

  isServerRunning(): boolean {
    return this.isRunning;
  }

  async shutdown(): Promise<void> {
    console.log('🌉 Shutting down WebSocket bridge...');
    
    if (this.server) {
      // Close all client connections
      this.clients.forEach(client => {
        client.close();
      });
      
      // Close server
      this.server.close(() => {
        console.log('✅ WebSocket bridge shut down');
      });
      
      this.isRunning = false;
    }
  }
}