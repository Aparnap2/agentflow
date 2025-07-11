#!/bin/bash

echo "🚀 Setting up Enhanced AgentFlow..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
    
    print_success "Python dependencies installed"
    cd ..
}

# Install Node.js dependencies
install_node_deps() {
    print_status "Installing Node.js dependencies..."
    cd frontend
    
    # Check if pnpm is available, otherwise use npm
    if command -v pnpm >/dev/null 2>&1; then
        print_status "Using pnpm..."
        pnpm install
    else
        print_status "Using npm..."
        npm install
    fi
    
    print_success "Node.js dependencies installed"
    cd ..
}

# Start Docker services
start_docker_services() {
    print_status "Starting Docker services (Redis, Neo4j, Qdrant)..."
    docker-compose up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check if Redis is ready
    if docker exec agentflow-redis redis-cli ping >/dev/null 2>&1; then
        print_success "Redis is ready"
    else
        print_warning "Redis might not be ready yet"
    fi
    
    # Check if Neo4j is ready
    if docker exec agentflow-neo4j cypher-shell -u neo4j -p agentflow123 "RETURN 1" >/dev/null 2>&1; then
        print_success "Neo4j is ready"
    else
        print_warning "Neo4j might not be ready yet"
    fi
    
    print_success "Docker services started"
}

# Setup environment files
setup_env_files() {
    print_status "Setting up environment files..."
    
    # Backend .env
    if [ ! -f "backend/.env" ]; then
        cp backend/.env.example backend/.env
        print_status "Created backend/.env from example"
    fi
    
    # Root .env
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_status "Created .env from example"
    fi
    
    print_success "Environment files ready"
}

# Create enhanced startup script
create_startup_script() {
    cat > start_enhanced.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting Enhanced AgentFlow..."

# Start Docker services
echo "Starting Docker services..."
docker-compose up -d

# Wait a bit for services to be ready
sleep 5

# Start backend in background
echo "Starting backend server..."
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!
cd ..

# Start frontend in background  
echo "Starting frontend server..."
cd frontend
if command -v pnpm >/dev/null 2>&1; then
    pnpm dev &
else
    npm run dev &
fi
FRONTEND_PID=$!
cd ..

echo "✅ Enhanced AgentFlow is starting..."
echo "🔧 Backend API: http://localhost:8000"
echo "🌐 Frontend: http://localhost:5173"
echo "📊 Redis: localhost:6379"
echo "🗄️ Neo4j: http://localhost:7474"
echo "🔍 Qdrant: http://localhost:6333"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo "Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    docker-compose down
    exit 0
}

# Set up trap to call cleanup function on script exit
trap cleanup SIGINT SIGTERM

# Wait for background processes
wait
EOF

    chmod +x start_enhanced.sh
    print_success "Created start_enhanced.sh script"
}

# Main setup process
main() {
    print_status "Enhanced AgentFlow Setup Starting..."
    
    # Check prerequisites
    check_docker
    
    # Setup environment
    setup_env_files
    
    # Install dependencies
    install_python_deps
    install_node_deps
    
    # Start services
    start_docker_services
    
    # Create startup script
    create_startup_script
    
    print_success "Enhanced AgentFlow setup completed!"
    echo ""
    echo "🎉 Ready to go! Run the following to start:"
    echo "   ./start_enhanced.sh"
    echo ""
    echo "📚 Enhanced Features:"
    echo "   ✅ Chat-to-execution workflow"
    echo "   ✅ Real-time agent monitoring"
    echo "   ✅ Queue-based task management"
    echo "   ✅ Automatic agent coordination"
    echo "   ✅ Beautiful UI with live updates"
    echo "   ✅ Redis-based batching system"
    echo ""
}

# Run main function
main "$@"
