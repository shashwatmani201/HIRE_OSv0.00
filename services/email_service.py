import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Configuration (Load from env vars or use defaults)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "hr@hireos.ai") 
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "mock_password")



# ... (Keep your existing imports and send_email function) ...

def send_shortlist_email(candidate_name, candidate_email, job_title):
    """
    Sends an email inviting the candidate to the AI Interview.
    """
    subject = f"Update on your application for {job_title} - HIRE_OS"
    
    body = f"""
    Dear {candidate_name},

    Great news! Your profile has been shortlisted for the {job_title} position at HIRE_OS.

    We were impressed with your resume and would like to invite you to the next round: An automated AI Technical Interview.

    NEXT STEPS:
    1. Log in to the Candidate Portal: http://localhost:8501
    2. Enter your email ({candidate_email}) to access the interview.
    3. Complete the chat assessment.

    Good luck!
    
    Best regards,
    The HIRE_OS Recruitment Team
    """
    
    # Reuse your existing send_email logic
    return send_email(candidate_email, subject, body)

def send_email(to_email, subject, body):
    """
    Sends a generic email using SMTP.
    """
    try:
        # If no valid password is set, use Mock Mode (print to terminal)
        if not SENDER_PASSWORD or "mock" in SENDER_PASSWORD:
            print(f"\n📧 [MOCK EMAIL SERVICE]")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Body: {body}\n")
            return True

        # Real Email Sending Logic
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Email Failed: {e}")
        return False

def send_offer_letter(candidate_name, candidate_email, job_title):
    """
    Constructs and sends the Offer Letter.
    """
    subject = f"Offer of Employment: {job_title} at HIRE_OS"
    body = f"""
    Dear {candidate_name},

    We are pleased to offer you the position of {job_title} at HIRE_OS!

    Your technical interview results were impressive, and we believe you will be a great asset to the team.

    Please reply to this email to discuss the start date and compensation details.

    Welcome aboard!
    
    Sincerely,
    The HIRE_OS Team
    """
    return send_email(candidate_email, subject, body)