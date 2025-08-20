const { ipcRenderer, contextBridge } = require('electron');

// Native API Bridge for Frontend
const nativeAPI = {
  // Browser Navigation
  async navigateTo(url) {
    return await ipcRenderer.invoke('native-navigate', url);
  },

  async goBack() {
    return await ipcRenderer.invoke('native-go-back');
  },

  async goForward() {
    return await ipcRenderer.invoke('native-go-forward');
  },

  async refresh() {
    return await ipcRenderer.invoke('native-refresh');
  },

  // Screenshot & DevTools
  async captureScreenshot(options) {
    return await ipcRenderer.invoke('native-screenshot', options);
  },

  async openDevTools() {
    return await ipcRenderer.invoke('native-open-devtools');
  },

  // Extension Management
  async loadExtension(path) {
    return await ipcRenderer.invoke('native-load-extension', path);
  },

  async getExtensions() {
    return await ipcRenderer.invoke('native-get-extensions');
  },

  // File System Access
  async showOpenDialog(options) {
    return await ipcRenderer.invoke('native-show-open-dialog', options);
  },

  async showSaveDialog(options) {
    return await ipcRenderer.invoke('native-show-save-dialog', options);
  },

  // Capabilities Check
  async getCapabilities() {
    return await ipcRenderer.invoke('native-get-capabilities');
  },

  // Helper Methods
  hasNativeChromium() {
    return true;
  },

  isElectronApp() {
    return true;
  },

  // Event Listeners
  onNavigationUpdate(callback) {
    ipcRenderer.on('navigation-updated', callback);
  },

  onNewTab(callback) {
    ipcRenderer.on('native-new-tab', callback);
  },

  onNativeCommand(callback) {
    ipcRenderer.on('native-command', callback);
  },

  // Remove listeners
  removeAllListeners(channel) {
    ipcRenderer.removeAllListeners(channel);
  }
};

// Expose Native API to the renderer process
contextBridge.exposeInMainWorld('nativeAPI', nativeAPI);

// Also expose to window for compatibility
window.nativeAPI = nativeAPI;

console.log('🔥 Native API Bridge Loaded - AETHER v6.0 Native Chromium Ready');