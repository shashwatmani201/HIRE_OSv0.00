import streamlit as st
import pandas as pd
import sys
import os
import re

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.database_manager import add_candidate, get_db_connection

st.set_page_config(page_title="HIRE_OS Careers", page_icon="🚀", layout="centered")

st.title("🚀 Join the HIRE_OS Team")
st.caption("Browse our open positions and apply instantly with our AI-powered portal.")

# 1. Fetch Open Jobs
conn = get_db_connection()
jobs = conn.execute("SELECT id, title, description FROM jobs WHERE status='OPEN'").fetchall()
conn.close()

if not jobs:
    st.warning("⚠️ No positions are currently open. Please check back later.")
else:
    # Create mapping for Dropdown
    job_options = {job['title']: job['id'] for job in jobs}
    selected_job_title = st.selectbox("Select Position", list(job_options.keys()))
    
    # Get ID and Description
    job_id = job_options[selected_job_title]
    # Find description for display
    job_desc = next((j['description'] for j in jobs if j['id'] == job_id), "No description available.")
    
    
    st.markdown("---")
    
    # --- APPLICATION FORM ---
    with st.form("application_form"):
        st.subheader(f"Apply for: {selected_job_title}")
        name = st.text_input("Full Name")
        email = st.text_input("Email Address")
        uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
        
        submitted = st.form_submit_button("Submit Application")
        
        if submitted:
            # 1. VALIDATION: Check for empty fields
            if not name or not email or not uploaded_file:
                st.error("⚠️ Please fill in all fields and upload a resume.")
            
            # 2. VALIDATION: Check Email Format (Regex)
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                st.error("⚠️ Please enter a valid email address.")

            else:
                # 3. DUPLICATE CHECK: Has this email already applied?
                conn = get_db_connection()
                existing_app = conn.execute(
                    "SELECT id FROM candidates WHERE email = ? AND job_id = ?",
                    (email, job_id)
                ).fetchone()
                conn.close()

                if existing_app:
                    st.warning("🚫 You have already applied for this position! Please check your email for updates.")
                
                else:
                    # 4. SAVE FILE
                    os.makedirs("data/resumes", exist_ok=True)
                    clean_name = name.replace(" ", "_")
                    file_path = os.path.join("data/resumes", f"{job_id}_{clean_name}.pdf")
                    
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # 5. SAVE TO DB
                    try:
                        add_candidate(job_id, name, email, file_path)
                        st.success(f"✅ Application Submitted! Good luck, {name}.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"An error occurred: {e}")