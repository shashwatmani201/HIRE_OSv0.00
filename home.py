import streamlit as st

st.set_page_config(
    page_title="HIRE_OS Portal",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 Welcome to HIRE_OS")
st.subheader("The AI-Powered Recruitment Suite")

st.markdown("""
### Please select a portal from the sidebar:

* **🕵️ Admin Dashboard:** For HR Managers to post jobs and track candidates.
* **📝 Apply Portal:** For candidates to view jobs and submit resumes.
* **🤖 Interview Portal:** For shortlisted candidates to take their AI Interview.

---
*Powered by CrewAI & LangChain*
""")