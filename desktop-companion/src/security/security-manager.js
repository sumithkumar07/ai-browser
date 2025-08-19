/**
 * Security Manager for AETHER Desktop Companion
 * Ensures secure operations and prevents malicious automation
 */

const crypto = require('crypto');
const path = require('path');
const fs = require('fs').promises;

class SecurityManager {
    constructor() {
        this.allowedOperations = new Set([
            'navigate',
            'click',
            'type',
            'screenshot',
            'script_execute',
            'cross_origin_automation',
            'computer_use'
        ]);
        
        this.securityPolicies = {
            maxAutomationDuration: 30000, // 30 seconds
            maxConcurrentOperations: 10,
            requireUserConfirmation: [
                'system_file_access',
                'registry_modification', 
                'process_termination'
            ],
            blockedDomains: [
                'banking.com',
                'financial.gov'
            ],
            rateLimits: {
                'computer_use': { max: 100, window: 60000 }, // 100 per minute
                'cross_origin': { max: 50, window: 60000 }    // 50 per minute
            }
        };
        
        this.operationHistory = [];
        this.rateLimitCounters = new Map();
        this.activeOperations = new Set();
    }

    async initialize() {
        try {
            // Load security configuration if exists
            await this.loadSecurityConfig();
            
            // Initialize rate limiting
            this.initializeRateLimiting();
            
            console.log('✅ Security Manager initialized');
            return { success: true };
        } catch (error) {
            console.error('❌ Security Manager initialization failed:', error);
            return { success: false, error: error.message };
        }
    }

    async validateOperation(operation) {
        try {
            const { type, target, params, requester } = operation;
            
            // Basic operation type validation
            if (!this.allowedOperations.has(type)) {
                return {
                    success: false,
                    error: `Operation type '${type}' not allowed`,
                    code: 'INVALID_OPERATION'
                };
            }
            
            // Rate limiting check
            const rateLimitResult = this.checkRateLimit(type, requester);
            if (!rateLimitResult.allowed) {
                return {
                    success: false,
                    error: 'Rate limit exceeded',
                    code: 'RATE_LIMIT_EXCEEDED',
                    retryAfter: rateLimitResult.retryAfter
                };
            }
            
            // Domain validation for navigation operations
            if (type === 'navigate' && target) {
                const domainCheck = this.validateDomain(target);
                if (!domainCheck.allowed) {
                    return {
                        success: false,
                        error: `Domain '${target}' is blocked`,
                        code: 'DOMAIN_BLOCKED'
                    };
                }
            }
            
            // Concurrent operations check
            if (this.activeOperations.size >= this.securityPolicies.maxConcurrentOperations) {
                return {
                    success: false,
                    error: 'Maximum concurrent operations exceeded',
                    code: 'CONCURRENT_LIMIT_EXCEEDED'
                };
            }
            
            // User confirmation check for sensitive operations
            if (this.securityPolicies.requireUserConfirmation.includes(type)) {
                const userConfirm = await this.requestUserConfirmation(operation);
                if (!userConfirm) {
                    return {
                        success: false,
                        error: 'User confirmation required but not granted',
                        code: 'USER_CONFIRMATION_DENIED'
                    };
                }
            }
            
            // Script validation for script execution operations
            if (type === 'script_execute') {
                const scriptValidation = this.validateScript(params.script);
                if (!scriptValidation.safe) {
                    return {
                        success: false,
                        error: 'Script contains potentially dangerous operations',
                        code: 'SCRIPT_VALIDATION_FAILED',
                        details: scriptValidation.issues
                    };
                }
            }
            
            // Generate operation token
            const operationToken = this.generateOperationToken(operation);
            
            // Log operation
            this.logOperation(operation, operationToken);
            
            // Track active operation
            this.activeOperations.add(operationToken);
            
            return {
                success: true,
                operationToken: operationToken,
                validatedParams: this.sanitizeParams(params),
                expiresAt: Date.now() + this.securityPolicies.maxAutomationDuration
            };
            
        } catch (error) {
            return {
                success: false,
                error: error.message,
                code: 'VALIDATION_ERROR'
            };
        }
    }

    checkRateLimit(operationType, requester) {
        const rateLimitConfig = this.securityPolicies.rateLimits[operationType];
        if (!rateLimitConfig) {
            return { allowed: true };
        }
        
        const now = Date.now();
        const windowStart = now - rateLimitConfig.window;
        const key = `${operationType}:${requester || 'anonymous'}`;
        
        if (!this.rateLimitCounters.has(key)) {
            this.rateLimitCounters.set(key, []);
        }
        
        const requests = this.rateLimitCounters.get(key);
        
        // Remove old requests outside the window
        while (requests.length > 0 && requests[0] < windowStart) {
            requests.shift();
        }
        
        if (requests.length >= rateLimitConfig.max) {
            const retryAfter = requests[0] + rateLimitConfig.window - now;
            return { 
                allowed: false, 
                retryAfter: Math.ceil(retryAfter / 1000) 
            };
        }
        
        requests.push(now);
        return { allowed: true };
    }

    validateDomain(url) {
        try {
            const urlObj = new URL(url);
            const hostname = urlObj.hostname.toLowerCase();
            
            // Check against blocked domains
            for (const blockedDomain of this.securityPolicies.blockedDomains) {
                if (hostname.includes(blockedDomain.toLowerCase())) {
                    return { 
                        allowed: false, 
                        reason: 'Domain is in blocklist' 
                    };
                }
            }
            
            // Additional security checks
            if (hostname === 'localhost' || hostname.startsWith('127.') || hostname.startsWith('192.168.')) {
                // Allow localhost but log it
                this.logSecurityEvent('local_domain_access', { hostname, url });
            }
            
            return { allowed: true };
        } catch (error) {
            return { 
                allowed: false, 
                reason: 'Invalid URL format' 
            };
        }
    }

    validateScript(script) {
        try {
            const dangerousPatterns = [
                /eval\s*\(/,
                /Function\s*\(/,
                /document\.write/,
                /innerHTML\s*=/,
                /outerHTML\s*=/,
                /location\s*=/,
                /window\.open/,
                /XMLHttpRequest/,
                /fetch\s*\(/,
                /localStorage/,
                /sessionStorage/,
                /indexedDB/
            ];
            
            const issues = [];
            
            for (const pattern of dangerousPatterns) {
                if (pattern.test(script)) {
                    issues.push(`Potentially dangerous pattern detected: ${pattern.source}`);
                }
            }
            
            return {
                safe: issues.length === 0,
                issues: issues
            };
        } catch (error) {
            return {
                safe: false,
                issues: ['Script validation error']
            };
        }
    }

    async requestUserConfirmation(operation) {
        // In a real implementation, this would show a dialog to the user
        // For now, we'll simulate user approval based on operation safety
        try {
            const { type, target, params } = operation;
            
            // Auto-approve safe operations
            const safeOperations = ['screenshot', 'navigate', 'click'];
            if (safeOperations.includes(type)) {
                return true;
            }
            
            // For demo purposes, log the confirmation request
            console.log(`🔒 Security: User confirmation requested for operation: ${type}`);
            
            // Simulate user approval (in real app, show dialog)
            return true;
        } catch (error) {
            return false;
        }
    }

    generateOperationToken(operation) {
        const tokenData = {
            timestamp: Date.now(),
            operation: operation.type,
            target: operation.target,
            nonce: crypto.randomBytes(16).toString('hex')
        };
        
        const token = crypto
            .createHash('sha256')
            .update(JSON.stringify(tokenData))
            .digest('hex');
            
        return token;
    }

    sanitizeParams(params) {
        if (!params) return {};
        
        const sanitized = { ...params };
        
        // Remove or sanitize potentially dangerous parameters
        if (sanitized.script) {
            // Remove dangerous functions from scripts
            sanitized.script = sanitized.script
                .replace(/eval\s*\(/g, '// eval removed //')
                .replace(/Function\s*\(/g, '// Function removed //');
        }
        
        // Sanitize URLs
        if (sanitized.url) {
            try {
                const url = new URL(sanitized.url);
                sanitized.url = url.toString(); // Normalized URL
            } catch (e) {
                // Invalid URL, remove it
                delete sanitized.url;
            }
        }
        
        return sanitized;
    }

    logOperation(operation, token) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            token: token,
            type: operation.type,
            target: operation.target,
            requester: operation.requester || 'unknown',
            params: operation.params ? Object.keys(operation.params) : []
        };
        
        this.operationHistory.push(logEntry);
        
        // Keep only last 1000 operations
        if (this.operationHistory.length > 1000) {
            this.operationHistory = this.operationHistory.slice(-1000);
        }
        
        console.log(`🔒 Security: Operation logged - ${operation.type} (${token.substr(0, 8)}...)`);
    }

    logSecurityEvent(event, details) {
        console.log(`🚨 Security Event: ${event}`, details);
    }

    completeOperation(operationToken) {
        this.activeOperations.delete(operationToken);
    }

    async loadSecurityConfig() {
        try {
            const configPath = path.join(__dirname, '../config/security.json');
            const configData = await fs.readFile(configPath, 'utf8');
            const config = JSON.parse(configData);
            
            // Merge with default policies
            this.securityPolicies = { ...this.securityPolicies, ...config };
        } catch (error) {
            // Use default configuration if file doesn't exist
            console.log('Using default security configuration');
        }
    }

    initializeRateLimiting() {
        // Clean up rate limit counters every minute
        setInterval(() => {
            const now = Date.now();
            for (const [key, requests] of this.rateLimitCounters.entries()) {
                const validRequests = requests.filter(timestamp => 
                    now - timestamp < Math.max(...Object.values(this.securityPolicies.rateLimits).map(r => r.window))
                );
                
                if (validRequests.length === 0) {
                    this.rateLimitCounters.delete(key);
                } else {
                    this.rateLimitCounters.set(key, validRequests);
                }
            }
        }, 60000); // Clean up every minute
    }

    getSecurityStatus() {
        return {
            activeOperations: this.activeOperations.size,
            totalOperationsLogged: this.operationHistory.length,
            rateLimitedOperations: this.rateLimitCounters.size,
            securityPolicies: {
                maxConcurrentOperations: this.securityPolicies.maxConcurrentOperations,
                maxAutomationDuration: this.securityPolicies.maxAutomationDuration,
                blockedDomains: this.securityPolicies.blockedDomains.length
            }
        };
    }
}

module.exports = { SecurityManager };