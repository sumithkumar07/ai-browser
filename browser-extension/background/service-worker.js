// AETHER Browser Extension Service Worker
class AetherExtensionEngine {
    constructor() {
        this.activeAutomations = new Map();
        this.crossOriginProxy = null;
        this.webAppURL = 'http://localhost:3000';
        this.initialize();
    }

    async initialize() {
        console.log('🚀 AETHER Extension Service Worker initialized');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize cross-origin proxy
        await this.initializeCrossOriginProxy();
        
        // Connect to main AETHER app
        await this.connectToMainApp();
    }

    setupEventListeners() {
        // Tab navigation events
        chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
            if (changeInfo.status === 'complete' && tab.url) {
                this.handlePageLoad(tabId, tab);
            }
        });

        // Context menu creation
        chrome.runtime.onInstalled.addListener(() => {
            this.createContextMenus();
        });

        // Message handling from content scripts
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            this.handleMessage(request, sender, sendResponse);
            return true; // Keep channel open for async response
        });

        // Web request interception for cross-origin support
        chrome.webRequest.onBeforeRequest.addListener(
            (details) => this.handleWebRequest(details),
            { urls: ["<all_urls>"] },
            ["requestBody"]
        );
    }

    async initializeCrossOriginProxy() {
        try {
            this.crossOriginProxy = new CrossOriginProxy();
            await this.crossOriginProxy.initialize();
            console.log('✅ Cross-origin proxy initialized');
        } catch (error) {
            console.error('❌ Failed to initialize cross-origin proxy:', error);
        }
    }

    async connectToMainApp() {
        try {
            // Establish WebSocket connection to main AETHER app
            const response = await fetch(`${this.webAppURL}/api/health`);
            if (response.ok) {
                console.log('✅ Connected to main AETHER app');
                this.sendNotification('AETHER Extension connected to main app', 'success');
            }
        } catch (error) {
            console.warn('⚠️ Main AETHER app not available, running in standalone mode');
        }
    }

    async handlePageLoad(tabId, tab) {
        try {
            // Inject AETHER capabilities into the page
            await chrome.scripting.executeScript({
                target: { tabId: tabId },
                files: ['content-scripts/aether-injector.js']
            });

            // Analyze page for automation opportunities
            const pageAnalysis = await this.analyzePage(tabId, tab.url);
            
            // Send analysis to main app if connected
            await this.sendToMainApp('page_analysis', {
                tabId: tabId,
                url: tab.url,
                analysis: pageAnalysis
            });

        } catch (error) {
            console.error('❌ Failed to handle page load:', error);
        }
    }

    async analyzePage(tabId, url) {
        try {
            const results = await chrome.scripting.executeScript({
                target: { tabId: tabId },
                function: () => {
                    return {
                        title: document.title,
                        forms: Array.from(document.querySelectorAll('form')).length,
                        buttons: Array.from(document.querySelectorAll('button, input[type="submit"]')).length,
                        links: Array.from(document.querySelectorAll('a')).length,
                        inputs: Array.from(document.querySelectorAll('input, textarea, select')).length,
                        automationOpportunities: this.identifyAutomationOpportunities()
                    };
                }
            });

            return results[0]?.result || {};
        } catch (error) {
            console.error('❌ Page analysis failed:', error);
            return {};
        }
    }

    createContextMenus() {
        const contexts = ['page', 'selection', 'link', 'image', 'video'];
        
        chrome.contextMenus.create({
            id: 'aether-automate-page',
            title: 'Automate this page with AETHER',
            contexts: contexts
        });

        chrome.contextMenus.create({
            id: 'aether-extract-data',
            title: 'Extract data with AETHER',
            contexts: contexts
        });

        chrome.contextMenus.create({
            id: 'aether-smart-actions',
            title: 'AETHER Smart Actions',
            contexts: contexts
        });

        // Context menu click handler
        chrome.contextMenus.onClicked.addListener((info, tab) => {
            this.handleContextMenuClick(info, tab);
        });
    }

    async handleContextMenuClick(info, tab) {
        switch (info.menuItemId) {
            case 'aether-automate-page':
                await this.initiatePageAutomation(tab.id, tab.url);
                break;
            case 'aether-extract-data':
                await this.initiateDataExtraction(tab.id, info);
                break;
            case 'aether-smart-actions':
                await this.showSmartActions(tab.id, info);
                break;
        }
    }

    async initiatePageAutomation(tabId, url) {
        try {
            // Create automation task
            const automationId = `auto_${Date.now()}`;
            
            // Analyze page structure for automation
            const pageStructure = await chrome.scripting.executeScript({
                target: { tabId: tabId },
                function: () => window.aetherAnalyzer?.getPageStructure()
            });

            // Send automation request to main app
            await this.sendToMainApp('create_automation', {
                automationId: automationId,
                url: url,
                tabId: tabId,
                pageStructure: pageStructure[0]?.result
            });

            this.sendNotification('Automation initiated for current page', 'info');
        } catch (error) {
            console.error('❌ Failed to initiate automation:', error);
            this.sendNotification('Failed to start automation', 'error');
        }
    }

    async initiateDataExtraction(tabId, contextInfo) {
        try {
            const extractionResult = await chrome.scripting.executeScript({
                target: { tabId: tabId },
                function: (info) => {
                    if (info.selectionText) {
                        return { type: 'selection', data: info.selectionText };
                    } else if (info.linkUrl) {
                        return { type: 'link', data: { url: info.linkUrl, text: info.linkText } };
                    } else {
                        return window.aetherAnalyzer?.extractPageData();
                    }
                },
                args: [contextInfo]
            });

            await this.sendToMainApp('data_extraction', {
                url: contextInfo.pageUrl,
                extraction: extractionResult[0]?.result
            });

            this.sendNotification('Data extracted successfully', 'success');
        } catch (error) {
            console.error('❌ Data extraction failed:', error);
            this.sendNotification('Data extraction failed', 'error');
        }
    }

    async handleMessage(request, sender, sendResponse) {
        try {
            switch (request.action) {
                case 'execute_automation':
                    const automationResult = await this.executeAutomation(request.config);
                    sendResponse({ success: true, result: automationResult });
                    break;

                case 'cross_origin_request':
                    const proxyResult = await this.crossOriginProxy.makeRequest(request.requestConfig);
                    sendResponse({ success: true, result: proxyResult });
                    break;

                case 'get_page_data':
                    const pageData = await this.getPageData(sender.tab.id);
                    sendResponse({ success: true, data: pageData });
                    break;

                case 'notification':
                    this.sendNotification(request.message, request.type);
                    sendResponse({ success: true });
                    break;

                default:
                    sendResponse({ success: false, error: 'Unknown action' });
            }
        } catch (error) {
            console.error('❌ Message handling failed:', error);
            sendResponse({ success: false, error: error.message });
        }
    }

    async executeAutomation(config) {
        try {
            const { tabId, steps } = config;
            const results = [];

            for (const step of steps) {
                const stepResult = await chrome.scripting.executeScript({
                    target: { tabId: tabId },
                    function: (stepConfig) => {
                        return window.aetherAutomation?.executeStep(stepConfig);
                    },
                    args: [step]
                });

                results.push(stepResult[0]?.result);
                
                // Add delay between steps
                await new Promise(resolve => setTimeout(resolve, step.delay || 1000));
            }

            return { success: true, results: results };
        } catch (error) {
            console.error('❌ Automation execution failed:', error);
            return { success: false, error: error.message };
        }
    }

    async sendToMainApp(action, data) {
        try {
            const response = await fetch(`${this.webAppURL}/api/extension-bridge`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ action, data })
            });

            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.log('Main app not available, operating in standalone mode');
        }
        return null;
    }

    sendNotification(message, type = 'info') {
        const iconUrl = type === 'error' ? 'icons/error.png' : 
                      type === 'success' ? 'icons/success.png' : 
                      'icons/icon-48.png';

        chrome.notifications.create({
            type: 'basic',
            iconUrl: iconUrl,
            title: 'AETHER Extension',
            message: message
        });
    }

    handleWebRequest(details) {
        // Handle cross-origin requests for automation
        if (details.url.includes('aether-proxy')) {
            return { cancel: false };
        }
        return {};
    }
}

// Cross-Origin Proxy for bypassing CORS limitations
class CrossOriginProxy {
    constructor() {
        this.proxyEndpoint = 'https://cors-anywhere.herokuapp.com/';
    }

    async initialize() {
        // Set up proxy configurations
        console.log('Cross-origin proxy ready');
    }

    async makeRequest(config) {
        try {
            const { url, method = 'GET', headers = {}, body } = config;
            
            const response = await fetch(this.proxyEndpoint + url, {
                method: method,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    ...headers
                },
                body: body ? JSON.stringify(body) : undefined
            });

            const data = await response.text();
            
            return {
                success: true,
                status: response.status,
                data: data,
                headers: Object.fromEntries(response.headers.entries())
            };
        } catch (error) {
            console.error('❌ Cross-origin request failed:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
}

// Initialize the extension engine
const aetherExtension = new AetherExtensionEngine();