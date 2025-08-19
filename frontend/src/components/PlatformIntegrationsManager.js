import React, { useState, useEffect } from 'react';

const PlatformIntegrationsManager = ({ backendUrl, userSession }) => {
  const [availablePlatforms, setAvailablePlatforms] = useState([]);
  const [connectedPlatforms, setConnectedPlatforms] = useState([]);
  const [isVisible, setIsVisible] = useState(false);
  const [activeTab, setActiveTab] = useState('available');

  useEffect(() => {
    if (userSession) {
      loadAvailablePlatforms();
      loadConnectedPlatforms();
    }
  }, [userSession]);

  const loadAvailablePlatforms = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/platforms/available`);
      if (response.ok) {
        const result = await response.json();
        setAvailablePlatforms(result.platforms || []);
      }
    } catch (error) {
      console.error('Failed to load available platforms:', error);
    }
  };

  const loadConnectedPlatforms = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/platforms/user-integrations/${userSession}`);
      if (response.ok) {
        const result = await response.json();
        setConnectedPlatforms(result.connections || []);
      }
    } catch (error) {
      console.error('Failed to load connected platforms:', error);
    }
  };

  const connectPlatform = async (platformId, authData = {}) => {
    try {
      // For demo purposes, we'll simulate connection
      const simulatedAuthData = {
        api_key: `demo_key_${platformId}_${Date.now()}`,
        token: `demo_token_${platformId}`,
        connected_at: new Date().toISOString()
      };

      const response = await fetch(`${backendUrl}/api/platforms/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_session: userSession,
          platform_id: platformId,
          auth_data: simulatedAuthData
        })
      });

      if (response.ok) {
        const result = await response.json();
        loadConnectedPlatforms(); // Refresh connected platforms
        return result;
      }
    } catch (error) {
      console.error('Failed to connect platform:', error);
    }
  };

  const disconnectPlatform = async (platformId) => {
    try {
      const response = await fetch(`${backendUrl}/api/platforms/disconnect/${userSession}/${platformId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        loadConnectedPlatforms(); // Refresh connected platforms
      }
    } catch (error) {
      console.error('Failed to disconnect platform:', error);
    }
  };

  const executePlatformAction = async (platformId, capabilityId, parameters = {}) => {
    try {
      const response = await fetch(`${backendUrl}/api/platforms/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_session: userSession,
          platform_id: platformId,
          capability_id: capabilityId,
          parameters
        })
      });

      if (response.ok) {
        const result = await response.json();
        return result;
      }
    } catch (error) {
      console.error('Failed to execute platform action:', error);
    }
  };

  const getPlatformIcon = (platformId) => {
    const icons = {
      linkedin: '💼',
      twitter: '🐦',
      github: '🐙',
      slack: '💬',
      youtube: '📺',
      instagram: '📷',
      facebook: '📘',
      discord: '🎮'
    };
    return icons[platformId] || '🔗';
  };

  const getCategoryColor = (category) => {
    const colors = {
      professional: 'bg-blue-600',
      social: 'bg-pink-600',
      development: 'bg-purple-600',
      communication: 'bg-green-600',
      productivity: 'bg-yellow-600'
    };
    return colors[category] || 'bg-gray-600';
  };

  return (
    <>
      {/* Platform Integrations Button */}
      <button
        className="nav-btn integrations-btn"
        onClick={() => setIsVisible(!isVisible)}
        title="Platform Integrations - Connect to 50+ Services"
        aria-label="Toggle platform integrations"
      >
        🔗
      </button>

      {/* Integrations Panel */}
      {isVisible && (
        <div className="fixed top-16 right-4 bg-gray-900 border border-gray-600 rounded-lg p-4 w-96 max-h-96 overflow-y-auto z-40">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-white font-medium flex items-center">
              <span className="mr-2">🔗</span>
              Platform Integrations
            </h3>
            <button
              onClick={() => setIsVisible(false)}
              className="text-gray-400 hover:text-white"
            >
              ×
            </button>
          </div>

          {/* Tabs */}
          <div className="flex mb-4">
            <button
              onClick={() => setActiveTab('available')}
              className={`flex-1 py-2 px-3 text-sm rounded-l ${
                activeTab === 'available'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Available ({availablePlatforms.length})
            </button>
            <button
              onClick={() => setActiveTab('connected')}
              className={`flex-1 py-2 px-3 text-sm rounded-r ${
                activeTab === 'connected'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Connected ({connectedPlatforms.length})
            </button>
          </div>

          {/* Available Platforms */}
          {activeTab === 'available' && (
            <div className="space-y-2">
              {availablePlatforms.map((platform) => (
                <div key={platform.platform_id} className="bg-gray-800 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{getPlatformIcon(platform.platform_id)}</span>
                      <div>
                        <h4 className="text-white font-medium text-sm">{platform.name}</h4>
                        <span className={`text-xs px-2 py-0.5 rounded text-white ${getCategoryColor(platform.category)}`}>
                          {platform.category}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => connectPlatform(platform.platform_id)}
                      className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700"
                      disabled={connectedPlatforms.some(c => c.platform_id === platform.platform_id && c.status === 'connected')}
                    >
                      {connectedPlatforms.some(c => c.platform_id === platform.platform_id && c.status === 'connected') ? 'Connected' : 'Connect'}
                    </button>
                  </div>
                  
                  <div className="text-gray-400 text-xs">
                    {platform.capabilities?.length || 0} capabilities available
                  </div>
                  
                  {/* Show first few capabilities */}
                  {platform.capabilities && platform.capabilities.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {platform.capabilities.slice(0, 3).map((capability) => (
                        <span key={capability.id} className="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded">
                          {capability.name}
                        </span>
                      ))}
                      {platform.capabilities.length > 3 && (
                        <span className="text-xs text-gray-400">
                          +{platform.capabilities.length - 3} more
                        </span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Connected Platforms */}
          {activeTab === 'connected' && (
            <div className="space-y-2">
              {connectedPlatforms.length === 0 ? (
                <div className="text-center py-6">
                  <span className="text-4xl mb-2 block">🔗</span>
                  <p className="text-gray-400 text-sm">No platforms connected yet</p>
                  <button
                    onClick={() => setActiveTab('available')}
                    className="mt-2 px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
                  >
                    Browse Available Platforms
                  </button>
                </div>
              ) : (
                connectedPlatforms.map((connection) => (
                  <div key={connection.connection_id} className="bg-gray-800 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">{getPlatformIcon(connection.platform_id)}</span>
                        <div>
                          <h4 className="text-white font-medium text-sm capitalize">{connection.platform_id}</h4>
                          <span className="text-xs text-gray-400">
                            Connected {new Date(connection.connected_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          connection.status === 'connected' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
                        }`}>
                          {connection.status}
                        </span>
                        <button
                          onClick={() => disconnectPlatform(connection.platform_id)}
                          className="text-red-400 hover:text-red-300 text-xs"
                          title="Disconnect"
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                    
                    <div className="text-gray-400 text-xs mb-2">
                      Used {connection.usage_count || 0} times
                    </div>

                    {/* Quick Actions */}
                    <div className="flex space-x-2">
                      {connection.platform_id === 'twitter' && (
                        <button
                          onClick={() => executePlatformAction('twitter', 'post_tweet', { text: 'Hello from AETHER!' })}
                          className="px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
                        >
                          Post Tweet
                        </button>
                      )}
                      {connection.platform_id === 'linkedin' && (
                        <button
                          onClick={() => executePlatformAction('linkedin', 'post_update', { content: 'Working with AETHER browser!' })}
                          className="px-2 py-1 bg-blue-700 text-white text-xs rounded hover:bg-blue-800"
                        >
                          Post Update
                        </button>
                      )}
                      {connection.platform_id === 'github' && (
                        <button
                          onClick={() => executePlatformAction('github', 'get_repos', {})}
                          className="px-2 py-1 bg-gray-700 text-white text-xs rounded hover:bg-gray-600"
                        >
                          Get Repos
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}
    </>
  );
};

// Export helper functions
export const executeQuickPlatformAction = async (backendUrl, userSession, platformId, capabilityId, parameters = {}) => {
  try {
    const response = await fetch(`${backendUrl}/api/platforms/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_session: userSession,
        platform_id: platformId,
        capability_id: capabilityId,
        parameters
      })
    });

    if (response.ok) {
      return await response.json();
    }
  } catch (error) {
    console.error('Failed to execute platform action:', error);
  }
  return null;
};

export const batchExecutePlatformActions = async (backendUrl, userSession, actions) => {
  try {
    const response = await fetch(`${backendUrl}/api/platforms/batch-execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_session: userSession,
        actions
      })
    });

    if (response.ok) {
      return await response.json();
    }
  } catch (error) {
    console.error('Failed to execute batch platform actions:', error);
  }
  return null;
};

export default PlatformIntegrationsManager;