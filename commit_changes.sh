#!/bin/bash

echo "Committing changes to repository..."

# Ensure data directory exists
mkdir -p ./data

# Add all files
git add .

# Commit with message
git commit -m "Add session persistence with SQLite and improve Redis resilience

- Added SQLite-based session storage for persistence across server restarts
- Improved Redis connection handling with better error recovery
- Implemented multi-level caching with hot cache and local memory cache
- Added timeout protection for all Redis operations
- Enhanced LangGraph agent execution with fallback mechanisms"

echo "Changes committed successfully!"