import streamlit as st
import pandas as pd
import sys
import os
import time
from datetime import datetime
import plotly.express as px  # <--- NEW LIBRARY FOR CHARTS
import plotly.graph_objects as go

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.database_manager import add_job, get_db_connection
from src.agents import run_resume_screening, run_interview_evaluation
from services.email_service import send_meeting_invite, send_offer_letter

st.set_page_config(page_title="HIRE_OS Admin", layout="wide")

st.title("🤖 HIRE_OS: Admin Dashboard")

# --- UPDATED TABS (Added 'Analytics') ---
tab1, tab2, tab3, tab4 = st.tabs(["Post New Job", "Applicant Tracking", "Finalists", "Analytics 📊"])

# --- TAB 1: POST JOB ---
with tab1:
    st.header("Create a New Job Opening")
    with st.form("job_form"):
        title = st.text_input("Job Title", placeholder="e.g. Senior Python Developer")
        description = st.text_area("Job Description", height=100)
        requirements = st.text_area("Key Requirements", placeholder="e.g. Python, CrewAI, AWS")
        duration = st.slider("Application Window (Minutes)", min_value=1, max_value=60, value=2)
        
        submitted = st.form_submit_button("Post Job & Start Timer")
        
        if submitted and title:
            add_job(title, description, requirements, minutes_open=duration)
            st.success(f"Job '{title}' posted! Applications close in {duration} minutes.")

# --- TAB 2: LIVE TRACKING ---
with tab2:
    st.header("Live Pipeline")
    
    if st.button("Refresh Data"):
        st.rerun()

    conn = get_db_connection()
    jobs_df = pd.read_sql("SELECT id, title, status, deadline FROM jobs WHERE status='OPEN'", conn)
    
    if not jobs_df.empty:
        job_options = {f"{row['title']} (ID: {row['id']})": row['id'] for index, row in jobs_df.iterrows()}
        selected_label = st.selectbox("Filter by Job", list(job_options.keys()))
        job_id = job_options[selected_label]
        
        # Timer Logic
        selected_job = jobs_df[jobs_df['id'] == job_id].iloc[0]
        deadline_str = selected_job['deadline']
        try:
            deadline_dt = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M:%S.%f")
        except:
            deadline_dt = datetime.now()

        time_left = deadline_dt - datetime.now()
        total_seconds = int(time_left.total_seconds())
        
        auto_run_key = f"auto_run_complete_{job_id}"

        if total_seconds <= 0:
            st.error("🛑 DEADLINE REACHED. Processing Candidates...")
            if auto_run_key not in st.session_state:
                with st.spinner("⏳ Timer finished! Automatically running AI Screener..."):
                    logs = run_resume_screening(job_id)
                    st.session_state[auto_run_key] = True
                    st.success("✅ Auto-Screening Complete!")
                    st.text(logs)
            else:
                st.info("✅ Auto-Screening has already run for this batch.")
        else:
            mins, secs = divmod(total_seconds, 60)
            st.info(f"⏳ Applications Open. Time Remaining: **{mins}m {secs}s**")

        # Candidates Table
        candidates_df = pd.read_sql(
            "SELECT id, name, email, status, resume_score FROM candidates WHERE job_id = ?", 
            conn, params=(job_id,)
        )
        st.dataframe(candidates_df, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Manual Controls")
            if st.button("Run AI Screener (Manual Force)"):
                with st.spinner("Forcing manual run..."):
                    logs = run_resume_screening(job_id)
                    st.session_state[auto_run_key] = True
                    st.success("Done!")
                    st.text(logs)
                    st.rerun()
        with col2:
            st.caption("Interview Stage")
            if st.button("Process Interviews"):
                with st.spinner("Grading transcripts..."):
                    logs = run_interview_evaluation(job_id) 
                    st.success("Done!")
                    st.text(logs)
                    st.rerun()
    else:
        st.info("No open jobs found.")
    conn.close()

# --- TAB 3: HR ROUND & FINAL OFFERS ---
with tab3:
    st.header("Step 3: Human Interview & Final Decision")
    conn = get_db_connection()
    
    # 1. Schedule HR Interview
    st.subheader("1. Schedule HR Interview")
    ready_for_hr = pd.read_sql("SELECT id, name, email, job_id, interview_score FROM candidates WHERE status='FINALIST'", conn)
    
    if not ready_for_hr.empty:
        for index, row in ready_for_hr.iterrows():
            with st.expander(f"📅 Schedule: {row['name']} (AI Score: {row['interview_score']})"):
                col1, col2 = st.columns(2)
                with col1:
                    meet_link = st.text_input("Google Meet Link", key=f"link_{row['id']}")
                with col2:
                    meet_time = st.text_input("Date & Time", key=f"time_{row['id']}")
                
                if st.button(f"Send Invite to {row['name']}", key=f"invite_{row['id']}"):
                    if meet_link and meet_time:
                        job_title = conn.execute("SELECT title FROM jobs WHERE id=?", (row['job_id'],)).fetchone()['title']
                        send_meeting_invite(row['email'], row['name'], job_title, meet_link, meet_time)
                        conn.execute("UPDATE candidates SET status='HR_ROUND_SCHEDULED', meeting_link=?, meeting_time=? WHERE id=?", (meet_link, meet_time, row['id']))
                        conn.commit()
                        st.success("Invite sent!")
                        st.rerun()

    st.markdown("---")

    # 2. Final Verdict
    st.subheader("2. Final Verdict")
    scheduled_cands = pd.read_sql("SELECT id, name, email, job_id, meeting_time FROM candidates WHERE status='HR_ROUND_SCHEDULED'", conn)
    
    if not scheduled_cands.empty:
        for index, row in scheduled_cands.iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{row['name']}** (Interview: {row['meeting_time']})")
            with col2:
                if st.button("✅ HIRE", key=f"hire_{row['id']}"):
                    job_title = conn.execute("SELECT title FROM jobs WHERE id=?", (row['job_id'],)).fetchone()['title']
                    with st.spinner("Sending Offer Letter..."):
                        send_offer_letter(row['email'], row['name'], job_title)
                        conn.execute("UPDATE candidates SET status='HIRED' WHERE id=?", (row['id'],))
                        conn.commit()
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
            with col3:
                if st.button("❌ REJECT", key=f"reject_{row['id']}"):
                    conn.execute("UPDATE candidates SET status='REJECTED_FINAL' WHERE id=?", (row['id'],))
                    conn.commit()
                    st.rerun()
    conn.close()

# --- TAB 4: ANALYTICS (NEW!) ---
with tab4:
    st.header("📊 Recruitment Analytics")
    conn = get_db_connection()
    
    # Load all data
    df = pd.read_sql("SELECT * FROM candidates", conn)
    
    if not df.empty:
        # 1. TOP METRICS ROW
        col1, col2, col3, col4 = st.columns(4)
        total = len(df)
        hired = len(df[df['status'] == 'HIRED'])
        avg_resume = df['resume_score'].mean()
        avg_interview = df[df['interview_score'] > 0]['interview_score'].mean() # Only count non-zeros

        col1.metric("Total Applicants", total)
        col2.metric("Hired Candidates", hired)
        col3.metric("Avg Resume Score", f"{avg_resume:.1f}")
        col4.metric("Avg Interview Score", f"{avg_interview:.1f}")
        
        st.markdown("---")

        # 2. THE RECRUITMENT FUNNEL
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("Recruitment Funnel")
            # Logic: Calculate drop-offs
            count_applied = total
            count_shortlisted = len(df[df['resume_score'] >= 70])
            count_finalist = len(df[df['status'].isin(['FINALIST', 'HR_ROUND_SCHEDULED', 'HIRED', 'REJECTED_FINAL'])])
            count_hired = hired
            
            data = dict(
                number=[count_applied, count_shortlisted, count_finalist, count_hired],
                stage=["Applied", "Resume Passed", "Interviewed", "Hired"]
            )
            fig_funnel = px.funnel(data, x='number', y='stage', color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_funnel, use_container_width=True)

        # 3. SCORE DISTRIBUTION
        with col_chart2:
            st.subheader("Candidate Quality Heatmap")
            # Scatter plot of Resume Score vs Interview Score
            # Filter out 0s for better visuals
            filtered_df = df[(df['resume_score'] > 0) & (df['interview_score'] > 0)]
            if not filtered_df.empty:
                fig_scatter = px.scatter(
                    filtered_df, 
                    x="resume_score", 
                    y="interview_score", 
                    color="status",
                    hover_data=['name'],
                    size_max=15,
                    title="Resume vs. Interview Performance"
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.info("Not enough interview data for correlation chart.")

    else:
        st.warning("No data available for analytics yet.")
    
    conn.close()