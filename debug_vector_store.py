#!/usr/bin/env python3
"""Debug script to check what's in the vector store."""

import asyncio
from brandgpt.core import VectorStore

async def debug_vector_store():
    vector_store = VectorStore()
    
    # Search without any user filter
    print("🔍 Searching without user filter...")
    results = await vector_store.search("Vodafone", user_id=None, limit=5)
    print(f"Found {len(results)} documents")
    
    for i, doc in enumerate(results, 1):
        print(f"\n📄 Document {i}:")
        print(f"   ID: {doc['id']}")
        print(f"   Score: {doc['score']:.3f}")
        print(f"   Text preview: {doc['text'][:100]}...")
        print(f"   Metadata: {doc['metadata']}")
    
    # Search with user_id=5 (test user)
    print(f"\n🔍 Searching with user_id=5...")
    results_user = await vector_store.search("Vodafone", user_id=5, limit=5)
    print(f"Found {len(results_user)} documents for user 5")
    
    # Search with session-based approach (old way)
    print(f"\n🔍 Searching all sessions from database...")
    import sqlite3
    conn = sqlite3.connect("data/brandgpt.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM sessions LIMIT 5")
    sessions = cursor.fetchall()
    conn.close()
    
    print(f"Found {len(sessions)} sessions")
    for session_id in sessions[:3]:
        # This won't work with current API but shows the concept
        print(f"   Session: {session_id[0]}")

if __name__ == "__main__":
    asyncio.run(debug_vector_store())