import os
import sqlite3
from typing import Dict, Any, List, Optional
from pathlib import Path

DB_PATH = Path(__file__).parent / "tenders.sqlite"

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Main tenders table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tenders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tender_id TEXT UNIQUE NOT NULL,
        reference_no TEXT,
        department TEXT,
        admin_type TEXT,
        authority TEXT,
        locality TEXT,
        zone TEXT,
        ward TEXT,
        title TEXT,
        work_description TEXT,
        tender_value REAL,
        category TEXT,
        subcategory TEXT,
        published_date TEXT,
        bid_opening_date TEXT,
        work_order_date TEXT,
        work_period_days INTEGER,
        expected_completion_date TEXT,
        status TEXT,
        status_note TEXT,
        source_url TEXT
    );
    """)

    # 2. Evidence table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evidence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tender_id TEXT NOT NULL,
        evidence_type TEXT,
        evidence_text TEXT,
        source_url TEXT,
        source_date TEXT,
        FOREIGN KEY (tender_id) REFERENCES tenders (tender_id)
    );
    """)

    # 3. Analysis results table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analysis_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        current_tender_id TEXT NOT NULL,
        silence_flag INTEGER DEFAULT 0,
        repetition_flag INTEGER DEFAULT 0,
        similar_tender_id TEXT,
        similarity_score REAL,
        time_difference_days INTEGER,
        explanation TEXT,
        created_at TEXT
    );
    """)

    # Indexes for fast lookup
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tenders_tender_id ON tenders(tender_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tenders_admin_type ON tenders(admin_type);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tenders_locality ON tenders(locality);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tenders_zone ON tenders(zone);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_tender_id ON evidence(tender_id);")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
