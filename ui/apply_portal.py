import streamlit as st
import pandas as pd
import sys
import os
import re  # <--- Added for Email Validation

# Add parent directory to path to import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.database_manager import add_candidate, get_db_connection
from src.interview_bot import get_interview_chain, save_transcript

st.set_page_config(page_title="Career Portal", page_icon="🚀")

# --- SESSION STATE INITIALIZATION ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "interview_active" not in st.session_state:
    st.session_state.interview_active = False
if "conversation_chain" not in st.session_state:
    st.session_state.conversation_chain = None

# --- SIDEBAR: LOGIN ---
with st.sidebar:
    st.title("Candidate Login")
    email_login = st.text_input("Check Application Status (Email)")
    check_btn = st.button("Check Status")
    
    candidate_info = None
    if check_btn and email_login:
        conn = get_db_connection()
        # Fetch candidate info along with job details
        query = """
            SELECT c.id, c.name, c.status, j.title, j.requirements 
            FROM candidates c
            JOIN jobs j ON c.job_id = j.id
            WHERE c.email = ?
        """
        candidate_info = conn.execute(query, (email_login,)).fetchone()
        conn.close()
        
        if candidate_info:
            st.session_state.candidate_id = candidate_info['id']
            st.session_state.candidate_name = candidate_info['name']
            st.session_state.job_title = candidate_info['title']
            st.session_state.job_reqs = candidate_info['requirements']
            st.session_state.status = candidate_info['status']
            st.success(f"Welcome back, {candidate_info['name']}!")
        else:
            st.error("Email not found.")

# --- MAIN AREA ---

# SCENARIO 1: INTERVIEW MODE (If Status is SHORTLISTED)
if "status" in st.session_state and st.session_state.status == "SHORTLISTED":
    st.header(f"AI Technical Interview: {st.session_state.job_title}")
    st.info("You have been shortlisted! Please complete this short technical chat assessment.")
    
    # Initialize Interview Chain if not ready
    if st.session_state.conversation_chain is None:
        st.session_state.conversation_chain = get_interview_chain(
            st.session_state.job_title, 
            st.session_state.job_reqs
        )
        # Initial greeting from AI
        greeting = st.session_state.conversation_chain.predict(input="Hi, I'm ready for the interview.")
        st.session_state.chat_history.append({"role": "assistant", "content": greeting})

    # Display Chat History
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User Input
    if user_input := st.chat_input("Type your answer here..."):
        # 1. Display User Message
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        # 2. Get AI Response
        with st.spinner("Interviewer is thinking..."):
            ai_response = st.session_state.conversation_chain.predict(input=user_input)
        
        # 3. Display AI Response
        with st.chat_message("assistant"):
            st.markdown(ai_response)
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})

    # End Interview Button
    if st.button("Finish Interview"):
        # Compile Transcript
        transcript_text = ""
        for msg in st.session_state.chat_history:
            transcript_text += f"{msg['role'].upper()}: {msg['content']}\n\n"
            
        save_transcript(st.session_state.candidate_id, transcript_text)
        st.success("Interview submitted successfully! HR will review your transcript.")
        st.session_state.status = "INTERVIEW_COMPLETED" # Update local state to hide chat
        st.rerun()

# SCENARIO 2: ALREADY COMPLETED
elif "status" in st.session_state and st.session_state.status == "INTERVIEW_COMPLETED":
    st.success("You have completed the interview stage. We will be in touch shortly.")

# SCENARIO 3: STANDARD APPLICATION (Default)
else:
    st.title("🚀 Join Our Team")
    
    # 1. Fetch Open Jobs
    conn = get_db_connection()
    jobs = conn.execute("SELECT id, title FROM jobs WHERE status='OPEN'").fetchall()
    conn.close()

    if not jobs:
        st.warning("No positions are currently open. Please check back later.")
    else:
        # Create mapping for Dropdown
        job_options = {job['title']: job['id'] for job in jobs}
        selected_job_title = st.selectbox("Select Position", list(job_options.keys()))
        
        # Get the ID for the form
        job_id = job_options[selected_job_title]
        
        st.write(f"Applying for: **{selected_job_title}**")
        st.markdown("---")
        
        # --- NEW VALIDATED FORM ---
        with st.form("application_form"):
            st.subheader("Apply Now")
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
                    st.error("⚠️ Please enter a valid email address (e.g., user@example.com).")

                else:
                    # 3. DUPLICATE CHECK: Has this email already applied for this job?
                    conn = get_db_connection()
                    existing_app = conn.execute(
                        "SELECT id FROM candidates WHERE email = ? AND job_id = ?",
                        (email, job_id)
                    ).fetchone()
                    conn.close()

                    if existing_app:
                        st.warning("🚫 You have already applied for this position! Please wait for a response.")
                    
                    else:
                        # Save the file
                        # Create directory if it doesn't exist
                        os.makedirs("data/resumes", exist_ok=True)
                        
                        file_path = os.path.join("data/resumes", f"{job_id}_{name.replace(' ', '_')}.pdf")
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # Add to Database
                        try:
                            add_candidate(job_id, name, email, file_path)
                            st.success(f"✅ Application Submitted Successfully! Good luck, {name}.")
                            st.balloons()
                        except Exception as e:
                            st.error(f"An error occurred: {e}")