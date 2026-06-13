import os
import instructor
from groq import Groq
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv() 

# 1. Initialize the Groq client, wrapped with Instructor
# This magically teaches Groq how to output perfect Pydantic objects
client = instructor.from_groq(
    Groq(
        # base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("GROQ_API_KEY")
    )
)

# 2. Your Exact Pydantic Schema (Unchanged!)
class WorkHistory(BaseModel):
    company: str | None = None
    title: str | None = None
    duration: str | None = None
    summary: str | None = None

class Education(BaseModel):
    degree: str | None = None
    institution: str | None = None
    year: str | None = None


class Project(BaseModel):
    name: str | None = None
    description: str | None = None
    tech_stack: list[str] = []

class ResumeData(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    total_years_experience: float | None = None
    skills: list[str] = []
    projects: list[Project] = []  # ← structured, not list[str]
    work_history: list[WorkHistory] = []
    education: list[Education] = []
    certifications: list[str] = []

# 3. The Clean Extraction Function
@retry(wait=wait_exponential(multiplier=2, min=2, max=10), stop=stop_after_attempt(3))
def extract_resume_data(raw_text: str) -> ResumeData:
    try:
        raw_text = raw_text[:6000]
        system_prompt = """
    You are an expert HR data extraction system. Your job is to extract structured information from resumes.
    - Extract ONLY facts explicitly stated in the text.
    - If a specific field is missing, leave it as null/empty. DO NOT guess or infer.
    - For total_years_experience: calculate from work history dates if possible, otherwise return null.
    - For skills: extract only explicitly listed skills, not inferred ones.
    - For projects: extract project name, descriptions and tech_stack(list of technologies used).
    """

        # Look how clean this is! No json parsing needed. 
        # Instructor returns your Python object directly.
        resume_data_object = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            response_model=ResumeData, # This is where the magic happens
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract all structured data from the following resume text:\n\n{raw_text}"}
            ],
            temperature=0.0
        )

        return resume_data_object
    except Exception as e:
        print(f"Parser error: {e}")
        raise