# -*- coding: utf-8 -*-
"""
Migration script: Update embedding column from VARCHAR(2000) to TEXT
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.core.config import settings


# Create synchronous engine for migration
sync_engine = create_engine(settings.sync_database_url)


def migrate_embedding_column():
    """Migrate embedding column from VARCHAR(2000) to TEXT"""
    print("=" * 60)
    print("Migration: Update embedding column to TEXT type")
    print("=" * 60)

    with sync_engine.connect() as conn:
        # Check current column type
        print("\n[Step 1] Checking current column type...")
        result = conn.execute(text("""
            SELECT
                column_name,
                data_type,
                character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'conversation_memories'
                AND column_name = 'embedding'
        """))
        row = result.fetchone()

        if row:
            col_name, data_type, max_length = row
            print(f"Current type: {data_type}")
            if max_length:
                print(f"Current max length: {max_length}")

        # Alter column to TEXT
        print("\n[Step 2] Altering column to TEXT type...")
        conn.execute(text("""
            ALTER TABLE conversation_memories
            ALTER COLUMN embedding TYPE TEXT
        """))
        conn.commit()

        print("[OK] Column altered successfully")

        # Verify new type
        print("\n[Step 3] Verifying new column type...")
        result = conn.execute(text("""
            SELECT
                column_name,
                data_type,
                character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'conversation_memories'
                AND column_name = 'embedding'
        """))
        row = result.fetchone()

        if row:
            col_name, data_type, max_length = row
            print(f"New type: {data_type}")
            if max_length:
                print(f"New max length: {max_length}")
            else:
                print(f"New max length: UNLIMITED (TEXT type)")

        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)


if __name__ == "__main__":
    migrate_embedding_column()
