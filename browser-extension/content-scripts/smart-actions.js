// Smart Actions Engine for AETHER Extension
class AetherSmartActions {
    constructor() {
        this.actionHistory = [];
        this.contextualActions = [];
        this.initialize();
    }

    initialize() {
        console.log('🧠 AETHER Smart Actions initialized');
        this.analyzePageContext();
        this.generateContextualActions();
        this.setupActionTriggers();
    }

    analyzePageContext() {
        const context = {
            domain: window.location.hostname,
            url: window.location.href,
            title: document.title,
            pageType: this.identifyPageType(),
            userIntent: this.predictUserIntent(),
            availableActions: this.discoverAvailableActions()
        };

        this.pageContext = context;
        return context;
    }

    identifyPageType() {
        const url = window.location.href.toLowerCase();
        const title = document.title.toLowerCase();
        const content = document.body.textContent.toLowerCase();

        // E-commerce detection
        if (url.includes('shop') || url.includes('store') || url.includes('cart') ||
            content.includes('add to cart') || content.includes('price') ||
            document.querySelectorAll('[data-price], .price, .cost').length > 0) {
            return 'ecommerce';
        }

        // Social media detection
        if (['twitter.com', 'facebook.com', 'linkedin.com', 'instagram.com'].some(domain => 
            window.location.hostname.includes(domain))) {
            return 'social_media';
        }

        // Documentation/article detection
        if (title.includes('documentation') || title.includes('docs') ||
            content.includes('tutorial') || content.includes('guide') ||
            document.querySelectorAll('article, .article, .documentation').length > 0) {
            return 'documentation';
        }

        // Form-heavy pages
        if (document.querySelectorAll('form').length > 2 ||
            document.querySelectorAll('input, textarea, select').length > 5) {
            return 'form_intensive';
        }

        // News/blog detection
        if (document.querySelectorAll('article, .post, .news-item').length > 0 ||
            title.includes('news') || url.includes('blog')) {
            return 'news_blog';
        }

        return 'general';
    }

    predictUserIntent() {
        const intents = [];
        const pageType = this.pageContext?.pageType;

        switch (pageType) {
            case 'ecommerce':
                intents.push('shopping', 'price_comparison', 'product_research');
                break;
            case 'social_media':
                intents.push('social_interaction', 'content_sharing', 'networking');
                break;
            case 'documentation':
                intents.push('learning', 'reference', 'implementation');
                break;
            case 'form_intensive':
                intents.push('data_entry', 'registration', 'application');
                break;
            case 'news_blog':
                intents.push('information_gathering', 'reading', 'research');
                break;
            default:
                intents.push('browsing', 'information_seeking');
        }

        return intents;
    }

    discoverAvailableActions() {
        const actions = [];

        // Form actions
        const forms = document.querySelectorAll('form');
        forms.forEach((form, index) => {
            actions.push({
                type: 'form_fill',
                target: this.generateSelector(form),
                description: `Auto-fill form ${index + 1}`,
                confidence: 0.9
            });
        });

        // Navigation actions
        const navLinks = document.querySelectorAll('nav a, .navigation a, .menu a');
        if (navLinks.length > 0) {
            actions.push({
                type: 'smart_navigation',
                description: `Navigate through ${navLinks.length} menu items`,
                confidence: 0.7
            });
        }

        // Data extraction actions
        const tables = document.querySelectorAll('table');
        const lists = document.querySelectorAll('ul, ol');
        if (tables.length > 0 || lists.length > 3) {
            actions.push({
                type: 'data_extraction',
                description: 'Extract structured data from page',
                confidence: 0.8
            });
        }

        // Search actions
        const searchInputs = document.querySelectorAll('input[type="search"], input[placeholder*="search"]');
        searchInputs.forEach(input => {
            actions.push({
                type: 'smart_search',
                target: this.generateSelector(input),
                description: 'Execute intelligent search',
                confidence: 0.8
            });
        });

        return actions;
    }

    generateContextualActions() {
        const pageType = this.pageContext?.pageType;
        const actions = [];

        switch (pageType) {
            case 'ecommerce':
                actions.push(
                    {
                        id: 'price_monitor',
                        title: '💰 Monitor Price Changes',
                        description: 'Set up price alerts for products on this page',
                        action: () => this.setupPriceMonitoring()
                    },
                    {
                        id: 'compare_prices',
                        title: '🔍 Compare Prices',
                        description: 'Find better prices for these products',
                        action: () => this.comparePrices()
                    },
                    {
                        id: 'auto_checkout',
                        title: '⚡ Smart Checkout',
                        description: 'Automate the checkout process',
                        action: () => this.automateCheckout()
                    }
                );
                break;

            case 'social_media':
                actions.push(
                    {
                        id: 'bulk_actions',
                        title: '📱 Bulk Social Actions',
                        description: 'Perform bulk likes, shares, or follows',
                        action: () => this.bulkSocialActions()
                    },
                    {
                        id: 'content_scheduler',
                        title: '📅 Schedule Content',
                        description: 'Schedule posts across platforms',
                        action: () => this.scheduleContent()
                    },
                    {
                        id: 'engagement_boost',
                        title: '🚀 Boost Engagement',
                        description: 'Optimize posting times and content',
                        action: () => this.boostEngagement()
                    }
                );
                break;

            case 'form_intensive':
                actions.push(
                    {
                        id: 'smart_form_fill',
                        title: '📝 Smart Form Filling',
                        description: 'Auto-fill forms with saved data',
                        action: () => this.smartFormFill()
                    },
                    {
                        id: 'form_validation',
                        title: '✅ Validate Before Submit',
                        description: 'Check all fields before submission',
                        action: () => this.validateForms()
                    },
                    {
                        id: 'save_form_data',
                        title: '💾 Save Form Progress',
                        description: 'Save form data for later completion',
                        action: () => this.saveFormProgress()
                    }
                );
                break;

            case 'documentation':
                actions.push(
                    {
                        id: 'smart_summarize',
                        title: '📋 Smart Summarize',
                        description: 'Create intelligent summary of content',
                        action: () => this.smartSummarize()
                    },
                    {
                        id: 'extract_code',
                        title: '💻 Extract Code Examples',
                        description: 'Collect all code snippets',
                        action: () => this.extractCodeExamples()
                    },
                    {
                        id: 'create_notes',
                        title: '📓 Create Study Notes',
                        description: 'Generate structured notes',
                        action: () => this.createStudyNotes()
                    }
                );
                break;

            default:
                actions.push(
                    {
                        id: 'page_analysis',
                        title: '🔍 Analyze Page',
                        description: 'Deep analysis of page structure and content',
                        action: () => this.analyzePage()
                    },
                    {
                        id: 'extract_links',
                        title: '🔗 Extract All Links',
                        description: 'Collect and organize all page links',
                        action: () => this.extractAllLinks()
                    }
                );
        }

        this.contextualActions = actions;
        return actions;
    }

    async setupPriceMonitoring() {
        try {
            const priceElements = document.querySelectorAll('[data-price], .price, .cost, .amount');
            const products = [];

            priceElements.forEach(el => {
                const price = this.extractPrice(el.textContent);
                if (price) {
                    products.push({
                        name: this.findProductName(el),
                        price: price,
                        url: window.location.href,
                        selector: this.generateSelector(el)
                    });
                }
            });

            await this.sendToBackground({
                action: 'setup_price_monitoring',
                products: products
            });

            this.showNotification('Price monitoring set up for ' + products.length + ' products');
        } catch (error) {
            console.error('Price monitoring setup failed:', error);
        }
    }

    async smartFormFill() {
        try {
            const forms = document.querySelectorAll('form');
            let filledCount = 0;

            for (const form of forms) {
                const inputs = form.querySelectorAll('input, textarea, select');
                
                for (const input of inputs) {
                    const fillValue = await this.predictFieldValue(input);
                    if (fillValue) {
                        input.value = fillValue;
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                        filledCount++;
                    }
                }
            }

            this.showNotification(`Smart-filled ${filledCount} form fields`);
        } catch (error) {
            console.error('Smart form fill failed:', error);
        }
    }

    async bulkSocialActions() {
        try {
            const likeButtons = document.querySelectorAll('[aria-label*="like"], .like-button, [data-action="like"]');
            const shareButtons = document.querySelectorAll('[aria-label*="share"], .share-button, [data-action="share"]');
            
            let actions = 0;

            // Perform actions with delays to avoid rate limiting
            for (const button of likeButtons.slice(0, 10)) {
                if (button.offsetParent !== null && !button.disabled) {
                    button.click();
                    actions++;
                    await this.delay(1000);
                }
            }

            this.showNotification(`Performed ${actions} bulk social actions`);
        } catch (error) {
            console.error('Bulk social actions failed:', error);
        }
    }

    async smartSummarize() {
        try {
            const content = this.extractMainContent();
            
            await this.sendToBackground({
                action: 'create_smart_summary',
                content: content,
                url: window.location.href,
                title: document.title
            });

            this.showNotification('Intelligent summary created');
        } catch (error) {
            console.error('Smart summarization failed:', error);
        }
    }

    extractMainContent() {
        // Priority selectors for main content
        const contentSelectors = [
            'article', '.article', '.content', '.main-content',
            '.post', '.blog-post', '#content', 'main',
            '.documentation', '.docs'
        ];

        for (const selector of contentSelectors) {
            const element = document.querySelector(selector);
            if (element) {
                return element.textContent.trim();
            }
        }

        // Fallback to body content
        return document.body.textContent.trim();
    }

    async predictFieldValue(input) {
        const fieldName = (input.name || input.id || input.placeholder || '').toLowerCase();
        const fieldType = input.type;

        // Get saved user data from storage
        const userData = await this.getUserData();

        if (fieldType === 'email' || fieldName.includes('email')) {
            return userData.email || '';
        }
        if (fieldName.includes('name') && !fieldName.includes('user')) {
            return userData.fullName || '';
        }
        if (fieldName.includes('phone')) {
            return userData.phone || '';
        }
        if (fieldName.includes('address')) {
            return userData.address || '';
        }
        if (fieldName.includes('city')) {
            return userData.city || '';
        }
        if (fieldName.includes('zip') || fieldName.includes('postal')) {
            return userData.zipCode || '';
        }

        return null;
    }

    async getUserData() {
        return new Promise((resolve) => {
            chrome.storage.sync.get(['userData'], (result) => {
                resolve(result.userData || {});
            });
        });
    }

    extractPrice(text) {
        const priceRegex = /[\$£€¥]\s*[\d,]+\.?\d*/g;
        const matches = text.match(priceRegex);
        return matches ? matches[0] : null;
    }

    findProductName(priceElement) {
        // Look for product name in nearby elements
        const parent = priceElement.closest('[data-product], .product, .item');
        if (parent) {
            const nameEl = parent.querySelector('.name, .title, h1, h2, h3');
            if (nameEl) return nameEl.textContent.trim();
        }
        
        // Fallback to page title
        return document.title;
    }

    generateSelector(element) {
        if (element.id) return `#${element.id}`;
        if (element.className) {
            const classes = element.className.split(' ').filter(c => c.length > 0);
            if (classes.length > 0) return `.${classes.join('.')}`;
        }
        return element.tagName.toLowerCase();
    }

    async sendToBackground(message) {
        return new Promise((resolve) => {
            chrome.runtime.sendMessage(message, resolve);
        });
    }

    showNotification(message) {
        // Create in-page notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4F46E5;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            z-index: 10000;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 14px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    async delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    setupActionTriggers() {
        // Set up keyboard shortcuts for quick actions
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey) {
                switch (e.key) {
                    case 'A':
                        e.preventDefault();
                        this.showActionPanel();
                        break;
                    case 'F':
                        e.preventDefault();
                        this.smartFormFill();
                        break;
                    case 'S':
                        e.preventDefault();
                        this.smartSummarize();
                        break;
                }
            }
        });
    }

    showActionPanel() {
        // Create floating action panel
        if (document.getElementById('aether-action-panel')) return;

        const panel = document.createElement('div');
        panel.id = 'aether-action-panel';
        panel.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 20px;
            z-index: 10001;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            max-width: 400px;
            width: 90%;
        `;

        const title = document.createElement('h3');
        title.textContent = 'AETHER Smart Actions';
        title.style.cssText = 'margin: 0 0 15px 0; color: #1f2937; font-size: 18px;';
        panel.appendChild(title);

        this.contextualActions.forEach(action => {
            const button = document.createElement('button');
            button.textContent = action.title;
            button.style.cssText = `
                display: block;
                width: 100%;
                padding: 10px 15px;
                margin: 5px 0;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                background: #f9fafb;
                color: #374151;
                cursor: pointer;
                font-size: 14px;
            `;
            
            button.onclick = () => {
                action.action();
                panel.remove();
            };
            
            panel.appendChild(button);
        });

        // Close button
        const closeBtn = document.createElement('button');
        closeBtn.textContent = '✕';
        closeBtn.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            border: none;
            background: none;
            font-size: 18px;
            cursor: pointer;
            color: #6b7280;
        `;
        closeBtn.onclick = () => panel.remove();
        panel.appendChild(closeBtn);

        document.body.appendChild(panel);
    }
}

// Initialize Smart Actions
window.aetherSmartActions = new AetherSmartActions();