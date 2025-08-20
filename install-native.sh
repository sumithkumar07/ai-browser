#!/bin/bash

# AETHER Native Chromium Browser Installation Script

echo "🚀 Installing AETHER Native Chromium Browser..."

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed."
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version)
echo "✅ Node.js found: $NODE_VERSION"

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed."
    exit 1
fi

echo "✅ npm found: $(npm --version)"

# Install yarn if not available
if ! command -v yarn &> /dev/null; then
    echo "📦 Installing Yarn..."
    npm install -g yarn
fi

echo "✅ Yarn found: $(yarn --version)"

# Check Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python is not installed."
    echo "Please install Python from https://python.org/"
    exit 1
fi

PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "✅ Python found: $($PYTHON_CMD --version)"

# Install main application dependencies
echo "📦 Installing main application dependencies..."
yarn install

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd backend
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt 2>/dev/null || pip install -r requirements.txt
else
    echo "⚠️  No requirements.txt found in backend"
fi
cd ..

# Build frontend for production
echo "🏗️  Building frontend for production..."
cd frontend
npm run build
cd ..

# Create desktop shortcuts (Linux/macOS)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🖥️  Creating Linux desktop entry..."
    mkdir -p ~/.local/share/applications
    
    cat > ~/.local/share/applications/aether-browser.desktop << EOF
[Desktop Entry]
Name=AETHER Browser
Comment=AI-First Browser with Native Chromium
Exec=$(pwd)/start-native.sh
Icon=$(pwd)/assets/icon.png
Type=Application
Categories=Network;WebBrowser;
StartupNotify=true
MimeType=text/html;text/xml;application/xhtml+xml;
EOF

    chmod +x ~/.local/share/applications/aether-browser.desktop
    echo "✅ Desktop entry created"
    
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 macOS detected - use 'yarn electron:dist' to create .dmg"
fi

# Set executable permissions
chmod +x start-native.sh
chmod +x electron-main.js

echo ""
echo "🎉 AETHER Native Chromium Browser installation completed!"
echo ""
echo "📋 Next steps:"
echo "  1. Run './start-native.sh' to start the native browser"
echo "  2. Or run 'yarn electron:start' for development mode"
echo "  3. Or run 'yarn electron:dist' to build distribution packages"
echo ""
echo "🔥 Features available:"
echo "  ✅ Native Chromium engine (no iframe limitations)"
echo "  ✅ Cross-origin resource access"
echo "  ✅ Browser extension support"
echo "  ✅ Native DevTools access"
echo "  ✅ Hardware acceleration"
echo "  ✅ File system access"
echo "  ✅ System notifications"
echo "  ✅ Fellou.ai-style AI interface"
echo ""
echo "Happy browsing with AETHER! 🚀"