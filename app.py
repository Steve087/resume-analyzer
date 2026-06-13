import os
import streamlit as st
import time

# Import your existing document text extractor (.pdf / .docx)
from extract_text import extract_document_text

# Import your updated Groq pipeline functions and schemas 
from llm_parser import extract_resume_data, ResumeData
from ranker import score_candidate, RankingResult

st.set_page_config(page_title="AI Resume Parser & Ranker", layout="wide", page_icon="📄")

st.title("📄 AI Resume Parser & Ranking System")
st.subheader("Upload candidate resumes and match them against a Job Description")
st.caption("Powered by Groq LPU Hardware & Llama 3.3 70B")

# --- Left Column: Inputs ---
st.markdown("### 1. Requirements & Resumes")

# Text area for Job Description
job_description = st.text_area(
    "Paste the Job Description (JD) here:",
    height=200,
    placeholder="We are looking for a Software Engineer with experience in Python..."
)

# File uploader allowing multiple files (PDF and DOCX)
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
        with st.spinner("Processing resumes and evaluating match scores via Groq..."):
            
            # Create a temporary folder to store files for your text extractor
            temp_dir = "temp_uploads"
            os.makedirs(temp_dir, exist_ok=True)
            
            ranked_candidates = []
            
            # Process files step-by-step through the upgraded Groq pipeline
            for uploaded_file in uploaded_files:
                file_path = os.path.join(temp_dir, uploaded_file.name)
                
                try:
                    # 1. Save uploaded file buffer to local disk temporary space
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # 2. Document Text Extraction Phase (.pdf/.docx to clean string)
                    raw_text = extract_document_text(file_path)
                    
                    if not raw_text.strip():
                        st.warning(f"⚠️ Could not extract text from {uploaded_file.name}. Skipping file.")
                        continue
                        
                    # 3. Pipeline Phase 1: Structured JSON Parsing via Groq/Instructor
                    structured_resume: ResumeData = extract_resume_data(raw_text)
                    
                    # 4. Pipeline Phase 2: Logic Evaluation Match via Groq/Instructor
                    evaluation: RankingResult = score_candidate(structured_resume, job_description)
                    
                    # 5. Append candidate data to tracking array
                    # 5. Append candidate data to tracking array
                    ranked_candidates.append({
                        "name": structured_resume.name if structured_resume.name else uploaded_file.name,
                        "filename": uploaded_file.name,
                        "score": evaluation.score,
                        "explanation": evaluation.explanation,
                        "category_breakdown": evaluation.category_breakdown,
                        "strengths": evaluation.strengths,
                        "gaps": evaluation.gaps
                    })
                    time.sleep(2)
                    
                except Exception as e:
                    st.error(f"❌ Pipeline breakdown on file {uploaded_file.name}: {e}")
                    st.exception(e)
                    
                finally:
                    # Cleanup individual temporary file immediately after processing to save disk space
                    if os.path.exists(file_path):
                        os.remove(file_path)
            
            # --- Results View Layout Rendering ---
            st.markdown("### 2. Evaluation Rankings")
            
            if not ranked_candidates:
                st.warning("No resumes were successfully completed through the pipeline.")
            else:
                # Dynamically sort the list by the candidate match score (Highest scores first)
                ranked_candidates.sort(key=lambda x: x["score"], reverse=True)
                
                for index, candidate in enumerate(ranked_candidates, start=1):
                    with st.expander(f"🏅 Rank #{index}: {candidate['name']} — Score: {candidate['score']}/100"):
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