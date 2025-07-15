# AgentFlow

A modular, efficient multi-agent orchestration system using LangGraph for agent coordination and communication.

## Core Features

- **LangGraph Integration**: Efficient agent workflows with state management
- **Lazy Initialization**: Resources are only initialized when needed
- **Caching System**: Reduces redundant data fetching and LLM calls
- **Modular Architecture**: Reusable components across the system
- **Queue Management**: Optimized task processing with priority handling

## Recent Optimizations

- **Session Persistence**: Added SQLite-based session storage for persistence across server restarts
- **Redis Connection Resilience**: Improved error handling and fallback mechanisms for Redis operations
- **Multi-level Caching**: Implemented hot cache and local memory cache for better performance
- **Lazy Queue Initialization**: Queue system now initializes only when needed, not at startup
- **Cached Context**: Global context is cached with TTL to reduce database queries
- **Efficient LLM Calls**: Implemented caching for similar prompts to reduce token usage
- **Optimized React Components**: Fixed ReactMarkdown implementation for better frontend performance
- **Streamlined Agent Communication**: Reduced data transfer between agents

## TODO

1. **Further Optimization**
   - Implement batched LLM calls for similar agent tasks
   - Add compression for large context objects
   - Optimize memory usage in vector store queries

2. **Code Reuse**
   - Extract common agent patterns into shared utilities
   - Create a unified prompt template system
   - Standardize error handling across agents

3. **Performance Monitoring**
   - Add detailed performance metrics for each agent
   - Implement token usage tracking
   - Create dashboard for system performance

4. **Architecture Improvements**
   - Consolidate duplicate agent functionality
   - Implement more efficient state transitions in LangGraph
   - Optimize WebSocket communication for real-time updates

## Getting Started

1. Install dependencies:
   ```
   # Quick install of critical dependencies
   chmod +x install_dependencies.sh
   ./install_dependencies.sh
   
   # Or full install
   pip install -r backend/requirements.txt
   ```

2. Set up environment variables:
   ```
   cp .env.example .env
   # Edit .env with your API keys for:
   # - OPENROUTER_API_KEY (for LLM access)
   # - QDRANT_URL and QDRANT_API_KEY (for vector storage)
   # - NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD (for graph storage)
   # - REDIS_URL and REDIS_TOKEN (for queue management)
   ```

3. Run the backend:
   ```
   cd backend
   uvicorn main:app --reload
   ```

4. Run the frontend:
   ```
   cd frontend
   npm install
   npm run dev
   ```
   
5. Troubleshooting:
   - If Redis connection fails, the system will operate with limited functionality using local caching
   - If Neo4j connection fails, the system will use fallback memory storage
   - If Qdrant connection fails, ensure your API key and URL are correct

## Architecture

The system uses a modular architecture with these key components:

- **LangGraph Core**: Efficient agent workflows with state management
- **Memory Systems**: Vector and graph databases for context
- **Queue Management**: Redis-based task processing
- **Agent Factory**: Dynamic agent creation and configuration
- **Event Bus**: Real-time communication between components