import { BrowserView, BrowserWindow, webContents } from 'electron';
import { EventEmitter } from 'events';

export interface NavigationResult {
  success: boolean;
  url: string;
  title: string;
  error?: string;
  securityState: 'secure' | 'insecure' | 'warning';
  loadTime: number;
}

export interface PageContent {
  html: string;
  text: string;
  links: string[];
  images: string[];
  forms: any[];
  metadata: any;
}

export class ChromiumBrowserEngine extends EventEmitter {
  private browserView: BrowserView | null = null;
  private parentWindow: BrowserWindow | null = null;
  private currentUrl: string = '';
  private isNavigating: boolean = false;

  async initialize(): Promise<void> {
    console.log('🌐 Initializing Chromium browser engine...');
    
    // Create browser view for native browsing
    this.browserView = new BrowserView({
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        webSecurity: false, // Disabled for cross-origin access
        allowRunningInsecureContent: true,
        experimentalFeatures: true,
        sandbox: false // Full system access
      }
    });

    // Set up event handlers
    this.setupEventHandlers();
    
    console.log('✅ Chromium browser engine initialized');
  }

  private setupEventHandlers(): void {
    if (!this.browserView) return;

    const webContents = this.browserView.webContents;

    // Navigation events
    webContents.on('did-start-loading', () => {
      this.isNavigating = true;
      this.emit('navigation-started');
    });

    webContents.on('did-finish-load', () => {
      this.isNavigating = false;
      this.emit('navigation-completed', {
        url: webContents.getURL(),
        title: webContents.getTitle()
      });
    });

    webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
      this.isNavigating = false;
      this.emit('navigation-failed', { errorCode, errorDescription });
    });

    // Security events
    webContents.on('certificate-error', (event, url, error, certificate, callback) => {
      // Allow all certificates for maximum compatibility
      event.preventDefault();
      callback(true);
    });

    // Content events
    webContents.on('dom-ready', () => {
      this.emit('dom-ready');
    });

    webContents.on('new-window', (event, url) => {
      event.preventDefault();
      this.navigateToUrl(url);
    });
  }

  async attachToWindow(window: BrowserWindow): Promise<void> {
    if (!this.browserView) {
      throw new Error('Browser engine not initialized');
    }

    this.parentWindow = window;
    window.setBrowserView(this.browserView);
    
    // Set browser view bounds
    const bounds = window.getBounds();
    this.browserView.setBounds({
      x: 0,
      y: 80, // Leave space for controls
      width: bounds.width,
      height: bounds.height - 80
    });

    console.log('🔗 Browser engine attached to window');
  }

  async navigateToUrl(url: string): Promise<NavigationResult> {
    if (!this.browserView) {
      throw new Error('Browser engine not initialized');
    }

    const startTime = Date.now();
    
    try {
      this.currentUrl = url;
      this.isNavigating = true;

      // Navigate using the browser view
      await this.browserView.webContents.loadURL(url);

      // Wait for navigation to complete
      await this.waitForNavigation();

      const loadTime = Date.now() - startTime;
      const webContents = this.browserView.webContents;

      return {
        success: true,
        url: webContents.getURL(),
        title: webContents.getTitle(),
        securityState: this.getSecurityState(url),
        loadTime
      };
    } catch (error) {
      const loadTime = Date.now() - startTime;
      
      return {
        success: false,
        url,
        title: 'Navigation Failed',
        error: error instanceof Error ? error.message : 'Unknown error',
        securityState: 'warning',
        loadTime
      };
    }
  }

  private async waitForNavigation(): Promise<void> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Navigation timeout'));
      }, 30000);

      const onComplete = () => {
        clearTimeout(timeout);
        resolve();
      };

      const onFailed = (error: any) => {
        clearTimeout(timeout);
        reject(new Error(error.errorDescription));
      };

      this.once('navigation-completed', onComplete);
      this.once('navigation-failed', onFailed);
    });
  }

  async executeJavaScript(script: string): Promise<any> {
    if (!this.browserView) {
      throw new Error('Browser engine not initialized');
    }

    try {
      return await this.browserView.webContents.executeJavaScript(script);
    } catch (error) {
      console.error('JavaScript execution failed:', error);
      throw error;
    }
  }

  async getPageContent(): Promise<PageContent> {
    if (!this.browserView) {
      throw new Error('Browser engine not initialized');
    }

    const script = `
      (function() {
        const content = {
          html: document.documentElement.outerHTML,
          text: document.body ? document.body.innerText : '',
          links: Array.from(document.links).map(link => link.href),
          images: Array.from(document.images).map(img => img.src),
          forms: Array.from(document.forms).map(form => ({
            action: form.action,
            method: form.method,
            elements: Array.from(form.elements).map(el => ({
              name: el.name,
              type: el.type,
              value: el.value
            }))
          })),
          metadata: {
            title: document.title,
            description: document.querySelector('meta[name="description"]')?.content || '',
            keywords: document.querySelector('meta[name="keywords"]')?.content || '',
            url: window.location.href
          }
        };
        return content;
      })();
    `;

    return await this.executeJavaScript(script);
  }

  async injectCSS(css: string): Promise<void> {
    if (!this.browserView) {
      throw new Error('Browser engine not initialized');
    }

    await this.browserView.webContents.insertCSS(css);
  }

  async takeScreenshot(): Promise<Buffer> {
    if (!this.browserView) {
      throw new Error('Browser engine not initialized');
    }

    return await this.browserView.webContents.capturePage();
  }

  private getSecurityState(url: string): 'secure' | 'insecure' | 'warning' {
    if (url.startsWith('https://')) {
      return 'secure';
    } else if (url.startsWith('http://')) {
      return 'warning';
    } else {
      return 'insecure';
    }
  }

  getCurrentUrl(): string {
    return this.currentUrl;
  }

  isCurrentlyNavigating(): boolean {
    return this.isNavigating;
  }

  async goBack(): Promise<void> {
    if (this.browserView?.webContents.canGoBack()) {
      await this.browserView.webContents.goBack();
    }
  }

  async goForward(): Promise<void> {
    if (this.browserView?.webContents.canGoForward()) {
      await this.browserView.webContents.goForward();
    }
  }

  async reload(): Promise<void> {
    if (this.browserView) {
      await this.browserView.webContents.reload();
    }
  }

  async shutdown(): Promise<void> {
    if (this.browserView) {
      this.browserView.webContents.destroy();
      this.browserView = null;
    }
    console.log('🌐 Chromium browser engine shut down');
  }
}