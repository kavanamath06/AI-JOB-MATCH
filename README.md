# AI Job Match Assistant

A beginner-friendly Flask web application powered by the Google GenAI SDK (Gemini API) that evaluates candidate resumes against job descriptions. The application provides structured match reports, extracts text from PDF resumes, and offers actionable resume improvements and plain-language match explanations.

---

## Features

- **PDF Resume Text Extraction**: Upload PDF resumes directly from the browser to extract plain text using PyPDF2.
- **AI Match Analysis**: Compare resume text against job descriptions using Gemini AI to compute a match score (0–100), identify matching/missing skills, evaluate experience, and highlight key gaps and recommendations.
- **Structured JSON Outputs**: Strictly enforced Pydantic schemas guarantee consistent and validated JSON responses.
- **Resume Improvement Suggestions**: Generate section-by-section wording and presentation advice based strictly on identified gaps without hallucinating experience.
- **Match Score Explanation**: Receive clear, student-friendly explanations of why a specific match score was given and how to improve.
- **Interactive UI**: Lightweight, responsive single-page web interface with real-time loading states and error handling.

---

## Tech Stack

- **Language**: Python 3.10+
- **Web Framework**: Flask
- **AI / LLM Integration**: Official Google GenAI SDK (`google-genai`), Pydantic
- **PDF Extraction**: PyPDF2
- **Environment Management**: `python-dotenv`
- **Frontend**: HTML5, CSS3, Vanilla JavaScript (Fetch API)

---

## Project Structure

```text
ai-job-match/
├── app.py
├── .env
├── .gitignore
├── requirements.txt
└── templates/
    └── index.html
```

---

## Setup & Configuration

### 1. Prerequisites
Ensure Python 3.10 or higher is installed on your system.

### 2. Install Dependencies
Navigate to the project root directory and install the required packages:

```bash
pip install -r requirements.txt
```

### 3. Environment Setup (`.env`)
Create a `.env` file in the project root directory (if not already present):

```env
FLASK_APP=app.py
FLASK_ENV=development
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

---

## How to Run

1. Start the Flask application:
   ```bash
   python app.py
   ```
2. Open your web browser and navigate to:
   ```text
   http://127.0.0.1:5000/
   ```

---

## How to Use

1. **Upload or Paste Resume**:
   - Click **Upload PDF** to select a PDF resume file and extract its text into the Resume text area, OR
   - Directly paste resume text into the **Resume** textarea.
2. **Enter Job Description**:
   - Paste the target job description into the **Job Description** textarea.
3. **Analyze Match**:
   - Click **Analyze Match** to generate the initial Match Report (Match Score, Skills, Experience, Gaps, Recommendations).
4. **Improve & Explain**:
   - Click **Improve My Resume** to view section-specific suggestions for addressing identified gaps.
   - Click **Explain My Match** to view an encouraging, plain-language breakdown of the match score.

---

## API Endpoints

### 1. `GET /`
Serves the single-page HTML frontend interface.

### 2. `GET /api/ai/test`
Diagnostic endpoint to verify connection to the Gemini API.
- **Response**: `{"success": true, "message": "Gemini API connection working"}`

### 3. `POST /api/extract-resume`
Extracts readable text from an uploaded PDF file.
- **Request**: `multipart/form-data` with field `resume_pdf`
- **Response**: `{"success": true, "resume_text": "..."}`

### 4. `POST /api/analyze`
Evaluates resume text against a job description.
- **Request JSON**:
  ```json
  {
    "resume": "Candidate resume text...",
    "job_description": "Job description text..."
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "match_score": 75,
    "matching_skills": ["Python", "Flask"],
    "missing_skills": ["Docker", "Kubernetes"],
    "experience_match": "Candidate meets experience requirements...",
    "gaps": ["No Docker experience mentioned."],
    "recommendations": ["Learn Docker containerization."]
  }
  ```

### 5. `POST /api/improve-resume`
Generates targeted resume improvement suggestions based on gaps and recommendations.
- **Request JSON**:
  ```json
  {
    "resume": "Candidate resume text...",
    "gaps": ["..."],
    "recommendations": ["..."]
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "improved_sections": [
      {
        "section": "Skills & Tools",
        "suggestion": "Add hands-on experience with Docker..."
      }
    ]
  }
  ```

### 6. `POST /api/explain-match`
Provides a beginner-friendly explanation of why a candidate received a given match score.
- **Request JSON**:
  ```json
  {
    "resume": "Candidate resume text...",
    "job_description": "Job description text...",
    "analysis": { /* Complete analysis result object */ }
  }
  ```
- **Response**: `{"success": true, "explanation": "..."}`

---

## Security Note

- **API Key Protection**: Never commit `.env` or hardcode API keys directly in source code.
- **Environment Isolation**: API keys are loaded strictly via `python-dotenv` and accessed through `os.getenv("GEMINI_API_KEY")`.
- **Git Safety**: The `.gitignore` file ensures `.env` and Python cached files (`__pycache__`) are excluded from source control.

---

## Future Improvements

- Support for additional resume file formats (e.g., `.docx`, `.txt`).
- Visual score gauge indicators and interactive skill comparison charts.
- Exporting generated Match Reports and Improvement plans to downloadable PDF reports.
- Multi-resume management workspace for tracking application tailored versions.
