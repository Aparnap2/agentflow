#!/bin/bash

echo "🧠 Setting up AgentFlow - Virtual AI Office Platform"

# Create environment file
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please update .env with your API keys before running the application"
fi

# Setup backend
echo "🐍 Setting up Python backend..."
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Setup frontend
echo "⚛️  Setting up React frontend..."
cd frontend
npm install
cd ..

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d

echo "✅ Setup complete!"
echo ""
echo "🚀 To start the application:"
echo "   Backend: cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo "   Frontend: cd frontend && npm run dev"
echo ""
echo "🌐 Access the application at: http://localhost:5173"
echo "📊 Neo4j Browser: http://localhost:7474"
echo "🔍 Qdrant Dashboard: http://localhost:6333/dashboard"