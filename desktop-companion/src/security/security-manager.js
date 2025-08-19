const crypto = require('crypto');
const fs = require('fs').promises;
const path = require('path');

class SecurityManager {
    constructor() {
        this.trustedDomains = new Set([
            'localhost',
            '127.0.0.1',
            'aether-app.com' // Add your production domain
        ]);
        
        this.operationHistory = [];
        this.maxHistorySize = 1000;
        
        this.riskLevels = {
            LOW: 'low',
            MEDIUM: 'medium',
            HIGH: 'high',
            CRITICAL: 'critical'
        };
    }

    async validateOperation(operation) {
        try {
            console.log('🔒 Validating operation:', operation.type);
            
            const validationResults = {
                operation: operation,
                timestamp: new Date().toISOString(),
                riskLevel: this.riskLevels.LOW,
                allowed: true,
                warnings: [],
                mitigations: []
            };

            // Domain validation
            if (operation.url) {
                const domainCheck = this.validateDomain(operation.url);
                if (!domainCheck.trusted) {
                    validationResults.riskLevel = this.riskLevels.MEDIUM;
                    validationResults.warnings.push(`Untrusted domain: ${domainCheck.domain}`);
                    validationResults.mitigations.push('Request user confirmation for external domain access');
                }
            }

            // Operation type risk assessment
            const riskAssessment = this.assessOperationRisk(operation);
            if (riskAssessment.riskLevel !== this.riskLevels.LOW) {
                validationResults.riskLevel = riskAssessment.riskLevel;
                validationResults.warnings.push(...riskAssessment.warnings);
                validationResults.mitigations.push(...riskAssessment.mitigations);
            }

            // Cross-origin validation
            if (operation.type === 'cross_origin') {
                const crossOriginCheck = this.validateCrossOriginOperation(operation);
                if (!crossOriginCheck.safe) {
                    validationResults.riskLevel = this.riskLevels.HIGH;
                    validationResults.warnings.push(...crossOriginCheck.warnings);
                    validationResults.mitigations.push(...crossOriginCheck.mitigations);
                }
            }

            // File system access validation
            if (operation.type === 'file_access') {
                const fileAccessCheck = this.validateFileAccess(operation);
                if (!fileAccessCheck.allowed) {
                    validationResults.allowed = false;
                    validationResults.riskLevel = this.riskLevels.CRITICAL;
                    validationResults.warnings.push(...fileAccessCheck.warnings);
                }
            }

            // Rate limiting check
            const rateLimitCheck = this.checkRateLimit(operation);
            if (!rateLimitCheck.allowed) {
                validationResults.riskLevel = this.riskLevels.MEDIUM;
                validationResults.warnings.push('Rate limit exceeded');
                validationResults.mitigations.push('Implement operation throttling');
            }

            // Log operation
            this.logOperation(operation, validationResults);

            return {
                success: true,
                validation: validationResults,
                allowed: validationResults.allowed && validationResults.riskLevel !== this.riskLevels.CRITICAL
            };
        } catch (error) {
            console.error('❌ Operation validation failed:', error);
            return {
                success: false,
                error: error.message,
                allowed: false
            };
        }
    }

    validateDomain(url) {
        try {
            const urlObj = new URL(url);
            const domain = urlObj.hostname;
            
            return {
                domain: domain,
                trusted: this.trustedDomains.has(domain) || domain.endsWith('.localhost'),
                protocol: urlObj.protocol,
                port: urlObj.port
            };
        } catch (error) {
            return {
                domain: 'invalid',
                trusted: false,
                error: error.message
            };
        }
    }

    assessOperationRisk(operation) {
        const riskFactors = {
            warnings: [],
            mitigations: [],
            riskLevel: this.riskLevels.LOW
        };

        switch (operation.type) {
            case 'automation':
                if (operation.actions && operation.actions.includes('form_submit')) {
                    riskFactors.riskLevel = this.riskLevels.MEDIUM;
                    riskFactors.warnings.push('Form submission automation detected');
                    riskFactors.mitigations.push('Verify form contents before submission');
                }
                break;

            case 'data_extraction':
                if (operation.dataTypes && operation.dataTypes.includes('personal_info')) {
                    riskFactors.riskLevel = this.riskLevels.HIGH;
                    riskFactors.warnings.push('Personal information extraction detected');
                    riskFactors.mitigations.push('Encrypt extracted data and limit storage time');
                }
                break;

            case 'system_command':
                riskFactors.riskLevel = this.riskLevels.CRITICAL;
                riskFactors.warnings.push('System command execution requested');
                riskFactors.mitigations.push('Require explicit user authorization');
                break;

            case 'network_request':
                if (operation.method === 'POST' && operation.data) {
                    riskFactors.riskLevel = this.riskLevels.MEDIUM;
                    riskFactors.warnings.push('POST request with data detected');
                    riskFactors.mitigations.push('Validate request payload');
                }
                break;

            default:
                // Default low risk for unknown operations
                break;
        }

        return riskFactors;
    }

    validateCrossOriginOperation(operation) {
        const result = {
            safe: true,
            warnings: [],
            mitigations: []
        };

        // Check for potentially dangerous cross-origin operations
        if (operation.actions) {
            const dangerousActions = ['form_submit', 'file_upload', 'payment', 'authentication'];
            const foundDangerous = operation.actions.filter(action => 
                dangerousActions.some(dangerous => action.includes(dangerous))
            );

            if (foundDangerous.length > 0) {
                result.safe = false;
                result.warnings.push(`Dangerous cross-origin actions detected: ${foundDangerous.join(', ')}`);
                result.mitigations.push('Require explicit user consent for sensitive cross-origin operations');
            }
        }

        // Check target domains
        if (operation.targetDomains) {
            const untrustedDomains = operation.targetDomains.filter(domain => 
                !this.trustedDomains.has(domain)
            );

            if (untrustedDomains.length > 0) {
                result.warnings.push(`Untrusted target domains: ${untrustedDomains.join(', ')}`);
                result.mitigations.push('Verify domain reputation and user intent');
            }
        }

        return result;
    }

    validateFileAccess(operation) {
        const result = {
            allowed: true,
            warnings: []
        };

        const restrictedPaths = [
            '/etc/',
            '/usr/bin/',
            '/System/',
            'C:\\Windows\\',
            'C:\\Program Files\\'
        ];

        const sensitiveFiles = [
            'passwd',
            'shadow',
            'hosts',
            '.ssh/',
            'id_rsa',
            'private.key'
        ];

        if (operation.path) {
            // Check for restricted system paths
            const hasRestrictedPath = restrictedPaths.some(restricted => 
                operation.path.startsWith(restricted)
            );

            if (hasRestrictedPath) {
                result.allowed = false;
                result.warnings.push(`Access to restricted system path: ${operation.path}`);
            }

            // Check for sensitive files
            const hasSensitiveFile = sensitiveFiles.some(sensitive => 
                operation.path.includes(sensitive)
            );

            if (hasSensitiveFile) {
                result.allowed = false;
                result.warnings.push(`Access to sensitive file detected: ${operation.path}`);
            }
        }

        return result;
    }

    checkRateLimit(operation) {
        const now = Date.now();
        const timeWindow = 60000; // 1 minute
        const maxOperationsPerWindow = 100;

        // Filter recent operations
        const recentOperations = this.operationHistory.filter(op => 
            (now - op.timestamp) < timeWindow && op.type === operation.type
        );

        return {
            allowed: recentOperations.length < maxOperationsPerWindow,
            currentCount: recentOperations.length,
            limit: maxOperationsPerWindow,
            windowMs: timeWindow
        };
    }

    logOperation(operation, validation) {
        const logEntry = {
            timestamp: Date.now(),
            operation: operation,
            validation: validation,
            sessionId: this.generateSessionId()
        };

        this.operationHistory.push(logEntry);

        // Trim history to max size
        if (this.operationHistory.length > this.maxHistorySize) {
            this.operationHistory = this.operationHistory.slice(-this.maxHistorySize);
        }

        // Log to console for debugging
        console.log(`🔒 Security Log: ${operation.type} - Risk: ${validation.riskLevel} - Allowed: ${validation.allowed}`);
    }

    generateSessionId() {
        return crypto.randomBytes(16).toString('hex');
    }

    async generateSecurityReport() {
        try {
            const now = Date.now();
            const last24Hours = now - (24 * 60 * 60 * 1000);

            const recentOperations = this.operationHistory.filter(op => 
                op.timestamp > last24Hours
            );

            const riskDistribution = {
                [this.riskLevels.LOW]: 0,
                [this.riskLevels.MEDIUM]: 0,
                [this.riskLevels.HIGH]: 0,
                [this.riskLevels.CRITICAL]: 0
            };

            const operationTypes = {};
            const blockedOperations = [];

            recentOperations.forEach(op => {
                riskDistribution[op.validation.riskLevel]++;
                
                operationTypes[op.operation.type] = (operationTypes[op.operation.type] || 0) + 1;
                
                if (!op.validation.allowed) {
                    blockedOperations.push(op);
                }
            });

            const report = {
                reportPeriod: '24 hours',
                generatedAt: new Date().toISOString(),
                summary: {
                    totalOperations: recentOperations.length,
                    blockedOperations: blockedOperations.length,
                    securityScore: this.calculateSecurityScore(riskDistribution, recentOperations.length)
                },
                riskDistribution: riskDistribution,
                operationTypes: operationTypes,
                topWarnings: this.getTopWarnings(recentOperations),
                recommendations: this.generateSecurityRecommendations(riskDistribution, blockedOperations)
            };

            return {
                success: true,
                report: report
            };
        } catch (error) {
            console.error('❌ Security report generation failed:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    calculateSecurityScore(riskDistribution, totalOperations) {
        if (totalOperations === 0) return 100;

        const weights = {
            [this.riskLevels.LOW]: 0,
            [this.riskLevels.MEDIUM]: 5,
            [this.riskLevels.HIGH]: 15,
            [this.riskLevels.CRITICAL]: 50
        };

        const riskScore = Object.keys(riskDistribution).reduce((score, level) => {
            return score + (riskDistribution[level] * weights[level]);
        }, 0);

        const maxPossibleScore = totalOperations * weights[this.riskLevels.CRITICAL];
        const securityScore = Math.max(0, 100 - ((riskScore / maxPossibleScore) * 100));

        return Math.round(securityScore);
    }

    getTopWarnings(operations) {
        const warningCounts = {};
        
        operations.forEach(op => {
            op.validation.warnings.forEach(warning => {
                warningCounts[warning] = (warningCounts[warning] || 0) + 1;
            });
        });

        return Object.entries(warningCounts)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 5)
            .map(([warning, count]) => ({ warning, count }));
    }

    generateSecurityRecommendations(riskDistribution, blockedOperations) {
        const recommendations = [];

        if (riskDistribution[this.riskLevels.HIGH] > 0) {
            recommendations.push('Review high-risk operations and consider implementing additional user confirmations');
        }

        if (riskDistribution[this.riskLevels.CRITICAL] > 0) {
            recommendations.push('Critical security risks detected - review system access policies');
        }

        if (blockedOperations.length > 0) {
            recommendations.push(`${blockedOperations.length} operations were blocked - review security policies if legitimate operations are being prevented`);
        }

        if (recommendations.length === 0) {
            recommendations.push('Security posture is good - continue monitoring');
        }

        return recommendations;
    }

    addTrustedDomain(domain) {
        this.trustedDomains.add(domain);
        console.log(`✅ Added trusted domain: ${domain}`);
    }

    removeTrustedDomain(domain) {
        this.trustedDomains.delete(domain);
        console.log(`❌ Removed trusted domain: ${domain}`);
    }

    getTrustedDomains() {
        return Array.from(this.trustedDomains);
    }

    clearOperationHistory() {
        this.operationHistory = [];
        console.log('🗑️ Operation history cleared');
    }
}

module.exports = { SecurityManager };