#!/usr/bin/env python3
"""Test database connections"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_connections():
    print("🔍 Testing Database Connections")
    print("=" * 40)
    
    # Test Vector Memory (Qdrant)
    print("1. Testing Qdrant Vector Memory...")
    try:
        from memory.vector_memory import VectorMemory
        vector_mem = VectorMemory()
        info = await vector_mem.get_collection_info()
        print(f"✅ Qdrant connected: {info['vectors_count']} vectors")
    except Exception as e:
        print(f"❌ Qdrant failed: {e}")
    
    # Test Graph Memory (Neo4j)
    print("\n2. Testing Neo4j Graph Memory...")
    try:
        from memory.graph_memory import GraphMemory
        graph_mem = GraphMemory()
        state = await graph_mem.get_graph_state()
        print(f"✅ Neo4j connected: {len(state['agents'])} agents")
    except Exception as e:
        print(f"❌ Neo4j failed: {e}")
    
    # Test Memory Manager Integration
    print("\n3. Testing Memory Manager...")
    try:
        from memory.memory_manager import OptimizedMemoryManager
        mem_mgr = OptimizedMemoryManager()
        stats = await mem_mgr.get_memory_stats()
        print(f"✅ Memory Manager: {stats['graph_memory']['agents']} agents, {stats['vector_memory']['total_documents']} docs")
    except Exception as e:
        print(f"❌ Memory Manager failed: {e}")
    
    print("\n" + "=" * 40)
    print("Database connection test completed!")

if __name__ == "__main__":
    asyncio.run(test_connections())