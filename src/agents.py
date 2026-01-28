import os
import json
import re
import sys
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from langchain_openai import ChatOpenAI
from pypdf import PdfReader
from openai import OpenAI  # <--- Need this for DALL-E

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.database_manager import get_db_connection
from services.email_service import send_shortlist_email  # <--- Imported Email Service


# --- 1. DEFINE TOOLS NATIVELY ---

class ResumeReadTool(BaseTool):
    name: str = "Read Resume PDF"
    description: str = "Reads a PDF resume from a file path. Input must be the full file path string."

    def _run(self, file_path: str) -> str:
        try:
            if not os.path.exists(file_path):
                return f"Error: File not found at {file_path}"
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            return f"Error reading PDF: {e}"

class TranscriptReadTool(BaseTool):
    name: str = "Read Interview Transcript"
    description: str = "Reads the text content of an interview transcript file. Input must be the file path."

    def _run(self, file_path: str) -> str:
        try:
            if not os.path.exists(file_path):
                return f"Error: File not found at {file_path}"
            with open(file_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"Error reading transcript: {e}"

# --- 2. AGENT FACTORY ---

def create_screener_agent():
    return Agent(
        role='Senior Technical Recruiter',
        goal='Analyze resumes to filter the top 10% of candidates.',
        backstory="""You are an expert HR recruiter. You look for specific keywords and project experience.""",
        tools=[ResumeReadTool()],
        verbose=True,
        llm=ChatOpenAI(model_name="gpt-4o", temperature=0)
    )

def create_grader_agent():
    return Agent(
        role='Chief Technology Officer',
        goal='Evaluate interview transcripts and make hiring decisions.',
        backstory="""You are a CTO who values deep technical understanding.""",
        tools=[TranscriptReadTool()],
        verbose=True,
        llm=ChatOpenAI(model_name="gpt-4o", temperature=0)
    )

# --- 3. ORCHESTRATION ---

def run_resume_screening(job_id):
    conn = get_db_connection()
    
    # Get Job
    job = conn.execute("SELECT title, description, requirements FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job:
        conn.close()
        return "Job not found."
    
    job_context = f"Job Title: {job['title']}\nDescription: {job['description']}\nRequirements: {job['requirements']}"

    # Get Candidates (Added 'email' to the query so we can send the notification)
    candidates = conn.execute("SELECT id, name, email, resume_path FROM candidates WHERE job_id=? AND status='APPLIED'", (job_id,)).fetchall()
    
    if not candidates:
        conn.close()
        return "No pending candidates to screen."

    screener = create_screener_agent()
    results_log = []

    print(f"🕵️ Starting screening for {len(candidates)} candidates...")

    for cand in candidates:
        cand_id = cand['id']
        name = cand['name']
        email = cand['email']  # Capture email
        resume_path = cand['resume_path']

        print(f"Processing {name} (File: {resume_path})...")

        task = Task(
            description=f"""
            1. Read the resume at path: '{resume_path}'.
            2. Match against: {job_context}
            3. Output JSON with score (0-100) and summary.
            """,
            expected_output="JSON with score and summary",
            agent=screener
        )

        crew = Crew(agents=[screener], tasks=[task], verbose=True)
        result = crew.kickoff()
        
        # Simple Parse
        try:
            output_str = str(result)
            json_match = re.search(r'\{.*\}', output_str, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                score = data.get('score', 0)
                summary = data.get('summary', "Parsed summary.")
            else:
                score = 0
                summary = "Parsing failed."
        except:
            score = 0
            summary = "Error parsing result."

        # Determine Status
        new_status = 'SHORTLISTED' if score >= 70 else 'REJECTED'
        
        # Update Database
        conn.execute("UPDATE candidates SET resume_score=?, resume_summary=?, status=? WHERE id=?", 
                     (score, summary, new_status, cand_id))
        conn.commit()

        # --- EMAIL NOTIFICATION TRIGGER ---
        if new_status == "SHORTLISTED":
            print(f"📧 Sending Shortlist Email to {name}...")
            try:
                send_shortlist_email(name, email, job['title'])
                results_log.append(f"{name}: {score} (SHORTLISTED & Emailed)")
            except Exception as e:
                print(f"❌ Failed to send email: {e}")
                results_log.append(f"{name}: {score} (SHORTLISTED - Email Failed)")
        else:
            results_log.append(f"{name}: {score} ({new_status})")
        # ----------------------------------

    conn.close()
    return "\n".join(results_log)

def run_interview_evaluation(job_id):
    conn = get_db_connection()
    job = conn.execute("SELECT title, requirements FROM jobs WHERE id=?", (job_id,)).fetchone()
    
    # Fetch candidates who are ready for evaluation
    # Note: We also include 'FINALIST' here so you can re-run it to fix/update scores if needed
    candidates = conn.execute("""
        SELECT id, name, interview_transcript_path 
        FROM candidates 
        WHERE job_id=? AND (status='INTERVIEW_COMPLETED' OR status='FINALIST')
    """, (job_id,)).fetchall()

    if not candidates:
        conn.close()
        return "No candidates ready for evaluation."

    grader = create_grader_agent()
    results_log = []

    print(f"👨‍💻 Evaluating {len(candidates)} transcripts...")

    for cand in candidates:
        cand_id = cand['id']
        name = cand['name']
        transcript_path = cand['interview_transcript_path']
        
        if not transcript_path or not os.path.exists(transcript_path):
            print(f"Skipping {name}: No transcript found.")
            continue

        print(f"Processing {name}...")
        
        task = Task(
            description=f"""
            1. Read the interview transcript at: '{transcript_path}'.
            2. Evaluate candidate '{name}' for the role of '{job['title']}'.
            3. Requirements: {job['requirements']}.
            
            OUTPUT FORMAT (Strict JSON, no markdown):
            {{
                "score": <integer_0_to_100>,
                "feedback": "<2-sentence_justification>",
                "decision": "<FINALIST_or_REJECTED>"
            }}
            """,
            expected_output="JSON object with score, feedback, and decision",
            agent=grader
        )

        crew = Crew(agents=[grader], tasks=[task], verbose=True)
        result = crew.kickoff()
        
        # --- PARSING LOGIC ---
        try:
            output_str = str(result)
            json_match = re.search(r'\{.*\}', output_str, re.DOTALL)
            
            if json_match:
                data = json.loads(json_match.group())
                score = data.get('score', 0)
                feedback = data.get('feedback', "No feedback provided.")
                decision = str(data.get('decision', "REJECTED")).upper()
            else:
                score = 50
                feedback = "Manual Review Needed (Parse Failed)"
                decision = "FINALIST" 
                
        except Exception as e:
            print(f"Error parsing: {e}")
            score = 0
            feedback = f"Error: {e}"
            decision = "REJECTED"

        # Determine Final Status
        final_status = "FINALIST" if "FINALIST" in decision else "REJECTED"

        # Update Database with REAL Score
        conn.execute("""
            UPDATE candidates 
            SET interview_score = ?, interview_feedback = ?, status = ?
            WHERE id = ?
        """, (score, feedback, final_status, cand_id))
        
        conn.commit()
        results_log.append(f"{name}: {score}/100 -> {final_status}")

    conn.close()
    return "\n".join(results_log) 


def generate_viral_linkedin_post(job_title, requirements, description):
    """
    Uses GPT-4o to write a high-engagement LinkedIn post with the Apply Link.
    """
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0.7)
    
    # 🔗 DEFINE THE LINK (Change this if you deploy to the cloud later)
    portal_link = "http://localhost:8501" 
    
    prompt = f"""
    You are an expert Social Media Manager for a tech startup called HIRE_OS.
    
    Task: Write a viral, engaging, and professional LinkedIn post to hire a '{job_title}'.
    
    Context:
    - Job Description: {description}
    - Key Requirements: {requirements}
    - Link to Apply: {portal_link}
    
    Guidelines:
    1. Start with a strong "Hook" (e.g., Are you the Python wizard we need?).
    2. Use bullet points for benefits.
    3. Emphasize that the interview is AI-Automated (Instant feedback!).
    4. **CRITICAL:** You MUST include the application link: {portal_link} clearly at the end.
    5. Use emojis (🚀, 🔗) and hashtags.
    
    Output: Just the post text.
    """
    
    response = llm.predict(prompt)
    return response



def generate_job_image(job_title, requirements):
    """
    Uses DALL-E 3 to generate a professional, tech-themed image for the job post.
    Returns the image URL.
    """
    client = OpenAI() 

    visual_prompt = f"""
    A professional, futuristic, and vibrant digital illustration suitable for a LinkedIn job announcement post.
    The central theme should visually represent the role of a '{job_title}'.
    
    Incorporate abstract visual elements related to these tech stacks: {requirements}. 
    (e.g., If Python, show stylized snakes or code structures; if Cloud, show interconnected data centers).
    
    Style: Clean, modern tech art.
    Color Palette: Professional deep blues, purples, and electric neon accents.
    
    Constraint: Do not include any actual text letters or words in the image itself.
    """

    try:
        print(f"🎨 Generating image for {job_title}...")
        response = client.images.generate(
            model="dall-e-3",
            prompt=visual_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        print(f"❌ Image generation failed: {e}")
        return "https://cdn.pixabay.com/photo/2018/05/08/08/44/artificial-intelligence-3382507_1280.jpg"