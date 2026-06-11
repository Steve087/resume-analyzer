import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

# Load env variables (The new SDK automatically finds GEMINI_API_KEY)
load_dotenv() 
client = genai.Client()

# 1. Clean, standard Pydantic Schema
class WorkHistory(BaseModel):
    company: str | None = None
    title: str | None = None
    duration: str | None = None
    summary: str | None = None

class Education(BaseModel):
    degree: str | None = None
    institution: str | None = None
    year: str | None = None

class ResumeData(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    total_years_experience: int | None = None
    skills: list[str]
    projects:list[str]
    work_history: list[WorkHistory]
    education: list[Education]
    certifications: list[str]

#@retry(wait=wait_exponential(multiplier=2, min=5, max=30), stop=stop_after_attempt(5))
# 2. The Extraction Function
def extract_resume_data(raw_text: str) -> ResumeData:
    system_prompt = """
    You are an expert HR data extraction system. Your job is to extract structured information from resumes.
    
    CRITICAL INSTRUCTIONS:
    - Extract ONLY facts explicitly stated in the text.
    - If a specific field is missing, leave it as null/empty. DO NOT guess.
    - For 'total_years_experience', calculate this based on dates if possible. If you cannot determine it, return null.
    """

    # We use the modern client and the newer 2.5-flash model
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=f"Extract data from this resume:\n\n{raw_text}",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=ResumeData,
            temperature=0.0
        ),
    )

    # Convert the resulting JSON directly into our Python object
    return ResumeData.model_validate_json(response.text)