const puppeteer = require('puppeteer-core');
const { chromium } = require('playwright');

class NativeBrowserEngine {
    constructor() {
        this.browser = null;
        this.page = null;
        this.sessions = new Map();
    }

    async initialize() {
        try {
            // Use Chromium with full access
            this.browser = await chromium.launch({
                headless: false,
                args: [
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
            });

            this.page = await this.browser.newPage();
            
            // Enable enhanced permissions
            await this.page.context().grantPermissions([
                'geolocation',
                'notifications',
                'camera',
                'microphone'
            ]);

            console.log('✅ Native Browser Engine initialized');
            return { success: true, message: 'Browser engine ready' };
        } catch (error) {
            console.error('❌ Browser Engine initialization failed:', error);
            return { success: false, error: error.message };
        }
    }

    async navigateToUrl(url) {
        try {
            if (!this.page) {
                await this.initialize();
            }

            // Enhanced navigation with cross-origin support
            await this.page.goto(url, { 
                waitUntil: 'networkidle',
                timeout: 30000 
            });

            const title = await this.page.title();
            const content = await this.page.content();

            return {
                success: true,
                url: url,
                title: title,
                content: content.substring(0, 5000) // Limit content size
            };
        } catch (error) {
            console.error('❌ Navigation failed:', error);
            return { success: false, error: error.message };
        }
    }

    async executeScript(script) {
        try {
            if (!this.page) {
                throw new Error('Browser not initialized');
            }

            const result = await this.page.evaluate(script);
            return { success: true, result: result };
        } catch (error) {
            console.error('❌ Script execution failed:', error);
            return { success: false, error: error.message };
        }
    }

    async getPageContent() {
        try {
            if (!this.page) {
                throw new Error('Browser not initialized');
            }

            const title = await this.page.title();
            const url = this.page.url();
            const content = await this.page.content();

            // Extract structured data
            const pageData = await this.page.evaluate(() => {
                return {
                    links: Array.from(document.querySelectorAll('a')).map(a => ({
                        text: a.textContent.trim(),
                        href: a.href
                    })).slice(0, 20),
                    forms: Array.from(document.querySelectorAll('form')).map(form => ({
                        action: form.action,
                        method: form.method,
                        inputs: Array.from(form.querySelectorAll('input')).map(input => ({
                            type: input.type,
                            name: input.name,
                            placeholder: input.placeholder
                        }))
                    })),
                    images: Array.from(document.querySelectorAll('img')).map(img => ({
                        src: img.src,
                        alt: img.alt
                    })).slice(0, 10)
                };
            });

            return {
                success: true,
                title: title,
                url: url,
                content: content,
                structured_data: pageData
            };
        } catch (error) {
            console.error('❌ Failed to get page content:', error);
            return { success: false, error: error.message };
        }
    }

    async executeCrossOriginAutomation(config) {
        try {
            if (!this.page) {
                await this.initialize();
            }

            const { steps, target_url } = config;
            const results = [];

            // Navigate to target if needed
            if (target_url && this.page.url() !== target_url) {
                await this.navigateToUrl(target_url);
            }

            // Execute automation steps
            for (const step of steps) {
                let stepResult;

                switch (step.action) {
                    case 'click':
                        await this.page.click(step.selector);
                        stepResult = { action: 'click', selector: step.selector, success: true };
                        break;

                    case 'type':
                        await this.page.fill(step.selector, step.text);
                        stepResult = { action: 'type', selector: step.selector, text: step.text, success: true };
                        break;

                    case 'extract':
                        const extractedData = await this.page.evaluate((selector) => {
                            const element = document.querySelector(selector);
                            return element ? element.textContent.trim() : null;
                        }, step.selector);
                        stepResult = { action: 'extract', selector: step.selector, data: extractedData, success: true };
                        break;

                    case 'wait':
                        await this.page.waitForSelector(step.selector, { timeout: step.timeout || 5000 });
                        stepResult = { action: 'wait', selector: step.selector, success: true };
                        break;

                    default:
                        stepResult = { action: step.action, success: false, error: 'Unknown action' };
                }

                results.push(stepResult);
                
                // Add delay between steps
                await this.page.waitForTimeout(step.delay || 1000);
            }

            return {
                success: true,
                automation_results: results,
                final_url: this.page.url()
            };
        } catch (error) {
            console.error('❌ Cross-origin automation failed:', error);
            return { success: false, error: error.message };
        }
    }

    async close() {
        try {
            if (this.browser) {
                await this.browser.close();
                this.browser = null;
                this.page = null;
            }
        } catch (error) {
            console.error('❌ Failed to close browser:', error);
        }
    }
}

module.exports = { NativeBrowserEngine };