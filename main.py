import os # <-- CRITICAL FIX: Added this so os.path.basename works!
import time
from extract_text import extract_document_text
from llm_parser import extract_resume_data
from ranker import score_candidate 

def process_and_rank_resume(file_path: str, job_description: str):
    print(f"1. Reading file: {file_path}...")
    raw_text = extract_document_text(file_path)
    
    print("2. Extracting structured data via AI...")
    structured_data = extract_resume_data(raw_text)
    
    print("3. Evaluating candidate against Job Description...")
    ranking = score_candidate(structured_data, job_description)
    
    return structured_data, ranking

def rank_a_batch_of_resumes(file_paths: list[str], job_description: str) -> list[dict]:
    """
    Processes a list of resume file paths, scores them all, 
    and returns a list sorted by score descending.
    """
    results = []
    
    for index,path in enumerate(file_paths):
        try:
            # Reuses your awesome existing single-file logic
            structured_data, ranking = process_and_rank_resume(path, job_description)
            
            results.append({
                "filename": os.path.basename(path),
                "name": structured_data.name or os.path.basename(path),
                "score": ranking.score,
                "explanation": ranking.explanation
            })

            if index < len(file_paths) - 1:
                print("⏳ Pausing for 6 seconds to respect API rate limits...")
                time.sleep(10)

        except Exception as e:
            # Ensure one bad file doesn't crash the whole batch execution
            print(f"Skipping corrupt or unreadable file {path}: {e}")
            
    # Sort the batch from highest score to lowest score
    ranked_results = sorted(results, key=lambda x: x['score'], reverse=True)
    return ranked_results

if __name__ == "__main__":
    # Let's test the batch function with a list of files!
    # (You can add more dummy file paths here if you create them)
    test_files = [
        r"C:\Users\steve\resume_analyzer\steve.pdf"
    ]
    
    # A dummy Job Description to test against
    sample_jd = """
    We are looking for a Software Engineer with at least 2 years of experience.
    Must have strong skills in Python and React. 
    Experience with cloud platforms like AWS or Azure is a huge plus.
    """
    
    print("Starting Batch Evaluation...")
    try:
        ranked_candidates = rank_a_batch_of_resumes(test_files, sample_jd)
        
        print("\n=== FINAL RANKED CANDIDATES ===")
        for index, candidate in enumerate(ranked_candidates, start=1):
            print(f"\nRANK #{index}: {candidate['name']} ({candidate['filename']})")
            print(f"MATCH SCORE: {candidate['score']}/100")
            print(f"EXPLANATION: {candidate['explanation']}")
            print("-" * 40)
        print("===============================")
        
    except Exception as e:
        print(f"\nPipeline failed: {e}")