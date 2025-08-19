import React, { useState, useEffect } from 'react';
import './OnboardingTour.css';

const OnboardingTour = ({ onComplete, isVisible }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);

  const tourSteps = [
    {
      target: '.aether-logo',
      title: 'Welcome to AETHER! ⚡',
      content: 'Your AI-first browser that transforms how you interact with the web. Let me show you around!',
      position: 'bottom'
    },
    {
      target: '.address-bar',
      title: 'Smart Address Bar 🔍',
      content: 'Type URLs or search queries. I provide intelligent suggestions and auto-complete. Press Ctrl+L to focus anytime!',
      position: 'bottom'
    },
    {
      target: '.ai-toggle',
      title: 'AI Assistant 🤖',
      content: 'Your intelligent companion! Click here or press Ctrl+Shift+A to open. I can summarize pages, create workflows, and much more.',
      position: 'left'
    },
    {
      target: '.voice-btn',
      title: 'Voice Commands 🎤',
      content: 'Speak to your browser! Press Ctrl+Shift+P or click to use voice commands for hands-free browsing.',
      position: 'left'
    },
    {
      target: '.suggestions-grid',
      title: 'Quick Access 🚀',
      content: 'Instant access to your favorite sites. These smart cards learn from your behavior and suggest relevant content.',
      position: 'top'
    },
    {
      target: '.actions-grid',
      title: 'AI-Powered Features ✨',
      content: 'One-click access to powerful AI features. Summarize pages, get system status, create workflows, and more!',
      position: 'top'
    },
    {
      target: '.browser-app',
      title: 'You\'re All Set! 🎉',
      content: 'Enjoy browsing with AI superpowers! Remember: this browser learns from you and gets smarter over time.',
      position: 'center'
    }
  ];

  const currentStepData = tourSteps[currentStep];

  useEffect(() => {
    if (!isVisible) return;

    // Scroll target into view
    const targetElement = document.querySelector(currentStepData.target);
    if (targetElement && currentStepData.target !== '.browser-app') {
      targetElement.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'center',
        inline: 'center'
      });
      
      // Add highlight class
      targetElement.classList.add('tour-highlight');
      
      return () => {
        targetElement.classList.remove('tour-highlight');
      };
    }
  }, [currentStep, currentStepData.target, isVisible]);

  const nextStep = () => {
    if (currentStep < tourSteps.length - 1) {
      setIsAnimating(true);
      setTimeout(() => {
        setCurrentStep(currentStep + 1);
        setIsAnimating(false);
      }, 200);
    } else {
      completeTour();
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setIsAnimating(true);
      setTimeout(() => {
        setCurrentStep(currentStep - 1);
        setIsAnimating(false);
      }, 200);
    }
  };

  const skipTour = () => {
    completeTour();
  };

  const completeTour = () => {
    // Store completion in localStorage
    localStorage.setItem('aether_tour_completed', 'true');
    localStorage.setItem('aether_tour_completed_date', new Date().toISOString());
    onComplete();
  };

  const getTooltipPosition = () => {
    const target = document.querySelector(currentStepData.target);
    if (!target) return { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' };

    const rect = target.getBoundingClientRect();
    const tooltipWidth = 320;
    const tooltipHeight = 200;
    let style = {};

    switch (currentStepData.position) {
      case 'bottom':
        style = {
          top: rect.bottom + 20,
          left: Math.max(10, Math.min(window.innerWidth - tooltipWidth - 10, rect.left + rect.width / 2 - tooltipWidth / 2)),
          transform: 'none'
        };
        break;
      case 'top':
        style = {
          top: rect.top - tooltipHeight - 20,
          left: Math.max(10, Math.min(window.innerWidth - tooltipWidth - 10, rect.left + rect.width / 2 - tooltipWidth / 2)),
          transform: 'none'
        };
        break;
      case 'left':
        style = {
          top: Math.max(10, rect.top + rect.height / 2 - tooltipHeight / 2),
          left: rect.left - tooltipWidth - 20,
          transform: 'none'
        };
        break;
      case 'right':
        style = {
          top: Math.max(10, rect.top + rect.height / 2 - tooltipHeight / 2),
          left: rect.right + 20,
          transform: 'none'
        };
        break;
      case 'center':
      default:
        style = {
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)'
        };
        break;
    }

    return style;
  };

  if (!isVisible) return null;

  return (
    <>
      {/* Overlay */}
      <div className="tour-overlay" onClick={skipTour} />
      
      {/* Tooltip */}
      <div 
        className={`tour-tooltip ${isAnimating ? 'animating' : ''}`}
        style={getTooltipPosition()}
      >
        {/* Progress indicator */}
        <div className="tour-progress">
          <div className="tour-progress-bar">
            <div 
              className="tour-progress-fill"
              style={{ width: `${((currentStep + 1) / tourSteps.length) * 100}%` }}
            />
          </div>
          <span className="tour-progress-text">
            {currentStep + 1} of {tourSteps.length}
          </span>
        </div>

        {/* Content */}
        <div className="tour-content">
          <h3 className="tour-title">{currentStepData.title}</h3>
          <p className="tour-description">{currentStepData.content}</p>
        </div>

        {/* Actions */}
        <div className="tour-actions">
          <button 
            className="tour-btn tour-btn-secondary"
            onClick={skipTour}
          >
            Skip Tour
          </button>
          
          <div className="tour-navigation">
            {currentStep > 0 && (
              <button 
                className="tour-btn tour-btn-outline"
                onClick={prevStep}
              >
                Previous
              </button>
            )}
            
            <button 
              className="tour-btn tour-btn-primary"
              onClick={nextStep}
            >
              {currentStep === tourSteps.length - 1 ? 'Get Started!' : 'Next'}
            </button>
          </div>
        </div>

        {/* Arrow pointer */}
        {currentStepData.position !== 'center' && (
          <div className={`tour-arrow tour-arrow-${currentStepData.position}`} />
        )}
      </div>

      {/* Keyboard shortcuts hint */}
      {currentStep === 0 && (
        <div className="tour-shortcuts-hint">
          <p>💡 <strong>Pro tip:</strong> Use Esc to close, Arrow keys to navigate</p>
        </div>
      )}
    </>
  );
};

// Hook to check if tour should be shown
export const useOnboardingTour = () => {
  const [shouldShowTour, setShouldShowTour] = useState(false);

  useEffect(() => {
    const tourCompleted = localStorage.getItem('aether_tour_completed');
    const isFirstVisit = !tourCompleted;
    
    // Show tour for first-time users or if user manually triggered it
    setShouldShowTour(isFirstVisit);
  }, []);

  const showTour = () => setShouldShowTour(true);
  const hideTour = () => setShouldShowTour(false);

  return {
    shouldShowTour,
    showTour,
    hideTour
  };
};

export default OnboardingTour;