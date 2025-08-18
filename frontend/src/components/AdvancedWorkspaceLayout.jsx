/**
 * PHASE 2-3: Advanced Workspace Layout with Drag & Drop, Resizable Panels
 * Modern UI with Framer Motion animations and intelligent layout management
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Maximize2, 
  Minimize2, 
  Settings, 
  Layout,
  Sidebar,
  Terminal,
  Globe,
  MessageSquare,
  Zap,
  BarChart3,
  Layers,
  Grid3X3,
  PanelLeftClose,
  PanelRightClose
} from 'lucide-react';
import { Resizable } from 'react-resizable';
import 'react-resizable/css/styles.css';

const LAYOUT_PRESETS = {
  default: {
    sidebar: { visible: true, width: 320 },
    browser: { visible: true, width: 'auto' },
    ai: { visible: true, width: 380 },
    timeline: { visible: false, height: 200 },
    performance: { visible: false, width: 300 }
  },
  focused: {
    sidebar: { visible: false, width: 320 },
    browser: { visible: true, width: 'auto' },
    ai: { visible: false, width: 380 },
    timeline: { visible: false, height: 200 },
    performance: { visible: false, width: 300 }
  },
  development: {
    sidebar: { visible: true, width: 250 },
    browser: { visible: true, width: 'auto' },
    ai: { visible: true, width: 350 },
    timeline: { visible: true, height: 180 },
    performance: { visible: true, width: 280 }
  },
  analytics: {
    sidebar: { visible: true, width: 280 },
    browser: { visible: true, width: 'auto' },
    ai: { visible: false, width: 380 },
    timeline: { visible: true, height: 220 },
    performance: { visible: true, width: 320 }
  }
};

const ANIMATION_VARIANTS = {
  panel: {
    initial: { opacity: 0, x: -20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -20 },
    transition: { duration: 0.3, ease: "easeOut" }
  },
  content: {
    initial: { opacity: 0, y: 10 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.2, delay: 0.1 }
  },
  toolbar: {
    initial: { opacity: 0, scale: 0.95 },
    animate: { opacity: 1, scale: 1 },
    transition: { duration: 0.2 }
  }
};

const AdvancedWorkspaceLayout = ({ 
  children, 
  onLayoutChange,
  sidebarContent,
  aiAssistantContent,
  timelineContent,
  performanceContent,
  currentUrl,
  isLoading
}) => {
  const [layout, setLayout] = useState('default');
  const [panels, setPanels] = useState(LAYOUT_PRESETS.default);
  const [isCustomizing, setIsCustomizing] = useState(false);
  const [draggedPanel, setDraggedPanel] = useState(null);
  const [workspaceMode, setWorkspaceMode] = useState('normal'); // normal, focus, presentation

  // Load saved layout from localStorage
  useEffect(() => {
    const savedLayout = localStorage.getItem('aether_workspace_layout');
    if (savedLayout) {
      try {
        const parsed = JSON.parse(savedLayout);
        setPanels(parsed.panels || LAYOUT_PRESETS.default);
        setLayout(parsed.layout || 'default');
      } catch (error) {
        console.error('Failed to load saved layout:', error);
      }
    }
  }, []);

  // Save layout changes
  const saveLayout = useCallback((newPanels, newLayout) => {
    const layoutData = { panels: newPanels, layout: newLayout };
    localStorage.setItem('aether_workspace_layout', JSON.stringify(layoutData));
    onLayoutChange?.(layoutData);
  }, [onLayoutChange]);

  // Apply preset layout
  const applyPreset = useCallback((presetName) => {
    const preset = LAYOUT_PRESETS[presetName];
    if (preset) {
      setPanels(preset);
      setLayout(presetName);
      saveLayout(preset, presetName);
    }
  }, [saveLayout]);

  // Toggle panel visibility
  const togglePanel = useCallback((panelName) => {
    setPanels(prev => {
      const newPanels = {
        ...prev,
        [panelName]: {
          ...prev[panelName],
          visible: !prev[panelName].visible
        }
      };
      saveLayout(newPanels, layout);
      return newPanels;
    });
  }, [layout, saveLayout]);

  // Resize panel
  const resizePanel = useCallback((panelName, dimension, value) => {
    setPanels(prev => {
      const newPanels = {
        ...prev,
        [panelName]: {
          ...prev[panelName],
          [dimension]: value
        }
      };
      saveLayout(newPanels, layout);
      return newPanels;
    });
  }, [layout, saveLayout]);

  // Calculate layout styles
  const layoutStyles = useMemo(() => {
    const sidebarWidth = panels.sidebar.visible ? panels.sidebar.width : 0;
    const aiWidth = panels.ai.visible ? panels.ai.width : 0;
    const performanceWidth = panels.performance.visible ? panels.performance.width : 0;
    const timelineHeight = panels.timeline.visible ? panels.timeline.height : 0;

    return {
      sidebar: {
        width: sidebarWidth,
        display: panels.sidebar.visible ? 'block' : 'none'
      },
      main: {
        marginLeft: sidebarWidth,
        marginRight: aiWidth + performanceWidth,
        marginBottom: timelineHeight
      },
      ai: {
        width: aiWidth,
        display: panels.ai.visible ? 'block' : 'none'
      },
      performance: {
        width: performanceWidth,
        display: panels.performance.visible ? 'block' : 'none'
      },
      timeline: {
        height: timelineHeight,
        display: panels.timeline.visible ? 'block' : 'none'
      }
    };
  }, [panels]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.metaKey || e.ctrlKey) {
        switch (e.key) {
          case '1':
            e.preventDefault();
            togglePanel('sidebar');
            break;
          case '2':
            e.preventDefault();
            togglePanel('ai');
            break;
          case '3':
            e.preventDefault();
            togglePanel('timeline');
            break;
          case '0':
            e.preventDefault();
            applyPreset('default');
            break;
          case 'f':
            e.preventDefault();
            applyPreset('focused');
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [togglePanel, applyPreset]);

  return (
    <div className="advanced-workspace h-screen flex flex-col bg-gray-50 dark:bg-gray-900 overflow-hidden">
      {/* Advanced Toolbar */}
      <motion.div 
        className="workspace-toolbar bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-2 flex items-center justify-between shadow-sm"
        variants={ANIMATION_VARIANTS.toolbar}
        initial="initial"
        animate="animate"
      >
        <div className="flex items-center space-x-4">
          {/* Layout Presets */}
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-600 dark:text-gray-300">Layout:</span>
            {Object.keys(LAYOUT_PRESETS).map((presetName) => (
              <button
                key={presetName}
                onClick={() => applyPreset(presetName)}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  layout === presetName
                    ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                    : 'text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'
                }`}
              >
                {presetName.charAt(0).toUpperCase() + presetName.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Panel toggles */}
          <div className="flex items-center space-x-1 border-r border-gray-200 dark:border-gray-600 pr-3">
            <ToolbarButton
              icon={Sidebar}
              active={panels.sidebar.visible}
              onClick={() => togglePanel('sidebar')}
              tooltip="Toggle Sidebar (Cmd+1)"
            />
            <ToolbarButton
              icon={MessageSquare}
              active={panels.ai.visible}
              onClick={() => togglePanel('ai')}
              tooltip="Toggle AI Assistant (Cmd+2)"
            />
            <ToolbarButton
              icon={BarChart3}
              active={panels.performance.visible}
              onClick={() => togglePanel('performance')}
              tooltip="Toggle Performance"
            />
            <ToolbarButton
              icon={Layers}
              active={panels.timeline.visible}
              onClick={() => togglePanel('timeline')}
              tooltip="Toggle Timeline (Cmd+3)"
            />
          </div>

          {/* Workspace modes */}
          <div className="flex items-center space-x-1">
            <ToolbarButton
              icon={Layout}
              active={workspaceMode === 'normal'}
              onClick={() => setWorkspaceMode('normal')}
              tooltip="Normal Mode"
            />
            <ToolbarButton
              icon={Maximize2}
              active={workspaceMode === 'focus'}
              onClick={() => setWorkspaceMode('focus')}
              tooltip="Focus Mode"
            />
          </div>

          {/* Settings */}
          <ToolbarButton
            icon={Settings}
            active={isCustomizing}
            onClick={() => setIsCustomizing(!isCustomizing)}
            tooltip="Customize Layout"
          />
        </div>
      </motion.div>

      {/* Main Workspace */}
      <div className="workspace-main flex-1 flex relative overflow-hidden">
        {/* Sidebar Panel */}
        <AnimatePresence>
          {panels.sidebar.visible && (
            <motion.div
              className="workspace-sidebar bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden shadow-sm"
              style={{ width: layoutStyles.sidebar.width }}
              variants={ANIMATION_VARIANTS.panel}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <ResizablePanel
                width={panels.sidebar.width}
                onResize={(width) => resizePanel('sidebar', 'width', width)}
                minWidth={200}
                maxWidth={500}
                axis="x"
              >
                <PanelHeader 
                  title="Navigator" 
                  icon={Sidebar}
                  onClose={() => togglePanel('sidebar')}
                />
                <div className="flex-1 overflow-auto">
                  {sidebarContent}
                </div>
              </ResizablePanel>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Content Area */}
        <div 
          className="workspace-content flex-1 flex flex-col"
          style={layoutStyles.main}
        >
          {/* Browser Content */}
          <motion.div 
            className="flex-1 bg-white dark:bg-gray-800 overflow-hidden"
            variants={ANIMATION_VARIANTS.content}
            initial="initial"
            animate="animate"
          >
            <div className="h-full relative">
              {isLoading && (
                <motion.div 
                  className="absolute inset-0 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm flex items-center justify-center z-10"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <div className="flex items-center space-x-3">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <span className="text-gray-600 dark:text-gray-300 font-medium">Loading...</span>
                  </div>
                </motion.div>
              )}
              {children}
            </div>
          </motion.div>

          {/* Timeline Panel */}
          <AnimatePresence>
            {panels.timeline.visible && (
              <motion.div
                className="workspace-timeline bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 overflow-hidden"
                style={{ height: layoutStyles.timeline.height }}
                variants={ANIMATION_VARIANTS.panel}
                initial="initial"
                animate="animate"
                exit="exit"
              >
                <ResizablePanel
                  height={panels.timeline.height}
                  onResize={(height) => resizePanel('timeline', 'height', height)}
                  minHeight={120}
                  maxHeight={400}
                  axis="y"
                >
                  <PanelHeader 
                    title="Timeline & History" 
                    icon={Layers}
                    onClose={() => togglePanel('timeline')}
                  />
                  <div className="flex-1 overflow-auto p-4">
                    {timelineContent}
                  </div>
                </ResizablePanel>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Right Side Panels */}
        <div className="workspace-right flex">
          {/* Performance Panel */}
          <AnimatePresence>
            {panels.performance.visible && (
              <motion.div
                className="workspace-performance bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden"
                style={{ width: layoutStyles.performance.width }}
                variants={ANIMATION_VARIANTS.panel}
                initial="initial"
                animate="animate"
                exit="exit"
              >
                <ResizablePanel
                  width={panels.performance.width}
                  onResize={(width) => resizePanel('performance', 'width', width)}
                  minWidth={250}
                  maxWidth={400}
                  axis="x"
                >
                  <PanelHeader 
                    title="Performance" 
                    icon={BarChart3}
                    onClose={() => togglePanel('performance')}
                  />
                  <div className="flex-1 overflow-auto">
                    {performanceContent}
                  </div>
                </ResizablePanel>
              </motion.div>
            )}
          </AnimatePresence>

          {/* AI Assistant Panel */}
          <AnimatePresence>
            {panels.ai.visible && (
              <motion.div
                className="workspace-ai bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden shadow-sm"
                style={{ width: layoutStyles.ai.width }}
                variants={ANIMATION_VARIANTS.panel}
                initial="initial"
                animate="animate"
                exit="exit"
              >
                <ResizablePanel
                  width={panels.ai.width}
                  onResize={(width) => resizePanel('ai', 'width', width)}
                  minWidth={300}
                  maxWidth={600}
                  axis="x"
                >
                  <PanelHeader 
                    title="AI Assistant" 
                    icon={MessageSquare}
                    onClose={() => togglePanel('ai')}
                  />
                  <div className="flex-1 overflow-hidden">
                    {aiAssistantContent}
                  </div>
                </ResizablePanel>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Customization Panel */}
      <AnimatePresence>
        {isCustomizing && (
          <motion.div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsCustomizing(false)}
          >
            <motion.div
              className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-2xl w-full mx-4"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <CustomizationPanel 
                panels={panels}
                onPanelChange={setPanels}
                onClose={() => setIsCustomizing(false)}
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Toolbar Button Component
const ToolbarButton = ({ icon: Icon, active, onClick, tooltip }) => (
  <button
    className={`p-2 rounded-md transition-colors ${
      active
        ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
        : 'text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'
    }`}
    onClick={onClick}
    title={tooltip}
  >
    <Icon size={16} />
  </button>
);

// Panel Header Component
const PanelHeader = ({ title, icon: Icon, onClose }) => (
  <div className="panel-header flex items-center justify-between p-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
    <div className="flex items-center space-x-2">
      <Icon size={16} className="text-gray-600 dark:text-gray-300" />
      <span className="text-sm font-medium text-gray-800 dark:text-gray-200">{title}</span>
    </div>
    <button
      onClick={onClose}
      className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400"
    >
      <PanelLeftClose size={14} />
    </button>
  </div>
);

// Resizable Panel Wrapper
const ResizablePanel = ({ children, width, height, onResize, minWidth, maxWidth, minHeight, maxHeight, axis = 'x' }) => {
  if (axis === 'x') {
    return (
      <Resizable
        width={width}
        height={0}
        onResize={(e, { size }) => onResize(size.width)}
        minConstraints={[minWidth, 0]}
        maxConstraints={[maxWidth, 0]}
        resizeHandles={['e']}
        handle={<ResizeHandle axis="vertical" />}
      >
        <div style={{ width, height: '100%' }} className="flex flex-col">
          {children}
        </div>
      </Resizable>
    );
  } else {
    return (
      <Resizable
        width={0}
        height={height}
        onResize={(e, { size }) => onResize(size.height)}
        minConstraints={[0, minHeight]}
        maxConstraints={[0, maxHeight]}
        resizeHandles={['s']}
        handle={<ResizeHandle axis="horizontal" />}
      >
        <div style={{ height, width: '100%' }} className="flex flex-col">
          {children}
        </div>
      </Resizable>
    );
  }
};

// Custom Resize Handle
const ResizeHandle = ({ axis }) => (
  <div
    className={`resize-handle ${
      axis === 'vertical' 
        ? 'resize-handle-vertical w-1 h-full bg-transparent hover:bg-blue-300 cursor-col-resize' 
        : 'resize-handle-horizontal h-1 w-full bg-transparent hover:bg-blue-300 cursor-row-resize'
    } transition-colors duration-150`}
  />
);

// Customization Panel Component
const CustomizationPanel = ({ panels, onPanelChange, onClose }) => {
  const handlePanelToggle = (panelName) => {
    onPanelChange(prev => ({
      ...prev,
      [panelName]: {
        ...prev[panelName],
        visible: !prev[panelName].visible
      }
    }));
  };

  const handleDimensionChange = (panelName, dimension, value) => {
    onPanelChange(prev => ({
      ...prev,
      [panelName]: {
        ...prev[panelName],
        [dimension]: parseInt(value)
      }
    }));
  };

  return (
    <div className="customization-panel">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">
          Customize Workspace
        </h3>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          ×
        </button>
      </div>

      <div className="space-y-6">
        {Object.entries(panels).map(([panelName, config]) => (
          <div key={panelName} className="panel-config">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium capitalize text-gray-700 dark:text-gray-300">
                {panelName}
              </span>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={config.visible}
                  onChange={() => handlePanelToggle(panelName)}
                  className="mr-2"
                />
                <span className="text-sm text-gray-600 dark:text-gray-400">Visible</span>
              </label>
            </div>

            {config.visible && (
              <div className="grid grid-cols-2 gap-4">
                {config.width !== undefined && (
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Width (px)</label>
                    <input
                      type="range"
                      min="200"
                      max="600"
                      value={config.width}
                      onChange={(e) => handleDimensionChange(panelName, 'width', e.target.value)}
                      className="w-full"
                    />
                    <span className="text-xs text-gray-500">{config.width}px</span>
                  </div>
                )}
                {config.height !== undefined && (
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Height (px)</label>
                    <input
                      type="range"
                      min="120"
                      max="400"
                      value={config.height}
                      onChange={(e) => handleDimensionChange(panelName, 'height', e.target.value)}
                      className="w-full"
                    />
                    <span className="text-xs text-gray-500">{config.height}px</span>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-600">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Keyboard shortcuts: Cmd+1-3 to toggle panels, Cmd+0 for default layout
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdvancedWorkspaceLayout;