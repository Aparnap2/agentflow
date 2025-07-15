#!/bin/bash
echo "Installing required packages for AgentFlow..."
pip install upstash-redis
pip install redis[asyncio]
pip install qdrant-client
pip install neo4j
pip install langgraph
pip install langchain
echo "Done!"