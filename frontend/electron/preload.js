/**
 * Preload script for AETHER Native Chromium Browser
 * Exposes native capabilities to the renderer process
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose native API to renderer process
contextBridge.exposeInMainWorld('aetherNative', {
    // Core browser navigation
    navigate: (url) => ipcRenderer.invoke('native-navigate', url),
    goBack: () => ipcRenderer.invoke('native-go-back'),
    goForward: () => ipcRenderer.invoke('native-go-forward'),
    refresh: () => ipcRenderer.invoke('native-refresh'),

    // Screenshot and visual
    screenshot: (options = {}) => ipcRenderer.invoke('native-screenshot', options),

    // JavaScript execution
    executeJS: (script) => ipcRenderer.invoke('native-execute-js', script),

    // DevTools management
    openDevTools: () => ipcRenderer.invoke('native-open-devtools'),
    closeDevTools: () => ipcRenderer.invoke('native-close-devtools'),

    // Extension management
    loadExtension: (path) => ipcRenderer.invoke('native-load-extension', path),
    getExtensions: () => ipcRenderer.invoke('native-get-extensions'),

    // File system access
    showOpenDialog: (options) => ipcRenderer.invoke('native-show-open-dialog', options),
    showSaveDialog: (options) => ipcRenderer.invoke('native-show-save-dialog', options),

    // Capabilities
    getCapabilities: () => ipcRenderer.invoke('native-get-capabilities'),

    // Event listeners
    onNavigationComplete: (callback) => {
        ipcRenderer.on('native-navigation-complete', callback);
        return () => ipcRenderer.removeListener('native-navigation-complete', callback);
    },

    onPageLoad: (callback) => {
        ipcRenderer.on('native-page-load', callback);
        return () => ipcRenderer.removeListener('native-page-load', callback);
    },

    // Menu commands
    onNewTab: (callback) => {
        ipcRenderer.on('native-new-tab', callback);
        return () => ipcRenderer.removeListener('native-new-tab', callback);
    },

    onNavigate: (callback) => {
        ipcRenderer.on('native-navigate', callback);
        return () => ipcRenderer.removeListener('native-navigate', callback);
    },

    onGoBack: (callback) => {
        ipcRenderer.on('native-go-back', callback);
        return () => ipcRenderer.removeListener('native-go-back', callback);
    },

    onGoForward: (callback) => {
        ipcRenderer.on('native-go-forward', callback);
        return () => ipcRenderer.removeListener('native-go-forward', callback);
    },

    onRefresh: (callback) => {
        ipcRenderer.on('native-refresh', callback);
        return () => ipcRenderer.removeListener('native-refresh', callback);
    },

    // Extension manager
    onOpenExtensionsManager: (callback) => {
        ipcRenderer.on('open-extensions-manager', callback);
        return () => ipcRenderer.removeListener('open-extensions-manager', callback);
    }
});

// Also expose electron info
contextBridge.exposeInMainWorld('electronAPI', {
    versions: process.versions,
    platform: process.platform,
    isElectron: true
});

// Enhanced native capabilities flag
contextBridge.exposeInMainWorld('nativeCapabilities', {
    hasNativeChromium: true,
    hasExtensionSupport: true,
    hasDevTools: true,
    hasFileSystemAccess: true,
    version: '6.0.0'
});

console.log('🔥 AETHER Native Preload Script Loaded - Full Chromium Access Enabled');