import streamlit as st
import pandas as pd
import sqlite3
import sys
import os
from dotenv import load_dotenv


load_dotenv()

# Add parent directory to path to import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.database_manager import add_job, get_db_connection
from src.agents import run_resume_screening, run_interview_evaluation
# from services.email_service import send_offer_letter # Uncomment if ready

st.set_page_config(page_title="HIRE_OS Admin", layout="wide")

st.title("🤖 HIRE_OS: Admin Dashboard")

# Tabs
tab1, tab2, tab3 = st.tabs(["Post New Job", "Applicant Tracking", "Finalists"])

# --- TAB 1: POST JOB ---
with tab1:
    st.header("Create a New Job Opening")
    with st.form("job_form"):
        title = st.text_input("Job Title", placeholder="e.g. Senior Python Developer")
        description = st.text_area("Job Description", height=150)
        requirements = st.text_area("Key Requirements", placeholder="e.g. Python, CrewAI, AWS")
        submitted = st.form_submit_button("Post Job")
        
        if submitted and title:
            add_job(title, description, requirements)
            st.success(f"Job '{title}' posted successfully!")

# --- TAB 2: APPLICANT TRACKING ---
with tab2:
    st.header("Live Pipeline")
    
    if st.button("Refresh Data"):
        st.rerun()

    conn = get_db_connection()
    
    # Query Jobs
    jobs_df = pd.read_sql("SELECT id, title, status FROM jobs WHERE status='OPEN'", conn)
    
    if not jobs_df.empty:
        # --- FIX: Show ID in the dropdown to distinguish duplicate titles ---
        job_options = {f"{row['title']} (ID: {row['id']})": row['id'] for index, row in jobs_df.iterrows()}
        
        selected_label = st.selectbox("Filter by Job", list(job_options.keys()))
        job_id = job_options[selected_label]
        
        st.caption(f"Showing candidates for Job ID: {job_id}")

        # Query Candidates
        query = """
            SELECT id, name, email, status, resume_score 
            FROM candidates 
            WHERE job_id = ?
        """
        candidates_df = pd.read_sql(query, conn, params=(job_id,))
        
        st.dataframe(candidates_df, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("Filter 1: Resume Screening")
            if st.button(f"Run AI Screener"):
                with st.spinner("Agents are reading resumes..."):
                    logs = run_resume_screening(job_id)
                    st.success("Screening Complete!")
                    st.text(logs)
                    st.rerun()
        
        with col2:
            st.info("Filter 2: Interview Analysis")
            if st.button("Process Interviews"):
                with st.spinner("CTO Agent is grading transcripts..."):
                    logs = run_interview_evaluation(job_id) 
                    st.success("Evaluation Complete!")
                    st.text(logs)
                    st.rerun()
                
    else:
        st.info("No open jobs found. Post a job in Tab 1.")
    
    conn.close()

# --- TAB 3: FINALISTS ---
with tab3:
    st.header("Finalists & Offers")
    conn = get_db_connection()
    finalists = pd.read_sql(
        "SELECT id, name, email, job_id, interview_score, interview_feedback FROM candidates WHERE status='FINALIST'", 
        conn
    )
    
    if not finalists.empty:
        st.dataframe(finalists)
        for index, row in finalists.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{row['name']}** (Score: {row['interview_score']})")
                st.caption(f"Feedback: {row['interview_feedback']}")
            with col2:
                if st.button(f"Send Offer to {row['name']}", key=f"offer_{row['id']}"):
                    st.success(f"Offer sent to {row['name']}! (Mock Email)")
    else:
        st.info("No candidates have reached the Finalist stage yet.")
    
    conn.close()