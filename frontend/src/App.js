import React, { useState, useEffect, useCallback } from 'react';
import { 
  ArrowLeft, 
  ArrowRight, 
  RotateCcw, 
  Menu, 
  Star, 
  Search,
  MessageCircle,
  X,
  Send,
  Globe,
  Play,
  Pause,
  Settings,
  Zap,
  Layout,
  BarChart3,
  Layers,
  Mic,
  MicOff,
  Keyboard,
  Workflow
} from 'lucide-react';
import axios from 'axios';
import './App.css';

// Import advanced components
import AdvancedWorkspaceLayout from './components/AdvancedWorkspaceLayout';
import VisualWorkflowBuilder from './components/WorkflowBuilder/VisualWorkflowBuilder';
import Timeline from './components/Timeline/Timeline';
import DragDropLayer from './components/DragDrop/DragDropLayer';
import EnhancedWebView from './components/EnhancedWebView';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [currentUrl, setCurrentUrl] = useState('');
  const [urlInput, setUrlInput] = useState('');
  const [recentTabs, setRecentTabs] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [isAssistantOpen, setIsAssistantOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [pageTitle, setPageTitle] = useState('New Tab');
  const [isNavigating, setIsNavigating] = useState(false);
  const [activeAutomations, setActiveAutomations] = useState([]);
  const [automationSuggestions, setAutomationSuggestions] = useState([]);
  const [showAutomationPanel, setShowAutomationPanel] = useState(false);

  // Advanced features state
  const [isWorkflowBuilderOpen, setIsWorkflowBuilderOpen] = useState(false);
  const [isTimelineOpen, setIsTimelineOpen] = useState(false);
  const [isAdvancedWorkspace, setIsAdvancedWorkspace] = useState(false);
  const [voiceRecording, setVoiceRecording] = useState(false);
  const [keyboardShortcuts, setKeyboardShortcuts] = useState([]);
  const [performanceData, setPerformanceData] = useState({});
  const [workspaceLayout, setWorkspaceLayout] = useState('default');
  const [aiProviders, setAiProviders] = useState(['groq']);
  const [selectedAiProvider, setSelectedAiProvider] = useState('groq');

  // Initialize session and load advanced features
  useEffect(() => {
    setSessionId(Date.now().toString());
    loadRecentTabs();
    loadRecommendations();
    loadActiveAutomations();
    loadKeyboardShortcuts();
    loadPerformanceData();
    initializeVoiceCommands();
  }, []);

  // Advanced features loaders
  const loadKeyboardShortcuts = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/keyboard-shortcuts/available`);
      setKeyboardShortcuts(response.data.shortcuts || []);
    } catch (error) {
      console.error('Failed to load keyboard shortcuts:', error);
    }
  };

  const loadPerformanceData = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/enhanced/system/overview`);
      setPerformanceData(response.data || {});
    } catch (error) {
      console.error('Failed to load performance data:', error);
    }
  };

  const initializeVoiceCommands = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/voice-commands/available`);
      console.log('Voice commands initialized:', response.data);
    } catch (error) {
      console.error('Failed to initialize voice commands:', error);
    }
  };

  const loadRecentTabs = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/recent-tabs`);
      setRecentTabs(response.data.tabs || []);
    } catch (error) {
      console.error('Failed to load recent tabs:', error);
    }
  };

  const loadRecommendations = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/recommendations`);
      setRecommendations(response.data.recommendations || []);
    } catch (error) {
      console.error('Failed to load recommendations:', error);
    }
  };

  const loadActiveAutomations = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/active-automations`);
      setActiveAutomations(response.data.active_tasks || []);
    } catch (error) {
      console.error('Failed to load active automations:', error);
    }
  };

  const loadAutomationSuggestions = async (url) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/automation-suggestions?current_url=${encodeURIComponent(url)}`);
      setAutomationSuggestions(response.data.suggestions || []);
    } catch (error) {
      console.error('Failed to load automation suggestions:', error);
    }
  };

  const navigateToUrl = async (url) => {
    if (!url) return;
    
    // Add protocol if missing
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'https://' + url;
    }
    
    setIsNavigating(true);
    setCurrentUrl(url);
    setUrlInput(url);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/api/browse`, {
        url: url
      });
      
      if (response.data.success) {
        setPageTitle(response.data.page_data.title);
        await loadRecentTabs();
        await loadRecommendations();
        await loadAutomationSuggestions(url);
      }
    } catch (error) {
      console.error('Navigation error:', error);
      setPageTitle('Error loading page');
    } finally {
      setIsNavigating(false);
    }
  };

  const handleUrlSubmit = (e) => {
    e.preventDefault();
    navigateToUrl(urlInput);
  };

  const handleTabClick = (tab) => {
    navigateToUrl(tab.url);
  };

  const handleRecommendationClick = (recommendation) => {
    navigateToUrl(recommendation.url);
  };

  const sendMessage = async () => {
    if (!chatInput.trim() || isLoading) return;

    const userMessage = chatInput.trim();
    setChatInput('');
    
    // Add user message to chat
    const newUserMessage = {
      id: Date.now(),
      type: 'user',
      content: userMessage,
      timestamp: new Date()
    };
    
    setChatMessages(prev => [...prev, newUserMessage]);

    // **PHASE 1: AI-FIRST COMMAND PROCESSING** (Fellou.ai Style)
    const processedUICommand = processAICommand(userMessage);
    if (processedUICommand.handled) {
      // Add AI response for UI action
      const uiResponseMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: processedUICommand.response,
        timestamp: new Date(),
        message_type: 'ui_action'
      };
      setChatMessages(prev => [...prev, uiResponseMessage]);
      return; // Don't send to backend for simple UI commands
    }

    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/chat`, {
        message: userMessage,
        session_id: sessionId,
        current_url: currentUrl
      });

      const aiMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.data.response,
        timestamp: new Date(),
        automation_task_id: response.data.automation_task_id,
        message_type: response.data.message_type,
        automation_suggestions: response.data.automation_suggestions
      };

      setChatMessages(prev => [...prev, aiMessage]);
      
      // Update active automations if a task was created
      if (response.data.automation_task_id) {
        await loadActiveAutomations();
      }
      
      // Update automation suggestions if provided
      if (response.data.automation_suggestions) {
        setAutomationSuggestions(response.data.automation_suggestions);
      }

    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // **PHASE 1: AI-FIRST COMMAND PROCESSOR** (Like Fellou.ai)
  const processAICommand = (message) => {
    const lowerMessage = message.toLowerCase();
    
    // Workflow Builder triggers
    if (lowerMessage.includes('workflow') || lowerMessage.includes('automation') || 
        lowerMessage.includes('create task') || lowerMessage.includes('build workflow')) {
      setIsWorkflowBuilderOpen(true);
      return {
        handled: true,
        response: "🔧 **Workflow Builder Opened**\n\nI've opened the visual workflow builder for you. You can now create, edit, and manage automation workflows with a drag-and-drop interface."
      };
    }
    
    // Timeline triggers  
    if (lowerMessage.includes('history') || lowerMessage.includes('timeline') || 
        lowerMessage.includes('yesterday') || lowerMessage.includes('visited') || 
        lowerMessage.includes('recent') || lowerMessage.includes('past')) {
      setIsTimelineOpen(true);
      return {
        handled: true,
        response: "📚 **Timeline & History Opened**\n\nHere's your browsing timeline. You can view your activity history, revisit previous sessions, and restore past states."
      };
    }
    
    // Advanced Workspace triggers
    if (lowerMessage.includes('advanced mode') || lowerMessage.includes('workspace') || 
        lowerMessage.includes('layout') || lowerMessage.includes('panels')) {
      setIsAdvancedWorkspace(true);
      return {
        handled: true,
        response: "🚀 **Advanced Workspace Activated**\n\nSwitched to advanced workspace layout with enhanced panels, multi-view capabilities, and professional productivity features."
      };
    }
    
    // Simple mode triggers
    if (lowerMessage.includes('simple mode') || lowerMessage.includes('basic') || 
        lowerMessage.includes('minimal') || lowerMessage.includes('clean')) {
      setIsAdvancedWorkspace(false);
      return {
        handled: true,
        response: "✨ **Simple Mode Activated**\n\nSwitched to clean, minimal interface for focused browsing. Less clutter, more clarity."
      };
    }
    
    // Close panels
    if (lowerMessage.includes('close') && (lowerMessage.includes('panel') || 
        lowerMessage.includes('workflow') || lowerMessage.includes('timeline'))) {
      setIsWorkflowBuilderOpen(false);
      setIsTimelineOpen(false);
      return {
        handled: true,
        response: "✅ **Panels Closed**\n\nAll additional panels have been closed. Back to focused browsing mode."
      };
    }
    
    // Voice command activation
    if (lowerMessage.includes('voice') || lowerMessage.includes('listen') || 
        lowerMessage.includes('speak')) {
      handleVoiceCommand();
      return {
        handled: true,
        response: "🎤 **Voice Command Activated**\n\nI'm now listening for your voice commands. Speak naturally and I'll help you navigate!"
      };
    }
    
    return { handled: false };
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Smart action handler for drag & drop
  const handleSmartAction = async ({ action, item, dropZone }) => {
    try {
      switch (action) {
        case 'summarize':
          const summaryResponse = await axios.post(`${API_BASE_URL}/api/summarize`, {
            url: item.url || currentUrl,
            length: 'medium'
          });
          
          const summaryMessage = {
            id: Date.now(),
            type: 'assistant',
            content: `📄 **Page Summary:**\n\n${summaryResponse.data.summary}`,
            timestamp: new Date()
          };
          setChatMessages(prev => [...prev, summaryMessage]);
          if (!isAssistantOpen) setIsAssistantOpen(true);
          break;
          
        case 'browse':
          if (item.url || item.content) {
            navigateToUrl(item.url || item.content);
          }
          break;
          
        case 'chat':
          const chatContent = item.content || item.title || 'Analyze this item';
          setChatInput(`Tell me about: ${chatContent}`);
          if (!isAssistantOpen) setIsAssistantOpen(true);
          break;
          
        case 'create_workflow':
          setIsWorkflowBuilderOpen(true);
          break;
          
        default:
          console.log('Smart action executed:', { action, item, dropZone });
      }
    } catch (error) {
      console.error('Smart action failed:', error);
    }
  };

  const executeAutomation = async (taskId) => {
    try {
      await axios.post(`${API_BASE_URL}/api/execute-automation/${taskId}`);
      
      // Add status message to chat
      const statusMessage = {
        id: Date.now(),
        type: 'assistant',
        content: '✅ Automation started! I\'ll work in the background and update you on progress.',
        timestamp: new Date(),
        message_type: 'automation_status'
      };
      setChatMessages(prev => [...prev, statusMessage]);
      
      // Reload active automations
      await loadActiveAutomations();
      
      // Poll for updates
      pollAutomationStatus(taskId);
      
    } catch (error) {
      console.error('Failed to execute automation:', error);
    }
  };

  const pollAutomationStatus = (taskId) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/automation-status/${taskId}`);
        const status = response.data.task_status;
        
        if (status.status === 'completed' || status.status === 'failed' || status.status === 'cancelled') {
          clearInterval(pollInterval);
          
          // Add completion message to chat
          const completionMessage = {
            id: Date.now(),
            type: 'assistant',
            content: status.status === 'completed' 
              ? `✅ **Automation Completed!**\n\nTask: ${status.description}\nResult: Successfully completed ${status.current_step}/${status.total_steps} steps.`
              : `⚠️ **Automation ${status.status.charAt(0).toUpperCase() + status.status.slice(1)}**\n\nTask: ${status.description}\n${status.error_message || 'Task was cancelled.'}`,
            timestamp: new Date(),
            message_type: 'automation_status'
          };
          setChatMessages(prev => [...prev, completionMessage]);
          
          // Reload automations
          await loadActiveAutomations();
        }
      } catch (error) {
        console.error('Failed to poll automation status:', error);
        clearInterval(pollInterval);
      }
    }, 3000); // Poll every 3 seconds
  };

  const cancelAutomation = async (taskId) => {
    try {
      await axios.post(`${API_BASE_URL}/api/cancel-automation/${taskId}`);
      await loadActiveAutomations();
      
      // Add cancellation message to chat
      const cancelMessage = {
        id: Date.now(),
        type: 'assistant',
        content: '🛑 Automation cancelled successfully.',
        timestamp: new Date(),
        message_type: 'automation_status'
      };
      setChatMessages(prev => [...prev, cancelMessage]);
      
    } catch (error) {
      console.error('Failed to cancel automation:', error);
    }
  };

  const handleVoiceCommand = async () => {
    if (!voiceRecording) {
      // Start voice recording
      try {
        setVoiceRecording(true);
        
        if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
          const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
          const recognition = new SpeechRecognition();
          
          recognition.continuous = false;
          recognition.interimResults = false;
          recognition.lang = 'en-US';
          
          recognition.onresult = async (event) => {
            const voiceText = event.results[0][0].transcript;
            console.log('Voice command:', voiceText);
            
            try {
              const response = await axios.post(`${API_BASE_URL}/api/voice-command`, {
                voice_text: voiceText,
                user_session: sessionId,
                current_url: currentUrl
              });
              
              if (response.data.success) {
                const { action, url, query, message } = response.data;
                
                switch (action) {
                  case 'navigate':
                    if (url) navigateToUrl(url);
                    break;
                  case 'search':
                    if (query) navigateToUrl(`https://www.google.com/search?q=${encodeURIComponent(query)}`);
                    break;
                  case 'chat':
                    if (message) {
                      setChatInput(message);
                      if (!isAssistantOpen) setIsAssistantOpen(true);
                    }
                    break;
                  default:
                    console.log('Voice command processed:', response.data);
                }
              }
            } catch (error) {
              console.error('Voice command processing failed:', error);
            }
          };
          
          recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            setVoiceRecording(false);
          };
          
          recognition.onend = () => {
            setVoiceRecording(false);
          };
          
          recognition.start();
        } else {
          alert('Speech recognition not supported in this browser');
          setVoiceRecording(false);
        }
      } catch (error) {
        console.error('Voice command failed:', error);
        setVoiceRecording(false);
      }
    } else {
      // Stop voice recording
      setVoiceRecording(false);
    }
  };

  const executeKeyboardShortcut = async (shortcut) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/keyboard-shortcut`, {
        shortcut: shortcut,
        user_session: sessionId
      });
      
      if (response.data.success) {
        const { action } = response.data;
        
        switch (action) {
          case 'home':
            setCurrentUrl('');
            setUrlInput('');
            break;
          case 'refresh':
            if (currentUrl) navigateToUrl(currentUrl);
            break;
          case 'new_tab':
            setCurrentUrl('');
            setUrlInput('');
            break;
          case 'automation':
            setShowAutomationPanel(true);
            break;
          case 'voice':
            handleVoiceCommand();
            break;
          default:
            console.log('Shortcut executed:', response.data);
        }
      }
    } catch (error) {
      console.error('Keyboard shortcut failed:', error);
    }
  };

  // Enhanced keyboard shortcuts handling
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Global shortcuts
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 'l':
            e.preventDefault();
            document.querySelector('.url-bar')?.focus();
            break;
          case 'h':
            e.preventDefault();
            executeKeyboardShortcut('ctrl+h');
            break;
          case 'r':
            e.preventDefault();
            executeKeyboardShortcut('ctrl+r');
            break;
          case 't':
            e.preventDefault();
            executeKeyboardShortcut('ctrl+t');
            break;
          case '/':
            e.preventDefault();
            executeKeyboardShortcut('ctrl+/');
            break;
        }
        
        if (e.shiftKey) {
          switch (e.key) {
            case 'A':
              e.preventDefault();
              executeKeyboardShortcut('ctrl+shift+a');
              break;
            case 'V':
              e.preventDefault();
              executeKeyboardShortcut('ctrl+shift+v');
              break;
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentUrl, sessionId]);

  return (
    <DragDropLayer onSmartAction={handleSmartAction} isEnabled={true}>
      <div className="h-screen flex flex-col bg-gray-25">
        {/* Enhanced Browser Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
          <div className="flex items-center space-x-6">
            {/* Enhanced Navigation Controls */}
            <div className="flex items-center space-x-1">
              <button 
                className="nav-button"
                disabled={!currentUrl}
                onClick={() => window.history.back()}
                title="Go back"
              >
                <ArrowLeft size={18} />
              </button>
              <button 
                className="nav-button"
                disabled={!currentUrl}
                onClick={() => window.history.forward()}
                title="Go forward"
              >
                <ArrowRight size={18} />
              </button>
              <button 
                className="nav-button"
                disabled={!currentUrl || isNavigating}
                onClick={() => navigateToUrl(currentUrl)}
                title="Refresh page"
              >
                <RotateCcw size={18} />
              </button>
            </div>

            {/* Enhanced URL Bar */}
            <form onSubmit={handleUrlSubmit} className="url-bar-container">
              <div className="relative">
                <Globe size={18} className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="Search or enter URL"
                  className="url-bar"
                />
                {isNavigating && (
                  <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
                    <div className="loading-dots">
                      <div className="loading-dot"></div>
                      <div className="loading-dot"></div>
                      <div className="loading-dot"></div>
                    </div>
                  </div>
                )}
                {activeAutomations.length > 0 && !isNavigating && (
                  <div className="absolute right-4 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
                    <Zap size={16} className="text-blue-500 animate-pulse" />
                    <span className="text-xs text-blue-600 font-medium">{activeAutomations.length}</span>
                  </div>
                )}
              </div>
            </form>

            {/* AI-First Minimalist Controls - Fellou.ai Inspired */}
            <div className="flex items-center space-x-3">
              <button 
                onClick={handleVoiceCommand}
                className={`ai-control-btn ${voiceRecording ? 'bg-red-500 text-white' : 'bg-gray-100 hover:bg-gray-200'}`}
                title={voiceRecording ? "Listening..." : "Voice Command"}
              >
                {voiceRecording ? <MicOff size={20} /> : <Mic size={20} />}
                {voiceRecording && <span className="ml-2 text-sm font-medium">Listening...</span>}
              </button>
              <button
                onClick={() => setIsAssistantOpen(!isAssistantOpen)}
                className={`btn-primary-enhanced ${isAssistantOpen ? 'bg-primary-700' : ''}`}
                title="AI-Powered Assistant - Controls Everything"
              >
                <MessageCircle size={20} className="mr-3" />
                <span className="font-semibold">Aether Assistant</span>
                <div className="ml-2 w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              </button>
            </div>
          </div>
        </div>

        {/* Advanced Workspace or Traditional Layout */}
        {isAdvancedWorkspace ? (
          <AdvancedWorkspaceLayout
            currentUrl={currentUrl}
            isLoading={isNavigating}
            onLayoutChange={(layout) => setWorkspaceLayout(layout)}
            sidebarContent={<SidebarContent />}
            aiAssistantContent={<AIAssistantContent />}
            timelineContent={<TimelineContent />}
            performanceContent={<PerformanceContent />}
          >
            <BrowserContent />
          </AdvancedWorkspaceLayout>
        ) : (
          <TraditionalLayout />
        )}

        {/* Advanced Feature Modals */}
        <VisualWorkflowBuilder
          isVisible={isWorkflowBuilderOpen}
          onClose={() => setIsWorkflowBuilderOpen(false)}
        />

        <Timeline
          isVisible={isTimelineOpen}
          onClose={() => setIsTimelineOpen(false)}
          sessionId={sessionId}
        />

        {/* Enhanced Status Bar */}
        <div className="status-bar">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-6">
              <button className="flex items-center space-x-2 text-gray-600 hover:text-gray-800 transition-colors">
                <span>Tabs</span>
                <span className="text-xs">▼</span>
              </button>
              {currentUrl && (
                <div className="flex items-center space-x-2 text-gray-500">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Secure Connection</span>
                </div>
              )}
              <div className="flex items-center space-x-2 text-gray-500">
                <Keyboard size={12} />
                <span className="text-xs">Shortcuts: Ctrl+L, Ctrl+H, Ctrl+R</span>
              </div>
            </div>
            <div className="flex items-center space-x-6 text-gray-500">
              <span>© 2025 Aether Browser v3.0</span>
              <div className="flex items-center space-x-1">
                <div className="w-1 h-1 bg-primary-500 rounded-full"></div>
                <span className="text-xs">AI Provider: {selectedAiProvider.toUpperCase()}</span>
              </div>
              {activeAutomations.length > 0 && (
                <div className="flex items-center space-x-1">
                  <Zap size={12} className="text-blue-500" />
                  <span className="text-xs">{activeAutomations.length} task{activeAutomations.length > 1 ? 's' : ''} running</span>
                </div>
              )}
              {voiceRecording && (
                <div className="flex items-center space-x-1">
                  <Mic size={12} className="text-red-500 animate-pulse" />
                  <span className="text-xs">Listening...</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </DragDropLayer>
  );

  // Traditional Layout Component (existing layout)
  function TraditionalLayout() {
    return (
      <>
        {/* Main Content */}
        <div className="flex-1 flex">
          {/* Enhanced Browser Content */}
          <div className={`${isAssistantOpen ? 'flex-1' : 'w-full'} flex flex-col`}>
            <BrowserContent />
          </div>

          {/* Enhanced AI Assistant Sidebar */}
          {isAssistantOpen && (
            <div className="w-96 assistant-sidebar flex flex-col">
              <AIAssistantContent />
            </div>
          )}
        </div>
      </>
    );
  }

  // Browser Content Component
  function BrowserContent() {
    return (
      <>
        {currentUrl ? (
          <div className="flex-1 relative bg-white m-4 rounded-xl overflow-hidden shadow-md">
            {/* **PHASE 2: ENHANCED BROWSER ENGINE** */}
            <EnhancedWebView
              url={currentUrl}
              title={pageTitle}
              isLoading={isNavigating}
              onNavigate={(newUrl) => navigateToUrl(newUrl)}
              onTitleChange={(newTitle) => setPageTitle(newTitle)}
              onSecurityChange={(security) => console.log('Security status:', security)}
              onPerformanceUpdate={(metrics) => console.log('Performance:', metrics)}
              className="h-full browser-frame"
            />
          </div>
        ) : (
          <HomepageContent />
        )}
      </>
    );
  }

  // Homepage Content Component
  function HomepageContent() {
    return (
      <div className="welcome-container">
        <div className="text-center mb-16 animate-fade-in">
          <h1 className="welcome-title">AETHER</h1>
          <p className="welcome-subtitle">AI-Powered Browser Experience</p>
          <div className="flex items-center justify-center space-x-4 mt-6">
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <BarChart3 size={16} />
              <span>Advanced Workspace Available</span>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Workflow size={16} />
              <span>Visual Workflow Builder</span>
            </div>
          </div>
        </div>

        {/* Enhanced Recent Tabs */}
        <div className="w-full max-w-6xl mb-16">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-bold text-gray-900">Recent Tabs</h2>
            <button 
              onClick={() => setIsTimelineOpen(true)}
              className="btn-secondary text-sm flex items-center space-x-2"
            >
              <Layers size={16} />
              <span>View Timeline</span>
            </button>
          </div>
          <RecentTabsGrid />
        </div>

        {/* Enhanced Recommendations */}
        <div className="w-full max-w-6xl">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-bold text-gray-900">Recommendations</h2>
            <button 
              onClick={loadRecommendations}
              className="btn-secondary text-sm"
            >
              Refresh
            </button>
          </div>
          <RecommendationsGrid />
        </div>
      </div>
    );
  }

  // Recent Tabs Grid Component
  function RecentTabsGrid() {
    return (
      <div className="tabs-grid">
        {recentTabs.length > 0 ? (
          recentTabs.map((tab, index) => (
            <div
              key={tab.id || index}
              onClick={() => handleTabClick(tab)}
              className="tab-card card-interactive group"
            >
              <div className="flex items-start space-x-3 h-full">
                <div className="w-10 h-10 bg-primary-50 rounded-lg flex items-center justify-center group-hover:bg-primary-100 transition-colors">
                  <Globe size={20} className="text-primary-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-900 truncate text-sm mb-2">
                    {tab.title || `Recent ${index + 1}`}
                  </h3>
                  <p className="text-xs text-gray-500 truncate">{tab.url}</p>
                </div>
              </div>
            </div>
          ))
        ) : (
          <>
            {['Recent 1', 'Recent 2', 'Pages', 'Apps'].map((title, index) => (
              <div key={index} className="tab-card card-interactive group">
                <div className="flex items-start space-x-3 h-full">
                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center group-hover:bg-gray-200 transition-colors">
                    <Globe size={20} className="text-gray-400" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 text-sm">{title}</h3>
                    <p className="text-xs text-gray-500 mt-1">No recent activity</p>
                  </div>
                </div>
              </div>
            ))}
          </>
        )}
      </div>
    );
  }

  // Recommendations Grid Component
  function RecommendationsGrid() {
    return (
      <div className="recommendations-grid">
        {recommendations.length > 0 ? (
          recommendations.map((rec, index) => (
            <div
              key={rec.id || index}
              onClick={() => handleRecommendationClick(rec)}
              className="recommendation-card card-interactive group"
            >
              <div className="flex items-start space-x-4">
                <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-purple-600 rounded-xl flex items-center justify-center flex-shrink-0">
                  <Globe size={24} className="text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-900 mb-2 group-hover:text-primary-700 transition-colors">
                    {rec.title}
                  </h3>
                  <p className="text-gray-600 text-sm leading-relaxed">{rec.description}</p>
                  <div className="mt-3 flex items-center text-xs text-gray-400">
                    <span>AI Recommended</span>
                    <div className="w-1 h-1 bg-gray-300 rounded-full mx-2"></div>
                    <span>Trending</span>
                  </div>
                </div>
              </div>
            </div>
          ))
        ) : (
          <>
            {[
              {
                title: "Discover AI Tools",
                description: "Explore the latest AI-powered tools and services to enhance your productivity and creativity.",
                icon: "🤖"
              },
              {
                title: "Tech News & Updates",
                description: "Stay informed with the latest technology trends, product launches, and industry insights.",
                icon: "📰"
              },
              {
                title: "Learning Resources",
                description: "Find educational content, tutorials, and courses to expand your knowledge and skills.",
                icon: "📚"
              }
            ].map((item, index) => (
              <div key={index} className="recommendation-card card-interactive group">
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-gray-100 to-gray-200 rounded-xl flex items-center justify-center flex-shrink-0 text-xl">
                    {item.icon}
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 mb-2 group-hover:text-primary-700 transition-colors">
                      {item.title}
                    </h3>
                    <p className="text-gray-600 text-sm leading-relaxed">{item.description}</p>
                    <div className="mt-3 flex items-center text-xs text-gray-400">
                      <span>Curated Content</span>
                      <div className="w-1 h-1 bg-gray-300 rounded-full mx-2"></div>
                      <span>Popular</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </>
        )}
      </div>
    );
  }

  // AI Assistant Content Component  
  function AIAssistantContent() {
    return (
      <>
        {/* Enhanced Assistant Header */}
        <div className="assistant-header flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-purple-600 rounded-lg flex items-center justify-center">
              <MessageCircle size={16} className="text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">Aether Assistant</h3>
              <p className="text-xs text-gray-500">AI-powered browsing companion</p>
            </div>
          </div>
          <button
            onClick={() => setIsAssistantOpen(false)}
            className="nav-button"
            title="Close assistant"
          >
            <X size={18} />
          </button>
        </div>

        {/* Enhanced Chat Messages */}
        <div className="assistant-messages">
          {chatMessages.length === 0 && (
            <div className="text-center py-12 animate-fade-in">
              <div className="w-16 h-16 bg-gradient-to-br from-primary-100 to-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <MessageCircle size={32} className="text-primary-600" />
              </div>
              <h4 className="text-lg font-semibold text-gray-900 mb-2">Hello! How can I help you?</h4>
              <p className="text-sm text-gray-500 max-w-xs mx-auto leading-relaxed">
                Ask me anything about the web, get help with browsing, or just have a conversation.
              </p>
            </div>
          )}
          
          {chatMessages.map((message) => (
            <div
              key={message.id}
              className={`chat-message ${message.type}`}
            >
              <div className={`message-bubble ${message.type}`}>
                <div className="leading-relaxed whitespace-pre-line">{message.content}</div>
                
                {/* Automation action buttons */}
                {message.message_type === 'automation_offer' && message.automation_task_id && (
                  <div className="flex items-center space-x-2 mt-3">
                    <button
                      onClick={() => executeAutomation(message.automation_task_id)}
                      className="flex items-center space-x-1 px-3 py-1 bg-blue-500 text-white text-xs rounded-lg hover:bg-blue-600 transition-colors"
                    >
                      <Play size={12} />
                      <span>Start</span>
                    </button>
                    <button
                      onClick={() => setShowAutomationPanel(true)}
                      className="flex items-center space-x-1 px-3 py-1 bg-gray-500 text-white text-xs rounded-lg hover:bg-gray-600 transition-colors"
                    >
                      <Settings size={12} />
                      <span>Customize</span>
                    </button>
                    <button
                      onClick={() => cancelAutomation(message.automation_task_id)}
                      className="flex items-center space-x-1 px-3 py-1 bg-red-500 text-white text-xs rounded-lg hover:bg-red-600 transition-colors"
                    >
                      <X size={12} />
                      <span>Cancel</span>
                    </button>
                  </div>
                )}
                
                {/* Automation suggestions */}
                {message.automation_suggestions && message.automation_suggestions.length > 0 && (
                  <div className="mt-3 p-2 bg-blue-50 rounded-lg">
                    <div className="text-xs font-medium text-blue-800 mb-2">💡 Quick Actions:</div>
                    {message.automation_suggestions.slice(0, 2).map((suggestion, index) => (
                      <button
                        key={index}
                        onClick={() => setChatInput(suggestion.command)}
                        className="block w-full text-left text-xs p-2 hover:bg-blue-100 rounded transition-colors mb-1 last:mb-0"
                      >
                        <span className="font-medium text-blue-700">{suggestion.title}</span>
                        <span className="text-blue-600 ml-1">({suggestion.estimated_time})</span>
                      </button>
                    ))}
                  </div>
                )}
                
                <div className="text-xs opacity-60 mt-2">
                  {new Date(message.timestamp).toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  })}
                </div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="chat-message assistant">
              <div className="message-bubble assistant">
                <div className="flex items-center space-x-2">
                  <div className="loading-dots">
                    <div className="loading-dot"></div>
                    <div className="loading-dot"></div>
                    <div className="loading-dot"></div>
                  </div>
                  <span className="text-sm text-gray-600">Thinking...</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Enhanced Chat Input */}
        <div className="assistant-input-container">
          <div className="flex items-end space-x-3">
            <div className="flex-1">
              <textarea
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                rows={1}
                className="input-primary resize-none min-h-[44px] max-h-[120px] text-sm"
                style={{
                  height: 'auto',
                  minHeight: '44px',
                  maxHeight: '120px'
                }}
              />
            </div>
            <button
              onClick={sendMessage}
              disabled={!chatInput.trim() || isLoading}
              className="btn-primary p-3 flex-shrink-0"
              title="Send message"
            >
              <Send size={16} />
            </button>
          </div>
          
          {currentUrl && (
            <div className="flex items-center space-x-2 mt-3 px-3 py-2 bg-primary-50 rounded-lg">
              <Globe size={14} className="text-primary-600" />
              <span className="text-xs text-primary-700 font-medium truncate">
                Analyzing: {pageTitle || currentUrl}
              </span>
            </div>
          )}
        </div>
      </>
    );
  }

  // Sidebar Content Component
  function SidebarContent() {
    return (
      <div className="p-4 space-y-4">
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">Navigation</h3>
          <div className="space-y-1">
            <button 
              onClick={() => setCurrentUrl('')}
              className="block w-full text-left px-3 py-2 text-sm rounded hover:bg-gray-100"
            >
              🏠 Home
            </button>
            <button 
              onClick={() => setIsTimelineOpen(true)}
              className="block w-full text-left px-3 py-2 text-sm rounded hover:bg-gray-100"
            >
              📋 History & Timeline
            </button>
            <button 
              onClick={() => setIsWorkflowBuilderOpen(true)}
              className="block w-full text-left px-3 py-2 text-sm rounded hover:bg-gray-100"
            >
              ⚡ Workflow Builder
            </button>
          </div>
        </div>
        
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">Quick Actions</h3>
          <div className="space-y-1">
            <button 
              onClick={loadRecommendations}
              className="block w-full text-left px-3 py-2 text-sm rounded hover:bg-gray-100"
            >
              🔄 Refresh Recommendations  
            </button>
            <button 
              onClick={loadActiveAutomations}
              className="block w-full text-left px-3 py-2 text-sm rounded hover:bg-gray-100"
            >
              🤖 Active Automations ({activeAutomations.length})
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Timeline Content Component
  function TimelineContent() {
    return (
      <div className="p-4">
        <p className="text-gray-600 text-sm">
          Timeline content will appear here when the Timeline component is integrated.
        </p>
      </div>
    );
  }

  // Performance Content Component  
  function PerformanceContent() {
    return (
      <div className="p-4 space-y-4">
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">System Status</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span>Status:</span>
              <span className="text-green-600 font-medium">
                {performanceData.status || 'Operational'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>AI Provider:</span>
              <span className="font-medium">{selectedAiProvider.toUpperCase()}</span>
            </div>
            <div className="flex justify-between">
              <span>Active Tasks:</span>
              <span className="font-medium">{activeAutomations.length}</span>
            </div>
          </div>
        </div>
        
        {performanceData.stats && (
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Statistics</h3>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span>Recent Tabs:</span>
                <span>{performanceData.stats.recent_tabs || 0}</span>
              </div>
              <div className="flex justify-between">
                <span>Chat Sessions:</span>
                <span>{performanceData.stats.chat_sessions || 0}</span>
              </div>
              <div className="flex justify-between">
                <span>Workflows:</span>
                <span>{performanceData.stats.workflows || 0}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

}

export default App;