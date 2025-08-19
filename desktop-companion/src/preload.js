const { contextBridge, ipcRenderer } = require('electron');

// Expose secure API to renderer process
contextBridge.exposeInMainWorld('aetherDesktop', {
    // Native Browser API
    browser: {
        navigate: (url) => ipcRenderer.invoke('native-browser-navigate', url),
        executeScript: (script) => ipcRenderer.invoke('native-browser-execute-script', script),
        getContent: () => ipcRenderer.invoke('native-browser-get-content'),
        executeCrossOriginAutomation: (config) => ipcRenderer.invoke('cross-origin-automation', config)
    },

    // Computer Use API
    computer: {
        screenshot: () => ipcRenderer.invoke('computer-use-screenshot'),
        click: (x, y) => ipcRenderer.invoke('computer-use-click', x, y),
        type: (text) => ipcRenderer.invoke('computer-use-type', text)
    },

    // Security API
    security: {
        validateOperation: (operation) => ipcRenderer.invoke('security-validate-operation', operation)
    },

    // Bridge API
    bridge: {
        sendMessage: (message) => ipcRenderer.invoke('bridge-send-message', message)
    },

    // Desktop-specific features
    desktop: {
        isDesktopApp: true,
        version: '1.0.0',
        platform: process.platform
    }
});