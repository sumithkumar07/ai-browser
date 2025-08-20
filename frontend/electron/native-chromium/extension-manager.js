/**
 * Extension Manager for Native Chromium
 * Manages Chrome extensions in Electron
 */

const path = require('path');
const fs = require('fs').promises;

class ExtensionManager {
    constructor() {
        this.loadedExtensions = new Map();
        this.extensionPaths = new Set();
        this.isEnabled = true;
        
        console.log('🧩 Extension Manager initialized');
    }

    async loadExtension(extensionPath, options = {}) {
        try {
            if (!this.isEnabled) {
                throw new Error('Extension Manager is disabled');
            }

            // Validate extension path
            const resolvedPath = path.resolve(extensionPath);
            const manifestPath = path.join(resolvedPath, 'manifest.json');

            // Check if manifest exists
            try {
                await fs.access(manifestPath);
            } catch {
                throw new Error('Extension manifest.json not found');
            }

            // Read and validate manifest
            const manifestContent = await fs.readFile(manifestPath, 'utf8');
            const manifest = JSON.parse(manifestContent);

            if (!manifest.name || !manifest.version) {
                throw new Error('Invalid extension manifest');
            }

            // Load extension using Electron's session API
            const { session } = require('electron');
            const extension = await session.defaultSession.loadExtension(
                resolvedPath,
                {
                    allowFileAccess: options.allowFileAccess !== false,
                    ...options
                }
            );

            const extensionInfo = {
                id: extension.id,
                name: manifest.name,
                version: manifest.version,
                description: manifest.description || '',
                path: resolvedPath,
                manifest: manifest,
                loaded: new Date(),
                extension: extension
            };

            this.loadedExtensions.set(extension.id, extensionInfo);
            this.extensionPaths.add(resolvedPath);

            console.log(`✅ Extension loaded: ${manifest.name} (${extension.id})`);

            return {
                success: true,
                extension_id: extension.id,
                name: manifest.name,
                version: manifest.version
            };

        } catch (error) {
            console.error(`❌ Extension load failed:`, error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async unloadExtension(extensionId) {
        try {
            const extensionInfo = this.loadedExtensions.get(extensionId);
            if (!extensionInfo) {
                throw new Error('Extension not found');
            }

            // Unload extension using Electron's session API
            const { session } = require('electron');
            session.defaultSession.removeExtension(extensionId);

            this.loadedExtensions.delete(extensionId);
            this.extensionPaths.delete(extensionInfo.path);

            console.log(`✅ Extension unloaded: ${extensionInfo.name} (${extensionId})`);

            return {
                success: true,
                extension_id: extensionId,
                name: extensionInfo.name
            };

        } catch (error) {
            console.error(`❌ Extension unload failed:`, error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async reloadExtension(extensionId) {
        try {
            const extensionInfo = this.loadedExtensions.get(extensionId);
            if (!extensionInfo) {
                throw new Error('Extension not found');
            }

            const extensionPath = extensionInfo.path;

            // Unload and reload
            await this.unloadExtension(extensionId);
            const result = await this.loadExtension(extensionPath);

            if (result.success) {
                console.log(`✅ Extension reloaded: ${extensionInfo.name}`);
            }

            return result;

        } catch (error) {
            console.error(`❌ Extension reload failed:`, error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }

    getLoadedExtensions() {
        const extensions = Array.from(this.loadedExtensions.values()).map(ext => ({
            id: ext.id,
            name: ext.name,
            version: ext.version,
            description: ext.description,
            loaded: ext.loaded.toISOString(),
            permissions: ext.manifest.permissions || [],
            content_scripts: ext.manifest.content_scripts || []
        }));

        return {
            success: true,
            extensions: extensions,
            total: extensions.length
        };
    }

    getExtensionInfo(extensionId) {
        const extensionInfo = this.loadedExtensions.get(extensionId);
        if (!extensionInfo) {
            return {
                success: false,
                error: 'Extension not found'
            };
        }

        return {
            success: true,
            extension: {
                id: extensionInfo.id,
                name: extensionInfo.name,
                version: extensionInfo.version,
                description: extensionInfo.description,
                path: extensionInfo.path,
                loaded: extensionInfo.loaded.toISOString(),
                manifest: extensionInfo.manifest
            }
        };
    }

    async installExtensionFromCRX(crxPath) {
        try {
            // This is a placeholder for CRX installation
            // In a full implementation, you would extract and validate the CRX file
            throw new Error('CRX installation not implemented yet');

        } catch (error) {
            console.error(`❌ CRX installation failed:`, error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async enableExtension(extensionId) {
        try {
            const extensionInfo = this.loadedExtensions.get(extensionId);
            if (!extensionInfo) {
                throw new Error('Extension not found');
            }

            // Enable extension
            extensionInfo.enabled = true;

            console.log(`✅ Extension enabled: ${extensionInfo.name}`);

            return {
                success: true,
                extension_id: extensionId,
                enabled: true
            };

        } catch (error) {
            console.error(`❌ Extension enable failed:`, error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async disableExtension(extensionId) {
        try {
            const extensionInfo = this.loadedExtensions.get(extensionId);
            if (!extensionInfo) {
                throw new Error('Extension not found');
            }

            // Disable extension
            extensionInfo.enabled = false;

            console.log(`⚠️ Extension disabled: ${extensionInfo.name}`);

            return {
                success: true,
                extension_id: extensionId,
                enabled: false
            };

        } catch (error) {
            console.error(`❌ Extension disable failed:`, error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }

    enable() {
        this.isEnabled = true;
        console.log('✅ Extension Manager enabled');
        return { success: true, enabled: true };
    }

    disable() {
        this.isEnabled = false;
        console.log('⚠️ Extension Manager disabled');
        return { success: true, enabled: false };
    }

    async loadDefaultExtensions() {
        try {
            const defaultExtensionsPath = path.join(__dirname, '..', 'extensions');
            
            try {
                const extensionDirs = await fs.readdir(defaultExtensionsPath);
                
                const loadPromises = extensionDirs.map(async (dir) => {
                    const extensionPath = path.join(defaultExtensionsPath, dir);
                    const stat = await fs.stat(extensionPath);
                    
                    if (stat.isDirectory()) {
                        return this.loadExtension(extensionPath);
                    }
                });

                const results = await Promise.allSettled(loadPromises);
                const successful = results.filter(r => r.status === 'fulfilled' && r.value.success);

                console.log(`✅ Loaded ${successful.length} default extensions`);

                return {
                    success: true,
                    loaded: successful.length,
                    total: results.length
                };

            } catch {
                // Default extensions directory doesn't exist, that's fine
                console.log('ℹ️ No default extensions directory found');
                return { success: true, loaded: 0, total: 0 };
            }

        } catch (error) {
            console.error(`❌ Default extensions load failed:`, error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async cleanup() {
        try {
            // Unload all extensions
            const extensionIds = Array.from(this.loadedExtensions.keys());
            
            for (const extensionId of extensionIds) {
                await this.unloadExtension(extensionId);
            }

            console.log('🧹 Extension Manager cleaned up');
            return { success: true };

        } catch (error) {
            console.error(`❌ Extension Manager cleanup failed:`, error.message);
            return { success: false, error: error.message };
        }
    }
}

module.exports = ExtensionManager;