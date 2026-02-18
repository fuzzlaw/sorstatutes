import json
import sqlite3
from pathlib import Path

def build_database(index_path, db_path):
    # Load the index
    with open(index_path, 'r', encoding='utf-8') as f:
        records = json.load(f)

    # Create SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create main table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            filename TEXT,
            state TEXT,
            year TEXT,
            page_count INTEGER,
            full_text TEXT
        )
    ''')

    # Create FTS5 virtual table for full-text search
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts
        USING fts5(
            id,
            state,
            year,
            full_text,
            content=documents,
            content_rowid=rowid
        )
    ''')

    # Insert records
    for record in records:
        cursor.execute('''
            INSERT OR REPLACE INTO documents
            (id, filename, state, year, page_count, full_text)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            record.get('id', ''),
            record.get('filename', ''),
            record.get('state', ''),
            record.get('year', ''),
            record.get('page_count', 0),
            record.get('full_text', '')
        ))

    # Populate FTS index
    cursor.execute('''
        INSERT INTO documents_fts(documents_fts) VALUES('rebuild')
    ''')

    conn.commit()
    conn.close()
    print(f"Database built successfully at {db_path}")
    print(f"Indexed {len(records)} documents.")

if __name__ == '__main__':
    build_database(
        index_path='output/index.json',
        db_path='output/statutes.db'
    )
