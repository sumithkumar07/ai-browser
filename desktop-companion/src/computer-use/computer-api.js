const robot = require('robotjs');
const screenshot = require('screenshot-desktop');
const fs = require('fs').promises;
const path = require('path');

class ComputerUseAPI {
    constructor() {
        this.screenshotDir = path.join(__dirname, '../../screenshots');
        this.ensureScreenshotDir();
        
        // Configure robot.js for better performance
        robot.setDelay(10);
    }

    async ensureScreenshotDir() {
        try {
            await fs.mkdir(this.screenshotDir, { recursive: true });
        } catch (error) {
            console.error('Failed to create screenshot directory:', error);
        }
    }

    async takeScreenshot(format = 'png') {
        try {
            const timestamp = Date.now();
            const filename = `screenshot_${timestamp}.${format}`;
            const filepath = path.join(this.screenshotDir, filename);

            // Take screenshot of primary display
            const img = await screenshot({ format: 'png' });
            await fs.writeFile(filepath, img);

            return {
                success: true,
                filepath: filepath,
                filename: filename,
                timestamp: timestamp,
                size: img.length
            };
        } catch (error) {
            console.error('❌ Screenshot failed:', error);
            return { success: false, error: error.message };
        }
    }

    async clickAt(x, y, button = 'left', doubleClick = false) {
        try {
            // Move to position
            robot.moveMouse(x, y);
            
            // Add small delay for accuracy
            await this.delay(100);

            // Perform click
            if (doubleClick) {
                robot.mouseClick(button, true); // Double click
            } else {
                robot.mouseClick(button, false); // Single click
            }

            return {
                success: true,
                action: doubleClick ? 'double_click' : 'click',
                position: { x, y },
                button: button
            };
        } catch (error) {
            console.error('❌ Click failed:', error);
            return { success: false, error: error.message };
        }
    }

    async typeText(text, typing_speed = 50) {
        try {
            // Clear any existing selection first
            robot.keyTap('a', 'command'); // Select all (Ctrl+A on Windows/Linux)
            await this.delay(100);

            // Type the text with specified speed
            for (const char of text) {
                robot.typeString(char);
                await this.delay(typing_speed);
            }

            return {
                success: true,
                action: 'type',
                text: text,
                length: text.length,
                typing_speed: typing_speed
            };
        } catch (error) {
            console.error('❌ Typing failed:', error);
            return { success: false, error: error.message };
        }
    }

    async sendKeySequence(keys, modifiers = []) {
        try {
            if (modifiers.length > 0) {
                robot.keyTap(keys, modifiers);
            } else {
                robot.keyTap(keys);
            }

            return {
                success: true,
                action: 'key_sequence',
                keys: keys,
                modifiers: modifiers
            };
        } catch (error) {
            console.error('❌ Key sequence failed:', error);
            return { success: false, error: error.message };
        }
    }

    async dragAndDrop(fromX, fromY, toX, toY, duration = 1000) {
        try {
            // Move to start position
            robot.moveMouse(fromX, fromY);
            await this.delay(100);

            // Start drag
            robot.mouseToggle('down');
            await this.delay(100);

            // Perform drag motion
            const steps = Math.max(Math.abs(toX - fromX), Math.abs(toY - fromY));
            const stepDuration = duration / steps;

            for (let i = 1; i <= steps; i++) {
                const currentX = fromX + (toX - fromX) * (i / steps);
                const currentY = fromY + (toY - fromY) * (i / steps);
                
                robot.moveMouse(Math.round(currentX), Math.round(currentY));
                await this.delay(stepDuration);
            }

            // End drag
            robot.mouseToggle('up');

            return {
                success: true,
                action: 'drag_and_drop',
                from: { x: fromX, y: fromY },
                to: { x: toX, y: toY },
                duration: duration
            };
        } catch (error) {
            console.error('❌ Drag and drop failed:', error);
            return { success: false, error: error.message };
        }
    }

    async scrollAt(x, y, direction = 'down', amount = 3) {
        try {
            // Move to position
            robot.moveMouse(x, y);
            await this.delay(100);

            // Perform scroll
            const scrollDirection = direction === 'down' ? -amount : amount;
            robot.scrollMouse(0, scrollDirection);

            return {
                success: true,
                action: 'scroll',
                position: { x, y },
                direction: direction,
                amount: amount
            };
        } catch (error) {
            console.error('❌ Scroll failed:', error);
            return { success: false, error: error.message };
        }
    }

    async getMousePosition() {
        try {
            const position = robot.getMousePos();
            return {
                success: true,
                position: position
            };
        } catch (error) {
            console.error('❌ Get mouse position failed:', error);
            return { success: false, error: error.message };
        }
    }

    async getScreenSize() {
        try {
            const size = robot.getScreenSize();
            return {
                success: true,
                screen_size: size
            };
        } catch (error) {
            console.error('❌ Get screen size failed:', error);
            return { success: false, error: error.message };
        }
    }

    async delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

module.exports = { ComputerUseAPI };