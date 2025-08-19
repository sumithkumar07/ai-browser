import React, { useState, useEffect } from 'react';

const ShadowWorkspaceManager = ({ backendUrl, userSession }) => {
  const [shadowTasks, setShadowTasks] = useState([]);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (userSession) {
      loadActiveShadowTasks();
      
      // Poll for updates every 10 seconds
      const interval = setInterval(loadActiveShadowTasks, 10000);
      return () => clearInterval(interval);
    }
  }, [userSession]);

  const loadActiveShadowTasks = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/shadow/active-tasks/${userSession}`);
      if (response.ok) {
        const result = await response.json();
        setShadowTasks(result.active_shadow_tasks || []);
      }
    } catch (error) {
      console.error('Failed to load shadow tasks:', error);
    }
  };

  const controlShadowTask = async (taskId, action) => {
    try {
      const response = await fetch(`${backendUrl}/api/shadow/control-task/${taskId}/${action}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        loadActiveShadowTasks(); // Refresh tasks
      }
    } catch (error) {
      console.error('Failed to control shadow task:', error);
    }
  };

  const createShadowTask = async (command, currentUrl, priority = 'normal') => {
    try {
      const response = await fetch(`${backendUrl}/api/shadow/create-task`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command,
          user_session: userSession,
          current_url: currentUrl,
          priority,
          background_mode: true
        })
      });

      if (response.ok) {
        const result = await response.json();
        loadActiveShadowTasks(); // Refresh tasks
        return result;
      }
    } catch (error) {
      console.error('Failed to create shadow task:', error);
    }
  };

  if (shadowTasks.length === 0 && !isVisible) {
    return null; // Don't show if no tasks and not manually opened
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {/* Shadow Tasks Indicator */}
      {shadowTasks.length > 0 && (
        <div 
          className="bg-gray-800 border border-gray-600 rounded-lg p-3 mb-2 cursor-pointer hover:bg-gray-700 transition-colors"
          onClick={() => setIsVisible(!isVisible)}
        >
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            <span className="text-white text-sm">
              {shadowTasks.length} task{shadowTasks.length !== 1 ? 's' : ''} running in background
            </span>
            <span className="text-gray-400 text-xs">🌙</span>
          </div>
        </div>
      )}

      {/* Shadow Tasks Panel */}
      {isVisible && (
        <div className="bg-gray-900 border border-gray-600 rounded-lg p-4 w-96 max-h-80 overflow-y-auto">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-white font-medium flex items-center">
              <span className="mr-2">🌙</span>
              Shadow Workspace
            </h3>
            <button
              onClick={() => setIsVisible(false)}
              className="text-gray-400 hover:text-white"
            >
              ×
            </button>
          </div>

          <div className="space-y-3">
            {shadowTasks.map((task) => (
              <div key={task.task_id} className="bg-gray-800 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white text-sm font-medium truncate">
                    {task.command.substring(0, 40)}...
                  </span>
                  <span className={`text-xs px-2 py-1 rounded ${
                    task.status === 'running' ? 'bg-blue-600 text-white' :
                    task.status === 'completed' ? 'bg-green-600 text-white' :
                    'bg-gray-600 text-gray-300'
                  }`}>
                    {task.status}
                  </span>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-gray-700 rounded-full h-1.5 mb-2">
                  <div 
                    className="bg-blue-600 h-1.5 rounded-full transition-all duration-500"
                    style={{ width: `${task.progress}%` }}
                  ></div>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-gray-400 text-xs">
                    Progress: {task.progress}%
                  </span>
                  
                  <div className="flex space-x-1">
                    {task.status === 'running' && (
                      <button
                        onClick={() => controlShadowTask(task.task_id, 'pause')}
                        className="text-yellow-400 hover:text-yellow-300 text-xs"
                        title="Pause task"
                      >
                        ⏸️
                      </button>
                    )}
                    
                    {task.status === 'paused' && (
                      <button
                        onClick={() => controlShadowTask(task.task_id, 'resume')}
                        className="text-green-400 hover:text-green-300 text-xs"
                        title="Resume task"
                      >
                        ▶️
                      </button>
                    )}
                    
                    <button
                      onClick={() => controlShadowTask(task.task_id, 'cancel')}
                      className="text-red-400 hover:text-red-300 text-xs"
                      title="Cancel task"
                    >
                      ❌
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {shadowTasks.length === 0 && (
            <div className="text-gray-400 text-center py-4">
              <span className="text-2xl mb-2 block">🌙</span>
              <p className="text-sm">No background tasks running</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Export both the component and a helper function
export default ShadowWorkspaceManager;

export const createShadowTask = async (backendUrl, userSession, command, currentUrl, priority = 'normal') => {
  try {
    const response = await fetch(`${backendUrl}/api/shadow/create-task`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        command,
        user_session: userSession,
        current_url: currentUrl,
        priority,
        background_mode: true
      })
    });

    if (response.ok) {
      const result = await response.json();
      return result;
    }
  } catch (error) {
    console.error('Failed to create shadow task:', error);
  }
  return null;
};