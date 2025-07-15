#!/bin/bash

echo "🚀 Starting AgentFlow system..."

# Check for required environment variables
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create one from .env.example"
    exit 1
fi

# Check for required Python packages
echo "🔍 Checking dependencies..."
python -c "import redis.asyncio" 2>/dev/null || { echo "⚠️ Redis package not found. Installing..."; pip install redis[asyncio]; }
python -c "import qdrant_client" 2>/dev/null || { echo "⚠️ Qdrant client not found. Installing..."; pip install qdrant-client; }
python -c "import neo4j" 2>/dev/null || { echo "⚠️ Neo4j package not found. Installing..."; pip install neo4j; }
python -c "import langgraph" 2>/dev/null || { echo "⚠️ LangGraph package not found. Installing..."; pip install langgraph; }

# Start the backend
echo "🔄 Starting backend server..."
cd backend
uvicorn main:app --reload &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Start the frontend
echo "🔄 Starting frontend server..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Function to handle shutdown
function cleanup {
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit 0
}

# Register the cleanup function for SIGINT
trap cleanup SIGINT

echo "✅ AgentFlow is running!"
echo "📊 Backend: http://localhost:8000"
echo "🖥️ Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop all servers"

# Wait for user to press Ctrl+C
wait