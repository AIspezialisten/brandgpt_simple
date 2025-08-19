#!/usr/bin/env python3
"""Add api_key field to users table for dual authentication support."""

import sqlite3
import sys
from pathlib import Path

def migrate_api_key_field():
    """Add api_key field to users table."""
    db_path = Path("data/brandgpt.db")
    
    if not db_path.exists():
        print("❌ Database not found at data/brandgpt.db")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if api_key column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "api_key" in columns:
            print("✅ api_key column already exists")
            return True
        
        print("📝 Adding api_key column to users table...")
        
        # Add the api_key column (nullable, without UNIQUE constraint initially)
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN api_key VARCHAR
        """)
        
        # Create unique index for api_key (handles NULL values properly)
        cursor.execute("""
            CREATE UNIQUE INDEX ix_users_api_key ON users (api_key) WHERE api_key IS NOT NULL
        """)
        
        conn.commit()
        print("✅ Successfully added api_key column and index")
        
        # Verify the change
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("\nUpdated users table schema:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = migrate_api_key_field()
    sys.exit(0 if success else 1)