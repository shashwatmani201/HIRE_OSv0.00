import sqlite3
import os
from datetime import datetime

# Configuration
DB_NAME = "data/hire_os.db"

def initialize_db():
    """
    Initializes the database, creates necessary directories, 
    and creates the tables if they do not exist.
    """
    # 1. Ensure data directories exist
    os.makedirs("data/resumes", exist_ok=True)
    os.makedirs("data/transcripts", exist_ok=True)
    os.makedirs("data/sent_emails", exist_ok=True)

    # 2. Connect to SQLite
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 3. Create JOBS Table
    # Stores job descriptions and current hiring status
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            requirements TEXT,
            status TEXT DEFAULT 'OPEN', -- OPEN, CLOSED
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 4. Create CANDIDATES Table
    # Tracks the candidate through the entire lifecycle
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            
            -- Filter 1: Resume Screening
            resume_path TEXT,
            resume_score INTEGER DEFAULT 0,
            resume_summary TEXT,
            
            -- Filter 2: AI Interview
            interview_transcript_path TEXT,
            interview_score INTEGER DEFAULT 0,
            interview_feedback TEXT,
            
            -- Logistics
            meeting_link TEXT,
            
            -- Lifecycle Status
            status TEXT DEFAULT 'APPLIED', 
            -- Enum: APPLIED, SHORTLISTED, INTERVIEW_PENDING, COMPLETED, FINALIST, REJECTED, OFFER_SENT
            
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs (id)
        )
    ''')

    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {DB_NAME}")
    print("✅ Tables 'jobs' and 'candidates' are ready.")

# Helper functions for basic DB operations

def get_db_connection():
    """Returns a connection object to the database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

def add_job(title, description, requirements=""):
    """Adds a new job opening."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO jobs (title, description, requirements) VALUES (?, ?, ?)",
        (title, description, requirements)
    )
    conn.commit()
    job_id = cursor.lastrowid
    conn.close()
    return job_id

def add_candidate(job_id, name, email, resume_path):
    """Adds a new candidate application."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO candidates (job_id, name, email, resume_path, status) VALUES (?, ?, ?, ?, 'APPLIED')",
        (job_id, name, email, resume_path)
    )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Run this file directly to set up the DB for the first time
    initialize_db()