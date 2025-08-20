const { session, app } = require('electron');
const path = require('path');
const fs = require('fs');

/**
 * Extension Manager - Chrome Extension Support
 * Enables loading and managing Chrome extensions in the native browser
 */
class ExtensionManager {
  constructor() {
    this.loadedExtensions = new Map();
    this.extensionSessions = new Map();
    this.extensionDirectory = path.join(app.getPath('userData'), 'extensions');
    
    // Ensure extensions directory exists
    this.ensureExtensionsDirectory();
    
    console.log('🧩 Extension Manager Initialized');
  }

  ensureExtensionsDirectory() {
    try {
      if (!fs.existsSync(this.extensionDirectory)) {
        fs.mkdirSync(this.extensionDirectory, { recursive: true });
      }
    } catch (error) {
      console.error('Failed to create extensions directory:', error);
    }
  }

  async loadExtension(extensionPath, sessionName = 'default') {
    try {
      // Validate extension path
      if (!fs.existsSync(extensionPath)) {
        return { success: false, error: 'Extension path does not exist' };
      }

      // Check for manifest.json
      const manifestPath = path.join(extensionPath, 'manifest.json');
      if (!fs.existsSync(manifestPath)) {
        return { success: false, error: 'manifest.json not found' };
      }

      // Read and parse manifest
      const manifestContent = fs.readFileSync(manifestPath, 'utf8');
      let manifest;
      
      try {
        manifest = JSON.parse(manifestContent);
      } catch (error) {
        return { success: false, error: 'Invalid manifest.json format' };
      }

      // Validate required manifest fields
      if (!manifest.name || !manifest.version) {
        return { success: false, error: 'Invalid manifest: missing name or version' };
      }

      // Get or create session
      const ses = sessionName === 'default' ? session.defaultSession : session.fromPartition(sessionName);

      // Load extension
      const extension = await ses.loadExtension(extensionPath);

      // Store extension info
      const extensionInfo = {
        id: extension.id,
        name: manifest.name,
        version: manifest.version,
        description: manifest.description || '',
        path: extensionPath,
        manifest,
        session: sessionName,
        loadedAt: Date.now()
      };

      this.loadedExtensions.set(extension.id, extensionInfo);

      console.log(`🧩 Extension loaded: ${manifest.name} v${manifest.version}`);

      return {
        success: true,
        extension: extensionInfo,
        id: extension.id
      };

    } catch (error) {
      console.error('Extension loading error:', error);
      return { success: false, error: error.message };
    }
  }

  async unloadExtension(extensionId, sessionName = 'default') {
    try {
      const extensionInfo = this.loadedExtensions.get(extensionId);
      
      if (!extensionInfo) {
        return { success: false, error: 'Extension not found' };
      }

      // Get session
      const ses = sessionName === 'default' ? session.defaultSession : session.fromPartition(sessionName);

      // Remove extension
      await ses.removeExtension(extensionId);

      // Remove from loaded extensions
      this.loadedExtensions.delete(extensionId);

      console.log(`🧩 Extension unloaded: ${extensionInfo.name}`);

      return {
        success: true,
        extension: extensionInfo
      };

    } catch (error) {
      console.error('Extension unloading error:', error);
      return { success: false, error: error.message };
    }
  }

  async installExtensionFromCRX(crxPath, sessionName = 'default') {
    try {
      // This is a simplified implementation
      // In a full implementation, you'd need to extract and validate the CRX file
      return { success: false, error: 'CRX installation not yet implemented' };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async installExtensionFromStore(extensionId) {
    try {
      // This would require Chrome Web Store API integration
      return { success: false, error: 'Chrome Web Store installation not yet implemented' };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  getLoadedExtensions() {
    return {
      success: true,
      extensions: Array.from(this.loadedExtensions.values()),
      count: this.loadedExtensions.size
    };
  }

  getExtensionInfo(extensionId) {
    const extension = this.loadedExtensions.get(extensionId);
    
    if (extension) {
      return { success: true, extension };
    }
    
    return { success: false, error: 'Extension not found' };
  }

  async enableExtension(extensionId, sessionName = 'default') {
    try {
      const extensionInfo = this.loadedExtensions.get(extensionId);
      
      if (!extensionInfo) {
        return { success: false, error: 'Extension not found' };
      }

      // Extensions are enabled by default when loaded
      // This could be extended to support enable/disable states
      
      return {
        success: true,
        extension: extensionInfo,
        status: 'enabled'
      };

    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async disableExtension(extensionId, sessionName = 'default') {
    try {
      // For now, disabling means unloading
      // In a full implementation, you'd maintain enabled/disabled state
      return await this.unloadExtension(extensionId, sessionName);

    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Extension Communication
  async sendMessageToExtension(extensionId, message) {
    try {
      const extensionInfo = this.loadedExtensions.get(extensionId);
      
      if (!extensionInfo) {
        return { success: false, error: 'Extension not found' };
      }

      // This would require implementing the Chrome extension messaging API
      // For now, it's a placeholder
      
      return {
        success: false,
        error: 'Extension messaging not yet implemented'
      };

    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Extension Development Tools
  async reloadExtension(extensionId) {
    try {
      const extensionInfo = this.loadedExtensions.get(extensionId);
      
      if (!extensionInfo) {
        return { success: false, error: 'Extension not found' };
      }

      // Unload and reload
      const unloadResult = await this.unloadExtension(extensionId, extensionInfo.session);
      if (!unloadResult.success) {
        return unloadResult;
      }

      const loadResult = await this.loadExtension(extensionInfo.path, extensionInfo.session);
      return loadResult;

    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async getExtensionManifest(extensionId) {
    const extensionInfo = this.loadedExtensions.get(extensionId);
    
    if (extensionInfo) {
      return {
        success: true,
        manifest: extensionInfo.manifest
      };
    }
    
    return { success: false, error: 'Extension not found' };
  }

  // Popular Extension Presets
  async loadPopularExtensions() {
    const popularExtensions = [
      // These would be popular extension directories if available
      // 'adblock-plus',
      // 'react-devtools',
      // 'vue-devtools',
      // 'redux-devtools'
    ];

    const results = [];

    for (const extName of popularExtensions) {
      const extPath = path.join(this.extensionDirectory, extName);
      if (fs.existsSync(extPath)) {
        const result = await this.loadExtension(extPath);
        results.push({ name: extName, result });
      }
    }

    return {
      success: true,
      loaded: results.filter(r => r.result.success).length,
      total: results.length,
      results
    };
  }

  // Chrome DevTools Extensions
  async loadDevToolsExtensions() {
    try {
      // Common DevTools extension paths
      const devToolsExtensions = [
        'React Developer Tools',
        'Vue.js devtools',
        'Redux DevTools',
        'Apollo Client Developer Tools'
      ];

      // This is a placeholder - actual implementation would locate these extensions
      return {
        success: true,
        message: 'DevTools extensions support available',
        availableExtensions: devToolsExtensions
      };

    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Extension Security
  validateExtensionSecurity(manifest) {
    const warnings = [];
    const errors = [];

    // Check permissions
    if (manifest.permissions) {
      const sensitivePermissions = ['<all_urls>', 'tabs', 'cookies', 'storage'];
      const requestedSensitive = manifest.permissions.filter(p => 
        sensitivePermissions.some(sp => p.includes(sp))
      );
      
      if (requestedSensitive.length > 0) {
        warnings.push(`Requests sensitive permissions: ${requestedSensitive.join(', ')}`);
      }
    }

    // Check content scripts
    if (manifest.content_scripts) {
      const allUrlsScripts = manifest.content_scripts.filter(cs => 
        cs.matches && cs.matches.includes('<all_urls>')
      );
      
      if (allUrlsScripts.length > 0) {
        warnings.push('Content scripts run on all URLs');
      }
    }

    return {
      safe: errors.length === 0,
      warnings,
      errors
    };
  }

  // Cleanup
  async cleanup() {
    try {
      // Unload all extensions
      const extensionIds = Array.from(this.loadedExtensions.keys());
      const unloadPromises = extensionIds.map(id => this.unloadExtension(id));
      
      await Promise.all(unloadPromises);
      
      this.loadedExtensions.clear();
      this.extensionSessions.clear();
      
      console.log('✅ Extension Manager Cleanup Complete');
      
      return { success: true, unloaded: extensionIds.length };

    } catch (error) {
      console.error('Extension cleanup error:', error);
      return { success: false, error: error.message };
    }
  }
}

module.exports = ExtensionManager;