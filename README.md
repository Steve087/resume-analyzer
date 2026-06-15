# AI Resume Parser & Ranking System

An end-to-end pipeline that extracts structured information from resumes (PDF/DOCX) and ranks candidates against a job description using LLMs.

---

## Features

- Upload multiple resumes (PDF or DOCX)
- Paste any job description
- Extracts structured data: skills, projects, work history, education, certifications
- Scores candidates across 5 weighted categories (Skills, Projects, Experience, Certifications, Leadership)
- Ranks candidates with detailed explanations, strengths, and gaps
- Supports multiple LLM providers: Ollama (local), Groq API, Gemini API
- Resume caching to minimize API usage
- Bias mitigation: candidate names and personal info anonymized before scoring

---

## Tech Stack

- **Frontend:** Streamlit
- **LLM Providers:** Groq (Llama 3.3 70B), Google Gemini 2.0 Flash, Ollama (Llama 3.1 8B)
- **Structured Output:** Instructor + Pydantic
- **PDF Extraction:** PyMuPDF (fitz)
- **DOCX Extraction:** python-docx
- **Retry Logic:** Tenacity

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/Steve087/resume-analyzer.git
cd resume-analyzer
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the root directory:
```
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

- Get Groq API key: https://console.groq.com
- Get Google API key: https://aistudio.google.com

### 5. (Optional) Set up Ollama for local inference
```bash
# Install Ollama from https://ollama.com
ollama pull llama3.1:8b
```

### 6. Run the app
```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## How to Use

1. Select a model provider from the sidebar (Ollama, Groq, or Gemini)
2. Paste a job description in the text area
3. Upload one or more resumes (PDF or DOCX)
4. Click **Rank Candidates**
5. View ranked results with score breakdowns, strengths, and gaps

---

## Scoring System

Each candidate is scored out of 100 across 5 weighted categories:

| Category | Weight | Description |
|---|---|---|
| Skills Match | 35 pts | Required and preferred skills from the JD |
| Projects | 25 pts | Relevance and quality of projects |
| Work Experience | 25 pts | Relevance of internships and jobs |
| Certifications | 10 pts | Relevance of certifications |
| Leadership | 5 pts | Technical leadership and extracurriculars |

---

## Project Structure

```
resume_analyzer/
├── app.py              # Streamlit UI
├── llm_parser.py       # Resume extraction pipeline
├── ranker.py           # Candidate scoring and ranking
├── extract_text.py     # PDF and DOCX text extraction
├── requirements.txt    # Dependencies
├── .env.example        # Environment variable template
└── README.md
```

---

## Design Decisions

**Why separate extraction and ranking?**
Resumes are parsed once and cached. Ranking runs on cached data, so switching JDs doesn't require re-parsing — saving API tokens and time.

**Why anonymize before ranking?**
Candidate names, emails, phone numbers, and locations are redacted before the ranker sees the resume. This reduces bias based on name or location.

**Why Instructor + Pydantic?**
Guarantees structured JSON output matching the schema on every run. Automatically retries if the model returns invalid output.

**Why multiple providers?**
Different providers have different rate limits and quality. Use Ollama locally for testing (no limits), and Groq or Gemini for production-quality results.

---

## Known Limitations

- Scanned image PDFs (no text layer) will be skipped
- Smaller models (8B) show score compression and occasional hallucinations
- Free tier API limits require caching to stay within daily quotas
- Scoring is relative — absolute scores matter less than ranking order

---

## Sample Run

**JD:** Data Analyst Intern  
**Model:** Gemini 2.0 Flash

| Rank | Candidate | Score |
|---|---|---|
| #1 | Aleena Mariya Sebastian | 91/100 |
| #2 | Sharon Devasia | 55/100 |
| #3 | Steve Jose | 40/100 |
| #4 | Joe Abraham K | 27/100 |
| #5 | Shijin Abraham | 22/100 |
| #6 | Sreya Satheesan | 14/100 |

---

## Requirements

See `requirements.txt`. Key packages:
```
streamlit
instructor
groq
openai
google-genai
pymupdf
python-docx
pydantic
tenacity
python-dotenv
jsonref
```
