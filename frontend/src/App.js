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
  Zap
} from 'lucide-react';
import axios from 'axios';
import './App.css';

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

  // Initialize session
  useEffect(() => {
    setSessionId(Date.now().toString());
    loadRecentTabs();
    loadRecommendations();
    loadActiveAutomations();
  }, []);

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
        timestamp: new Date()
      };

      setChatMessages(prev => [...prev, aiMessage]);
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

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
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
            </div>
          </form>

          {/* Enhanced Right Controls */}
          <div className="flex items-center space-x-1">
            <button className="nav-button" title="Menu">
              <Menu size={18} />
            </button>
            <button className="nav-button" title="Bookmarks">
              <Star size={18} />
            </button>
            <button className="nav-button" title="Search">
              <Search size={18} />
            </button>
            <button
              onClick={() => setIsAssistantOpen(!isAssistantOpen)}
              className={`btn-primary ml-3 ${isAssistantOpen ? 'bg-primary-700' : ''}`}
              title="Toggle AI Assistant"
            >
              <MessageCircle size={18} className="mr-2" />
              Aether Assistant
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Enhanced Browser Content */}
        <div className={`${isAssistantOpen ? 'flex-1' : 'w-full'} flex flex-col`}>
          {currentUrl ? (
            <div className="flex-1 relative bg-white m-4 rounded-xl overflow-hidden shadow-md">
              {isNavigating && (
                <div className="absolute inset-0 bg-white bg-opacity-90 flex items-center justify-center z-10 backdrop-blur-sm">
                  <div className="text-center">
                    <div className="loading-dots mb-3">
                      <div className="loading-dot"></div>
                      <div className="loading-dot"></div>
                      <div className="loading-dot"></div>
                    </div>
                    <p className="text-gray-600 font-medium">Loading page...</p>
                  </div>
                </div>
              )}
              <iframe
                src={currentUrl}
                className="browser-frame"
                title={pageTitle}
                sandbox="allow-same-origin allow-scripts allow-forms allow-navigation"
              />
            </div>
          ) : (
            /* Enhanced Homepage */
            <div className="welcome-container">
              <div className="text-center mb-16 animate-fade-in">
                <h1 className="welcome-title">AETHER</h1>
                <p className="welcome-subtitle">AI-Powered Browser Experience</p>
              </div>

              {/* Enhanced Recent Tabs */}
              <div className="w-full max-w-6xl mb-16">
                <div className="flex items-center justify-between mb-8">
                  <h2 className="text-2xl font-bold text-gray-900">Recent Tabs</h2>
                  <button className="btn-secondary text-sm">
                    View All
                  </button>
                </div>
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
              </div>

              {/* Enhanced Recommendations */}
              <div className="w-full max-w-6xl">
                <div className="flex items-center justify-between mb-8">
                  <h2 className="text-2xl font-bold text-gray-900">Recommendations</h2>
                  <button className="btn-secondary text-sm">
                    Refresh
                  </button>
                </div>
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
              </div>
            </div>
          )}
        </div>

        {/* Enhanced AI Assistant Sidebar */}
        {isAssistantOpen && (
          <div className="w-96 assistant-sidebar flex flex-col">
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
                    <p className="leading-relaxed">{message.content}</p>
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
          </div>
        )}
      </div>

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
          </div>
          <div className="flex items-center space-x-6 text-gray-500">
            <span>© 2025 Aether Browser</span>
            <div className="flex items-center space-x-1">
              <div className="w-1 h-1 bg-primary-500 rounded-full"></div>
              <span className="text-xs">Powered by AI</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;