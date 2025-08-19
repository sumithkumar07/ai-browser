import { screen, mouse, keyboard } from 'robotjs';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs/promises';
import * as path from 'path';

const execAsync = promisify(exec);

export interface ScreenshotResult {
  success: boolean;
  imagePath?: string;
  base64Data?: string;
  error?: string;
  metadata: {
    width: number;
    height: number;
    timestamp: number;
  };
}

export interface ClickResult {
  success: boolean;
  position: { x: number; y: number };
  error?: string;
  timestamp: number;
}

export interface TypeResult {
  success: boolean;
  text: string;
  error?: string;
  timestamp: number;
}

export interface SystemInfo {
  platform: string;
  arch: string;
  screenSize: { width: number; height: number };
  mousePosition: { x: number; y: number };
  timestamp: number;
}

export class ComputerUseAPI {
  private screenshotsDir: string;
  private isInitialized: boolean = false;

  constructor() {
    this.screenshotsDir = path.join(__dirname, '../screenshots');
  }

  async initialize(): Promise<void> {
    console.log('🖥️ Initializing Computer Use API...');
    
    try {
      // Create screenshots directory
      await fs.mkdir(this.screenshotsDir, { recursive: true });
      
      // Set robot.js speed for smoother interactions
      mouse.setDelay(50);
      keyboard.setDelay(50);
      
      this.isInitialized = true;
      console.log('✅ Computer Use API initialized');
    } catch (error) {
      console.error('❌ Failed to initialize Computer Use API:', error);
      throw error;
    }
  }

  async takeScreenshot(region?: { x: number; y: number; width: number; height: number }): Promise<ScreenshotResult> {
    if (!this.isInitialized) {
      throw new Error('Computer Use API not initialized');
    }

    try {
      const timestamp = Date.now();
      const screenSize = screen.getScreenSize();
      
      // Capture screenshot
      const bitmap = region 
        ? screen.capture(region.x, region.y, region.width, region.height)
        : screen.capture();

      // Convert to base64
      const base64Data = bitmap.image.toString('base64');
      
      // Save to file
      const filename = `screenshot_${timestamp}.png`;
      const imagePath = path.join(this.screenshotsDir, filename);
      
      await fs.writeFile(imagePath, Buffer.from(base64Data, 'base64'));

      return {
        success: true,
        imagePath,
        base64Data,
        metadata: {
          width: bitmap.width,
          height: bitmap.height,
          timestamp
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        metadata: {
          width: 0,
          height: 0,
          timestamp: Date.now()
        }
      };
    }
  }

  async clickAtPosition(x: number, y: number, button: 'left' | 'right' | 'middle' = 'left'): Promise<ClickResult> {
    if (!this.isInitialized) {
      throw new Error('Computer Use API not initialized');
    }

    try {
      const timestamp = Date.now();
      
      // Move mouse to position
      mouse.moveMouse(x, y);
      
      // Click at position
      mouse.mouseClick(button);
      
      return {
        success: true,
        position: { x, y },
        timestamp
      };
    } catch (error) {
      return {
        success: false,
        position: { x, y },
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now()
      };
    }
  }

  async dragMouse(startX: number, startY: number, endX: number, endY: number): Promise<ClickResult> {
    if (!this.isInitialized) {
      throw new Error('Computer Use API not initialized');
    }

    try {
      const timestamp = Date.now();
      
      // Move to start position
      mouse.moveMouse(startX, startY);
      
      // Mouse down
      mouse.mouseToggle('down');
      
      // Drag to end position
      mouse.dragMouse(endX, endY);
      
      // Mouse up
      mouse.mouseToggle('up');
      
      return {
        success: true,
        position: { x: endX, y: endY },
        timestamp
      };
    } catch (error) {
      return {
        success: false,
        position: { x: endX, y: endY },
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now()
      };
    }
  }

  async typeText(text: string, delay: number = 50): Promise<TypeResult> {
    if (!this.isInitialized) {
      throw new Error('Computer Use API not initialized');
    }

    try {
      const timestamp = Date.now();
      
      // Set typing delay
      keyboard.setDelay(delay);
      
      // Type the text
      keyboard.typeString(text);
      
      return {
        success: true,
        text,
        timestamp
      };
    } catch (error) {
      return {
        success: false,
        text,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now()
      };
    }
  }

  async pressKey(key: string, modifiers?: string[]): Promise<TypeResult> {
    if (!this.isInitialized) {
      throw new Error('Computer Use API not initialized');
    }

    try {
      const timestamp = Date.now();
      
      if (modifiers && modifiers.length > 0) {
        keyboard.keyTap(key, modifiers);
      } else {
        keyboard.keyTap(key);
      }
      
      return {
        success: true,
        text: `Key pressed: ${key}${modifiers ? ` with ${modifiers.join('+')}` : ''}`,
        timestamp
      };
    } catch (error) {
      return {
        success: false,
        text: key,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now()
      };
    }
  }

  async getMousePosition(): Promise<{ x: number; y: number }> {
    return mouse.getMousePos();
  }

  async getSystemInfo(): Promise<SystemInfo> {
    const screenSize = screen.getScreenSize();
    const mousePos = mouse.getMousePos();
    
    return {
      platform: process.platform,
      arch: process.arch,
      screenSize,
      mousePosition: mousePos,
      timestamp: Date.now()
    };
  }

  async executeCommand(command: string): Promise<{ success: boolean; output?: string; error?: string }> {
    try {
      const { stdout, stderr } = await execAsync(command);
      return {
        success: true,
        output: stdout || stderr
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  async findImageOnScreen(templateImagePath: string): Promise<{ found: boolean; position?: { x: number; y: number } }> {
    try {
      // Take screenshot
      const screenshot = await this.takeScreenshot();
      if (!screenshot.success || !screenshot.imagePath) {
        return { found: false };
      }

      // Use OpenCV or similar library for template matching
      // For now, return a placeholder implementation
      console.log(`Searching for image template: ${templateImagePath}`);
      
      return { found: false };
    } catch (error) {
      console.error('Image search failed:', error);
      return { found: false };
    }
  }

  async shutdown(): Promise<void> {
    console.log('🖥️ Computer Use API shut down');
    this.isInitialized = false;
  }
}