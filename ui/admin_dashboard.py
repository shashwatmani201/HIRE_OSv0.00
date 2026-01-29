import streamlit as st
import pandas as pd
import sys
import os
import time
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components 

# 1. SETUP PATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 2. IMPORTS
from src.database_manager import add_job, get_db_connection, delete_job_permanently
from services.email_service import send_meeting_invite, send_offer_letter, send_rejection_email
from src.agents import (
    run_resume_screening, 
    run_interview_evaluation, 
    generate_viral_linkedin_post, 
    generate_job_image
)


st.set_page_config(page_title="HIRE_OS Admin", layout="wide")

# ==========================================
# 🔐 AUTHENTICATION LOGIC
# ==========================================

# Simple hardcoded credentials (in a real app, use .env or a database)
ADMIN_USER = "admin"
ADMIN_PASS = "hire123"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def login():
    st.title("🔒 HIRE_OS Admin Login")
    
    # Center the login box using columns
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            st.markdown("### Please verify your identity")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if username == ADMIN_USER and password == ADMIN_PASS:
                    st.session_state.authenticated = True
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid Username or Password")

def logout():
    st.session_state.authenticated = False
    st.rerun()

# ==========================================
# 🚀 MAIN APP LOGIC
# ==========================================

if not st.session_state.authenticated:
    login()
else:
    # --- SIDEBAR (Logout Button) ---
    with st.sidebar:
        st.title("Admin Controls")
        st.write(f"Logged in as: **{ADMIN_USER}**")
        if st.button("🚪 Logout"):
            logout()
    st.title("🤖 HIRE_OS: Admin Dashboard")    

    # --- UPDATED TABS (Added 'Analytics') ---
    tab1, tab2, tab3, tab4 = st.tabs(["Post New Job", "Applicant Tracking", "Finalists", "Analytics 📊"])    
    
    

    # --- TAB 1: POST JOB & SOCIAL SHARE ---
    with tab1:
        st.header("Create a New Job Opening")
        
        # Initialize Session State for post AND image
        if "latest_job_post" not in st.session_state:
            st.session_state.latest_job_post = None
        if "latest_job_image_url" not in st.session_state:
            st.session_state.latest_job_image_url = None    

        with st.form("job_form"):
            title = st.text_input("Job Title", placeholder="e.g. Senior Python Developer")
            description = st.text_area("Job Description", height=100)
            requirements = st.text_area("Key Requirements", placeholder="e.g. Python, CrewAI, AWS")
            duration = st.slider("Application Window (Minutes)", min_value=1, max_value=60, value=2)
            
            submitted = st.form_submit_button("Post Job & Start Timer")
            
            if submitted and title:
                # 1. Save to Database
                add_job(title, description, requirements, minutes_open=duration)
                st.success(f"✅ Job '{title}' posted! Applications close in {duration} minutes.")
                
                # 2. GENERATE CONTENT & IMAGE (Takes longer now)
                with st.spinner("🎨 AI Marketing Agent is writing the post AND generating a unique image... (approx 10s)"):
                    # Generate Text
                    ai_post = generate_viral_linkedin_post(title, requirements, description)
                    st.session_state.latest_job_post = ai_post
                    
                    # Generate Image
                    ai_image_url = generate_job_image(title, requirements)
                    st.session_state.latest_job_image_url = ai_image_url
                    
                    st.toast("Draft & Image Ready!", icon="✨")    

        # --- SOCIAL MEDIA & JOB BOARD ASSISTANT ---
        if st.session_state.latest_job_post:
            st.markdown("---")
            st.subheader("📢 Multi-Platform Distributor (Text + Image)")
            st.caption("Follow the 2 steps below to post complete content.")    

            # Create columns for Image vs Text
            col_img, col_text = st.columns([2, 3], gap="medium")    

            with col_img:
                st.markdown("#### 1. Get Image")
                if st.session_state.latest_job_image_url:
                    st.image(st.session_state.latest_job_image_url, use_container_width=True)
                    st.info("👉 **Right-click image above** and select **'Copy Image'** first.")
                else:
                    st.error("Image generation failed.")    

            with col_text:
                st.markdown("#### 2. Copy Text & Open Site")
                st.text_area("Job Announcement Draft", value=st.session_state.latest_job_post, height=250, label_visibility="collapsed")
                
                # PREPARE JAVASCRIPT TEXT
                js_text = st.session_state.latest_job_post.replace("\n", "\\n").replace("'", "\\'").replace('"', '\\"')
                
                # THE COMMAND CENTER BUTTONS (Same as before)
                components.html(f"""
                    <html>
                        <head>
                            <style>
                                .btn-container {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; }}
                                .job-btn {{
                                    color: white; padding: 10px 15px; border: none; border-radius: 6px;
                                    font-family: sans-serif; font-size: 13px; cursor: pointer;
                                    text-decoration: none; display: flex; align-items: center; font-weight: bold;
                                    transition: transform 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                                }}
                                .job-btn:hover {{ transform: translateY(-2px); opacity: 0.9; }}
                                .linkedin {{ background-color: #0077b5; }}
                                .naukri {{ background-color: #2d2d2d; border-bottom: 3px solid #f05537; }}
                                .glassdoor {{ background-color: #0caa41; }}
                                .internshala {{ background-color: #1295c9; }}
                                .twitter {{ background-color: #000000; }}
                                #msg {{
                                    color: #2e7d32; font-family: sans-serif; font-weight: bold; margin-top: 10px;
                                    display: none; padding: 8px; background: #e8f5e9; border-radius: 4px; font-size: 12px;
                                }}
                            </style>
                        </head>
                        <body>
                            <div class="btn-container">
                                <a class="job-btn linkedin" onclick="postTo('https://www.linkedin.com/feed/?shareActive=true')">🔹 LinkedIn</a>
                                <a class="job-btn naukri" onclick="postTo('https://www.naukri.com/recruit/login')">🇮🇳 Naukri</a>
                                <a class="job-btn glassdoor" onclick="postTo('https://www.glassdoor.com/employers/')">🚪 Glassdoor</a>
                                <a class="job-btn twitter" onclick="postTo('https://twitter.com/intent/tweet')">✖️ Twitter/X</a>
                            </div>
                            <div id="msg">✅ Text copied! Opening site... Paste image (Ctrl+V) next.</div>
                            <script>
                                function postTo(url) {{
                                    const text = "{js_text}";
                                    navigator.clipboard.writeText(text).then(function() {{
                                        document.getElementById('msg').style.display = 'block';
                                        setTimeout(function() {{ window.open(url, '_blank'); }}, 300);
                                    }});
                                }}
                            </script>
                        </body>
                    </html>
                """, height=180)    
    

                
    # --- TAB 2: LIVE TRACKING ---
    with tab2:
        st.header("Live Pipeline")
        
        if st.button("Refresh Data"):
            st.rerun()    

        conn = get_db_connection()
        jobs_df = pd.read_sql("SELECT id, title, status, deadline FROM jobs", conn) # Changed query to show ALL jobs, not just OPEN
        
        if not jobs_df.empty:
            job_options = {f"{row['title']} (ID: {row['id']}) - {row['status']}": row['id'] for index, row in jobs_df.iterrows()}
            selected_label = st.selectbox("Filter by Job", list(job_options.keys()))
            job_id = job_options[selected_label]
            
            # --- NEW: DELETE JOB SECTION ---
            with st.expander("🗑️ Danger Zone: Manage Job"):
                st.warning(f"Warning: This will permanently delete '{selected_label}' and all its candidate data.")
                col_del1, col_del2 = st.columns([1, 4])
                with col_del1:
                    if st.button("Delete Job Permanently", type="primary"):
                        success = delete_job_permanently(job_id)
                        if success:
                            st.success("Job Deleted!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to delete.")
            # -------------------------------    

            # Timer Logic
            selected_job = jobs_df[jobs_df['id'] == job_id].iloc[0]
            
            # Only show timer if status is OPEN
            if selected_job['status'] == 'OPEN':
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
            else:
                st.info("ℹ️ This job is closed or archived.")    

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
            st.info("No jobs found.")
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
                        # 1. Get Job Title
                        job_title = conn.execute("SELECT title FROM jobs WHERE id=?", (row['job_id'],)).fetchone()['title']

                        # 2. Send Rejection Email
                        with st.spinner("Sending Rejection Email..."):
                            send_rejection_email(row['email'], row['name'], job_title)

                            # 3. Update Status
                            conn.execute("UPDATE candidates SET status='REJECTED_FINAL' WHERE id=?", (row['id'],))
                            conn.commit()

                            st.toast(f"Rejection sent to {row['name']}", icon="📉")
                            time.sleep(1)
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

    