#!/usr/bin/env python3
"""Make session_id nullable in documents table for user-scoped content."""

import sqlite3
import sys
from pathlib import Path

def migrate_session_nullable():
    """Make session_id nullable in documents table."""
    db_path = Path("data/brandgpt.db")
    
    if not db_path.exists():
        print("❌ Database not found at data/brandgpt.db")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("📝 Making session_id nullable in documents table...")
        
        # SQLite doesn't support ALTER COLUMN directly, so we need to:
        # 1. Create new table with nullable session_id
        # 2. Copy data from old table 
        # 3. Drop old table
        # 4. Rename new table
        
        # Check if documents table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
        if not cursor.fetchone():
            print("✅ Documents table doesn't exist yet - nothing to migrate")
            return True
        
        print("   Creating new documents table with nullable session_id...")
        
        # Create new table structure
        cursor.execute("""
            CREATE TABLE documents_new (
                id INTEGER NOT NULL,
                session_id VARCHAR,
                filename VARCHAR,
                url VARCHAR,
                content_type VARCHAR NOT NULL,
                doc_metadata JSON,
                processed VARCHAR,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                processed_at DATETIME,
                PRIMARY KEY (id),
                FOREIGN KEY(session_id) REFERENCES sessions (id)
            )
        """)
        
        # Copy existing data
        cursor.execute("""
            INSERT INTO documents_new 
            SELECT id, session_id, filename, url, content_type, doc_metadata, 
                   processed, error_message, created_at, processed_at
            FROM documents
        """)
        
        # Drop old table
        cursor.execute("DROP TABLE documents")
        
        # Rename new table
        cursor.execute("ALTER TABLE documents_new RENAME TO documents")
        
        # Recreate indexes
        cursor.execute("CREATE INDEX ix_documents_id ON documents (id)")
        
        conn.commit()
        print("✅ Successfully migrated documents table to nullable session_id")
        
        # Verify the change
        cursor.execute("PRAGMA table_info(documents)")
        columns = cursor.fetchall()
        print("\nUpdated documents table schema:")
        for col in columns:
            nullable = "NULL" if col[3] == 0 else "NOT NULL"
            print(f"  - {col[1]} ({col[2]}) {nullable}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = migrate_session_nullable()
    sys.exit(0 if success else 1)