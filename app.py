import os
import streamlit as st

# Import your existing pipeline functions
from extract_text import extract_document_text
from llm_parser import extract_resume_data
from ranker import score_candidate
# Import your batch function (the one we added to main.py or pipeline.py)
from main import rank_a_batch_of_resumes 

st.set_page_config(page_title="AI Resume Parser & Ranker", layout="wide")

st.title("📄 AI Resume Parser & Ranking System")
st.subheader("Upload candidate resumes and match them against a Job Description")

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
        with st.spinner("Processing resumes and evaluating match scores..."):
            
            # Temporary directory to save files so your extraction functions can read them
            temp_dir = "temp_uploads"
            os.makedirs(temp_dir, exist_ok=True)
            
            saved_file_paths = []
            
            # Save uploaded files locally to pass paths into your batch function
            for uploaded_file in uploaded_files:
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                saved_file_paths.append(file_path)
            
            try:
                # Run your exact backend logic!
                ranked_candidates = rank_a_batch_of_resumes(saved_file_paths, job_description)
                
                # --- Right Column / Results View ---
                st.markdown("### 2. Evaluation Rankings")
                
                if not ranked_candidates:
                    st.warning("No resumes were successfully processed.")
                
                for index, candidate in enumerate(ranked_candidates, start=1):
                    # Display metrics for clear visual sorting
                    with st.expander(f"🏅 Rank #{index}: {candidate['name']} — Score: {candidate['score']}/100"):
                        st.markdown(f"**Filename:** {candidate['filename']}")
                        st.markdown(f"**Fit Evaluation:**")
                        st.write(candidate['explanation'])
                        
            except Exception as e:
                st.error(f"An error occurred during batch processing: {e}")
                
            finally:
                # Cleanup temporary files cleanly so your system stays organized
                for path in saved_file_paths:
                    if os.path.exists(path):
                        os.remove(path)