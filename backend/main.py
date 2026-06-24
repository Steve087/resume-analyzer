import os
import json
import shutil
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn

from extract_text import (
    extract_document_text,
    EmptyTextExtractionError,
    UnsupportedLanguageError,
    CorruptFileError
)
from llm_parser import extract_resume_data, ResumeData
from ranker import score_candidate, RankingResult

@asynccontextmanager
async def lifespan(app):
    groq_key = os.environ.get("GROQ_API_KEY", "")
    gemini_key = os.environ.get("GOOGLE_API_KEY", "")
    print(f"GROQ_API_KEY: {'✓ Found' if groq_key else '✗ Missing'} ({groq_key[:10]}...)")
    print(f"GOOGLE_API_KEY: {'✓ Found' if gemini_key else '✗ Missing'} ({gemini_key[:10]}...)")
    yield

app = FastAPI(title="Resume Analyzer API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
        "http://localhost:3000",
        "https://resume-analyzer-gamma-snowy.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

def get_cached_resume(filename: str) -> ResumeData | None:
    cache_path = CACHE_DIR / f"{filename}.json"
    if cache_path.exists():
        return ResumeData(**json.loads(cache_path.read_text(encoding='utf-8')))
    return None

def save_cached_resume(filename: str, resume: ResumeData):
    cache_path = CACHE_DIR / f"{filename}.json"
    cache_path.write_text(resume.model_dump_json(), encoding='utf-8')

def is_rate_limit(e: Exception) -> bool:
    return any(x in str(e) for x in ["429", "RESOURCE_EXHAUSTED", "quota", "RateLimitError", "rate_limit", "503", "UNAVAILABLE"])

class CandidateResult(BaseModel):
    name: str
    filename: str
    score: int
    category_breakdown: str
    explanation: str
    strengths: list[str]
    gaps: list[str]
    log: str = ""

class RankResponse(BaseModel):
    candidates: list[CandidateResult]
    errors: list[str]

@app.get("/")
def root():
    return {"status": "Resume Analyzer API is running"}

@app.post("/rank", response_model=RankResponse)
async def rank_resumes(
    files: List[UploadFile] = File(...),
    job_description: str = Form(...)
):
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)

    candidates = []
    errors = []

    for uploaded_file in files:
        file_path = temp_dir / uploaded_file.filename

        try:
            with open(file_path, "wb") as f:
                f.write(await uploaded_file.read())

            raw_text = extract_document_text(str(file_path))

            if not raw_text.strip():
                errors.append(f"{uploaded_file.filename}: No text found. May be a scanned PDF.")
                continue

            # Parse — check cache first
            cached = False
            parse_provider = ""
            structured_resume = get_cached_resume(uploaded_file.filename)

            if structured_resume:
                cached = True
                print(f"[{uploaded_file.filename}] 📦 Using cached parse data")
            else:
                for provider in ["Gemini (API)", "Groq (API)", "Ollama (Local)"]:
                    try:
                        print(f"[{uploaded_file.filename}] Trying parse with {provider}...")
                        structured_resume = extract_resume_data(raw_text, provider=provider)
                        parse_provider = provider
                        print(f"[{uploaded_file.filename}] ✓ Parsed with {provider}")
                        save_cached_resume(uploaded_file.filename, structured_resume)
                        break
                    except Exception as e:
                        if is_rate_limit(e):
                            print(f"[{uploaded_file.filename}] ✗ {provider} — {'Daily quota exhausted' if 'quota' in str(e).lower() else 'Rate limited'}")
                            continue
                        raise

            if not structured_resume:
                errors.append(f"{uploaded_file.filename}: All API providers rate limited.")
                continue

            # Rank
            rank_provider = ""
            evaluation = None
            for provider in ["Gemini (API)", "Groq (API)", "Ollama (Local)"]:
                try:
                    print(f"[{uploaded_file.filename}] Trying rank with {provider}...")
                    evaluation = score_candidate(structured_resume, job_description, provider=provider)
                    rank_provider = provider
                    print(f"[{uploaded_file.filename}] ✓ Ranked with {provider}")
                    break
                except Exception as e:
                    if is_rate_limit(e):
                        print(f"[{uploaded_file.filename}] ✗ {provider} — {'Daily quota exhausted' if 'quota' in str(e).lower() else 'Rate limited'}")
                        continue
                    raise

            if not evaluation:
                errors.append(f"{uploaded_file.filename}: All API providers rate limited for ranking.")
                continue

            # Build log
            if cached:
                log = "📦 Cached parse"
            else:
                log = f"🔍 Parsed with {parse_provider.replace(' (API)', '').replace(' (Local)', '')}"
            log += f" · ⚡ Ranked with {rank_provider.replace(' (API)', '').replace(' (Local)', '')}"

            candidates.append(CandidateResult(
                name=structured_resume.name or uploaded_file.filename,
                filename=uploaded_file.filename,
                score=evaluation.score,
                category_breakdown=evaluation.category_breakdown,
                explanation=evaluation.explanation,
                strengths=evaluation.strengths,
                gaps=evaluation.gaps,
                log=log
            ))

        except EmptyTextExtractionError:
            errors.append(f"{uploaded_file.filename}: No text found. May be a scanned PDF.")
        except UnsupportedLanguageError:
            errors.append(f"{uploaded_file.filename}: Non-English resume detected.")
        except CorruptFileError:
            errors.append(f"{uploaded_file.filename}: File appears corrupt or password-protected.")
        except ValueError as e:
            errors.append(f"{uploaded_file.filename}: {str(e)}")
        except Exception as e:
            errors.append(f"{uploaded_file.filename}: Unexpected error — {str(e)}")

        finally:
            if file_path.exists():
                file_path.unlink()

    candidates.sort(key=lambda x: x.score, reverse=True)
    return RankResponse(candidates=candidates, errors=errors)

@app.delete("/cache")
def clear_cache():
    shutil.rmtree("cache", ignore_errors=True)
    CACHE_DIR.mkdir(exist_ok=True)
    return {"message": "Cache cleared successfully"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)