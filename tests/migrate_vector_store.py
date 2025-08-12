#!/usr/bin/env python3
"""Migration script to add user_id to existing vectors in Qdrant."""

import asyncio
import sqlite3
from qdrant_client import QdrantClient
from brandgpt.config import settings

async def migrate_vectors():
    print("🚀 Starting vector store migration...")
    
    # Connect to SQLite to get session->user mapping
    conn = sqlite3.connect("data/brandgpt.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id FROM sessions")
    session_user_map = {session_id: user_id for session_id, user_id in cursor.fetchall()}
    conn.close()
    
    print(f"📊 Found {len(session_user_map)} sessions in database")
    
    # Connect to Qdrant
    client = QdrantClient(url=settings.qdrant_url)
    collection_name = settings.qdrant_collection_name
    
    # Get all points from the collection
    print(f"🔍 Fetching all vectors from collection '{collection_name}'...")
    
    # Scroll through all points
    points, next_page_offset = client.scroll(
        collection_name=collection_name,
        limit=10000,  # Adjust if you have more than 10k documents
        with_payload=True,
        with_vectors=False  # We don't need vectors for this migration
    )
    
    print(f"📄 Found {len(points)} vectors to migrate")
    
    # Update each point with user_id
    migration_count = 0
    for point in points:
        session_id = point.payload.get('session_id')
        if session_id and session_id in session_user_map:
            user_id = session_user_map[session_id]
            
            # Update the payload with user_id
            new_payload = {**point.payload, 'user_id': user_id}
            
            # Update the point in Qdrant
            client.set_payload(
                collection_name=collection_name,
                payload=new_payload,
                points=[point.id]
            )
            
            migration_count += 1
            if migration_count % 10 == 0:
                print(f"   ✅ Migrated {migration_count} vectors...")
        else:
            print(f"   ⚠️  No user found for session {session_id}, skipping vector {point.id}")
    
    print(f"✅ Migration complete! Updated {migration_count} vectors with user_id")
    
    # Verify migration
    print("\n🔍 Verifying migration...")
    test_results = client.scroll(
        collection_name=collection_name,
        limit=5,
        with_payload=True,
        with_vectors=False
    )[0]
    
    for point in test_results:
        has_user_id = 'user_id' in point.payload
        user_id = point.payload.get('user_id', 'MISSING')
        session_id = point.payload.get('session_id', 'MISSING')
        print(f"   📄 Vector {point.id}: user_id={user_id}, session_id={session_id}, has_user_id={has_user_id}")

if __name__ == "__main__":
    asyncio.run(migrate_vectors())