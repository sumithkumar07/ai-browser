// DOM Analyzer for AETHER Extension
class AetherDOMAnalyzer {
    constructor() {
        this.pageStructure = null;
        this.automationElements = [];
        this.initialize();
    }

    initialize() {
        console.log('🔍 AETHER DOM Analyzer initialized');
        this.analyzePageStructure();
        this.identifyAutomationElements();
        this.setupMutationObserver();
    }

    analyzePageStructure() {
        const structure = {
            url: window.location.href,
            title: document.title,
            domain: window.location.hostname,
            timestamp: Date.now(),
            
            // Navigation elements
            navigation: this.findNavigationElements(),
            
            // Forms and inputs
            forms: this.analyzeForms(),
            
            // Interactive elements
            buttons: this.findButtons(),
            links: this.findLinks(),
            
            // Content areas
            content: this.analyzeContent(),
            
            // Media elements
            media: this.findMediaElements(),
            
            // Automation opportunities
            automationTargets: this.identifyAutomationTargets()
        };

        this.pageStructure = structure;
        return structure;
    }

    findNavigationElements() {
        const navSelectors = [
            'nav', '[role="navigation"]', '.navigation', '.navbar', 
            '.nav', '.menu', '.header-nav', '#nav', '#navigation'
        ];

        const navElements = [];
        
        navSelectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                navElements.push({
                    selector: this.generateSelector(el),
                    text: el.textContent.trim().substring(0, 100),
                    links: Array.from(el.querySelectorAll('a')).map(a => ({
                        text: a.textContent.trim(),
                        href: a.href
                    }))
                });
            });
        });

        return navElements;
    }

    analyzeForms() {
        const forms = Array.from(document.querySelectorAll('form')).map(form => {
            const inputs = Array.from(form.querySelectorAll('input, textarea, select')).map(input => ({
                type: input.type || input.tagName.toLowerCase(),
                name: input.name,
                id: input.id,
                placeholder: input.placeholder,
                required: input.required,
                selector: this.generateSelector(input),
                value: input.value
            }));

            return {
                selector: this.generateSelector(form),
                action: form.action,
                method: form.method,
                inputs: inputs,
                submitButtons: Array.from(form.querySelectorAll('input[type="submit"], button[type="submit"]')).map(btn => ({
                    text: btn.textContent || btn.value,
                    selector: this.generateSelector(btn)
                }))
            };
        });

        return forms;
    }

    findButtons() {
        const buttons = Array.from(document.querySelectorAll('button, input[type="button"], input[type="submit"], [role="button"]')).map(btn => ({
            text: btn.textContent || btn.value || btn.title,
            selector: this.generateSelector(btn),
            type: btn.type,
            disabled: btn.disabled,
            clickable: !btn.disabled && btn.offsetParent !== null
        }));

        return buttons;
    }

    findLinks() {
        const links = Array.from(document.querySelectorAll('a[href]')).map(link => ({
            text: link.textContent.trim(),
            href: link.href,
            selector: this.generateSelector(link),
            target: link.target,
            internal: link.hostname === window.location.hostname
        }));

        return links.filter(link => link.text.length > 0);
    }

    analyzeContent() {
        const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6')).map(h => ({
            level: parseInt(h.tagName[1]),
            text: h.textContent.trim(),
            selector: this.generateSelector(h)
        }));

        const paragraphs = Array.from(document.querySelectorAll('p')).slice(0, 10).map(p => ({
            text: p.textContent.trim().substring(0, 200),
            selector: this.generateSelector(p)
        }));

        return { headings, paragraphs };
    }

    findMediaElements() {
        const images = Array.from(document.querySelectorAll('img')).map(img => ({
            src: img.src,
            alt: img.alt,
            selector: this.generateSelector(img)
        }));

        const videos = Array.from(document.querySelectorAll('video')).map(video => ({
            src: video.src,
            selector: this.generateSelector(video)
        }));

        return { images: images.slice(0, 20), videos };
    }

    identifyAutomationTargets() {
        const targets = [];

        // Login forms
        const loginForms = Array.from(document.querySelectorAll('form')).filter(form => {
            const formText = form.textContent.toLowerCase();
            return formText.includes('login') || formText.includes('sign in') || 
                   formText.includes('email') || formText.includes('password');
        });

        loginForms.forEach(form => {
            targets.push({
                type: 'login_form',
                selector: this.generateSelector(form),
                confidence: 0.9,
                description: 'Login form detected'
            });
        });

        // Search functionality
        const searchInputs = Array.from(document.querySelectorAll('input[type="search"], input[placeholder*="search"], input[name*="search"]'));
        searchInputs.forEach(input => {
            targets.push({
                type: 'search_input',
                selector: this.generateSelector(input),
                confidence: 0.8,
                description: 'Search input detected'
            });
        });

        // Shopping/ecommerce elements
        const buyButtons = Array.from(document.querySelectorAll('button, a')).filter(el => {
            const text = el.textContent.toLowerCase();
            return text.includes('buy') || text.includes('add to cart') || 
                   text.includes('purchase') || text.includes('checkout');
        });

        buyButtons.forEach(btn => {
            targets.push({
                type: 'purchase_button',
                selector: this.generateSelector(btn),
                confidence: 0.7,
                description: 'Purchase/buy button detected'
            });
        });

        return targets;
    }

    generateSelector(element) {
        // Generate a unique CSS selector for the element
        if (element.id) {
            return `#${element.id}`;
        }

        if (element.className && typeof element.className === 'string') {
            const classes = element.className.split(' ').filter(c => c.length > 0);
            if (classes.length > 0) {
                return `.${classes.join('.')}`;
            }
        }

        // Fallback to tag + nth-child
        const parent = element.parentElement;
        if (parent) {
            const siblings = Array.from(parent.children);
            const index = siblings.indexOf(element);
            return `${element.tagName.toLowerCase()}:nth-child(${index + 1})`;
        }

        return element.tagName.toLowerCase();
    }

    setupMutationObserver() {
        const observer = new MutationObserver((mutations) => {
            let shouldReanalyze = false;

            mutations.forEach(mutation => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // Check if important elements were added
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === 1) { // Element node
                            const tagName = node.tagName?.toLowerCase();
                            if (['form', 'button', 'input', 'a'].includes(tagName)) {
                                shouldReanalyze = true;
                            }
                        }
                    });
                }
            });

            if (shouldReanalyze) {
                setTimeout(() => this.analyzePageStructure(), 1000);
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    getPageStructure() {
        return this.pageStructure;
    }

    extractPageData() {
        return {
            type: 'full_page',
            data: {
                title: document.title,
                url: window.location.href,
                content: document.body.textContent.trim().substring(0, 5000),
                structure: this.pageStructure,
                extractedAt: Date.now()
            }
        };
    }

    identifyAutomationOpportunities() {
        const opportunities = [];

        // Form automation opportunities
        this.pageStructure?.forms?.forEach(form => {
            if (form.inputs.length > 0) {
                opportunities.push({
                    type: 'form_automation',
                    target: form.selector,
                    description: `Automate form with ${form.inputs.length} fields`,
                    confidence: 0.8
                });
            }
        });

        // Navigation automation
        if (this.pageStructure?.navigation?.length > 0) {
            opportunities.push({
                type: 'navigation_automation',
                description: 'Automate navigation through site menu',
                confidence: 0.6
            });
        }

        return opportunities;
    }
}

// Initialize DOM Analyzer
window.aetherAnalyzer = new AetherDOMAnalyzer();