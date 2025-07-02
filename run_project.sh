#!/bin/bash

# Script to run the project

echo "🚀 Starting AgentFlow..."

# Start backend in background
echo "Starting backend server..."
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Start frontend
echo "Starting frontend server..."
cd frontend
npm run dev

# Kill backend when frontend is stopped
kill $BACKEND_PID