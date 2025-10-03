#!/bin/bash

# QuitTxt Protocol Test - Startup Script
# This script starts both the API server and Streamlit app

echo "🚭 Starting QuitTxt Protocol Testing System..."
echo ""

# Check if protocol document exists
if [ ! -f "protocol_document.txt" ]; then
    echo "❌ Error: protocol_document.txt not found"
    echo "Please ensure the protocol document has been extracted"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "Please ensure .env file exists with GOOGLE_API_KEY"
    exit 1
fi

echo "✅ Protocol document found"
echo "✅ Environment configuration found"
echo ""

# Kill any existing processes on these ports
echo "🧹 Cleaning up any existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:8501 | xargs kill -9 2>/dev/null
sleep 2

echo ""
echo "📡 Starting FastAPI server on http://localhost:8000..."
python api_server.py &
API_PID=$!
echo "   API Server PID: $API_PID"

# Wait for API to be ready
echo "⏳ Waiting for API to be ready..."
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API server is ready!"
        break
    fi
    sleep 1
    if [ $i -eq 10 ]; then
        echo "❌ API server failed to start"
        kill $API_PID 2>/dev/null
        exit 1
    fi
done

echo ""
echo "🎨 Starting Streamlit app on http://localhost:8501..."
streamlit run streamlit_app.py &
STREAMLIT_PID=$!
echo "   Streamlit PID: $STREAMLIT_PID"

echo ""
echo "✅ Both servers started successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 Streamlit UI:  http://localhost:8501"
echo "🔌 API Server:    http://localhost:8000"
echo "📚 API Docs:      http://localhost:8000/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for Ctrl+C
trap 'echo ""; echo "🛑 Stopping servers..."; kill $API_PID $STREAMLIT_PID 2>/dev/null; echo "✅ Servers stopped"; exit 0' INT

# Keep script running
wait
