import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "hr@hireos.ai") 
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "mock_password")

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

# --- SPECIFIC EMAILS ---

def send_shortlist_email(candidate_email, candidate_name, job_title):
    """
    Sends the invite to the AI Interview Portal.
    """
    subject = f"Update on your application for {job_title} - HIRE_OS"
    
    # Points to Port 8503/8502 (Candidate Portal) - Make sure this matches your running port!
    portal_link = "http://localhost:8503"
    
    body = f"""
    Dear {candidate_name},

    Great news! Your profile has been shortlisted for the {job_title} position at HIRE_OS.

    We were impressed with your resume and would like to invite you to the next round: An automated AI Technical Interview.

    NEXT STEPS:
    1. Log in to the Candidate Portal: {portal_link}
    2. Enter your email ({candidate_email}) to access the interview.
    3. Complete the chat assessment.

    Good luck!
    The HIRE_OS Recruitment Team
    """
    return send_email(candidate_email, subject, body)

def send_meeting_invite(candidate_email, candidate_name, job_title, meeting_link, meeting_time):
    """
    Sends a Google Meet invitation for the final HR round.
    """
    subject = f"Final HR Interview Invitation - {job_title}"
    
    body = f"""
    Dear {candidate_name},

    Congratulations! You have successfully cleared our AI Technical Assessment. 
    We would like to invite you to the final Human HR Interview.

    📅 Date & Time: {meeting_time}
    🔗 Meeting Link: {meeting_link}

    Please ensure you are in a quiet environment.

    Best regards,
    The HIRE_OS Recruitment Team
    """
    return send_email(candidate_email, subject, body)

def send_offer_letter(candidate_email, candidate_name, job_title):
    """
    Sends the official Job Offer email.
    """
    subject = f"🎉 Job Offer: {job_title} at HIRE_OS"
    
    body = f"""
    Dear {candidate_name},

    We are delighted to offer you the position of {job_title} at HIRE_OS!

    Your performance in both the AI Technical Assessment and the HR Interview was outstanding. We believe you will be a great addition to our team.

    NEXT STEPS:
    Please reply to this email within 48 hours to accept the offer.
    
    Welcome aboard!

    Sincerely,
    The HIRE_OS Team
    """
    return send_email(candidate_email, subject, body)

def send_rejection_email(candidate_email, candidate_name, job_title):
    """
    Sends a polite, professional rejection email.
    """
    subject = f"Update on your application for {job_title} - HIRE_OS"
    
    body = f"""
    Dear {candidate_name},

    Thank you for giving us the opportunity to consider your application for the {job_title} position at HIRE_OS.

    We have reviewed your qualifications and experience. While your background is impressive, we have decided to move forward with other candidates who more closely match our current requirements for this specific role.

    We will keep your resume in our database and may contact you if a suitable opening arises in the future.

    We wish you the best in your job search.

    Sincerely,
    The HIRE_OS Recruitment Team
    """
    return send_email(candidate_email, subject, body)