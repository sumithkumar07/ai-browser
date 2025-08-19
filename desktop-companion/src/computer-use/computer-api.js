/**
 * Computer Use API for AETHER Desktop Companion  
 * Provides system-level automation and control capabilities
 */

const screenshot = require('screenshot-desktop');
const { spawn, exec } = require('child_process');
const fs = require('fs').promises;
const path = require('path');

class ComputerUseAPI {
    constructor() {
        this.isInitialized = false;
        this.screenshotPath = path.join(__dirname, '../screenshots');
        this.automationHistory = [];
        this.systemInfo = null;
    }

    async initialize() {
        try {
            // Create screenshots directory
            await fs.mkdir(this.screenshotPath, { recursive: true });
            
            // Get system information
            this.systemInfo = await this.getSystemInfo();
            
            this.isInitialized = true;
            console.log('✅ Computer Use API initialized');
            return { success: true, systemInfo: this.systemInfo };
        } catch (error) {
            console.error('❌ Failed to initialize Computer Use API:', error);
            return { success: false, error: error.message };
        }
    }

    async getSystemInfo() {
        try {
            const platform = process.platform;
            const arch = process.arch;
            const version = process.version;
            
            return {
                platform: platform,
                architecture: arch,
                nodeVersion: version,
                capabilities: this.getPlatformCapabilities(platform)
            };
        } catch (error) {
            return { error: error.message };
        }
    }

    getPlatformCapabilities(platform) {
        const baseCapabilities = [
            'screenshot',
            'file_operations',
            'process_management',
            'system_monitoring'
        ];

        const platformSpecific = {
            'win32': ['windows_automation', 'registry_access', 'wmi_queries'],
            'darwin': ['applescript', 'accessibility_api', 'cocoa_automation'], 
            'linux': ['x11_automation', 'dbus_interface', 'systemd_control']
        };

        return [...baseCapabilities, ...(platformSpecific[platform] || [])];
    }

    async takeScreenshot(options = {}) {
        try {
            if (!this.isInitialized) {
                await this.initialize();
            }

            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const filename = `screenshot_${timestamp}.png`;
            const filepath = path.join(this.screenshotPath, filename);

            const screenshotData = await screenshot({
                format: 'png',
                quality: options.quality || 100,
                ...options
            });

            await fs.writeFile(filepath, screenshotData);

            const result = {
                success: true,
                filename: filename,
                filepath: filepath,
                timestamp: timestamp,
                size: screenshotData.length,
                options: options
            };

            this.automationHistory.push({
                action: 'screenshot',
                timestamp: new Date(),
                result: result
            });

            return result;
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async clickAt(x, y, button = 'left') {
        try {
            const platform = process.platform;
            let command;

            switch (platform) {
                case 'win32':
                    // Windows: Use PowerShell to simulate click
                    command = `powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point(${x}, ${y}); [System.Windows.Forms.Application]::DoEvents(); Start-Sleep -Milliseconds 100"`;
                    break;
                    
                case 'darwin':
                    // macOS: Use osascript for clicking
                    command = `osascript -e 'tell application "System Events" to click at {${x}, ${y}}'`;
                    break;
                    
                case 'linux':
                    // Linux: Use xdotool
                    command = `xdotool mousemove ${x} ${y} click ${button === 'right' ? 3 : 1}`;
                    break;
                    
                default:
                    throw new Error(`Platform ${platform} not supported for click automation`);
            }

            const result = await this.executeCommand(command);
            
            const clickResult = {
                success: result.success,
                coordinates: { x, y },
                button: button,
                platform: platform,
                timestamp: new Date()
            };

            this.automationHistory.push({
                action: 'click',
                timestamp: new Date(),
                result: clickResult
            });

            return clickResult;
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async typeText(text, delay = 50) {
        try {
            const platform = process.platform;
            let command;

            // Escape special characters for shell
            const escapedText = text.replace(/"/g, '\\"').replace(/\$/g, '\\$');

            switch (platform) {
                case 'win32':
                    // Windows: Use PowerShell with SendKeys
                    command = `powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('${escapedText}')"`;
                    break;
                    
                case 'darwin':
                    // macOS: Use osascript to type
                    command = `osascript -e 'tell application "System Events" to keystroke "${escapedText}"'`;
                    break;
                    
                case 'linux':
                    // Linux: Use xdotool
                    command = `xdotool type --delay ${delay} "${escapedText}"`;
                    break;
                    
                default:
                    throw new Error(`Platform ${platform} not supported for text automation`);
            }

            const result = await this.executeCommand(command);
            
            const typeResult = {
                success: result.success,
                text: text,
                length: text.length,
                delay: delay,
                platform: platform,
                timestamp: new Date()
            };

            this.automationHistory.push({
                action: 'type',
                timestamp: new Date(),
                result: typeResult
            });

            return typeResult;
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async sendKeyPress(key, modifiers = []) {
        try {
            const platform = process.platform;
            let command;

            switch (platform) {
                case 'win32':
                    // Windows: Use PowerShell SendKeys
                    let keyCode = this.mapKeyToWindows(key, modifiers);
                    command = `powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('${keyCode}')"`;
                    break;
                    
                case 'darwin':
                    // macOS: Use osascript
                    let macKeyCode = this.mapKeyToMac(key, modifiers);
                    command = `osascript -e '${macKeyCode}'`;
                    break;
                    
                case 'linux':
                    // Linux: Use xdotool
                    let linuxKeyCode = this.mapKeyToLinux(key, modifiers);
                    command = `xdotool ${linuxKeyCode}`;
                    break;
                    
                default:
                    throw new Error(`Platform ${platform} not supported for key automation`);
            }

            const result = await this.executeCommand(command);
            
            return {
                success: result.success,
                key: key,
                modifiers: modifiers,
                platform: platform,
                timestamp: new Date()
            };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    mapKeyToWindows(key, modifiers) {
        const modifierMap = {
            'ctrl': '^',
            'alt': '%',
            'shift': '+',
            'cmd': '^' // Map cmd to ctrl on Windows
        };

        const keyMap = {
            'enter': '{ENTER}',
            'tab': '{TAB}',
            'escape': '{ESC}',
            'space': ' ',
            'backspace': '{BACKSPACE}',
            'delete': '{DELETE}',
            'f1': '{F1}', 'f2': '{F2}', 'f3': '{F3}', 'f4': '{F4}',
            'f5': '{F5}', 'f6': '{F6}', 'f7': '{F7}', 'f8': '{F8}',
            'f9': '{F9}', 'f10': '{F10}', 'f11': '{F11}', 'f12': '{F12}'
        };

        let modifierString = modifiers.map(mod => modifierMap[mod] || '').join('');
        let keyString = keyMap[key.toLowerCase()] || key;
        
        return `${modifierString}${keyString}`;
    }

    mapKeyToMac(key, modifiers) {
        const modifierMap = {
            'cmd': 'command',
            'ctrl': 'control', 
            'alt': 'option',
            'shift': 'shift'
        };

        let modifierString = modifiers.map(mod => modifierMap[mod] || mod).join(' ');
        let keyString = key;

        if (modifierString) {
            return `tell application "System Events" to key code ${this.getMacKeyCode(key)} using {${modifierString} down}`;
        } else {
            return `tell application "System Events" to key code ${this.getMacKeyCode(key)}`;
        }
    }

    getMacKeyCode(key) {
        const keyCodes = {
            'enter': 36, 'tab': 48, 'escape': 53, 'space': 49,
            'backspace': 51, 'delete': 117,
            'f1': 122, 'f2': 120, 'f3': 99, 'f4': 118,
            'f5': 96, 'f6': 97, 'f7': 98, 'f8': 100,
            'f9': 101, 'f10': 109, 'f11': 103, 'f12': 111
        };
        
        return keyCodes[key.toLowerCase()] || key.charCodeAt(0);
    }

    mapKeyToLinux(key, modifiers) {
        const modifierMap = {
            'ctrl': 'ctrl',
            'alt': 'alt',
            'shift': 'shift',
            'cmd': 'Super_L' // Map cmd to Super key on Linux
        };

        let modifierString = modifiers.map(mod => modifierMap[mod] || mod).join('+');
        let keyString = key;

        if (modifierString) {
            return `key ${modifierString}+${keyString}`;
        } else {
            return `key ${keyString}`;
        }
    }

    async executeCommand(command) {
        return new Promise((resolve) => {
            exec(command, (error, stdout, stderr) => {
                if (error) {
                    resolve({ success: false, error: error.message, stderr: stderr });
                } else {
                    resolve({ success: true, stdout: stdout, stderr: stderr });
                }
            });
        });
    }

    async getRunningProcesses() {
        try {
            const platform = process.platform;
            let command;

            switch (platform) {
                case 'win32':
                    command = 'tasklist /FO CSV';
                    break;
                case 'darwin':
                    command = 'ps -eo pid,comm,cpu,rss';
                    break;
                case 'linux':
                    command = 'ps -eo pid,comm,cpu,rss';
                    break;
                default:
                    throw new Error(`Platform ${platform} not supported`);
            }

            const result = await this.executeCommand(command);
            
            return {
                success: result.success,
                processes: this.parseProcessList(result.stdout, platform),
                platform: platform
            };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    parseProcessList(output, platform) {
        try {
            const lines = output.split('\n').filter(line => line.trim());
            
            if (platform === 'win32') {
                // Parse CSV format from Windows tasklist
                return lines.slice(1).map(line => {
                    const fields = line.split(',').map(field => field.replace(/"/g, ''));
                    return {
                        name: fields[0],
                        pid: fields[1],
                        memory: fields[4]
                    };
                });
            } else {
                // Parse Unix-style ps output
                return lines.slice(1).map(line => {
                    const fields = line.trim().split(/\s+/);
                    return {
                        pid: fields[0],
                        name: fields[1],
                        cpu: fields[2],
                        memory: fields[3]
                    };
                });
            }
        } catch (error) {
            return [];
        }
    }

    async getAutomationHistory(limit = 50) {
        return {
            success: true,
            history: this.automationHistory.slice(-limit),
            total: this.automationHistory.length
        };
    }

    async clearHistory() {
        this.automationHistory = [];
        return { success: true, message: 'Automation history cleared' };
    }

    async getCapabilities() {
        return {
            success: true,
            capabilities: this.getPlatformCapabilities(process.platform),
            platform: process.platform,
            features: {
                screenshot: true,
                click_automation: true,
                keyboard_automation: true,
                process_monitoring: true,
                file_operations: true,
                cross_platform: true
            }
        };
    }
}

module.exports = { ComputerUseAPI };