import os
import re
import instructor
from groq import Groq
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
from llm_parser import ResumeData
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

# --- Clients ---
ollama_client = instructor.from_openai(
    OpenAI(base_url="http://localhost:11434/v1", api_key="ollama"),
    mode=instructor.Mode.JSON
)

groq_client = instructor.from_groq(
    Groq(api_key=os.environ.get("GROQ_API_KEY")),
    mode=instructor.Mode.JSON
)

gemini_client = instructor.from_provider(
    "google/gemini-2.5-flash",
     mode=instructor.Mode.GENAI_STRUCTURED_OUTPUTS
)

# --- Schema ---
class RankingResult(BaseModel):
    score: int
    category_breakdown: str = ""
    explanation: str
    strengths: list[str] = []
    gaps: list[str] = []

# --- Helper ---
def parse_breakdown_sum(category_breakdown: str) -> int | None:
    numbers = re.findall(r'(\d+)/\d+', category_breakdown)
    if len(numbers) == 5:
        return sum(int(n) for n in numbers)
    return None

# --- Scoring Function ---
@retry(wait=wait_exponential(multiplier=2, min=4, max=30), stop=stop_after_attempt(3))
def score_candidate(resume: ResumeData, job_description: str, provider: str = "Ollama (Local)") -> RankingResult:
    try:
        if provider == "Groq (API)":
            client = groq_client
            model_name = "llama-3.3-70b-versatile"
        elif provider == "Gemini (API)":
            client = gemini_client
            model_name = None
        else:
            client = ollama_client
            model_name = "llama3.1:8b"

        system_prompt = """
You are an expert technical recruiter evaluating candidates for any job role.

Score using EXACTLY this breakdown — no exceptions:
- Skills Match: /35
- Projects: /25
- Work Experience: /25
- Certifications: /10
- Leadership: /5
- TOTAL: /100

SKILLS MATCH (35 points):
- Start at 35, deduct 7 per REQUIRED skill missing, deduct 3 per PREFERRED skill missing
- Check skills, projects, AND work history before marking any skill as missing
- Abbreviations count as full forms (DSA, OOP, ML, GCP, REST, CI/CD etc)
- Any LLM API (Gemini, Groq, Anthropic, Claude) = OpenAI API experience
- NEVER penalize a skill found anywhere in the resume

PROJECTS (25 points):
- 20-25: Deployed, real-world, directly relevant to JD
- 15-19: Relevant but basic or not deployed
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

LEADERSHIP (5 points — HARD CAP, never exceed 5):
- 5: Head or chairperson of any technical organization or club
- 3-4: Secretary, co-lead, or core member of technical forum or department club
- 2-3: Campus ambassador, community leader, organizer of technical events
- 1-2: Member of any club, volunteer, or holder of any recognized certificate
- 0: Nothing mentioned
- ABSOLUTE MAXIMUM = 5.

TIEBREAKER (when scores would be equal):
- Candidate with real internship ranks higher than one with only projects
- Candidate with more deployed projects ranks higher
- Never give the same final score to two candidates with clearly different profiles

BEFORE LISTING ANY GAP:
- Check skills, project tech stacks, and work history summaries
- Only list as a gap if 100% absent from ALL sources
- If unsure, do not list it as a gap

RULES:
- Output breakdown as: Skills:X/35, Projects:X/25, Experience:X/25, Certs:X/10, Leadership:X/5
- Base evaluation ONLY on what is provided
- Be deterministic and consistent
"""

        resume_anon = resume.model_copy(deep=True)
        resume_anon.name = "[REDACTED]"
        resume_anon.email = "[REDACTED]"
        resume_anon.phone = "[REDACTED]"
        resume_anon.location = "[REDACTED]"

        resume_dict = resume_anon.model_dump()

        user_content = f"""Job Description:
<job_description>
{job_description}
</job_description>

Candidate Resume:
<resume_data>
{resume_dict}
</resume_data>

Extracted fields for quick reference:
- Skills: {resume_dict.get('skills', [])}
- Certifications: {resume_dict.get('certifications', [])}
- Work titles and summaries: {[(w['title'], w['summary']) for w in resume_dict.get('work_history', []) if isinstance(w, dict)]}
- Project tech stacks: {[p['tech_stack'] for p in resume_dict.get('projects', []) if isinstance(p, dict) and p.get('tech_stack')]}

INSTRUCTIONS:
1. Check extracted fields above before marking any skill as missing
2. Tech in project tech stacks or work summaries counts as a skill
3. Score each category per the rubric
4. Output: Skills:X/35, Projects:X/25, Experience:X/25, Certs:X/10, Leadership:X/5
5. Five scores MUST sum to final score
6. Leadership max is 5
7. Never list something as a gap if it appears in extracted fields above"""

        kwargs = {
            "response_model": RankingResult,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            
        }
        if model_name:  # Groq and Ollama
            kwargs["model"] = model_name
            kwargs["temperature"] = 0.0

        ranking_result_object = client.chat.completions.create(**kwargs)

        # Fix math errors by recalculating from breakdown
        calculated = parse_breakdown_sum(ranking_result_object.category_breakdown)
        if calculated:
            ranking_result_object.score = min(calculated, 100)

        return ranking_result_object

    except Exception as e:
        print(f"Raw error: {e}")
        raise