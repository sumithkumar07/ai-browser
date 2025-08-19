import React, { useState, useEffect } from 'react';

const VoiceCommandPanel = ({ 
  visible, 
  onClose, 
  voiceListening, 
  setVoiceListening, 
  onProcessVoiceCommand, 
  availableShortcuts 
}) => {
  const [recognition, setRecognition] = useState(null);
  const [transcript, setTranscript] = useState('');
  const [confidence, setConfidence] = useState(0);

  // Initialize speech recognition
  useEffect(() => {
    if (typeof window !== 'undefined' && 'webkitSpeechRecognition' in window) {
      const speechRecognition = new window.webkitSpeechRecognition();
      speechRecognition.continuous = false;
      speechRecognition.interimResults = true;
      speechRecognition.lang = 'en-US';

      speechRecognition.onstart = () => {
        setVoiceListening(true);
        setTranscript('Listening...');
      };

      speechRecognition.onresult = (event) => {
        const result = event.results[event.results.length - 1];
        setTranscript(result[0].transcript);
        setConfidence(result[0].confidence);

        if (result.isFinal) {
          onProcessVoiceCommand(result[0].transcript);
          setTimeout(() => {
            setVoiceListening(false);
            setTranscript('');
          }, 1000);
        }
      };

      speechRecognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setVoiceListening(false);
        setTranscript(`Error: ${event.error}`);
      };

      speechRecognition.onend = () => {
        setVoiceListening(false);
      };

      setRecognition(speechRecognition);
    }
  }, [setVoiceListening, onProcessVoiceCommand]);

  const startListening = () => {
    if (recognition) {
      recognition.start();
    }
  };

  const stopListening = () => {
    if (recognition) {
      recognition.stop();
    }
    setVoiceListening(false);
  };

  if (!visible) return null;

  return (
    <div className="voice-panel-overlay">
      <div className="voice-panel">
        <div className="voice-header">
          <div className="voice-title">
            <span className="voice-icon">🎤</span>
            <span>Voice Commands</span>
          </div>
          <button className="voice-close" onClick={onClose}>×</button>
        </div>

        <div className="voice-content">
          <div className="voice-control-section">
            <div className="voice-status">
              <div className={`voice-indicator ${voiceListening ? 'active' : ''}`}>
                <div className="pulse-ring"></div>
                <div className="pulse-ring"></div>
                <div className="pulse-ring"></div>
                <div className="microphone-icon">🎤</div>
              </div>
              
              <div className="voice-feedback">
                {voiceListening ? (
                  <>
                    <h3>Listening...</h3>
                    <p className="transcript">{transcript}</p>
                    {confidence > 0 && (
                      <div className="confidence-meter">
                        Confidence: {Math.round(confidence * 100)}%
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    <h3>Ready to Listen</h3>
                    <p>Click the microphone to start voice commands</p>
                  </>
                )}
              </div>
            </div>

            <div className="voice-controls">
              {!voiceListening ? (
                <button className="voice-btn start" onClick={startListening}>
                  <span>🎤</span>
                  Start Listening
                </button>
              ) : (
                <button className="voice-btn stop" onClick={stopListening}>
                  <span>⏹️</span>
                  Stop Listening
                </button>
              )}
            </div>
          </div>

          <div className="available-commands">
            <h4>Available Commands</h4>
            <div className="commands-list">
              {availableShortcuts.map((shortcut, index) => (
                <div key={index} className="command-item">
                  <div className="command-text">"{shortcut.command}"</div>
                  <div className="command-description">{shortcut.description}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="voice-examples">
            <h4>Example Commands</h4>
            <div className="examples-grid">
              <div className="example-item">
                <strong>"Navigate to google.com"</strong>
                <span>Opens Google</span>
              </div>
              <div className="example-item">
                <strong>"Search for AI tools"</strong>
                <span>Searches the web</span>
              </div>
              <div className="example-item">
                <strong>"Summarize page"</strong>
                <span>Summarizes current page</span>
              </div>
              <div className="example-item">
                <strong>"Chat about this page"</strong>
                <span>Opens AI chat</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceCommandPanel;