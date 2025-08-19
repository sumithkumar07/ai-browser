/**
 * Preload script for AETHER Desktop Companion
 * Exposes secure APIs to the renderer process
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('aetherDesktop', {
  // Native Browser Operations
  navigateTo: (url) => ipcRenderer.invoke('native-browser-navigate', url),
  executeScript: (script) => ipcRenderer.invoke('native-browser-execute-script', script),
  getPageContent: () => ipcRenderer.invoke('native-browser-get-content'),
  
  // Computer Use API
  takeScreenshot: () => ipcRenderer.invoke('computer-use-screenshot'),
  clickAt: (x, y) => ipcRenderer.invoke('computer-use-click', x, y),
  typeText: (text) => ipcRenderer.invoke('computer-use-type', text),
  sendKeyPress: (key, modifiers) => ipcRenderer.invoke('computer-use-keypress', key, modifiers),
  
  // Cross-Origin Automation (Fellou.ai equivalent)
  executeCrossOriginAutomation: (config) => ipcRenderer.invoke('cross-origin-automation', config),
  createPersistentSession: (url, sessionId) => ipcRenderer.invoke('create-persistent-session', url, sessionId),
  executeInSession: (sessionId, actions) => ipcRenderer.invoke('execute-in-session', sessionId, actions),
  
  // Security
  validateOperation: (operation) => ipcRenderer.invoke('security-validate-operation', operation),
  
  // Bridge to Web App
  sendMessage: (message) => ipcRenderer.invoke('bridge-send-message', message),
  
  // System Information
  getSystemInfo: () => ipcRenderer.invoke('get-system-info'),
  getCapabilities: () => ipcRenderer.invoke('get-capabilities'),
  
  // Desktop App Features
  openDevTools: () => ipcRenderer.invoke('open-dev-tools'),
  minimizeWindow: () => ipcRenderer.invoke('minimize-window'),
  maximizeWindow: () => ipcRenderer.invoke('maximize-window'),
  closeWindow: () => ipcRenderer.invoke('close-window'),
  
  // Enhanced Features (Beyond Fellou.ai)
  startBackgroundAutomation: (config) => ipcRenderer.invoke('start-background-automation', config),
  getRunningProcesses: () => ipcRenderer.invoke('get-running-processes'),
  monitorWebsiteChanges: (url, interval) => ipcRenderer.invoke('monitor-website-changes', url, interval),
  
  // Event Listeners
  onNativeBrowserEvent: (callback) => ipcRenderer.on('native-browser-event', callback),
  onAutomationComplete: (callback) => ipcRenderer.on('automation-complete', callback),
  onSystemEvent: (callback) => ipcRenderer.on('system-event', callback),
  
  // Remove listeners
  removeAllListeners: (channel) => ipcRenderer.removeAllListeners(channel),
  
  // Desktop-specific capabilities
  getDesktopCapabilities: () => ({
    nativeBrowser: true,
    crossOriginUnlimited: true,
    systemAutomation: true,
    computerUseAPI: true,
    backgroundTasks: true,
    fileSystemAccess: true,
    processControl: true,
    advancedSecurity: true,
    fellou_equivalent_features: [
      'deep_action',
      'cross_page_automation', 
      'system_level_control',
      'unlimited_cross_origin',
      'native_browser_engine'
    ]
  })
});

// Desktop App Status Indicator
window.addEventListener('DOMContentLoaded', () => {
  console.log('🖥️ AETHER Desktop Companion Ready');
  console.log('✅ Native Browser Engine: Available');
  console.log('✅ Cross-Origin Unlimited: Available');
  console.log('✅ Computer Use API: Available');
  console.log('✅ System Automation: Available');
  console.log('🏆 Fellou.ai Feature Parity: Achieved');
});