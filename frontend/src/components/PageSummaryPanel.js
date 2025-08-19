import React, { useState } from 'react';

const PageSummaryPanel = ({ 
  currentUrl, 
  summary, 
  summaryLoading, 
  onGetSummary, 
  visible, 
  onClose 
}) => {
  const [selectedLength, setSelectedLength] = useState('medium');

  const handleSummarize = () => {
    if (currentUrl) {
      onGetSummary(currentUrl, selectedLength);
    }
  };

  if (!visible) return null;

  return (
    <div className="summary-panel-overlay">
      <div className="summary-panel">
        <div className="summary-header">
          <div className="summary-title">
            <span className="summary-icon">📄</span>
            <span>Page Summary</span>
          </div>
          <button className="summary-close" onClick={onClose}>×</button>
        </div>

        <div className="summary-content">
          {!currentUrl ? (
            <div className="summary-placeholder">
              <div className="placeholder-icon">🌐</div>
              <p>Navigate to a webpage to generate a summary</p>
            </div>
          ) : (
            <>
              <div className="summary-controls">
                <div className="length-selector">
                  <label>Summary Length:</label>
                  <select 
                    value={selectedLength} 
                    onChange={(e) => setSelectedLength(e.target.value)}
                    className="length-select"
                  >
                    <option value="short">Short</option>
                    <option value="medium">Medium</option>
                    <option value="long">Detailed</option>
                  </select>
                </div>
                <button 
                  className="summarize-btn"
                  onClick={handleSummarize}
                  disabled={summaryLoading}
                >
                  {summaryLoading ? (
                    <>
                      <span className="loading-spinner">⟳</span>
                      Summarizing...
                    </>
                  ) : (
                    <>
                      <span>✨</span>
                      Summarize Page
                    </>
                  )}
                </button>
              </div>

              {summary && (
                <div className="summary-result">
                  <div className="summary-meta">
                    <h3 className="summary-page-title">{summary.title}</h3>
                    <div className="summary-stats">
                      <span className="word-count">{summary.word_count} words</span>
                      <span className="summary-length">{summary.length} summary</span>
                    </div>
                  </div>
                  
                  <div className="summary-text">
                    {summary.summary}
                  </div>

                  <div className="summary-actions">
                    <button className="action-btn secondary">
                      <span>📋</span>
                      Copy Summary
                    </button>
                    <button className="action-btn secondary">
                      <span>💾</span>
                      Save Summary
                    </button>
                    <button className="action-btn primary">
                      <span>🔄</span>
                      Regenerate
                    </button>
                  </div>
                </div>
              )}

              {summaryLoading && (
                <div className="summary-loading">
                  <div className="loading-animation">
                    <div className="loading-dots">
                      <span></span><span></span><span></span>
                    </div>
                  </div>
                  <p>Analyzing webpage content and generating summary...</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default PageSummaryPanel;