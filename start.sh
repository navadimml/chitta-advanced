#!/bin/bash
#
# Start Chitta Full Stack (Frontend + Backend)
#
# This script starts both the FastAPI backend and React frontend
# in separate terminal processes.
#

set -e

echo "🚀 Starting Chitta Full Stack..."
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ] || [ ! -d "backend" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check backend .env
if [ ! -f "backend/.env" ]; then
    echo "⚠️  backend/.env not found"
    echo "   Creating from backend/.env.example..."
    cp backend/.env.example backend/.env
    echo "   ✅ Created backend/.env"
    echo "   📝 Please edit backend/.env and add your GEMINI_API_KEY"
    echo ""
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
    echo ""
fi

# Check if backend venv exists
if [ ! -d "backend/venv" ]; then
    echo "📦 Creating backend virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
    echo ""
fi

echo "="*70
echo "🎬 Starting Services"
echo "="*70
echo ""

# Start backend in background
echo "1️⃣  Starting Backend (FastAPI)..."
echo "   URL: http://localhost:8000"
echo "   API: http://localhost:8000/api"
echo ""

cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

echo "   ✅ Backend started (PID: $BACKEND_PID)"
echo "   📝 Logs: backend.log"
echo ""

# Wait for backend to start
echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "   ✅ Backend is ready!"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "   ❌ Backend failed to start"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
done
echo ""

# Start frontend
echo "2️⃣  Starting Frontend (React + Vite)..."
echo "   URL: http://localhost:3000"
echo ""

npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!

echo "   ✅ Frontend started (PID: $FRONTEND_PID)"
echo "   📝 Logs: frontend.log"
echo ""

echo "="*70
echo "✅ Chitta is Running!"
echo "="*70
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Backend logs:  tail -f backend.log"
echo "Frontend logs: tail -f frontend.log"
echo ""
echo "To stop:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo "  Or just Ctrl+C and run: pkill -f uvicorn; pkill -f vite"
echo ""
echo "🎉 Open http://localhost:3000 in your browser!"
echo ""

# Keep script running and show logs
echo "Press Ctrl+C to stop all services..."
echo ""
tail -f backend.log frontend.log
