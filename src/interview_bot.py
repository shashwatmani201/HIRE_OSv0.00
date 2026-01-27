import os
from dotenv import load_dotenv  # <--- Add this import
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate

# Load environment variables (API Key)
load_dotenv()  # <--- Add this function call

# Configuration
LLM_MODEL = "gpt-4o" 

def get_interview_chain(job_title, job_requirements):
    # ... (rest of the code remains exactly the same)
    
    # Ensure key is loaded (Optional safety check)
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment.")

    template = f"""
    You are an expert Technical Interviewer for the role of {job_title}.
    The candidate requirements are: {job_requirements}.
    
    Your goal is to assess the candidate's technical depth, problem-solving skills, and communication.
    
    Guidelines:
    - Start by welcoming the candidate and asking them to introduce themselves.
    - Ask 1 technical question at a time.
    - If their answer is vague, ask a follow-up digging deeper.
    - If their answer is correct, move to a harder concept.
    - Keep the tone professional but encouraging.
    - Do not give away answers.
    - After 5-7 exchanges, thank them and conclude the interview.
    
    Current Conversation:
    {{history}}
    
    Candidate: {{input}}
    Interviewer:"""
    
    prompt = PromptTemplate(
        input_variables=["history", "input"],
        template=template
    )

    llm = ChatOpenAI(model_name=LLM_MODEL, temperature=0.7)

    memory = ConversationBufferMemory(ai_prefix="Interviewer", human_prefix="Candidate")

    conversation = ConversationChain(
        prompt=prompt,
        llm=llm,
        memory=memory,
        verbose=True
    )
    
    return conversation

def save_transcript(candidate_id, transcript_text):
    """
    Saves the final interview transcript to a file and updates the DB.
    """
    from src.database_manager import get_db_connection
    
    # Save to file
    filename = f"data/transcripts/interview_{candidate_id}.txt"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, "w") as f:
        f.write(transcript_text)
        
    # Update DB
    conn = get_db_connection()
    conn.execute(
        "UPDATE candidates SET interview_transcript_path = ?, status = 'INTERVIEW_COMPLETED' WHERE id = ?",
        (filename, candidate_id)
    )
    conn.commit()
    conn.close()
    return filename