import React, { useState, useEffect, useCallback } from 'react';
import { Bot, Zap, Menu, Eye, EyeOff } from 'lucide-react';
import FellouCommandInterface from './FellouCommandInterface';

const SimplifiedInterface = ({ 
  onCommand, 
  currentUrl, 
  sessionId,
  aiLoading = false,
  nativeAPI = null
}) => {
  const [interfaceMode, setInterfaceMode] = useState('fellou'); // 'fellou' or 'traditional'
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [proactiveSuggestions, setProactiveSuggestions] = useState([]);
  const [behavioralInsights, setBehavioralInsights] = useState(null);
  const [aiActive, setAiActive] = useState(false);

  // Load interface preferences
  useEffect(() => {
    const savedMode = localStorage.getItem('aether-interface-mode') || 'fellou';
    setInterfaceMode(savedMode);
  }, []);

  // Enhanced command processor with native API integration
  const processEnhancedCommand = useCallback(async (commandData) => {
    setAiActive(true);
    
    try {
      // Use native API if available (desktop app)
      if (nativeAPI?.hasNativeChromium() && nativeAPI.processCommand) {
        const result = await nativeAPI.processCommand(commandData.command);
        
        if (result.success) {
          // Update proactive suggestions based on native response
          if (result.suggestions) {
            setProactiveSuggestions(result.suggestions);
          }
          
          // Handle native browser actions
          if (result.action === 'navigate') {
            await nativeAPI.navigateTo(result.url);
          }
        }
      }
      
      // Fallback to regular backend processing
      await onCommand(commandData);
      
      // Simulate behavioral learning insights
      updateBehavioralInsights(commandData);
      
    } catch (error) {
      console.error('Enhanced command processing error:', error);
    } finally {
      setAiActive(false);
    }
  }, [onCommand, nativeAPI]);

  // Behavioral learning system
  const updateBehavioralInsights = (commandData) => {
    const command = commandData.command.toLowerCase();
    
    // Pattern detection
    if (command.includes('extract') || command.includes('data')) {
      setBehavioralInsights({
        pattern: 'Data Extraction Workflow',
        confidence: 85,
        suggestion: 'You frequently extract data. Consider creating an automation template.'
      });
    } else if (command.includes('navigate') || command.includes('search')) {
      setBehavioralInsights({
        pattern: 'Research & Navigation',
        confidence: 92,
        suggestion: 'Your browsing suggests research tasks. I can help streamline this.'
      });
    } else if (command.includes('monitor') || command.includes('track')) {
      setBehavioralInsights({
        pattern: 'Content Monitoring',
        confidence: 78,
        suggestion: 'Setting up automated monitoring might save you time.'
      });
    }
    
    // Clear insights after 5 seconds
    setTimeout(() => setBehavioralInsights(null), 5000);
  };

  // Proactive AI suggestions based on context
  useEffect(() => {
    if (currentUrl) {
      generateProactiveSuggestions(currentUrl);
    }
  }, [currentUrl]);

  const generateProactiveSuggestions = (url) => {
    const domain = new URL(url).hostname.toLowerCase();
    
    let suggestions = [];
    
    if (domain.includes('linkedin')) {
      suggestions = [
        "Extract all professional contacts from this page",
        "Monitor this profile for job updates",
        "Create outreach automation for similar profiles"
      ];
    } else if (domain.includes('github')) {
      suggestions = [
        "Track this repository for new releases",
        "Extract contributor information",
        "Monitor issues and pull requests"
      ];
    } else if (domain.includes('amazon') || domain.includes('shop')) {
      suggestions = [
        "Monitor this product for price changes",
        "Extract product reviews and ratings",
        "Set up automated purchase when price drops"
      ];
    } else {
      suggestions = [
        "Extract key information from this page",
        "Monitor this page for content changes",
        "Find similar websites or competitors"
      ];
    }
    
    setProactiveSuggestions(suggestions);
  };

  // Toggle between Fellou-style and traditional interface
  const toggleInterfaceMode = () => {
    const newMode = interfaceMode === 'fellou' ? 'traditional' : 'fellou';
    setInterfaceMode(newMode);
    localStorage.setItem('aether-interface-mode', newMode);
  };

  if (interfaceMode === 'fellou') {
    return (
      <div className="simplified-interface fellou-mode">
        {/* Minimal Header - Only Essential Controls */}
        <div className="minimal-header">
          <div className="aether-brand">
            <Zap className="w-6 h-6 text-purple-400" />
            <span className="brand-text">AETHER</span>
            {nativeAPI?.hasNativeChromium() && (
              <span className="native-badge">Native</span>
            )}
          </div>
          
          {/* Minimal Controls - Only 2 buttons like Fellou.ai */}
          <div className="minimal-controls">
            <button
              className={`control-btn ai-btn ${aiActive ? 'active' : ''}`}
              title="AI Assistant"
            >
              <Bot className="w-5 h-5" />
            </button>
            
            <button
              className="control-btn menu-btn"
              onClick={() => setShowAdvanced(!showAdvanced)}
              title="Toggle Advanced View"
            >
              {showAdvanced ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Advanced Controls (Hidden by default) */}
        {showAdvanced && (
          <div className="advanced-controls">
            <button
              onClick={toggleInterfaceMode}
              className="interface-toggle"
              title="Switch to Traditional Interface"
            >
              <Menu className="w-4 h-4" />
              <span>Traditional Mode</span>
            </button>
            
            {nativeAPI?.hasNativeChromium() && (
              <div className="native-features">
                <button
                  onClick={() => nativeAPI.openDevTools()}
                  className="native-btn"
                  title="Open Chrome DevTools"
                >
                  DevTools
                </button>
                
                <button
                  onClick={() => nativeAPI.getExtensions()}
                  className="native-btn"
                  title="Manage Extensions"
                >
                  Extensions
                </button>
              </div>
            )}
          </div>
        )}

        {/* Fellou-style Command Interface */}
        <FellouCommandInterface
          onCommand={processEnhancedCommand}
          currentUrl={currentUrl}
          sessionId={sessionId}
          aiLoading={aiLoading || aiActive}
          proactiveSuggestions={proactiveSuggestions}
          behavioralInsights={behavioralInsights}
        />

        <style jsx>{`
          .simplified-interface {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 999;
            background: rgba(10, 10, 15, 0.95);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(147, 51, 234, 0.1);
          }

          .fellou-mode .minimal-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 20px;
            height: 60px;
          }

          .aether-brand {
            display: flex;
            align-items: center;
            gap: 8px;
          }

          .brand-text {
            font-size: 18px;
            font-weight: 700;
            background: linear-gradient(135deg, #9333ea, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
          }

          .native-badge {
            font-size: 10px;
            font-weight: 600;
            padding: 2px 6px;
            background: rgba(34, 197, 94, 0.2);
            color: #22c55e;
            border-radius: 4px;
            text-transform: uppercase;
          }

          .minimal-controls {
            display: flex;
            align-items: center;
            gap: 12px;
          }

          .control-btn {
            padding: 8px;
            border-radius: 12px;
            border: none;
            background: rgba(147, 51, 234, 0.1);
            color: rgba(255, 255, 255, 0.8);
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
          }

          .control-btn:hover {
            background: rgba(147, 51, 234, 0.2);
            color: white;
            transform: scale(1.05);
          }

          .control-btn.active {
            background: rgba(147, 51, 234, 0.3);
            color: white;
          }

          .advanced-controls {
            padding: 12px 20px;
            border-top: 1px solid rgba(147, 51, 234, 0.1);
            display: flex;
            align-items: center;
            gap: 12px;
            animation: slideDown 0.3s ease-out;
          }

          .interface-toggle {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 8px;
            border: 1px solid rgba(147, 51, 234, 0.2);
            background: rgba(147, 51, 234, 0.05);
            color: rgba(255, 255, 255, 0.7);
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 14px;
          }

          .interface-toggle:hover {
            background: rgba(147, 51, 234, 0.1);
            color: white;
          }

          .native-features {
            display: flex;
            gap: 8px;
          }

          .native-btn {
            padding: 6px 10px;
            border-radius: 6px;
            border: 1px solid rgba(34, 197, 94, 0.2);
            background: rgba(34, 197, 94, 0.05);
            color: #22c55e;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 12px;
            font-weight: 500;
          }

          .native-btn:hover {
            background: rgba(34, 197, 94, 0.1);
          }

          @keyframes slideDown {
            from {
              opacity: 0;
              transform: translateY(-10px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }

          /* Mobile responsiveness */
          @media (max-width: 768px) {
            .minimal-header {
              padding: 10px 16px;
              height: 56px;
            }

            .brand-text {
              font-size: 16px;
            }

            .minimal-controls {
              gap: 8px;
            }

            .advanced-controls {
              padding: 10px 16px;
              flex-wrap: wrap;
              gap: 8px;
            }

            .native-features {
              gap: 6px;
            }
          }
        `}</style>
      </div>
    );
  }

  // Traditional interface fallback
  return (
    <div className="simplified-interface traditional-mode">
      <div className="traditional-header">
        <button onClick={toggleInterfaceMode} className="mode-toggle">
          Switch to Fellou Mode
        </button>
      </div>
    </div>
  );
};

export default SimplifiedInterface;