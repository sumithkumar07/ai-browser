import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import './components/EnhancedApp.css';

// Detect if running in native Electron environment
const isNativeAether = window.isNativeAether || false;

// Choose the appropriate app version
const AppComponent = isNativeAether ? EnhancedAetherApp : App;

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <AppComponent />
  </React.StrictMode>
);

console.log(`AETHER Browser initialized - ${isNativeAether ? 'Native Chromium' : 'Web'} version`);