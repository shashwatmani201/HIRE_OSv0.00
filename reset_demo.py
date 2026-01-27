import sqlite3
import os
import glob

# Configuration
DB_PATH = "data/hire_os.db"
RESUME_DIR = "data/resumes"
TRANSCRIPT_DIR = "data/transcripts"

def clean_folder(folder_path, extension="*"):
    """Deletes all files in a folder matching the extension."""
    files = glob.glob(os.path.join(folder_path, extension))
    for f in files:
        try:
            os.remove(f)
            print(f"   Deleted: {f}")
        except Exception as e:
            print(f"   Error deleting {f}: {e}")

def reset_database():
    """Clears candidates but keeps the Job Postings."""
    if not os.path.exists(DB_PATH):
        print("❌ Database not found. Nothing to reset.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Count current candidates
        count = cursor.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
        print(f"📊 Found {count} candidates to remove.")

        # 2. Delete all candidates
        cursor.execute("DELETE FROM candidates")
        
        # 3. Reset the auto-increment counter for candidates (Optional, for clean IDs)
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='candidates'")

        conn.commit()
        print("✅ Database cleared (Job Posts preserved).")
        
    except Exception as e:
        print(f"❌ Error resetting DB: {e}")
    finally:
        conn.close()

def main():
    print("🔄 --- HIRE_OS DEMO RESET --- 🔄")
    confirm = input("Are you sure you want to delete all CANDIDATE data? (yes/no): ")
    
    if confirm.lower() == "yes":
        print("\n1. Cleaning Database...")
        reset_database()
        
        print("\n2. Cleaning Resume Files...")
        clean_folder(RESUME_DIR, "*.pdf")
        
        print("\n3. Cleaning Interview Transcripts...")
        clean_folder(TRANSCRIPT_DIR, "*.txt")
        
        print("\n✨ SYSTEM READY FOR DEMO! ✨")
        print("---------------------------------")
        print("Next Steps:")
        print("1. Restart your Admin Dashboard terminal.")
        print("2. Restart your Candidate Portal terminal.")
    else:
        print("❌ Reset cancelled.")

if __name__ == "__main__":
    main()