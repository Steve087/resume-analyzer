import os
from google import genai
from google.genai import types
from pydantic import BaseModel
from llm_parser import ResumeData 
from tenacity import retry, stop_after_attempt, wait_exponential

client = genai.Client()

class RankingResult(BaseModel):
    score: int
    explanation: str

#@retry(wait=wait_exponential(multiplier=2, min=5, max=30), stop=stop_after_attempt(5))
def score_candidate(resume: ResumeData, job_description: str) -> RankingResult:
    system_prompt = """
    You are an expert technical recruiter. You will be given a candidate's structured resume data and a Job Description.
    Evaluate the candidate's fit for the role.
    
    Scoring rules:
    - 90-100: Exceptional match. Has almost all required skills and experience.
    - 70-89: Strong match. Has core skills but missing nice-to-haves.
    - 50-69: Partial match. Missing key skills.
    - 0-49: Poor match. Do not recommend.
    
    Be objective and base your score purely on the provided text.
    """

    # Anonymize data to prevent LLM bias
    resume_anon = resume.model_copy()
    resume_anon.name = "[REDACTED]"
    resume_anon.email = "[REDACTED]"
    resume_anon.phone = "[REDACTED]"
    resume_anon.location = "[REDACTED]" 

    resume_json = resume_anon.model_dump_json()

    # We use the heavier Pro model for logic and reasoning
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=f"Job Description:\n{job_description}\n\nCandidate Resume JSON:\n{resume_json}",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=RankingResult,
            temperature=0.2 
        ),
    )

    return RankingResult.model_validate_json(response.text)