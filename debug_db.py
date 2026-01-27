import sqlite3
import pandas as pd

# Connect to the database
conn = sqlite3.connect("data/hire_os.db")

print("--- 1. ALL JOBS ---")
jobs = pd.read_sql("SELECT * FROM jobs", conn)
print(jobs)

print("\n--- 2. ALL CANDIDATES ---")
candidates = pd.read_sql("SELECT * FROM candidates", conn)
print(candidates)

conn.close()