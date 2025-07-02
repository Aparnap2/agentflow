#!/bin/bash

# 🚀 AgentFlow Startup Script
# Comprehensive startup for the AgentFlow AI platform

echo "🚀 Starting AgentFlow - AI Virtual Office Platform"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "prd.md" ]; then
    print_error "Please run this script from the agentflow root directory"
    exit 1
fi

print_info "Checking system requirements..."

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_status "Python found: $PYTHON_VERSION"
else
    print_error "Python 3 is required but not installed"
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_status "Node.js found: $NODE_VERSION"
else
    print_error "Node.js is required but not installed"
    exit 1
fi

# Check pnpm
if command -v pnpm &> /dev/null; then
    PNPM_VERSION=$(pnpm --version)
    print_status "pnpm found: v$PNPM_VERSION"
else
    print_warning "pnpm not found, installing..."
    npm install -g pnpm
fi

# Check environment file
if [ ! -f ".env" ]; then
    print_warning "No .env file found, copying from .env.example"
    cp .env.example .env
    print_info "Please edit .env file with your API keys before continuing"
    read -p "Press Enter after configuring .env file..."
fi

print_info "Starting backend services..."

# Start backend
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_info "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
print_info "Installing Python dependencies..."
pip install -r requirements.txt

# Start backend server in background
print_status "Starting FastAPI backend server..."
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Test backend health
if curl -s http://localhost:8000/api/health > /dev/null; then
    print_status "Backend server is running on http://localhost:8000"
else
    print_error "Backend server failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend
cd ../frontend

print_info "Installing frontend dependencies..."
pnpm install

print_status "Starting React frontend server..."
pnpm dev &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 3

print_status "Frontend server is starting on http://localhost:5173"

echo ""
echo "🎉 AgentFlow is now running!"
echo "================================"
echo ""
echo "📊 Enhanced UI:       http://localhost:5173"
echo "🔧 Backend API:        http://localhost:8000"
echo "📚 API Documentation:  http://localhost:8000/docs"
echo ""
echo "🧠 Meet Your AI Team:"
echo "   • Alex Chen (Cofounder)   - Vision & Strategy"
echo "   • Sarah Kim (Manager)     - Project Management"
echo "   • Jordan Martinez (Product) - Product Development"
echo "   • David Park (Finance)    - Financial Analysis"
echo "   • Emma Rodriguez (Marketing) - Marketing Strategy"
echo "   • Michael Thompson (Legal) - Legal Compliance"
echo "   • Lisa Wang (Sales)       - Sales Strategy"
echo "   • Ryan Foster (Operations) - Operations Planning"
echo ""
echo "💡 Enhanced Experience:"
echo "   1. Open http://localhost:5173 in your browser"
echo "   2. Meet your AI team with personality profiles"
echo "   3. Chat with Alex Chen (Cofounder) about your startup idea"
echo "   4. Watch your AI team collaborate in real-time!"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    print_info "Shutting down AgentFlow services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    print_status "All services stopped. Goodbye!"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Keep script running
while true; do
    sleep 1
done