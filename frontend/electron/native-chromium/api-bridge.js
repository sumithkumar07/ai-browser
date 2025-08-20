/**
 * Native API Bridge - Communication Layer between Native Engine and Frontend
 * Provides seamless integration between Electron main process and React renderer
 */
class NativeAPIBridge {
  constructor(nativeEngine) {
    this.nativeEngine = nativeEngine;
    this.eventListeners = new Map();
    
    console.log('🔗 Native API Bridge Initialized');
  }

  // Navigation Methods
  async navigateToUrl(sessionId, url) {
    try {
      const result = await this.nativeEngine.navigate(url);
      
      if (result.success) {
        this.emitEvent('navigation-success', {
          sessionId,
          url: result.url,
          canGoBack: result.canGoBack,
          canGoForward: result.canGoForward,
          timestamp: Date.now()
        });
      }
      
      return result;
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async browserGoBack(sessionId) {
    try {
      const result = await this.nativeEngine.goBack();
      
      if (result.success) {
        this.emitEvent('navigation-back', {
          sessionId,
          url: result.url,
          canGoBack: result.canGoBack,
          canGoForward: result.canGoForward
        });
      }
      
      return result;
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async browserGoForward(sessionId) {
    try {
      const result = await this.nativeEngine.goForward();
      
      if (result.success) {
        this.emitEvent('navigation-forward', {
          sessionId,
          url: result.url,
          canGoBack: result.canGoBack,
          canGoForward: result.canGoForward
        });
      }
      
      return result;
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async browserRefresh(sessionId) {
    try {
      const result = await this.nativeEngine.refresh();
      
      if (result.success) {
        this.emitEvent('navigation-refresh', {
          sessionId,
          url: result.url
        });
      }
      
      return result;
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Screenshot and DevTools
  async captureScreenshot(sessionId, options = {}) {
    try {
      const result = await this.nativeEngine.captureScreenshot(options);
      
      if (result.success) {
        this.emitEvent('screenshot-captured', {
          sessionId,
          size: result.size,
          timestamp: Date.now()
        });
      }
      
      return result;
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async executeJavaScript(sessionId, code) {
    try {
      const result = await this.nativeEngine.executeJavaScript(code);
      
      if (result.success) {
        this.emitEvent('javascript-executed', {
          sessionId,
          code: code.substring(0, 100) + (code.length > 100 ? '...' : ''),
          result: result.result
        });
      }
      
      return result;
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async injectCSS(sessionId, css) {
    try {
      const result = await this.nativeEngine.injectCSS(css);
      
      if (result.success) {
        this.emitEvent('css-injected', {
          sessionId,
          cssLength: css.length
        });
      }
      
      return result;
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // State Queries
  getCurrentState() {
    return {
      url: this.nativeEngine.getCurrentUrl(),
      canGoBack: this.nativeEngine.canGoBack(),
      canGoForward: this.nativeEngine.canGoForward(),
      history: this.nativeEngine.getNavigationHistory()
    };
  }

  // Enhanced Web Automation
  async automateWebAction(sessionId, action) {
    try {
      let result = { success: false };

      switch (action.type) {
        case 'click':
          result = await this.executeJavaScript(sessionId, `
            (function() {
              const element = document.querySelector('${action.selector}');
              if (element) {
                element.click();
                return { success: true, action: 'clicked', selector: '${action.selector}' };
              }
              return { success: false, error: 'Element not found' };
            })();
          `);
          break;

        case 'type':
          result = await this.executeJavaScript(sessionId, `
            (function() {
              const element = document.querySelector('${action.selector}');
              if (element) {
                element.value = '${action.text}';
                element.dispatchEvent(new Event('input', { bubbles: true }));
                return { success: true, action: 'typed', text: '${action.text}' };
              }
              return { success: false, error: 'Element not found' };
            })();
          `);
          break;

        case 'scroll':
          result = await this.executeJavaScript(sessionId, `
            window.scrollTo(${action.x || 0}, ${action.y || 0});
            return { success: true, action: 'scrolled', x: ${action.x || 0}, y: ${action.y || 0} };
          `);
          break;

        case 'extract':
          result = await this.executeJavaScript(sessionId, `
            (function() {
              const elements = document.querySelectorAll('${action.selector}');
              const data = Array.from(elements).map(el => ({
                text: el.textContent?.trim(),
                html: el.innerHTML,
                attributes: Object.fromEntries(Array.from(el.attributes).map(attr => [attr.name, attr.value]))
              }));
              return { success: true, action: 'extracted', data: data };
            })();
          `);
          break;

        case 'wait':
          await new Promise(resolve => setTimeout(resolve, action.duration || 1000));
          result = { success: true, action: 'waited', duration: action.duration || 1000 };
          break;

        default:
          result = { success: false, error: 'Unknown action type' };
      }

      if (result.success) {
        this.emitEvent('web-action-completed', {
          sessionId,
          action: action.type,
          result: result.result || result
        });
      }

      return result;

    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Batch Web Automation
  async executeBatchActions(sessionId, actions) {
    const results = [];
    
    for (const action of actions) {
      try {
        const result = await this.automateWebAction(sessionId, action);
        results.push(result);
        
        // Stop on first failure if specified
        if (!result.success && action.stopOnFailure) {
          break;
        }
        
        // Add delay between actions
        if (action.delay) {
          await new Promise(resolve => setTimeout(resolve, action.delay));
        }
        
      } catch (error) {
        results.push({ success: false, error: error.message, action });
        break;
      }
    }
    
    this.emitEvent('batch-actions-completed', {
      sessionId,
      totalActions: actions.length,
      completedActions: results.length,
      successfulActions: results.filter(r => r.success).length,
      results
    });
    
    return {
      success: true,
      totalActions: actions.length,
      results
    };
  }

  // Page Analysis
  async analyzePage(sessionId) {
    try {
      const result = await this.executeJavaScript(sessionId, `
        (function() {
          const analysis = {
            title: document.title,
            url: window.location.href,
            domain: window.location.hostname,
            
            // Content analysis
            wordCount: document.body.textContent.trim().split(/\\s+/).length,
            images: document.images.length,
            links: document.links.length,
            forms: document.forms.length,
            
            // SEO elements
            metaDescription: document.querySelector('meta[name="description"]')?.content || '',
            metaKeywords: document.querySelector('meta[name="keywords"]')?.content || '',
            headings: {
              h1: document.querySelectorAll('h1').length,
              h2: document.querySelectorAll('h2').length,
              h3: document.querySelectorAll('h3').length
            },
            
            // Technical details
            hasJavaScript: !!document.scripts.length,
            hasCSS: !!document.styleSheets.length,
            viewport: document.querySelector('meta[name="viewport"]')?.content || '',
            
            // Performance hints
            loadTime: performance.timing.loadEventEnd - performance.timing.navigationStart,
            domContentLoaded: performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart,
            
            // Accessibility
            altTexts: Array.from(document.images).filter(img => !img.alt).length,
            
            timestamp: Date.now()
          };
          
          return analysis;
        })();
      `);
      
      if (result.success) {
        this.emitEvent('page-analyzed', {
          sessionId,
          analysis: result.result
        });
      }
      
      return result;
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Event System
  addEventListener(event, callback) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(callback);
  }

  removeEventListener(event, callback) {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  emitEvent(event, data) {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Event listener error:', error);
        }
      });
    }
  }

  // Cleanup
  cleanup() {
    this.eventListeners.clear();
    console.log('✅ Native API Bridge Cleanup Complete');
  }
}

module.exports = NativeAPIBridge;