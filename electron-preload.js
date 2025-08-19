const { contextBridge, ipcRenderer } = require('electron');

// Native Chromium API for frontend
contextBridge.exposeInMainWorld('nativeAPI', {
  // Native browser controls
  navigateTo: (url) => ipcRenderer.invoke('navigate-to', url),
  browserBack: () => ipcRenderer.invoke('browser-back'),
  browserForward: () => ipcRenderer.invoke('browser-forward'),
  browserRefresh: () => ipcRenderer.invoke('browser-refresh'),
  
  // DevTools access
  openDevTools: () => ipcRenderer.invoke('open-devtools'),
  
  // Extension management
  getExtensions: () => ipcRenderer.invoke('get-extensions'),
  
  // Fellou.ai-style command processing
  processCommand: (command) => ipcRenderer.invoke('process-command', command),
  
  // Session management
  createSession: (options) => ipcRenderer.invoke('create-session', options),
  
  // Event listeners
  onNavigationChange: (callback) => {
    ipcRenderer.on('navigation-change', (event, data) => callback(data));
  },
  
  onAIToggle: (callback) => {
    ipcRenderer.on('toggle-ai-panel', () => callback());
  },
  
  onVoiceToggle: (callback) => {
    ipcRenderer.on('toggle-voice-commands', () => callback());
  },
  
  // Native capabilities detection
  isNativeApp: () => true,
  hasNativeChromium: () => true,
  hasExtensionSupport: () => true,
  hasCrossOriginAccess: () => true
});

console.log('🔌 Native API bridge initialized - Chromium features available');