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
  Globe
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

  // Initialize session
  useEffect(() => {
    setSessionId(Date.now().toString());
    loadRecentTabs();
    loadRecommendations();
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
        {/* Browser Content */}
        <div className={`${isAssistantOpen ? 'flex-1' : 'w-full'} flex flex-col`}>
          {currentUrl ? (
            <div className="flex-1 relative">
              {isNavigating && (
                <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
                  <div className="text-gray-600">Loading page...</div>
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
            /* Homepage */
            <div className="flex-1 flex flex-col items-center justify-center p-8">
              <div className="text-center mb-12">
                <h1 className="text-6xl font-bold text-gray-900 mb-4">AETHER</h1>
                <p className="text-xl text-gray-600">AI-Powered Browser Experience</p>
              </div>

              {/* Recent Tabs */}
              <div className="w-full max-w-4xl mb-8">
                <h2 className="text-2xl font-semibold text-gray-900 mb-6">Recent Tabs</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {recentTabs.length > 0 ? (
                    recentTabs.map((tab, index) => (
                      <div
                        key={tab.id || index}
                        onClick={() => handleTabClick(tab)}
                        className="bg-white rounded-lg p-4 border border-gray-200 hover:border-primary-500 hover:shadow-md transition-all cursor-pointer"
                      >
                        <h3 className="font-medium text-gray-900 truncate">{tab.title || `Recent ${index + 1}`}</h3>
                        <p className="text-sm text-gray-500 truncate mt-1">{tab.url}</p>
                      </div>
                    ))
                  ) : (
                    <>
                      <div className="bg-white rounded-lg p-4 border border-gray-200 hover:border-primary-500 transition-colors cursor-pointer">
                        <h3 className="font-medium text-gray-900">Recent 1</h3>
                      </div>
                      <div className="bg-white rounded-lg p-4 border border-gray-200 hover:border-primary-500 transition-colors cursor-pointer">
                        <h3 className="font-medium text-gray-900">Recent 2</h3>
                      </div>
                      <div className="bg-white rounded-lg p-4 border border-gray-200 hover:border-primary-500 transition-colors cursor-pointer">
                        <h3 className="font-medium text-gray-900">Pages</h3>
                      </div>
                      <div className="bg-white rounded-lg p-4 border border-gray-200 hover:border-primary-500 transition-colors cursor-pointer">
                        <h3 className="font-medium text-gray-900">Apps</h3>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Recommendations */}
              <div className="w-full max-w-4xl">
                <h2 className="text-2xl font-semibold text-gray-900 mb-6">Recommendations</h2>
                <div className="space-y-4">
                  {recommendations.length > 0 ? (
                    recommendations.map((rec, index) => (
                      <div
                        key={rec.id || index}
                        onClick={() => handleRecommendationClick(rec)}
                        className="bg-white rounded-lg p-6 border border-gray-200 hover:border-primary-500 hover:shadow-md transition-all cursor-pointer"
                      >
                        <h3 className="font-medium text-gray-900 mb-2">{rec.title}</h3>
                        <p className="text-gray-600">{rec.description}</p>
                      </div>
                    ))
                  ) : (
                    <>
                      <div className="bg-white rounded-lg p-6 border border-gray-200 hover:border-primary-500 transition-colors cursor-pointer">
                        <h3 className="font-medium text-gray-900 mb-2">Recommendation 1</h3>
                        <p className="text-gray-600">Discover new content based on your interests</p>
                      </div>
                      <div className="bg-white rounded-lg p-6 border border-gray-200 hover:border-primary-500 transition-colors cursor-pointer">
                        <h3 className="font-medium text-gray-900 mb-2">Recommendation 2</h3>
                        <p className="text-gray-600">Explore trending topics and discussions</p>
                      </div>
                      <div className="bg-white rounded-lg p-6 border border-gray-200 hover:border-primary-500 transition-colors cursor-pointer">
                        <h3 className="font-medium text-gray-900 mb-2">Recommendation 3</h3>
                        <p className="text-gray-600">Find resources to enhance your productivity</p>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* AI Assistant Sidebar */}
        {isAssistantOpen && (
          <div className="w-96 bg-white border-l border-gray-200 flex flex-col">
            {/* Assistant Header */}
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Aether Assistant</h3>
              <button
                onClick={() => setIsAssistantOpen(false)}
                className="p-1 rounded-lg hover:bg-gray-100"
              >
                <X size={20} className="text-gray-500" />
              </button>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {chatMessages.length === 0 && (
                <div className="text-center text-gray-500 mt-8">
                  <MessageCircle size={48} className="mx-auto mb-4 text-gray-300" />
                  <p className="text-lg font-medium">Hello! How can I help you?</p>
                  <p className="text-sm mt-2">Ask me anything or get help with browsing</p>
                </div>
              )}
              
              {chatMessages.map((message) => (
                <div
                  key={message.id}
                  className={`chat-message ${
                    message.type === 'user' ? 'text-right' : 'text-left'
                  }`}
                >
                  <div
                    className={`inline-block max-w-[80%] p-3 rounded-lg ${
                      message.type === 'user'
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <p className="text-sm leading-relaxed">{message.content}</p>
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="text-left">
                  <div className="inline-block bg-gray-100 text-gray-900 p-3 rounded-lg">
                    <p className="text-sm loading-dots">Thinking...</p>
                  </div>
                </div>
              )}
            </div>

            {/* Chat Input */}
            <div className="p-4 border-t border-gray-200">
              <div className="flex items-end space-x-2">
                <div className="flex-1">
                  <textarea
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Type a message..."
                    rows={1}
                    className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    style={{ minHeight: '44px', maxHeight: '120px' }}
                  />
                </div>
                <button
                  onClick={sendMessage}
                  disabled={!chatInput.trim() || isLoading}
                  className="p-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Send size={18} />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Status Bar */}
      <div className="bg-white border-t border-gray-200 px-4 py-2">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div className="flex items-center space-x-4">
            <span>Tabs ▼</span>
          </div>
          <div className="flex items-center space-x-4">
            <span>© Aether</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;