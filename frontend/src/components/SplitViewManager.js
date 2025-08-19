import React, { useState, useEffect } from 'react';

const SplitViewManager = ({ backendUrl, userSession, onNavigate }) => {
  const [splitSessions, setSplitSessions] = useState([]);
  const [activeSplitSession, setActiveSplitSession] = useState(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    loadSplitSessions();
  }, [userSession]);

  const loadSplitSessions = async () => {
    // For now, we'll manage split sessions in local state
    // In production, this would fetch from backend
  };

  const createSplitView = async (layout = 'horizontal', initialUrls = []) => {
    try {
      const response = await fetch(`${backendUrl}/api/split-view/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_session: userSession,
          layout,
          initial_urls: initialUrls
        })
      });

      if (response.ok) {
        const result = await response.json();
        setActiveSplitSession(result.session_id);
        setIsVisible(true);
        return result;
      }
    } catch (error) {
      console.error('Failed to create split view:', error);
    }
  };

  const addSplitPane = async (url) => {
    if (!activeSplitSession) return;

    try {
      const response = await fetch(`${backendUrl}/api/split-view/add-pane/${activeSplitSession}?url=${encodeURIComponent(url)}`, {
        method: 'POST'
      });

      if (response.ok) {
        const result = await response.json();
        return result;
      }
    } catch (error) {
      console.error('Failed to add split pane:', error);
    }
  };

  const navigateSplitPane = async (paneId, url, syncAll = false) => {
    if (!activeSplitSession) return;

    try {
      const response = await fetch(`${backendUrl}/api/split-view/navigate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: activeSplitSession,
          pane_id: paneId,
          url,
          sync_all: syncAll
        })
      });

      if (response.ok) {
        const result = await response.json();
        return result;
      }
    } catch (error) {
      console.error('Failed to navigate split pane:', error);
    }
  };

  const changeSplitLayout = async (layout) => {
    if (!activeSplitSession) return;

    try {
      const response = await fetch(`${backendUrl}/api/split-view/change-layout/${activeSplitSession}/${layout}`, {
        method: 'POST'
      });

      if (response.ok) {
        const result = await response.json();
        return result;
      }
    } catch (error) {
      console.error('Failed to change split layout:', error);
    }
  };

  return (
    <>
      {/* Split View Toggle Button */}
      <button
        className="nav-btn split-view-btn"
        onClick={() => createSplitView('horizontal', ['https://google.com', 'https://github.com'])}
        title="Split View - Browse Multiple Sites"
        aria-label="Create split view"
      >
        🔀
      </button>

      {/* Split View Controls Panel */}
      {isVisible && activeSplitSession && (
        <div className="fixed top-16 right-4 bg-gray-900 border border-gray-600 rounded-lg p-4 w-80 z-40">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-white font-medium flex items-center">
              <span className="mr-2">🔀</span>
              Split View Controls
            </h3>
            <button
              onClick={() => setIsVisible(false)}
              className="text-gray-400 hover:text-white"
            >
              ×
            </button>
          </div>

          <div className="space-y-3">
            {/* Layout Controls */}
            <div>
              <label className="text-gray-300 text-sm block mb-2">Layout</label>
              <div className="flex space-x-2">
                <button
                  onClick={() => changeSplitLayout('horizontal')}
                  className="px-3 py-1 bg-gray-700 text-white text-xs rounded hover:bg-gray-600"
                  title="Horizontal Split"
                >
                  ⬌
                </button>
                <button
                  onClick={() => changeSplitLayout('vertical')}
                  className="px-3 py-1 bg-gray-700 text-white text-xs rounded hover:bg-gray-600"
                  title="Vertical Split"
                >
                  ⬍
                </button>
                <button
                  onClick={() => changeSplitLayout('grid')}
                  className="px-3 py-1 bg-gray-700 text-white text-xs rounded hover:bg-gray-600"
                  title="Grid Layout"
                >
                  ⊞
                </button>
              </div>
            </div>

            {/* Quick Add URLs */}
            <div>
              <label className="text-gray-300 text-sm block mb-2">Quick Add</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => addSplitPane('https://google.com')}
                  className="px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
                >
                  + Google
                </button>
                <button
                  onClick={() => addSplitPane('https://github.com')}
                  className="px-2 py-1 bg-gray-700 text-white text-xs rounded hover:bg-gray-600"
                >
                  + GitHub
                </button>
                <button
                  onClick={() => addSplitPane('https://stackoverflow.com')}
                  className="px-2 py-1 bg-orange-600 text-white text-xs rounded hover:bg-orange-700"
                >
                  + Stack Overflow
                </button>
                <button
                  onClick={() => addSplitPane('https://chat.openai.com')}
                  className="px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700"
                >
                  + ChatGPT
                </button>
              </div>
            </div>

            {/* Sync Options */}
            <div>
              <label className="text-gray-300 text-sm block mb-2">Sync Options</label>
              <div className="flex flex-col space-y-1">
                <label className="flex items-center text-sm text-gray-300">
                  <input type="checkbox" className="mr-2" />
                  Sync Navigation
                </label>
                <label className="flex items-center text-sm text-gray-300">
                  <input type="checkbox" className="mr-2" />
                  Sync Scroll
                </label>
              </div>
            </div>

            {/* Actions */}
            <div className="flex space-x-2">
              <button
                onClick={() => {
                  setActiveSplitSession(null);
                  setIsVisible(false);
                }}
                className="flex-1 px-3 py-2 bg-red-600 text-white text-sm rounded hover:bg-red-700"
              >
                Close Split View
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// Export helper functions
export const createQuickSplitView = async (backendUrl, userSession, urls) => {
  try {
    const response = await fetch(`${backendUrl}/api/split-view/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_session: userSession,
        layout: 'horizontal',
        initial_urls: urls
      })
    });

    if (response.ok) {
      return await response.json();
    }
  } catch (error) {
    console.error('Failed to create quick split view:', error);
  }
  return null;
};

export default SplitViewManager;