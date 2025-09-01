#!/usr/bin/env python3
"""
Migration script to add user_id and group_id fields to documents table.
This migration is needed for the v1 API compatibility features.
"""

import sqlite3
import os
from pathlib import Path

def migrate_database():
    # Database paths
    db_paths = [
        "./data/brandgpt.db",  # Local development
        "./brandgpt.db",      # Legacy location
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ No database found. Database will be created with new schema on first run.")
        return
    
    print(f"📊 Migrating database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("PRAGMA table_info(documents)")
        columns = [col[1] for col in cursor.fetchall()]
        
        print(f"Current columns: {columns}")
        
        # Check if we need to add user_id
        needs_user_id = 'user_id' not in columns
        needs_group_id = 'group_id' not in columns
        
        if not (needs_user_id or needs_group_id):
            print("✅ Database already has user_id and group_id columns. No migration needed.")
            conn.close()
            return
        
        print("🔄 Adding missing columns...")
        
        if needs_user_id:
            # Add user_id column (we'll need to populate it)
            cursor.execute("""
                ALTER TABLE documents 
                ADD COLUMN user_id INTEGER REFERENCES users(id)
            """)
            print("✅ Added user_id column")
            
            # Populate user_id from session data where possible
            cursor.execute("""
                UPDATE documents 
                SET user_id = (
                    SELECT sessions.user_id 
                    FROM sessions 
                    WHERE sessions.id = documents.session_id
                )
                WHERE documents.session_id IS NOT NULL
            """)
            rows_updated = cursor.rowcount
            print(f"✅ Updated user_id for {rows_updated} documents from session data")
            
            # For documents without session_id, we'll set a default user (ID 1 if exists)
            cursor.execute("SELECT id FROM users LIMIT 1")
            result = cursor.fetchone()
            if result:
                default_user_id = result[0]
                cursor.execute("""
                    UPDATE documents 
                    SET user_id = ? 
                    WHERE user_id IS NULL
                """, (default_user_id,))
                orphaned_docs = cursor.rowcount
                if orphaned_docs > 0:
                    print(f"⚠️  Set user_id={default_user_id} for {orphaned_docs} orphaned documents")
        
        if needs_group_id:
            # Add group_id column (nullable)
            cursor.execute("""
                ALTER TABLE documents 
                ADD COLUMN group_id TEXT
            """)
            print("✅ Added group_id column")
            
            # Create index for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_group_id 
                ON documents(group_id)
            """)
            print("✅ Created index on group_id")
        
        # Create index on user_id for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_user_id 
            ON documents(user_id)
        """)
        print("✅ Created index on user_id")
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()