import io
import json
import os
from typing import List
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field, ValidationError
import PyPDF2

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Initialize the Gemini client using the environment variable
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

class MatchAnalysis(BaseModel):
    match_score: int = Field(..., ge=0, le=100, description="Match score integer between 0 and 100")
    matching_skills: List[str] = Field(..., description="Array of matching skill strings")
    missing_skills: List[str] = Field(..., description="Array of missing skill strings")
    experience_match: str = Field(..., description="Short string evaluating experience match")
    gaps: List[str] = Field(..., description="Array of gap strings")
    recommendations: List[str] = Field(..., description="Array of practical recommendation strings")

class ImprovedSection(BaseModel):
    section: str = Field(..., description="Name of the resume section or area to improve")
    suggestion: str = Field(..., description="Specific improvement suggestion or wording advice based only on gaps and recommendations")

class ResumeImprovement(BaseModel):
    improved_sections: List[ImprovedSection] = Field(..., description="List of section suggestions")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/ai/test", methods=["GET"])
def test_ai():
    try:
        current_api_key = os.getenv("GEMINI_API_KEY")
        if not current_api_key:
            return jsonify({
                "success": False,
                "message": "Gemini API connection failed"
            })

        # Ensure client instance is ready
        ai_client = client or genai.Client(api_key=current_api_key)

        # Make a minimal real Gemini API request
        response = ai_client.models.generate_content(
            model="gemini-3.6-flash",
            contents="ping"
        )

        if response and response.text:
            return jsonify({
                "success": True,
                "message": "Gemini API connection working"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Gemini API connection failed"
            })
    except Exception:
        return jsonify({
            "success": False,
            "message": "Gemini API connection failed"
        })

@app.route("/api/analyze", methods=["POST"])
def analyze_match():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid or missing JSON body"
        }), 400

    resume = data.get("resume")
    job_description = data.get("job_description")

    # Validation: resume and job_description are required and must contain non-whitespace text
    if not resume or not isinstance(resume, str) or not resume.strip():
        return jsonify({
            "success": False,
            "message": "Resume is required and cannot be empty"
        }), 400

    if not job_description or not isinstance(job_description, str) or not job_description.strip():
        return jsonify({
            "success": False,
            "message": "Job description is required and cannot be empty"
        }), 400

    prompt = f"""You are an AI job matching assistant.

Compare the candidate's resume against the supplied job description.

Evaluate ONLY information explicitly present in the supplied resume and job description.

Do not invent:
-Skills
-Work experience
-Education
-Certifications
-Projects

Return a match analysis containing:
-match_score: integer from 0 to 100
-matching_skills: array of strings
-missing_skills: array of strings
-experience_match: short string
-gaps: array of strings
-recommendations: array of strings

The recommendations must be  practical and based only  on the identified gaps.

Candidate Resume:
\"\"\"{resume.strip()}\"\"\"

Job Description:
\"\"\"{job_description.strip()}\"\"\"
"""

    try:
        current_api_key = os.getenv("GEMINI_API_KEY")
        if not current_api_key:
            return jsonify({
                "success": False,
                "message": "AI analysis failed"
            }), 502

        ai_client = client or genai.Client(api_key=current_api_key)

        response = ai_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=MatchAnalysis
            )
        )

        if not response or not response.text:
            return jsonify({
                "success": False,
                "message": "AI analysis failed"
            }), 502

    except Exception:
        return jsonify({
            "success": False,
            "message": "AI analysis failed"
        }), 502

    # Parse and validate structured output using Pydantic
    try:
        parsed_json = json.loads(response.text)
        analysis = MatchAnalysis.model_validate(parsed_json)
    except (json.JSONDecodeError, ValidationError, Exception):
        return jsonify({
            "success": False,
            "message": "AI response validation failed"
        }), 502

    # Return validated structured JSON response with EXACTLY the required fields
    return jsonify({
        "success": True,
        "match_score": analysis.match_score,
        "matching_skills": analysis.matching_skills,
        "missing_skills": analysis.missing_skills,
        "experience_match": analysis.experience_match,
        "gaps": analysis.gaps,
        "recommendations": analysis.recommendations
    }), 200

@app.route("/api/improve-resume", methods=["POST"])
def improve_resume():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid or missing JSON body"
        }), 400

    resume = data.get("resume")
    gaps = data.get("gaps", [])
    recommendations = data.get("recommendations", [])

    # Validation: resume is required and must contain non-whitespace text
    if not resume or not isinstance(resume, str) or not resume.strip():
        return jsonify({
            "success": False,
            "message": "Resume is required and cannot be empty"
        }), 400

    if not isinstance(gaps, list):
        gaps = []
    if not isinstance(recommendations, list):
        recommendations = []

    prompt = f"""You are an AI resume improvement assistant.

Suggest improvements to the candidate's resume based ONLY on the provided gaps and recommendations.

CRITICAL RULES:
- Never invent:
  - work experience
  - projects
  - skills
  - certifications
  - education
  - achievements
- You may:
  - improve wording
  - improve clarity
  - suggest where existing experience could be presented better
  - suggest what the student should learn or add in the future
- Do not rewrite the entire resume automatically. Provide targeted section suggestions.

Candidate Resume:
\"\"\"{resume.strip()}\"\"\"

Identified Gaps:
{json.dumps(gaps, indent=2)}

Recommendations:
{json.dumps(recommendations, indent=2)}
"""

    try:
        current_api_key = os.getenv("GEMINI_API_KEY")
        if not current_api_key:
            return jsonify({
                "success": False,
                "message": "Resume improvement failed"
            }), 502

        ai_client = client or genai.Client(api_key=current_api_key)

        response = ai_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ResumeImprovement
            )
        )

        if not response or not response.text:
            return jsonify({
                "success": False,
                "message": "Resume improvement failed"
            }), 502

    except Exception:
        return jsonify({
            "success": False,
            "message": "Resume improvement failed"
        }), 502

    # Parse and validate structured output using Pydantic
    try:
        parsed_json = json.loads(response.text)
        improvement = ResumeImprovement.model_validate(parsed_json)
    except (json.JSONDecodeError, ValidationError, Exception):
        return jsonify({
            "success": False,
            "message": "Resume improvement failed"
        }), 502

    return jsonify({
        "success": True,
        "improved_sections": [
            {
                "section": sec.section,
                "suggestion": sec.suggestion
            }
            for sec in improvement.improved_sections
        ]
    }), 200

class MatchExplanation(BaseModel):
    explanation: str = Field(..., description="Beginner-friendly explanation of the match score based only on the supplied data")

@app.route("/api/explain-match", methods=["POST"])
def explain_match():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid or missing JSON body"
        }), 400

    resume = data.get("resume")
    job_description = data.get("job_description")
    analysis = data.get("analysis")

    # Validation
    if not resume or not isinstance(resume, str) or not resume.strip():
        return jsonify({
            "success": False,
            "message": "Resume is required and cannot be empty"
        }), 400

    if not job_description or not isinstance(job_description, str) or not job_description.strip():
        return jsonify({
            "success": False,
            "message": "Job description is required and cannot be empty"
        }), 400

    if not analysis or not isinstance(analysis, dict):
        return jsonify({
            "success": False,
            "message": "Analysis object is required"
        }), 400

    prompt = f"""You are an AI career advisor explaining a job match result to a student or early-career professional.

Based ONLY on the resume, job description, and analysis provided below, write a beginner-friendly explanation of why the candidate received their match score.

CRITICAL RULES:
- Do NOT recalculate or change the match score
- Do NOT invent any information not present in the resume, job description, or analysis
- The explanation must:
  - Mention the strongest matching skills and why they help
  - Explain the most important gaps clearly and simply
  - Explain what the candidate could realistically do to improve their match
  - Use plain, encouraging language a student can understand

Candidate Resume:
\"\"\"{resume.strip()}\"\"\"

Job Description:
\"\"\"{job_description.strip()}\"\"\"

Match Analysis:
{json.dumps(analysis, indent=2)}
"""

    try:
        current_api_key = os.getenv("GEMINI_API_KEY")
        if not current_api_key:
            return jsonify({
                "success": False,
                "message": "Match explanation failed"
            }), 502

        ai_client = client or genai.Client(api_key=current_api_key)

        response = ai_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=MatchExplanation
            )
        )

        if not response or not response.text:
            return jsonify({
                "success": False,
                "message": "Match explanation failed"
            }), 502

    except Exception:
        return jsonify({
            "success": False,
            "message": "Match explanation failed"
        }), 502

    # Parse and validate structured output using Pydantic
    try:
        parsed_json = json.loads(response.text)
        result = MatchExplanation.model_validate(parsed_json)
    except (json.JSONDecodeError, ValidationError, Exception):
        return jsonify({
            "success": False,
            "message": "Match explanation failed"
        }), 502

    return jsonify({
        "success": True,
        "explanation": result.explanation
    }), 200

@app.route("/api/extract-resume", methods=["POST"])
def extract_resume():
    # Verify a file was provided
    if "resume_pdf" not in request.files:
        return jsonify({
            "success": False,
            "message": "Resume PDF is required"
        }), 400

    file = request.files["resume_pdf"]

    # Verify the file has content and a name
    if not file or not file.filename:
        return jsonify({
            "success": False,
            "message": "Resume PDF is required"
        }), 400

    # Verify it is a PDF by extension
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({
            "success": False,
            "message": "Only PDF files are allowed"
        }), 400

    # Extract text from the PDF
    try:
        pdf_bytes = io.BytesIO(file.read())
        reader = PyPDF2.PdfReader(pdf_bytes)

        extracted_pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_pages.append(text.strip())

        resume_text = "\n".join(extracted_pages).strip()

        if not resume_text:
            return jsonify({
                "success": False,
                "message": "Could not extract text from PDF"
            }), 400

    except Exception:
        return jsonify({
            "success": False,
            "message": "Could not extract text from PDF"
        }), 400

    return jsonify({
        "success": True,
        "resume_text": resume_text
    }), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)
