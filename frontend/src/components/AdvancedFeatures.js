import { useState, useEffect, useCallback } from 'react';

// Advanced Features Component to utilize all backend capabilities
const AdvancedFeatures = ({ backendUrl, currentUrl, onNavigate }) => {
  const [searchSuggestions, setSearchSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [workflowBuilder, setWorkflowBuilder] = useState({ visible: false, workflows: [] });
  const [systemStatus, setSystemStatus] = useState(null);
  const [voiceListening, setVoiceListening] = useState(false);
  const [availableShortcuts, setAvailableShortcuts] = useState([]);
  
  // Fetch smart search suggestions
  const getSearchSuggestions = async (query) => {
    if (!query || query.length < 2) {
      setSearchSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    try {
      const response = await fetch(`${backendUrl}/api/search-suggestions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      
      if (response.ok) {
        const result = await response.json();
        setSearchSuggestions(result.suggestions || []);
        setShowSuggestions(true);
      }
    } catch (error) {
      console.error('Search suggestions error:', error);
    }
  };

  // Get page summary
  const getPageSummary = async (url, length = 'medium') => {
    if (!url) return;
    
    setSummaryLoading(true);
    try {
      const response = await fetch(`${backendUrl}/api/summarize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, length })
      });
      
      if (response.ok) {
        const result = await response.json();
        setSummary(result);
      }
    } catch (error) {
      console.error('Summarization error:', error);
    } finally {
      setSummaryLoading(false);
    }
  };

  // Create workflow
  const createWorkflow = async (workflowData) => {
    try {
      const response = await fetch(`${backendUrl}/api/create-workflow`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(workflowData)
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('Workflow created:', result);
        return result;
      }
    } catch (error) {
      console.error('Workflow creation error:', error);
    }
  };

  // Get system status with useCallback
  const getSystemStatus = useCallback(async () => {
    try {
      const response = await fetch(`${backendUrl}/api/enhanced/system/overview`);
      if (response.ok) {
        const result = await response.json();
        setSystemStatus(result);
      }
    } catch (error) {
      console.error('System status error:', error);
    }
  }, [backendUrl]);

  // Voice command processing
  const processVoiceCommand = async (command) => {
    try {
      const response = await fetch(`${backendUrl}/api/voice-command`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command })
      });
      
      if (response.ok) {
        const result = await response.json();
        
        // Process voice command result
        if (result.action === 'navigate' && result.url) {
          onNavigate(result.url);
        } else if (result.action === 'search' && result.query) {
          onNavigate(`https://www.google.com/search?q=${encodeURIComponent(result.query)}`);
        }
        
        return result;
      }
    } catch (error) {
      console.error('Voice command error:', error);
    }
  };

  // Get available keyboard shortcuts
  useEffect(() => {
    const fetchShortcuts = async () => {
      try {
        const response = await fetch(`${backendUrl}/api/voice-commands/available`);
        if (response.ok) {
          const result = await response.json();
          setAvailableShortcuts(result.commands || []);
        }
      } catch (error) {
        console.error('Shortcuts fetch error:', error);
      }
    };
    
    fetchShortcuts();
    getSystemStatus();
  }, [backendUrl, getSystemStatus]);

  return {
    // Search suggestions
    searchSuggestions,
    showSuggestions,
    getSearchSuggestions,
    setShowSuggestions,
    
    // Page summarization
    summary,
    summaryLoading,
    getPageSummary,
    
    // Workflows
    workflowBuilder,
    setWorkflowBuilder,
    createWorkflow,
    
    // System status
    systemStatus,
    getSystemStatus,
    
    // Voice commands
    voiceListening,
    setVoiceListening,
    processVoiceCommand,
    availableShortcuts
  };
};

export default AdvancedFeatures;