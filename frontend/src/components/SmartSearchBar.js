import React, { useState, useEffect, useRef } from 'react';

const SmartSearchBar = ({ 
  urlInput, 
  setUrlInput, 
  onNavigate, 
  searchSuggestions, 
  showSuggestions, 
  onGetSuggestions, 
  setShowSuggestions 
}) => {
  const [focused, setFocused] = useState(false);
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);

  // Handle input change with debounced suggestions
  const handleInputChange = (e) => {
    const value = e.target.value;
    setUrlInput(value);
    
    // Debounce search suggestions
    setTimeout(() => {
      if (value === urlInput) {
        onGetSuggestions(value);
      }
    }, 300);
  };

  // Handle suggestion selection
  const selectSuggestion = (suggestion) => {
    setUrlInput(suggestion);
    setShowSuggestions(false);
    onNavigate(suggestion);
  };

  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      setShowSuggestions(false);
      inputRef.current?.blur();
    } else if (e.key === 'ArrowDown' && showSuggestions && searchSuggestions.length > 0) {
      e.preventDefault();
      // Focus first suggestion
      const firstSuggestion = suggestionsRef.current?.firstChild;
      firstSuggestion?.focus();
    }
  };

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (inputRef.current && !inputRef.current.contains(event.target) &&
          suggestionsRef.current && !suggestionsRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [setShowSuggestions]);

  return (
    <div className="smart-search-container">
      <input
        ref={inputRef}
        type="text"
        className={`url-input ${focused ? 'focused' : ''}`}
        value={urlInput}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onKeyPress={(e) => e.key === 'Enter' && onNavigate(urlInput)}
        onFocus={() => {
          setFocused(true);
          if (urlInput.length >= 2) {
            onGetSuggestions(urlInput);
          }
        }}
        onBlur={() => setFocused(false)}
        placeholder="Search or type a URL"
        autoComplete="off"
      />
      
      {showSuggestions && searchSuggestions.length > 0 && (
        <div ref={suggestionsRef} className="search-suggestions-dropdown">
          {searchSuggestions.map((suggestion, index) => (
            <div
              key={index}
              className="search-suggestion-item"
              onClick={() => selectSuggestion(suggestion)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') selectSuggestion(suggestion);
                else if (e.key === 'ArrowDown') e.currentTarget.nextSibling?.focus();
                else if (e.key === 'ArrowUp') e.currentTarget.previousSibling?.focus();
              }}
              tabIndex={0}
            >
              <span className="suggestion-icon">🔍</span>
              <span className="suggestion-text">{suggestion}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SmartSearchBar;