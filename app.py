import os
import json
import shutil
import streamlit as st
from pathlib import Path

from extract_text import (
    extract_document_text,
    EmptyTextExtractionError,
    ScannedPDFError,
    UnsupportedLanguageError,
    CorruptFileError
)
from llm_parser import extract_resume_data, ResumeData
from ranker import score_candidate, RankingResult

st.set_page_config(page_title="AI Resume Parser & Ranker", layout="wide", page_icon="📄")

st.title("📄 AI Resume Parser & Ranking System")
st.subheader("Upload candidate resumes and match them against a Job Description")

# --- Sidebar ---
st.sidebar.title("⚙️ Settings")
model_provider = st.sidebar.selectbox(
    "Select Model Provider",
    ["Ollama (Local)", "Groq (API)", "Gemini (API)"]
)

if st.sidebar.button("🗑️ Clear Cache"):
    shutil.rmtree("cache", ignore_errors=True)
    st.sidebar.success("Cache cleared!")

if model_provider == "Groq (API)":
    st.caption("Powered by Groq LPU Hardware & Llama 3.3 70B")
else:
    st.caption("Powered by Local Ollama & Llama 3.1 8B")

# --- Caching ---
def get_or_parse(filename: str, raw_text: str, provider: str) -> ResumeData:
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)
    cache_path = cache_dir / f"{filename}.json"

    if cache_path.exists():
        st.info(f"📦 Using cached data for {filename}")
        return ResumeData(**json.loads(cache_path.read_text(encoding='utf-8')))

    result = extract_resume_data(raw_text, provider=provider)
    cache_path.write_text(result.model_dump_json(), encoding='utf-8')
    return result

# --- Inputs ---
st.markdown("### 1. Requirements & Resumes")

job_description = st.text_area(
    "Paste the Job Description (JD) here:",
    height=200,
    placeholder="We are looking for a Software Engineer with experience in Python..."
)

uploaded_files = st.file_uploader(
    "Upload Resumes (PDF or DOCX)",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

# --- Process Button ---
if st.button("🚀 Rank Candidates", type="primary"):
    if not job_description.strip():
        st.error("Please provide a job description first.")
    elif not uploaded_files:
        st.error("Please upload at least one resume.")
    else:
        with st.spinner(f"Processing resumes via {model_provider}..."):

            temp_dir = "temp_uploads"
            os.makedirs(temp_dir, exist_ok=True)

            ranked_candidates = []

            for uploaded_file in uploaded_files:
                file_path = os.path.join(temp_dir, uploaded_file.name)

                try:
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    raw_text = extract_document_text(file_path)

                    if not raw_text.strip():
                        st.warning(f"⚠️ Could not extract text from {uploaded_file.name}. Skipping.")
                        continue

                    # Parse with caching
                    structured_resume: ResumeData = get_or_parse(
                        uploaded_file.name, raw_text, model_provider
                    )

                    # Rank
                    evaluation: RankingResult = score_candidate(
                        structured_resume, job_description, provider=model_provider
                    )

                    ranked_candidates.append({
                        "name": structured_resume.name if structured_resume.name else uploaded_file.name,
                        "filename": uploaded_file.name,
                        "score": evaluation.score,
                        "explanation": evaluation.explanation,
                        "category_breakdown": evaluation.category_breakdown,
                        "strengths": evaluation.strengths,
                        "gaps": evaluation.gaps
                    })

                    if model_provider == "Groq (API)":
                        import time
                        time.sleep(2)

                except EmptyTextExtractionError as e:
                    st.warning(f"⚠️ {uploaded_file.name}: No text found. This may be a scanned PDF.")
                except UnsupportedLanguageError as e:
                    st.warning(f"⚠️ {uploaded_file.name}: Non-English resume detected. Only English is supported.")
                except CorruptFileError as e:
                    st.error(f"❌ {uploaded_file.name}: File appears corrupt or password-protected.")
                except ValueError as e:
                    st.error(f"❌ {uploaded_file.name}: {e}")
                except Exception as e:
                    st.error(f"❌ Pipeline breakdown on file {uploaded_file.name}: {e}")
                    st.exception(e)

                finally:
                    if os.path.exists(file_path):
                        os.remove(file_path)

        # --- Results ---
        st.markdown("### 2. Evaluation Rankings")

        if not ranked_candidates:
            st.warning("No resumes were successfully completed through the pipeline.")
        else:
            ranked_candidates.sort(key=lambda x: x["score"], reverse=True)

            for index, candidate in enumerate(ranked_candidates, start=1):
                with st.expander(
                    f"🏅 Rank #{index}: {candidate['name']} — Score: {candidate['score']}/100"
                ):
                    st.markdown(f"**Filename:** {candidate['filename']}")

                    if candidate['category_breakdown']:
                        st.markdown("**Score Breakdown:**")
                        st.write(candidate['category_breakdown'])

                    st.markdown("**Fit Evaluation:**")
                    st.write(candidate['explanation'])

                    col1, col2 = st.columns(2)
                    with col1:
                        if candidate['strengths']:
                            st.markdown("✅ **Strengths:**")
                            for s in candidate['strengths']:
                                st.write(f"- {s}")
                    with col2:
                        if candidate['gaps']:
                            st.markdown("❌ **Gaps:**")
                            for g in candidate['gaps']:
                                st.write(f"- {g}")