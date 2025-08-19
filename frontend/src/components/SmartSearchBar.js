import React, { useState, useRef, useEffect } from 'react';

const SmartSearchBar = ({ 
  urlInput, 
  setUrlInput, 
  onNavigate, 
  searchSuggestions, 
  showSuggestions, 
  onGetSuggestions, 
  setShowSuggestions 
}) => {
  const [isTyping, setIsTyping] = useState(false);
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);

  // Handle input changes with smart suggestions
  const handleInputChange = (e) => {
    const value = e.target.value;
    setUrlInput(value);
    setIsTyping(true);
    
    // Show suggestions for text input
    if (value.length > 2 && !value.startsWith('http')) {
      onGetSuggestions(value);
    } else {
      setShowSuggestions(false);
    }
    
    // Clear typing indicator after delay
    setTimeout(() => setIsTyping(false), 500);
  };

  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      onNavigate(urlInput);
      setShowSuggestions(false);
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
      inputRef.current?.blur();
    } else if (e.key === 'Tab') {
      // Accessibility: Tab to suggestions
      if (showSuggestions && searchSuggestions.length > 0) {
        e.preventDefault();
        suggestionsRef.current?.focus();
      }
    }
  };

  // Handle clicks outside to close suggestions
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!event.target.closest('.smart-search-container')) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [setShowSuggestions]);

  // Auto-focus on Ctrl+L
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey && e.key === 'l') {
        e.preventDefault();
        inputRef.current?.focus();
        inputRef.current?.select();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleSuggestionClick = (suggestion) => {
    setUrlInput(suggestion);
    onNavigate(suggestion);
    setShowSuggestions(false);
  };

  return (
    <div className="smart-search-container">
      <input
        ref={inputRef}
        type="text"
        className={`url-input ${isTyping ? 'typing' : ''}`}
        value={urlInput}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onFocus={() => {
          if (urlInput.length > 2 && !urlInput.startsWith('http')) {
            onGetSuggestions(urlInput);
          }
        }}
        placeholder="Search or enter URL... (Ctrl+L to focus)"
        spellCheck={false}
        autoComplete="off"
        aria-label="Search or enter URL"
        aria-expanded={showSuggestions}
        aria-haspopup="listbox"
        role="combobox"
      />

      {/* Smart Suggestions Dropdown */}
      {showSuggestions && searchSuggestions.length > 0 && (
        <div 
          className="search-suggestions"
          role="listbox"
          aria-label="Search suggestions"
          ref={suggestionsRef}
          tabIndex={-1}
        >
          {searchSuggestions.map((suggestion, index) => (
            <div
              key={index}
              className="suggestion-item"
              onClick={() => handleSuggestionClick(suggestion)}
              role="option"
              aria-selected={false}
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleSuggestionClick(suggestion);
                }
              }}
            >
              <div className="suggestion-icon">
                🔍
              </div>
              <div className="suggestion-text">
                {suggestion}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SmartSearchBar;