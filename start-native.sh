#!/bin/bash

# AETHER Native Chromium Browser Startup Script

echo "🚀 Starting AETHER Native Chromium Browser..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm/yarn is installed
if ! command -v yarn &> /dev/null; then
    echo "❌ Yarn is not installed. Please install Yarn first."
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    yarn install
fi

# Start backend server in background
echo "🔧 Starting FastAPI backend server..."
cd backend
python server.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 3

# Start frontend development server in background
echo "⚛️ Starting React frontend..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo "⏳ Waiting for frontend to initialize..."
sleep 5

# Start Electron desktop application
echo "🔥 Starting AETHER Native Chromium Engine..."
yarn electron:start

# Cleanup function
cleanup() {
    echo "🛑 Shutting down AETHER..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Trap cleanup on script termination
trap cleanup SIGINT SIGTERM

# Wait for Electron to exit
wait