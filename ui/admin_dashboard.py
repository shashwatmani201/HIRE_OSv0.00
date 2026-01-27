import streamlit as st
import pandas as pd
import sys
import os
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.database_manager import add_job, get_db_connection
from src.agents import run_resume_screening, run_interview_evaluation
from streamlit_autorefresh import st_autorefresh  # Optional: helps keep time accurate
from services.email_service import send_meeting_invite, send_offer_letter # <--- Add this

st.set_page_config(page_title="HIRE_OS Admin", layout="wide")

# --- AUTO-REFRESH (Optional Hack) ---
# This forces the page to reload every 30 seconds to check the timer
# If you don't want to install 'streamlit-autorefresh', just remove this line.
count = st.empty()

st.title("🤖 HIRE_OS: Admin Dashboard")
tab1, tab2, tab3 = st.tabs(["Post New Job", "Applicant Tracking", "Finalists"])

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

# --- TAB 2: LIVE TRACKING (The Automatic Part) ---
with tab2:
    st.header("Live Pipeline")
    
    if st.button("Refresh Data"):
        st.rerun()

    conn = get_db_connection()
    jobs_df = pd.read_sql("SELECT id, title, status, deadline FROM jobs WHERE status='OPEN'", conn)
    
    if not jobs_df.empty:
        # 1. Job Selector
        job_options = {f"{row['title']} (ID: {row['id']})": row['id'] for index, row in jobs_df.iterrows()}
        selected_label = st.selectbox("Filter by Job", list(job_options.keys()))
        job_id = job_options[selected_label]
        
        # 2. Calculate Time Left
        selected_job = jobs_df[jobs_df['id'] == job_id].iloc[0]
        deadline_str = selected_job['deadline']
        
        try:
            deadline_dt = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M:%S.%f")
        except:
            deadline_dt = datetime.now()

        time_left = deadline_dt - datetime.now()
        total_seconds = int(time_left.total_seconds())

        # 3. AUTO-TRIGGER LOGIC
        # We use Session State to remember if we already ran it, so it doesn't loop forever.
        auto_run_key = f"auto_run_complete_{job_id}"
        
        if total_seconds <= 0:
            # DEADLINE PASSED
            st.error("🛑 DEADLINE REACHED. Processing Candidates...")
            
            # --- THE AUTOMATION BLOCK ---
            if auto_run_key not in st.session_state:
                with st.spinner("⏳ Timer finished! Automatically running AI Screener..."):
                    logs = run_resume_screening(job_id)
                    st.session_state[auto_run_key] = True  # Mark as done
                    st.success("✅ Auto-Screening Complete!")
                    st.text(logs)
            else:
                st.info("✅ Auto-Screening has already run for this batch.")
            # -----------------------------
            
        else:
            # TIMER IS RUNNING
            mins, secs = divmod(total_seconds, 60)
            st.info(f"⏳ Applications Open. Time Remaining: **{mins}m {secs}s**")

        # 4. Display Table
        candidates_df = pd.read_sql(
            "SELECT id, name, email, status, resume_score FROM candidates WHERE job_id = ?", 
            conn, params=(job_id,)
        )
        st.dataframe(candidates_df, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        # Manual Override Button (Always available)
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
    
    # 1. CANDIDATES READY FOR HR ROUND (Passed AI)
    st.subheader("1. Schedule HR Interview")
    # Fetch candidates who passed AI but haven't been scheduled yet
    ready_for_hr = pd.read_sql(
        "SELECT id, name, email, job_id, interview_score FROM candidates WHERE status='FINALIST'", 
        conn
    )
    
    if not ready_for_hr.empty:
        for index, row in ready_for_hr.iterrows():
            with st.expander(f"📅 Schedule: {row['name']} (AI Score: {row['interview_score']})"):
                col1, col2 = st.columns(2)
                with col1:
                    meet_link = st.text_input("Google Meet Link", key=f"link_{row['id']}")
                with col2:
                    meet_time = st.text_input("Date & Time (e.g. Tomorrow 10 AM)", key=f"time_{row['id']}")
                
                if st.button(f"Send Invite to {row['name']}", key=f"invite_{row['id']}"):
                    if meet_link and meet_time:
                        # 1. Send Email
                        job_title = conn.execute("SELECT title FROM jobs WHERE id=?", (row['job_id'],)).fetchone()['title']
                        send_meeting_invite(row['email'], row['name'], job_title, meet_link, meet_time)
                        
                        # 2. Update DB
                        conn.execute(
                            "UPDATE candidates SET status='HR_ROUND_SCHEDULED', meeting_link=?, meeting_time=? WHERE id=?",
                            (meet_link, meet_time, row['id'])
                        )
                        conn.commit()
                        st.success(f"Invite sent to {row['name']}!")
                        st.rerun()
                    else:
                        st.error("Please enter both Link and Time.")
    else:
        st.info("No candidates waiting for scheduling.")

    st.markdown("---")

    # 2. FINAL DECISION (After Interview)
    st.subheader("2. Final Verdict (Hire/Reject)")
    # Fetch candidates who are scheduled
    scheduled_cands = pd.read_sql(
        "SELECT id, name, email, job_id, meeting_time FROM candidates WHERE status='HR_ROUND_SCHEDULED'", 
        conn
    )
    
    if not scheduled_cands.empty:
        for index, row in scheduled_cands.iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{row['name']}**")
                st.caption(f"Interviewed at: {row['meeting_time']}")
            
            with col2:
                if st.button("✅ HIRE", key=f"hire_{row['id']}"):
                    # 1. Get Job Title for the email
                    job_title = conn.execute("SELECT title FROM jobs WHERE id=?", (row['job_id'],)).fetchone()['title']
                    
                    # 2. SEND THE EMAIL
                    with st.spinner("Sending Offer Letter..."):
                        try:
                            send_offer_letter(row['email'], row['name'], job_title)
                            st.success(f"Offer Letter sent to {row['name']}!")
                            
                            # 3. Update Status
                            conn.execute("UPDATE candidates SET status='HIRED' WHERE id=?", (row['id'],))
                            conn.commit()
                            st.balloons()
                            time.sleep(1) # Wait a second so you can see the success message
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to send email: {e}")
            
            with col3:
                if st.button("❌ REJECT", key=f"reject_{row['id']}"):
                    conn.execute("UPDATE candidates SET status='REJECTED_FINAL' WHERE id=?", (row['id'],))
                    conn.commit()
                    st.error(f"Candidate {row['name']} rejected.")
                    st.rerun()
    else:
        st.info("No interviews scheduled yet.")
        
    conn.close()