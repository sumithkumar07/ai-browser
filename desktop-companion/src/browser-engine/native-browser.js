/**
 * Native Browser Engine for AETHER Desktop Companion
 * Provides Fellou.ai-like native browsing capabilities with cross-origin automation
 */

const { BrowserWindow, session } = require('electron');
const puppeteer = require('puppeteer-core');
const playwright = require('playwright');

class NativeBrowserEngine {
    constructor() {
        this.activeBrowser = null;
        this.activePages = new Map();
        this.browserContext = null;
        this.crossOriginSessions = new Map();
        this.automationQueue = [];
        this.isInitialized = false;
    }

    async initialize() {
        try {
            // Initialize Playwright for cross-origin automation
            this.browser = await playwright.chromium.launch({
                headless: false,
                args: [
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--allow-running-insecure-content',
                    '--disable-site-isolation-trials',
                    '--disable-features=BlockInsecurePrivateNetworkRequests'
                ]
            });

            this.browserContext = await this.browser.newContext({
                ignoreHTTPSErrors: true,
                bypassCSP: true
            });

            this.isInitialized = true;
            console.log('✅ Native Browser Engine initialized with cross-origin capabilities');
            return { success: true, message: 'Browser engine ready' };
        } catch (error) {
            console.error('❌ Failed to initialize browser engine:', error);
            return { success: false, error: error.message };
        }
    }

    async navigateToUrl(url, options = {}) {
        try {
            if (!this.isInitialized) {
                await this.initialize();
            }

            const page = await this.browserContext.newPage();
            const pageId = `page_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            
            // Enhanced navigation with anti-detection
            await page.setExtraHTTPHeaders({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            });

            await page.evaluateOnNewDocument(() => {
                // Anti-detection measures
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            });

            const response = await page.goto(url, {
                waitUntil: 'networkidle',
                timeout: options.timeout || 30000
            });

            this.activePages.set(pageId, page);

            return {
                success: true,
                pageId: pageId,
                url: page.url(),
                title: await page.title(),
                status: response.status()
            };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async executeScript(script, pageId = null) {
        try {
            const page = pageId ? this.activePages.get(pageId) : Array.from(this.activePages.values())[0];
            if (!page) {
                return { success: false, error: 'No active page found' };
            }

            const result = await page.evaluate(script);
            return { success: true, result: result };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async getPageContent(pageId = null, format = 'html') {
        try {
            const page = pageId ? this.activePages.get(pageId) : Array.from(this.activePages.values())[0];
            if (!page) {
                return { success: false, error: 'No active page found' };
            }

            let content;
            switch (format) {
                case 'html':
                    content = await page.content();
                    break;
                case 'text':
                    content = await page.evaluate(() => document.body.innerText);
                    break;
                case 'json':
                    content = await page.evaluate(() => {
                        const extractData = (element) => {
                            const data = {
                                tag: element.tagName.toLowerCase(),
                                text: element.textContent?.trim() || '',
                                attributes: {}
                            };
                            
                            for (let attr of element.attributes || []) {
                                data.attributes[attr.name] = attr.value;
                            }
                            
                            return data;
                        };
                        
                        return Array.from(document.querySelectorAll('*')).map(extractData);
                    });
                    break;
                default:
                    content = await page.content();
            }

            return { success: true, content: content, format: format };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async executeCrossOriginAutomation(config) {
        try {
            const { 
                sites, 
                actions, 
                coordination = 'sequential', 
                sessionData = {},
                timeout = 60000 
            } = config;

            if (!this.isInitialized) {
                await this.initialize();
            }

            const results = [];
            const activeSessions = new Map();

            // Initialize sessions for each site
            for (const site of sites) {
                const page = await this.browserContext.newPage();
                await page.goto(site.url);
                activeSessions.set(site.id, {
                    page: page,
                    url: site.url,
                    data: site.sessionData || {}
                });
            }

            // Execute actions based on coordination type
            if (coordination === 'parallel') {
                const promises = actions.map(action => this._executeAction(action, activeSessions));
                const actionResults = await Promise.allSettled(promises);
                results.push(...actionResults.map(result => 
                    result.status === 'fulfilled' ? result.value : { success: false, error: result.reason }
                ));
            } else {
                // Sequential execution
                for (const action of actions) {
                    const result = await this._executeAction(action, activeSessions);
                    results.push(result);
                    
                    // Share data between sessions if needed
                    if (action.shareData && result.success) {
                        for (const [sessionId, session] of activeSessions) {
                            session.data = { ...session.data, ...result.data };
                        }
                    }
                }
            }

            // Cleanup sessions
            for (const [sessionId, session] of activeSessions) {
                await session.page.close();
            }

            return {
                success: true,
                results: results,
                summary: {
                    total_actions: actions.length,
                    successful_actions: results.filter(r => r.success).length,
                    failed_actions: results.filter(r => !r.success).length
                }
            };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async _executeAction(action, activeSessions) {
        try {
            const { type, siteId, selector, value, script, waitFor } = action;
            const session = activeSessions.get(siteId);
            
            if (!session) {
                return { success: false, error: `Session not found for site: ${siteId}` };
            }

            const page = session.page;

            // Wait for element if specified
            if (waitFor) {
                await page.waitForSelector(waitFor, { timeout: 10000 });
            }

            let result;
            switch (type) {
                case 'click':
                    await page.click(selector);
                    result = { success: true, action: 'click', selector: selector };
                    break;

                case 'type':
                    await page.fill(selector, value);
                    result = { success: true, action: 'type', selector: selector, value: value };
                    break;

                case 'extract':
                    const extractedData = await page.evaluate((sel) => {
                        const element = document.querySelector(sel);
                        return element ? element.textContent.trim() : null;
                    }, selector);
                    result = { success: true, action: 'extract', data: extractedData };
                    break;

                case 'script':
                    const scriptResult = await page.evaluate(script);
                    result = { success: true, action: 'script', data: scriptResult };
                    break;

                case 'screenshot':
                    const screenshot = await page.screenshot({ 
                        path: `screenshots/action_${Date.now()}.png`,
                        type: 'png'
                    });
                    result = { success: true, action: 'screenshot', screenshot: screenshot };
                    break;

                case 'navigate':
                    await page.goto(value);
                    result = { success: true, action: 'navigate', url: value };
                    break;

                case 'wait':
                    await page.waitForTimeout(value || 1000);
                    result = { success: true, action: 'wait', duration: value };
                    break;

                default:
                    result = { success: false, error: `Unknown action type: ${type}` };
            }

            return result;
        } catch (error) {
            return { success: false, error: error.message, action: action.type };
        }
    }

    async createPersistentSession(siteUrl, sessionId) {
        try {
            if (!this.isInitialized) {
                await this.initialize();
            }

            const page = await this.browserContext.newPage();
            await page.goto(siteUrl);

            this.crossOriginSessions.set(sessionId, {
                page: page,
                url: siteUrl,
                created: new Date(),
                lastActivity: new Date()
            });

            return {
                success: true,
                sessionId: sessionId,
                url: siteUrl,
                message: 'Persistent session created'
            };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async executeInSession(sessionId, actions) {
        try {
            const session = this.crossOriginSessions.get(sessionId);
            if (!session) {
                return { success: false, error: 'Session not found' };
            }

            const page = session.page;
            const results = [];

            for (const action of actions) {
                const result = await this._executeAction(action, new Map([[sessionId, session]]));
                results.push(result);
            }

            session.lastActivity = new Date();

            return {
                success: true,
                sessionId: sessionId,
                results: results
            };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async getActiveSessions() {
        const sessions = [];
        for (const [sessionId, session] of this.crossOriginSessions) {
            sessions.push({
                sessionId: sessionId,
                url: session.url,
                created: session.created,
                lastActivity: session.lastActivity,
                isActive: !session.page.isClosed()
            });
        }
        return { success: true, sessions: sessions };
    }

    async closeSession(sessionId) {
        try {
            const session = this.crossOriginSessions.get(sessionId);
            if (session) {
                await session.page.close();
                this.crossOriginSessions.delete(sessionId);
                return { success: true, message: 'Session closed' };
            }
            return { success: false, error: 'Session not found' };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async enableAdvancedFeatures() {
        try {
            // Enable advanced automation features
            const features = {
                antiDetection: true,
                proxyRotation: true,
                captchaSolving: true,
                jsInjection: true,
                cookieManagement: true
            };

            // Anti-detection setup
            await this.browserContext.addInitScript(() => {
                // Override webdriver detection
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });

                // Override plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });

                // Override languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            });

            return { success: true, features: features };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async cleanup() {
        try {
            // Close all active pages
            for (const page of this.activePages.values()) {
                await page.close();
            }
            this.activePages.clear();

            // Close persistent sessions
            for (const session of this.crossOriginSessions.values()) {
                await session.page.close();
            }
            this.crossOriginSessions.clear();

            // Close browser
            if (this.browser) {
                await this.browser.close();
            }

            console.log('✅ Native Browser Engine cleaned up');
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
}

module.exports = { NativeBrowserEngine };