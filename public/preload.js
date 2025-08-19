const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Native browser operations
  createNativeBrowser: (config) => ipcRenderer.invoke('create-native-browser', config),
  openDevTools: (windowId) => ipcRenderer.invoke('open-devtools', windowId),
  nativeNavigate: (data) => ipcRenderer.invoke('native-navigate', data),
  executeNativeScript: (data) => ipcRenderer.invoke('execute-native-script', data),
  takeNativeScreenshot: (data) => ipcRenderer.invoke('take-native-screenshot', data),
  
  // Extension management
  manageExtension: (data) => ipcRenderer.invoke('manage-extension', data),
  
  // System information
  platform: process.platform,
  versions: process.versions,
  
  // Enhanced capabilities detection
  capabilities: {
    nativeChromium: true,
    devTools: true,
    extensions: true,
    crossOrigin: true,
    automation: true
  }
});

// Enhanced browser detection
contextBridge.exposeInMainWorld('isNativeAether', true);

// Native Chromium integration helpers
contextBridge.exposeInMainWorld('nativeChromium', {
  // Check if native Chromium is available
  isAvailable: () => true,
  
  // Get enhanced capabilities
  getCapabilities: () => ({
    version: process.versions.chrome,
    devTools: true,
    extensions: true,
    crossOrigin: true,
    automation: true,
    webGL: true,
    webRTC: true,
    serviceWorkers: true,
    pushNotifications: true,
    fileSystem: true
  }),
  
  // Native performance metrics
  getPerformanceMetrics: () => ({
    memory: process.memoryUsage(),
    platform: process.platform,
    arch: process.arch,
    cpuUsage: process.cpuUsage()
  })
});

console.log('AETHER Native Preload Script initialized');