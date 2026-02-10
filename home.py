import streamlit as st
import base64

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="HIRE_OS | Autonomous Recruitment",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* 1. BACKGROUND GRADIENT */
    .stApp {
        background: radial-gradient(circle at 10% 20%, #0f1219 0%, #000000 90%);
    }

    /* 2. NEON HEADLINE */
    .hero-title {
        font-family: 'Inter', sans-serif;
        font-size: 4.2rem !important;
        font-weight: 900;
        line-height: 1.1;
        background: -webkit-linear-gradient(0deg, #00C9FF, #92FE9D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(0, 201, 255, 0.3);
        margin-bottom: 10px;
    }

    .hero-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.3rem;
        color: #cfcfcf;
        margin-bottom: 2rem;
        font-weight: 300;
    }

    /* 3. CARD STYLING */
    .custom-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 25px;
        height: 100%;
        transition: all 0.3s ease-in-out;
    }
    .custom-card:hover {
        transform: translateY(-8px);
        border: 1px solid #00C9FF;
        box-shadow: 0 10px 40px -10px rgba(0, 201, 255, 0.2);
        background: rgba(0, 201, 255, 0.05);
    }
    
    /* 4. BADGES */
    .tech-badge {
        background: rgba(0, 201, 255, 0.1);
        border: 1px solid rgba(0, 201, 255, 0.3);
        color: #00C9FF;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- HERO SECTION ---
col1, col2 = st.columns([1.2, 1], gap="large")

with col1:
    st.write("") 
    st.write("") 
    st.markdown('<div class="hero-title">Hire Faster.<br>Hire Smarter.</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">The autonomous AI recruitment suite. HIRE_OS screens, interviews, and ranks talent while you sleep.</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="display: flex; gap: 10px; margin-bottom: 30px;">
        <span class="tech-badge">⚡ POWERED BY CREWAI</span>
        <span class="tech-badge">🧠 BUILT WITH LANGCHAIN</span>
        <span class="tech-badge">🚀 V1.0 PRODUCTION</span>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # --- VIDEO BACKGROUND HACK ---
    # We read the file and embed it as HTML to remove controls & add blending
    try:
        video_path = "assets/promo_video.mp4"
        with open(video_path, "rb") as f:
            video_bytes = f.read()
            video_b64 = base64.b64encode(video_bytes).decode()

        st.markdown(
            f"""
            <style>
            .video-container {{
                mask-image: linear-gradient(to bottom, black 80%, transparent 100%);
                -webkit-mask-image: linear-gradient(to bottom, black 80%, transparent 100%);
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 0 50px rgba(0, 201, 255, 0.1);
            }}
            </style>
            <div class="video-container">
                <video width="100%" autoplay loop muted playsinline style="border-radius: 20px;">
                    <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
                </video>
            </div>
            """,
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        st.error("Video file not found. Please check assets/promo_video.mp4")

# --- ACTION GRID ---
st.write("") 
st.markdown("### 🚀 Launch Your Workflow")

c1, c2, c3 = st.columns(3, gap="medium")

# Card 1: Admin
with c1:
    st.markdown("""
    <div class="custom-card">
        <div style="font-size: 2rem;">👮‍♂️</div>
        <div style="font-size: 1.2rem; font-weight: 700; color: white;">Admin Console</div>
        <div style="font-size: 0.9rem; color: #a0a0a0;">Post jobs, track pipelines, and view AI insights.</div>
    </div>
    """, unsafe_allow_html=True)
    st.write("")
    if st.button("Access Admin Suite →", type="primary", use_container_width=True):
        st.switch_page("pages/1_Admin_Dashboard.py")

# Card 2: Apply
with c2:
    st.markdown("""
    <div class="custom-card">
        <div style="font-size: 2rem;">⚡</div>
        <div style="font-size: 1.2rem; font-weight: 700; color: white;">Apply Now</div>
        <div style="font-size: 0.9rem; color: #a0a0a0;">Friction-free portal for candidates.</div>
    </div>
    """, unsafe_allow_html=True)
    st.write("")
    if st.button("Apply in Seconds →", use_container_width=True):
        st.switch_page("pages/2_Apply_Portal.py")

# Card 3: Interview
with c3:
    st.markdown("""
    <div class="custom-card">
        <div style="font-size: 2rem;">🎙️</div>
        <div style="font-size: 1.2rem; font-weight: 700; color: white;">AI Interviewer</div>
        <div style="font-size: 0.9rem; color: #a0a0a0;">"Alex" conducts full technical interviews.</div>
    </div>
    """, unsafe_allow_html=True)
    st.write("")
    if st.button("Begin AI Interview →", use_container_width=True):
        st.switch_page("pages/3_Interview_Portal.py")

# --- FOOTER ---
st.write("")
st.divider()
st.markdown('<div style="text-align: center; color: #666; font-size: 0.8rem;">REDEFINING HIRING WITH AUTONOMOUS AI • © 2026 HIRE_OS</div>', unsafe_allow_html=True)