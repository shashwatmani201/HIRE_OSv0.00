import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = "data/hire_os.db"

def get_db_connection():
    if not os.path.exists("data"):
        os.makedirs("data")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            requirements TEXT,
            status TEXT DEFAULT 'OPEN',
            deadline DATETIME
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            name TEXT,
            email TEXT,
            resume_path TEXT,
            status TEXT DEFAULT 'APPLIED',
            resume_score INTEGER DEFAULT 0,
            resume_summary TEXT,
            interview_transcript_path TEXT,
            interview_score INTEGER DEFAULT 0,
            interview_feedback TEXT,
            meeting_link TEXT,      -- <--- NEW
            meeting_time TEXT,      -- <--- NEW
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        )
    ''')
    conn.commit()
    conn.close()

# Updated to accept 'minutes_open'
def add_job(title, description, requirements, minutes_open=10):
    conn = get_db_connection()
    
    # Calculate Deadline
    deadline = datetime.now() + timedelta(minutes=minutes_open)
    
    conn.execute(
        "INSERT INTO jobs (title, description, requirements, deadline) VALUES (?, ?, ?, ?)",
        (title, description, requirements, deadline)
    )
    conn.commit()
    conn.close()

def add_candidate(job_id, name, email, resume_path):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO candidates (job_id, name, email, resume_path) VALUES (?, ?, ?, ?)",
        (job_id, name, email, resume_path)
    )
    conn.commit()
    conn.close()

# Run table creation on import
create_tables()

def delete_job_permanently(job_id):
    """
    Deletes a job and ALL linked candidates from the database.
    """
    conn = get_db_connection()
    try:
        # 1. Delete all candidates linked to this job first (to prevent orphans)
        conn.execute("DELETE FROM candidates WHERE job_id = ?", (job_id,))
        
        # 2. Delete the job itself
        conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting job: {e}")
        return False
    finally:
        conn.close()