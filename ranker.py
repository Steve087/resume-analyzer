import os
import instructor
from groq import Groq
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
from llm_parser import ResumeData 
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv() 

# 1. Initialize the Groq client wrapped with Instructor
client = instructor.from_groq(
    Groq(
        # base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("GROQ_API_KEY")),
    mode=instructor.Mode.JSON
)

# 2. Your Schema for the Output
class RankingResult(BaseModel):
    score: int
    category_breakdown: str = ""
    explanation: str
    strengths: list[str] = []
    gaps: list[str] = []
# At the top of score_candidate() in ranker.py

# 3. The Scoring Function
@retry(wait=wait_exponential(multiplier=2, min=4, max=30), stop=stop_after_attempt(3))
def score_candidate(resume: ResumeData, job_description: str) -> RankingResult:
    try:
        system_prompt = """
You are an expert technical recruiter evaluating candidates for a job.

You MUST score candidates using EXACTLY this breakdown — no exceptions:
- Skills Match: /35
- Projects: /25
- Work Experience: /25
- Certifications: /10
- Leadership: /5
- TOTAL: /100

SKILLS MATCH (35 points):
- Start at 35, deduct 7 for each REQUIRED skill missing, deduct 3 for each PREFERRED skill missing
- A skill counts as present if found ANYWHERE in skills, projects, or work history
- count Abbreviations of skills
- NEVER penalize a skill that appears anywhere in the resume

PROJECTS (25 points):
- 20-25: Deployed, real-world, directly relevant to JD
- 15-19: Relevant but not deployed or basic
- 5-14: Exist but unrelated to JD
- 0: No projects

WORK EXPERIENCE (25 points):
- 20-25: Directly relevant internship or job
- 12-19: Partially relevant experience
- 3-11: Unrelated work experience
- 0: No experience

CERTIFICATIONS (10 points):
- 8-10: Directly relevant to JD tech stack
- 4-7: Loosely related
- 0: None

LEADERSHIP (5 points):
- 5: Strong leadership
- 3-4: Good Leadership
- 1-2: Moderate leadership
- 0: None

RULES:
- Always output the breakdown as: Skills:X/35, Projects:X/25, Experience:X/25, Certs:X/10, Leadership:X/5
- Sum must equal the final score
- Base evaluation ONLY on what is explicitly stated
- Do not ask for more information
- Be deterministic and consistent
- Leadership ABSOLUTE MAXIMUM = 5. If your calculation exceeds 5, set it to 5. No exceptions.
CRITICAL RULES:
- Before listing a gap, verify the skill is NOT present in the extracted skills list
- If a skill appears anywhere in the resume, it is NOT a gap
- Only list something as a gap if you are 100 percent certain it is absent
- When uncertain, do not list it as a gap
"""

        # Anonymize data to prevent LLM bias (Excellent implementation!)
        resume_anon = resume.model_copy()
        resume_anon.name = "[REDACTED]"
        resume_anon.email = "[REDACTED]"
        resume_anon.phone = "[REDACTED]"
        resume_anon.location = "[REDACTED]" 

        # We can pass the dictionary structure straight into the chat messages list
        resume_dict = resume_anon.model_dump()

        # Call Groq utilizing Instructor to return a validated Pydantic object
        ranking_result_object = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            response_model=RankingResult, # Guarantees matching schema output
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user", 
                    "content": f"""Job Description:
{job_description}

Candidate Resume:
{resume_dict}

Score this candidate. Check skills, project tech stacks, and work history before marking anything missing."""
                }
            ],
            temperature=0.0 # Changed from 0.2 to 0.0 to ensure deterministic, consistent scoring!
        )
        return ranking_result_object
    except Exception as e:
        print(f"Raw error: {e}")
        raise


    