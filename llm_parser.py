import os
import instructor
from groq import Groq
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
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

# --- Schemas ---
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
    projects: list[Project] = []
    work_history: list[WorkHistory] = []
    education: list[Education] = []
    certifications: list[str] = []

# --- Extraction Function ---
@retry(wait=wait_exponential(multiplier=2, min=2, max=10), stop=stop_after_attempt(3))
def extract_resume_data(raw_text: str, provider: str = "Ollama (Local)") -> ResumeData:
    try:
        raw_text = raw_text[:6000]

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
You are an expert HR data extraction system. Extract structured information from resumes.
- Extract ONLY facts explicitly stated in the text.
- If a field is missing, leave it null/empty. DO NOT guess.
- For total_years_experience: calculate from work history dates if possible, otherwise null.
- For skills: extract only explicitly listed skills.
- For projects: extract name, description, and tech_stack (ALL technologies mentioned for that project).
- For work_history: extract company, title, duration, and summary
  (summary must include responsibilities AND technologies used in that role).
"""

        kwargs = {
            "response_model": ResumeData,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract all structured data from the following resume text:\n\n{raw_text}"}
            ],
            
        }
        if model_name:  # Groq and Ollama
            kwargs["model"] = model_name
            kwargs["temperature"] = 0.0

        return client.chat.completions.create(**kwargs)

    except Exception as e:
        print(f"Parser error: {e}")
        raise