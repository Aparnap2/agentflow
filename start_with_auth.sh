#!/bin/bash

echo "🚀 Starting AgentFlow with Authentication"

# Set demo mode environment variable
export DEMO_MODE=true
export PORT=8000

# Start backend in background
echo "Starting backend server..."
cd backend
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Start frontend
echo "Starting frontend..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo "✅ AgentFlow started!"
echo "📱 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Demo credentials:"
echo "Email: demo@agentflow.ai"
echo "Password: demo123"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait