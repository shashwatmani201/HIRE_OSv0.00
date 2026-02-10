import streamlit as st
import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.database_manager import get_db_connection
from src.interview_bot import get_interview_chain, save_transcript # <--- IMPORT THE SMART AGENT

st.set_page_config(page_title="HIRE_OS Interview", layout="centered")

# --- SESSION STATE ---
if "candidate_data" not in st.session_state:
    st.session_state.candidate_data = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "interview_chain" not in st.session_state:
    st.session_state.interview_chain = None

# ==========================================
# 🔐 LOGIN SCREEN
# ==========================================
def login_candidate():
    st.title("🔐 Candidate Login")
    st.info("Please enter the email address you used to apply.")
    
    with st.form("candidate_login"):
        raw_email = st.text_input("Email Address")
        submitted = st.form_submit_button("Start Interview")
        
        if submitted and raw_email:
            email = raw_email.strip().lower() # Auto-clean input
            conn = get_db_connection()
            
            # 1. Fetch Candidate + Job Details
            query = """
                SELECT c.id, c.name, c.email, c.status, j.title, j.requirements 
                FROM candidates c
                JOIN jobs j ON c.job_id = j.id
                WHERE LOWER(c.email) = ?
            """
            user = conn.execute(query, (email,)).fetchone()
            conn.close()
            
            if user:
                # Check Status
                if user['status'] in ['SHORTLISTED', 'INTERVIEW_PENDING']:
                    st.session_state.candidate_data = dict(user)
                    st.success(f"Welcome, {user['name']}!")
                    time.sleep(1)
                    st.rerun()
                elif user['status'] == 'INTERVIEW_COMPLETED':
                    st.warning("You have already completed your interview. HR will contact you soon.")
                else:
                    st.error(f"Access Denied. Current Status: {user['status']}")
            else:
                st.error("Email not found in our records.")

# ==========================================
# 💬 SMART INTERVIEW SCREEN
# ==========================================
def interview_screen():
    cand = st.session_state.candidate_data
    
    st.header(f"🤖 AI Technical Interview: {cand['title']}")
    st.caption(f"Candidate: {cand['name']}")
    st.divider()

    # 1. Initialize the SMART BRAIN (Only once)
    if st.session_state.interview_chain is None:
        st.session_state.interview_chain = get_interview_chain(cand['title'], cand['requirements'])
        
        # Trigger the first greeting automatically
        with st.spinner("Interviewer is connecting..."):
            greeting = st.session_state.interview_chain.predict(input="Hello, I am ready.")
            st.session_state.chat_history.append({"role": "assistant", "content": greeting})

    # 2. Display Chat History
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 3. User Input
    if user_input := st.chat_input("Type your answer here..."):
        # Show User Message
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        # Get AI Response (SMART AGENT)
        with st.spinner("Thinking..."):
            ai_response = st.session_state.interview_chain.predict(input=user_input)
        
        # Show AI Message
        with st.chat_message("assistant"):
            st.markdown(ai_response)
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})

    # 4. Finish Button
    if st.button("End Interview & Submit"):
        # Save transcript string
        transcript = ""
        for msg in st.session_state.chat_history:
            transcript += f"{msg['role'].upper()}: {msg['content']}\n\n"
            
        save_transcript(cand['id'], transcript)
        st.success("✅ Interview Submitted! You may close this tab.")
        st.session_state.candidate_data = None # Logout
        time.sleep(3)
        st.rerun()

# ==========================================
# 🚀 APP CONTROLLER
# ==========================================
if st.session_state.candidate_data is None:
    login_candidate()
else:
    interview_screen()