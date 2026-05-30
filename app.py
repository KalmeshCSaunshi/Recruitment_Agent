import os
import re
import json
import requests
import ollama
import urllib.parse
from flask import Flask, request, jsonify, render_template, Response, send_file
from datetime import datetime
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed

import PyPDF2
import io
import asyncio
import threading
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import sourcing_agent
from naukri_session_service import (
    get_or_create_profile,
)
from auth import register_user, login_user

from flask_jwt_extended import JWTManager,jwt_required, get_jwt_identity

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = "your_super_secret_key"

jwt = JWTManager(app)




# ── Skill Normalization ──────────────────────────────────────────────────────
def normalize_skill(skill: str) -> str:
    """Normalize skill name purely by case and spacing to keep aggregation stack-agnostic."""
    return skill.lower().strip()



def market_analyze_candidate(lead: dict, requirements: list, jd_min_exp: int = 2, jd_max_exp: int = 10) -> dict:
    """
    Lightweight DETERMINISTIC-ONLY scorer for market analysis.
    Uses candidate's skills + current role text as the match surface.
    Scores dynamically based on Mandatory Skills (60%), Nice-to-Have Skills (20%),
    and Target Experience Alignment (20%) to yield a beautiful granular distribution.
    No Ollama calls — designed to score 200 candidates in ~5 seconds.
    """
    # Match surface: skills text + current role (both from search card)
    skills_raw = lead.get('skills', '') or ''
    current_raw = lead.get('current', '') or ''
    experience_text = f"{skills_raw} {current_raw}".lower()

    matched_skills = []
    requirements_analysis = []

    for req in requirements:
        req_name = req.get('display_name', '')
        valid_keywords = [k.lower().strip() for k in req.get('keywords', [req_name])]
        is_mandatory = req.get('mandatory', False)
        found = False
        matching_keyword = ""

        for kw in valid_keywords:
            # 1. Direct match
            if kw in experience_text:
                found = True
                matching_keyword = kw
                break
            # 2. Singular form
            if kw.endswith('s') and len(kw) > 3 and kw[:-1] in experience_text:
                found = True
                matching_keyword = kw[:-1]
                break
            # 3. Multi-word: all sub-words present
            sub_words = [w.strip() for w in kw.split() if len(w.strip()) > 1]
            if len(sub_words) > 1 and all(w in experience_text for w in sub_words):
                found = True
                matching_keyword = sub_words[0]
                break

        if found:
            matched_skills.append(req_name)
            requirements_analysis.append({
                "requirement": req_name, "status": "met",
                "keyword": matching_keyword, "is_mandatory": is_mandatory
            })
        else:
            requirements_analysis.append({
                "requirement": req_name, "status": "not_met",
                "keyword": "NOT_FOUND", "is_mandatory": is_mandatory
            })

    # ── Parse Candidate Experience Years ──────────────────────────────────
    def parse_exp_years(exp_str):
        if not exp_str or exp_str == "N/A":
            return None
        m = re.search(r'(\d+(?:\.\d+)?)\s*(?:yrs?|years?|yr\b|y\b)', exp_str, re.IGNORECASE)
        if m:
            return int(float(m.group(1)))
        m2 = re.search(r'(\d+)', exp_str)
        return int(m2.group(1)) if m2 else None

    yrs = parse_exp_years(lead.get('experience', ''))

    # ── High-Precision Granular Score Calculations ───────────────────────
    mandatory_reqs = [r for r in requirements if r.get('mandatory', False)]
    optional_reqs = [r for r in requirements if not r.get('mandatory', False)]

    # 1. Mandatory Skills Match (60% weight) - Zero Tolerance Base
    if mandatory_reqs:
        met_mandatory_count = sum(
            1 for name in matched_skills
            if any(r.get('display_name') == name and r.get('mandatory', False) for r in mandatory_reqs)
        )
        mand_ratio = met_mandatory_count / len(mandatory_reqs)
        mandatory_score = mand_ratio * 60
    else:
        met_mandatory_count = 0
        mandatory_score = 60
        mand_ratio = 1.0

    # 2. Nice-to-Have (Optional) Skills Match (20% weight)
    if optional_reqs:
        met_optional_count = sum(
            1 for name in matched_skills
            if any(r.get('display_name') == name and not r.get('mandatory', False) for r in optional_reqs)
        )
        optional_score = (met_optional_count / len(optional_reqs)) * 20
    else:
        optional_score = 0
        if mandatory_reqs:
            mandatory_score = mand_ratio * 80  # Redistribute nice-to-have points to mandatory if none in JD
        else:
            mandatory_score = 80

    # 3. Experience Alignment Score (20% weight)
    experience_score = 0
    if yrs is not None:
        if jd_min_exp <= yrs <= jd_max_exp:
            experience_score = 20  # Perfect experience range match
        elif (jd_min_exp - 1) <= yrs <= (jd_max_exp + 2):
            experience_score = 10  # Close experience match (1 year under or 2 years over)
        else:
            experience_score = 0   # Out of bounds

    # Zero Tolerance: Perfect experience but zero technical skills gets capped extremely low
    if mandatory_reqs and met_mandatory_count == 0:
        match_percentage = round(experience_score * 0.5)  # Max 10%
    else:
        match_percentage = round(mandatory_score + optional_score + experience_score)

    match_percentage = min(100, max(0, match_percentage))

    lead.update({
        "match_percentage": match_percentage,
        "matched_skills": matched_skills,
        "requirements_analysis": requirements_analysis,
    })
    return lead



def generate_feedback_signals(requirements_analysis, match_percentage, jd_min_exp=2, experience_years=0, domain_experience=None, active_status="", notice_period=""):
    strengths = []
    missing_skills = []
    risk_areas = []

    # 1. Strengths & Missing Skills
    has_testing = False
    testing_keywords = {"test", "qa", "unittest", "pytest", "gtest", "selenium", "coverage", "automation"}

    for req in requirements_analysis:
        req_name = req.get('requirement', '')
        status = req.get('status', 'not_met')
        is_mandatory = req.get('is_mandatory', False) or req.get('mandatory', False)
        years = req.get('years_of_experience', 0)

        # Check if the requirement name itself relates to testing
        if any(tk in req_name.lower() for tk in testing_keywords):
            if status == 'met':
                has_testing = True

        if status == 'met':
            if years >= 3:
                strengths.append(f"Strong {req_name} experience")
            elif years > 0:
                strengths.append(f"Good {req_name} exposure")
            else:
                strengths.append(f"Knowledge of {req_name}")
        else:
            missing_skills.append(req_name)
            if is_mandatory:
                risk_areas.append(f"Missing mandatory {req_name}")

    # 2. Risk Area: Low experience depth
    if experience_years > 0 and experience_years < jd_min_exp:
        risk_areas.append(f"Low career depth ({experience_years}y vs target {jd_min_exp}y+)")

    # 3. Risk Area: Missing domain skills
    has_domain = False
    if domain_experience:
        for dom in domain_experience:
            if dom.get('years', 0) > 0:
                has_domain = True
                break
    if not has_domain and domain_experience is not None:
        risk_areas.append("No proven domain-specific experience mentioned")

    # 4. Risk Area: Missing testing exposure
    if not has_testing:
        # Check if "testing" or related term is mentioned in the strengths
        all_skills_str = " ".join(strengths).lower()
        if not any(tk in all_skills_str for tk in testing_keywords):
            risk_areas.append("No explicit testing or verification experience listed")

    # 5. Risk Area: No recent activity (External Sourcing)
    if active_status:
        ast_lower = active_status.lower()
        if any(term in ast_lower for term in ["30+", "30 days", "month", "inactive", "older"]):
            risk_areas.append(f"Inactive profile (Last active: {active_status})")

    # 6. Risk Area: Long notice period
    if notice_period:
        np_lower = notice_period.lower()
        if any(term in np_lower for term in ["90", "3 month", "60", "2 month", "3-month", "2-month"]):
            risk_areas.append(f"Long notice period ({notice_period})")

    return {
        "strengths": strengths,
        "missing_skills": missing_skills,
        "risk_areas": risk_areas
    }


def generate_feedback_summary(jd_summary, matched_skills, requirements_analysis, project_insights, missing_skills, risk_areas):
    req_details = []
    for r in (requirements_analysis or []):
        status = r.get('status', 'unknown')
        req_name = r.get('requirement', '')
        yrs = r.get('years_of_experience', 0)
        evidence = r.get('evidence', '')
        req_details.append(f"- Requirement: {req_name} (Status: {status}, Years: {yrs}y, Evidence: {evidence})")
    
    req_details_str = "\n".join(req_details)
    
    project_details = []
    for p in (project_insights or []):
        project_details.append(f"- Project: {p.get('name', 'Project')} (Description: {p.get('description', '')})")
    proj_details_str = "\n".join(project_details)

    prompt = f"""
    Act as an elite technical recruiter reviewing a candidate for a hiring manager.
    Analyze the candidate's matched requirements, experience details, and project insights to write a professional review.
    
    JOB DESCRIPTION CONTEXT:
    {jd_summary}
    
    CANDIDATE MATCHED DETAILS:
    {req_details_str}
    
    PROJECT INSIGHTS:
    {proj_details_str}
    
    TASK:
    Write exactly 4 comprehensive, professional technical evaluation sentences summarizing the candidate's alignment.
    You MUST output exactly one sentence for each of the 4 patterns defined below. Do not omit any pattern!
    
    STRICT SENTENCE STRUCTURE RULES:
    You must output exactly 4 sentences, where each sentence strictly matches one of these specific recruiter patterns:
    1. "Strong experience in [matched skill/domain] with hands-on exposure to [tools, environments, sub-skills]."
    2. "Good knowledge in [diagnostic/validation/technology area] including [sub-concepts, verification details] across [domains/projects]."
    3. "Experience in [specific tech/feature validation] with [particular variables, protocols, features]."
    4. "Strong V&V / development background in [process/activities like requirement analysis, testing, Jira, etc.] across [project contexts]."
    
    ADDITIONAL RULES:
    1. GROUND EVERYTHING: Ground all tools, protocols, systems, and processes strictly in the candidate's actual matched details and projects.
    2. AVOID FLUFF: Do not use generic filler words, do not mention scores/percentages, and do not use recommendation tags like "Recommended", "Highly Recommended", or "Rejected".
    
    Return ONLY a valid JSON:
    {{
        "evaluation_bullets": [
            "Sentence 1 (matching pattern 1 exactly)",
            "Sentence 2 (matching pattern 2 exactly)",
            "Sentence 3 (matching pattern 3 exactly)",
            "Sentence 4 (matching pattern 4 exactly)"
        ]
    }}
    """

    try:
        raw = call_ollama(prompt, format_json=True)
        parsed = extract_json(raw)
        if parsed and parsed.get("evaluation_bullets"):
            bullets = parsed["evaluation_bullets"]
            if isinstance(bullets, list) and len(bullets) > 0:
                return {"evaluation_bullets": [b.strip() for b in bullets if b.strip()]}
    except Exception as e:
        print(f"Error calling LLM for feedback summary: {e}")

    # Fallback in case of Ollama timeout or error
    fallback = []
    # Sentence 1: Strong experience
    if matched_skills:
        fallback.append(f"Strong experience in {matched_skills[0]} with hands-on exposure to development and validation environments.")
    else:
        fallback.append("Strong technical background with professional experience matching domain requirements.")
        
    # Sentence 2: Good knowledge
    if len(matched_skills) > 1:
        fallback.append(f"Good knowledge in technical validation including {matched_skills[1]} across project lifecycles.")
    else:
        fallback.append("Good knowledge in system verification including functional testing and analysis.")
        
    # Sentence 3: Experience in
    if len(matched_skills) > 2:
        fallback.append(f"Experience in validation with {matched_skills[2]} integration and feature testing.")
    else:
        fallback.append("Experience in engineering workflows with system-level functional test execution.")
        
    # Sentence 4: Strong V&V background
    fallback.append("Strong V&V background in requirement analysis, test case creation, and regression testing across automotive/software projects.")
    
    return {"evaluation_bullets": fallback}



# app = Flask(__name__)

OLLAMA_API_URL = "http://10.153.204.33:11434/api/generate"
MODEL_NAME = "llama3:latest"

# Global lock — Naukri only allows ONE active Resdex session at a time.
# This prevents sourcing + market analysis from launching two Chromium windows simultaneously.
naukri_browser_lock = threading.Lock()
naukri_browser_in_use = {"by": None}  # tracks who is using it

executor = ThreadPoolExecutor(max_workers=1)

def call_ollama(prompt, format_json=False):
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0,
                "num_ctx": 8192
            }
        }
        if format_json:
            payload["format"] = "json"
            
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=180)
        response.raise_for_status()
        return response.json().get('response', '')
    except Exception as e:
        print(f"Ollama Error: {e}")
        return ""

def parse_date(date_str):
    if not date_str:
        return None
    date_str = date_str.lower().strip()
    if 'present' in date_str or 'current' in date_str or 'now' in date_str:
        return datetime.now()
    
    # Try parsing MM/YYYY
    for fmt in ("%m/%Y", "%m/%y", "%Y-%m-%d", "%Y-%m", "%B %Y", "%b %Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except:
            pass
            
    # Try parsing YYYY
    try:
        year = int(date_str)
        if 1900 <= year <= 2100:
            return datetime(year, 1, 1)
    except:
        pass
        
    # Regex fallback to extract year
    year_match = re.search(r'\b(19\d\d|20\d\d)\b', date_str)
    if year_match:
        year = int(year_match.group(1))
        # Try to find month words
        months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        month = 1
        for idx, m in enumerate(months):
            if m in date_str:
                month = idx + 1
                break
        return datetime(year, month, 1)
        
    return None

def calculate_total_experience_years(experience_blocks):
    intervals = []
    for block in experience_blocks:
        start = parse_date(block.get('start_date'))
        end = parse_date(block.get('end_date'))
        if start and end:
            if start > end:
                start, end = end, startos.environ.get
            intervals.append((start, end))
            
    if not intervals:
        return 0.0
        
    # Sort and merge overlapping intervals
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    for current in intervals[1:]:
        prev = merged[-1]
        if current[0] <= prev[1]:
            # Overlap, merge
            merged[-1] = (prev[0], max(prev[1], current[1]))
        else:
            merged.append(current)
            
    # Sum the durations in days
    total_days = sum((end - start).days for start, end in merged)
    return round(total_days / 365.25, 1)

def extract_json(text):
    if not text: return None
    try:
        # 1. Clean up potential markdown backticks
        text = text.strip()
        if "```" in text:
            text = re.search(r'\{.*\}', text, re.DOTALL).group(0)
            
        # 2. Find the first '{' and the last '}'
        start = text.find('{')
        end = text.rfind('}')
        if start == -1 or end == -1: return None
        
        json_str = text[start:end+1]
        
        # 3. Safe Repair Strategy
        # Remove inline comments (// ...) which are invalid in strict JSON
        json_str = re.sub(r'//.*', '', json_str)
        # Heal lazy LLM array truncation (e.g., [item1, item2, ..., itemN] or with trailing dots before close)
        json_str = re.sub(r',\s*\.\.\.\s*(,)?', r'\1', json_str)
        json_str = re.sub(r',\s*\.\.\.\s*([\]}])', r'\1', json_str)
        json_str = re.sub(r'\.\.\.', '', json_str)
        # Fix trailing commas (common LLM error that breaks json.loads)
        json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
        
        return json.loads(json_str)
    except Exception as e:
        print(f"DEBUG: Failed JSON string:\n{json_str}")
        # Final desperate attempt: raw load
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match: return json.loads(match.group(0))
        except:
            print(f"JSON Extract Error: {e}")
        return None

JSON_SCHEMA_PROMPT = """
    Return ONLY valid JSON in this structure:
    {
      "candidate_name": "Full Name",
      "email": "Email Address",
      "summary": "2-3 line professional executive summary",
      "experience_blocks": [
        {
          "title": "Job Title or Role",
          "company": "Company Name",
          "start_date": "MM/YYYY",
          "end_date": "MM/YYYY or Present",
          "description": "Full technical details of what they did",
          "skills_used": ["Skill1", "Skill2"]
        }
      ],
      "project_insights": [
        {
          "name": "Project Name",
          "start_date": "MM/YYYY (if available)",
          "end_date": "MM/YYYY (if available)",
          "description": "2-line technical summary of the project",
          "skills_used": ["Skill1", "Skill2"]
        }
      ]
    }

    STRICT RULES:
    1. Extract EVERY job and EVERY technical project.
    2. Use MM/YYYY dates.
    3. You MUST write a 2-3 line professional executive summary. DO NOT leave the 'summary' field blank.
    4. Return ONLY valid JSON.
"""

def extract_resume_structure(resume_text):
    prompt = f"""
    Analyze this resume and extract the full technical career history.
    
    {JSON_SCHEMA_PROMPT}

    Resume:
    {resume_text}
    """
    raw = call_ollama(prompt, format_json=False)
    return extract_json(raw) or {"experience_blocks": [], "project_insights": []}

def extract_jd_structure(jd_text):
    prompt = f"""
    Extract technical requirements from this Job Description (or search query).
    
    STRICT RULES:
    1. For each requirement, 'keywords' MUST be a list of atomic technical terms, common variations, abbreviations, singular/plural forms, and direct low-level technical equivalents (e.g., for 'Object-Oriented Design', include ["OOD", "OOP", "object-oriented", "classes"]; for 'Microcontrollers', include ["microcontrollers", "microcontroller", "mcu", "stm32", "pic"]; for 'HAL and MCAL', include ["HAL", "MCAL", "device driver", "driver", "bsp", "bootloader"]). This ensures search flexibility.
    2. NEVER include sentences.
    3. Return ONLY raw JSON.

    JSON FORMAT:
    {{
      "requirements": [
        {{
          "display_name": "short title",
          "keywords": [],
          "mandatory": true
        }}
      ]
    }}

    JD:
    {jd_text}
    """
    raw = call_ollama(prompt, format_json=False)
    print("DEBUG: RAW JD OUTPUT:", raw[:500] + "...")
    data = extract_json(raw)
    
    if data and data.get('requirements'):
        return data
        
    print("DEBUG: JD extraction failed or empty. Using deterministic fallback parser directly.", flush=True)
    requirements = []
    fallback_keywords = []
    
    # Split on commas, newlines, or logical operators
    import re
    raw_parts = re.split(r'\s+(?:AND|OR|and|or)\s+|,|\n', jd_text)
    for part in raw_parts:
        clean_part = re.sub(r'[\(\)"\']', '', part).strip()
        # Keep only reasonable length keywords (ignore full sentences in fallback)
        if clean_part and len(clean_part) < 40 and clean_part.upper() not in ("NOT", "AND", "OR", "VS", "THE", "AND/OR", "WITH", "IN"):
            fallback_keywords.append(clean_part)
            
    seen_kws = set()
    for kw in fallback_keywords:
        kw_lower = kw.lower()
        if kw_lower not in seen_kws:
            seen_kws.add(kw_lower)
            requirements.append({
                "display_name": kw,
                "keywords": [kw],
                "mandatory": True
            })
            
    return {"requirements": requirements}


def extract_text_from_docx(file_path):
    try:
        return docx2txt.process(file_path)
    except Exception as e:
        # Fallback: Try reading as plain text in case it's a mislabeled .txt file
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except:
            raise e


def ai_audit_match(jd_json, resume_json):
    """The 2nd Step: AI matches the Small JD to the Clean Resume JSON."""
    prompt = f"""
    Act as a Technical Recruiter.
    
    JD REQUIREMENTS:
    {json.dumps(jd_json)}
    
    CANDIDATE JSON:
    {json.dumps(resume_json)}
    
    TASK:
    1. Determine the candidate's PRIMARY DOMAIN (e.g., Web, Embedded, Sales).
    2. If the Primary Domain is NOT the same as the JD's domain, the Final Score MUST BE 3/10 OR LOWER. If they meet 0 mandatory requirements, the score MUST be exactly 0/10.
    3. For every requirement, find proof by checking BOTH 'experience_blocks' and 'project_insights'. If the proof is from a different technical context, mark it as 'partial' or 'not_met'.
    4. Calculate total tenure years across both experience blocks and projects.
    5. Provide a Final Score (0-10). A score of 7+ means they are a strong technical fit for the specific domain.

    SCORING RULES:
    1. NO SUMMARY GUESSING: Do not use general years from the candidate's 'summary' (e.g., '7 years of total experience') for a specific skill OR for the domain_experience. You MUST calculate years based strictly on chronological dates inside 'experience_blocks' or 'project_insights'.
    2. EVIDENCE STRICTNESS: You must find the exact keyword or direct equivalent. Do NOT assume a candidate has a specific skill just because of their general industry experience. If the requirement is not explicitly proven, years MUST be 0.
    3. DETERMINISTIC PENALTY: For every 'is_mandatory': true requirement that is 'not_met', subtract 1 point from the total score.
    4. ANTI-DOUBLE COUNTING (SKILLS & DOMAINS): When calculating years for a skill OR a domain, if a project's dates overlap with an experience block, do NOT count the overlapping years twice. Only count unique chronological time.
    5. CURRENT YEAR: If a date says "Present" or "Current", assume it means the year {datetime.now().year}.
    6. VAGUE DATES: If a candidate only provides years (e.g., "2021-2022") with no months, assume the minimum logical timeframe to prevent over-calculating.
    7. DOMAIN CAP: If the candidate's Primary Domain mismatches the JD domain, the score CANNOT exceed 3. If they meet 0 mandatory skills, the score MUST be 0.
    8. SPECIALIST RULE: If a core tool (e.g. DaVinci, AWS, React) is marked mandatory but is missing, the score CANNOT exceed 5.
    9. NO TRUNCATION OR PLACEHOLDERS: You MUST evaluate and output EVERY SINGLE requirement in the 'requirements_analysis' array. Do NOT skip, abbreviate, or use placeholders like '...' or '// rest of requirements'. Truncating this list will crash the system parser!

    RETURN ONLY RAW VALID JSON. DO NOT INCLUDE ANY MARKDOWN CODE BLOCKS (```).
    
    REQUIRED FORMAT:
    {{
      "requirements_analysis": [
        {{
          "requirement": "Requirement Name",
          "exact_matching_keyword": "Quote words inside ONE string (e.g., 'HAL, MCAL'). NEVER use multiple quotes like 'A' and 'B'. If missing, write 'NOT_FOUND'.",
          "status": "met/not_met",
          "years_of_experience": number,
          "evidence": "proof",
          "is_mandatory": true
        }}
      ],
      "domain_experience": [
        {{"domain": "Name", "years": number, "evidence": "Short proof of domain expertise"}}
      ],
      "final_score": number (integer only, do not write /10),
      "scoring_logic": "Explain score"
    }}
    """
    raw = call_ollama(prompt, format_json=False)
    print("DEBUG: AUDITOR RAW OUTPUT:", raw[:500] + "...")
    data = extract_json(raw)
    return data or {"requirements_analysis": [], "domain_experience": [], "final_score": 0}

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    result = register_user(
        name,
        email,
        password
    )

    return jsonify(result)

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()

    result = login_user(
        data.get("email"),
        data.get("password")
    )

    return jsonify(result)

@app.route(
    "/api/connect-naukri",
    methods=["POST"]
)
@jwt_required()
def connect_naukri():

    user_id = get_jwt_identity()

    profile_path = (
        get_or_create_profile(user_id)
    )

    return jsonify({
        "success": True,
        "profile_path": profile_path
    })

@app.route("/api/me", methods=["GET"])
@jwt_required()
def me():

    user_id = get_jwt_identity()

    return jsonify({
        "success": True,
        "user_id": user_id
    })



@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        jd_text = request.form.get('jd', '')
        files = request.files.getlist('resumes')

        if not jd_text or not files:
            return jsonify({"error": "Missing JD or resumes"}), 400

        # 1. READ ALL FILES FIRST (Before the request context closes)
        file_data = []
        for file in files:
            file_data.append((file.filename, file.read()))

        def generate():
            # 2. Extract JD Once
            structured_jd = extract_jd_structure(jd_text)

            def process_resume(file_info):
                file_name, file_content = file_info
                try:
                    filename = file_name.lower()
                    resume_text = ""
                    
                    if filename.endswith('.pdf'):
                        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                        for page in pdf_reader.pages:
                            resume_text += page.extract_text() + "\n"
                    elif filename.endswith('.docx'):
                        import docx2txt
                        temp_path = f"temp_{file_name}"
                        with open(temp_path, "wb") as f:
                            f.write(file_content)
                        resume_text = docx2txt.process(temp_path)
                        import os
                        os.remove(temp_path)
                    else:
                        resume_text = file_content.decode('utf-8', errors='ignore')

                    if len(resume_text) > 12000:
                        resume_text = resume_text[:6000] + "\n...[TRUNCATED]...\n" + resume_text[-6000:]

                    structured_resume = extract_resume_structure(resume_text)
                    analysis_report = ai_audit_match(structured_jd, structured_resume)

                    # --- PYTHON TRUTH-CHECKER FIREWALL ---
                    resume_lower = resume_text.lower()
                    final_score = analysis_report.get('final_score', 0)
                    requirements_analysis = analysis_report.get('requirements_analysis', [])
                    
                    for req in requirements_analysis:
                        # 1. Confession Override: If the AI itself writes "not_found" in evidence or keyword, instantly fail it.
                        evidence_lower = req.get('evidence', '').lower()
                        kw_lower = req.get('exact_matching_keyword', '').lower()
                        if 'not_found' in evidence_lower or 'not_found' in kw_lower:
                            req['status'] = 'not_met'
                            req['years_of_experience'] = 0
                            req['evidence'] = f"Evidence Verification: Required keywords not found in resume."
                            if req.get('is_mandatory', False):
                                final_score = max(0, final_score - 1)
                            continue

                        if req.get('status') == 'met' or req.get('years_of_experience', 0) > 0:
                            req_name = req.get('requirement', '').lower().strip()
                            # Find the original keywords using a fuzzy substring match
                            valid_keywords = []
                            for jd_req in structured_jd.get('requirements', []):
                                jd_name = jd_req.get('display_name', '').lower().strip()
                                if jd_name == req_name or jd_name in req_name or req_name in jd_name:
                                    valid_keywords = [k.lower() for k in jd_req.get('keywords', [])]
                                    break
                            
                            if valid_keywords:
                                found = False
                                for kw in valid_keywords:
                                    kw_clean = kw.lower().strip()
                                    if kw_clean in resume_lower:
                                        found = True
                                        break
                                    # Singular match for plural keywords (e.g., microcontrollers -> microcontroller)
                                    if kw_clean.endswith('s') and len(kw_clean) > 3 and kw_clean[:-1] in resume_lower:
                                        found = True
                                        break
                                
                                if not found:
                                    # Overwrite the AI's hallucination!
                                    req['status'] = 'not_met'
                                    req['years_of_experience'] = 0
                                    req['evidence'] = f"Evidence Verification: Required keywords not found in resume."
                                    
                                    # Apply the deterministic penalty
                                    if req.get('is_mandatory', False):
                                        final_score = max(0, final_score - 1)
                    
                    # Calculate total career duration in Python to prevent domain experience hallucination
                    total_career_years = calculate_total_experience_years(structured_resume.get('experience_blocks', []))
                    
                    # Cap individual skill experience years at total career years
                    for req in requirements_analysis:
                        skill_years = req.get('years_of_experience', 0)
                        if total_career_years > 0.0 and skill_years > total_career_years:
                            req['years_of_experience'] = total_career_years
                            req['evidence'] = (req.get('evidence', '') + 
                                               f" [Audit Adjustment: Experience capped at career limit of {total_career_years}y]")
                    
                    domain_experience = analysis_report.get('domain_experience', [])
                    for domain in domain_experience:
                        domain_years = domain.get('years', 0)
                        if total_career_years > 0.0 and domain_years > total_career_years:
                            domain['years'] = total_career_years
                    
                    # --- DYNAMIC ARITHMETIC HYBRID SCORING ENGINE ---
                    mandatory_reqs = [r for r in requirements_analysis if r.get('is_mandatory', False)]
                    if mandatory_reqs:
                        met_count = sum(1 for r in mandatory_reqs if r.get('status') == 'met')
                        calc_score = round((met_count / len(mandatory_reqs)) * 10)
                        
                        # Special Case 1: 0/10 if they met exactly 0 skills
                        if met_count == 0:
                            final_score = 0
                        else:
                            # Special Case 2: Preserve AI's Domain Cap (Capped at 3 if there's a domain mismatch)
                            ai_original_score = analysis_report.get('final_score', 0)
                            if ai_original_score <= 3 and calc_score > 3:
                                final_score = 3
                            else:
                                final_score = calc_score
                    else:
                        final_score = 0
                    
                    analysis_report['final_score'] = final_score
                    # --- END TRUTH-CHECKER ---

                    # Parse target experience range from JD text directly
                    jd_min_exp = 2
                    import re
                    exp_match = re.search(r'(\d+)\s*-\s*(\d+)\s*(?:years?|yrs?)', jd_text.lower())
                    if exp_match:
                        jd_min_exp = int(exp_match.group(1))

                    # ── Calculate deterministic feedback signals ──
                    signals = generate_feedback_signals(
                        requirements_analysis=requirements_analysis,
                        match_percentage=final_score * 10,
                        jd_min_exp=jd_min_exp,
                        experience_years=total_career_years,
                        domain_experience=domain_experience
                    )
                    
                    # ── Summarize overall narrative via lightweight Ollama ──
                    summary = generate_feedback_summary(
                        jd_summary=jd_text[:300], 
                        matched_skills=signals['strengths'],
                        requirements_analysis=requirements_analysis,
                        project_insights=structured_resume.get('project_insights', []),
                        missing_skills=signals['missing_skills'],
                        risk_areas=signals['risk_areas']
                    )

                    return {
                        "filename": file_name,
                        "candidate_name": structured_resume.get('candidate_name', 'Unknown'),
                        "score": final_score,
                        "summary": structured_resume.get('summary', ''),
                        "requirements_analysis": requirements_analysis,
                        "domain_experience": domain_experience,
                        "project_insights": structured_resume.get('project_insights', []),
                        "scoring_logic": analysis_report.get('scoring_logic', ''),
                        "feedback": {
                            "evaluation_bullets": summary.get('evaluation_bullets', [])
                        }
                    }
                except Exception as e:
                    return {"filename": file_name, "error": str(e)}

            # Execute all resumes in parallel using the executor
            from concurrent.futures import as_completed
            futures = [executor.submit(process_resume, info) for info in file_data]
            
            for future in as_completed(futures):
                result = future.result()
                yield json.dumps(result) + "\n"

        return Response(generate(), mimetype='text/event-stream')

    except Exception as e:
        print(f"Global Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/source', methods=['POST'])
# @jwt_required()
def source():
    # user_id = get_jwt_identity()
    user_id = 1
    print(f"Source request from user {user_id}")
    # profile_path = get_profile_path(user_id)
    profile_path = "naukri_profile"
    print(profile_path)
    if 'jd' not in request.form:
        return jsonify({"error": "Missing job description"}), 400
    
    jd = request.form['jd']
    page_num = int(request.form.get('page', 1))
    
    print(f"--- SOURCING REQUEST RECEIVED (Page {page_num}) ---", flush=True)
    
    keywords = sourcing_agent.get_search_keywords(jd)
    
    # Perform the real authenticated search
    # Acquire the browser lock — Naukri only allows ONE session at a time
    if not naukri_browser_lock.acquire(blocking=False):
        busy_by = naukri_browser_in_use.get('by', 'another task')
        return jsonify({'error': f'Naukri browser is currently busy ({busy_by}). Please wait and try again.'}), 429
    
    naukri_browser_in_use['by'] = 'Sourcing'
    try:
        raw_leads = asyncio.run(sourcing_agent.perform_authenticated_search(
            keywords, 
            min_exp=keywords.get('min_exp', 2), 
            max_exp=keywords.get('max_exp', 8),
            page_num=page_num
        ))
    except Exception as e:
        print(f"Async search error: {e}")
        raw_leads = []
        other_candidates = []
    finally:
        naukri_browser_in_use['by'] = None
        naukri_browser_lock.release()
        
    # Unpack the new dict structure from the scraper
    if isinstance(raw_leads, dict) and "deep_results" in raw_leads:
        other_candidates = raw_leads.get("other_candidates", [])
        raw_leads = raw_leads.get("deep_results", [])
    else:
        other_candidates = []
        
    # Check if raw_leads returned a session error dictionary
    if isinstance(raw_leads, dict) and "error" in raw_leads:
        err_type = raw_leads["error"]
        if err_type == "session_expired":
            return jsonify({
                "error": "Your Naukri Resdex session has expired or requires authentication.<br><br>"
                         "<a href='https://resdex.naukri.com' target='_blank' "
                         "style='color:#8b5cf6; font-weight:bold; text-decoration:underline; font-size:1.1rem; display:inline-block; margin-top:10px;'>"
                         "🔑 Click here to open Resdex & log in manually</a>"
            }), 400
        elif err_type == "session_locked":
            return jsonify({
                "error": "Someone is already logged into Resdex with this username.<br><br>"
                         "<a href='https://resdex.naukri.com' target='_blank' "
                         "style='color:#8b5cf6; font-weight:bold; text-decoration:underline; font-size:1.1rem; display:inline-block; margin-top:10px;'>"
                         "🔗 Click here to open Resdex & Reset Subuser manually</a>"
            }), 400
    
    import concurrent.futures
    import re
    
    # 1. Extract clean structured requirements from the JD
    try:
        structured_jd = extract_jd_structure(jd)
        requirements = structured_jd.get('requirements', [])
    except Exception as jd_err:
        print(f"Error extracting JD structure: {jd_err}")
        requirements = []
        
    # FALLBACK: If Ollama fails, build requirements from search keywords!
    if not requirements:
        print("Ollama extraction failed or timed out. Initiating deterministic keyword fallback...", flush=True)
        fallback_keywords = []
        clean_query = keywords.get('boolean_query', jd)
        
        # Split on logical operators (AND, OR) case-insensitively
        raw_parts = re.split(r'\s+(?:AND|OR|and|or)\s+', clean_query)
        for part in raw_parts:
            # Strip outer parentheses, quotes, and whitespace
            clean_part = re.sub(r'[\(\)"\']', '', part).strip()
            if clean_part and clean_part.upper() not in ("NOT", "AND", "OR", "VS", "THE", "AND/OR"):
                fallback_keywords.append(clean_part)
                
        # Deduplicate case-insensitively
        seen_kws = set()
        for kw in fallback_keywords:
            kw_lower = kw.lower()
            if kw_lower not in seen_kws:
                seen_kws.add(kw_lower)
                requirements.append({
                    "display_name": kw,
                    "keywords": [kw],
                    "mandatory": True
                })
        print(f"Fallback requirements generated: {requirements}", flush=True)
    
    def analyze_lead(lead):
        # 2. Extract and clean the scraped experience text
        experience_text = lead.get('experience_text', '').lower().strip()
        
        matched_skills = []
        matched_sentences = []
        requirements_analysis = []
        
        # Split text into clean sentences for context finding
        # Split on periods, exclamation marks, question marks, AND newlines (profile text uses newlines heavily)
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+|\t+', experience_text) if len(s.strip()) > 15]

        def clean_evidence(sentence, keyword):
            """Return a clean 1-2 line evidence snippet (max 200 chars)."""
            if not sentence:
                return ""
            # Remove noise: lines that are only skill names, table headers, URLs, or single words
            noise_patterns = [
                r'^https?://',            # URLs
                r'^\d+\s*(y|m|year)',     # "9y" "5 years"
                r'^[\w\s]{1,20}$',        # Very short fragments (skill names alone)
            ]
            for pattern in noise_patterns:
                if re.match(pattern, sentence.strip(), re.IGNORECASE):
                    # Try to find a better nearby sentence containing the keyword
                    for s in sentences:
                        if keyword in s.lower() and len(s) > 30 and not re.match(pattern, s.strip(), re.IGNORECASE):
                            sentence = s
                            break
            # Hard cap at 200 characters, end at last word boundary
            if len(sentence) > 200:
                sentence = sentence[:200].rsplit(' ', 1)[0] + '…'
            return sentence.strip()


        # 3. Deterministic Python Keyword Matching against Experience & Projects ONLY
        for req in requirements:
            req_name = req.get('display_name', '')
            valid_keywords = [k.lower().strip() for k in req.get('keywords', [])]
            is_mandatory = req.get('mandatory', False)
            
            found = False
            matching_keyword = ""
            matching_sentence = ""
            
            if valid_keywords:
                for kw in valid_keywords:
                    # Direct check of whole phrase
                    if kw in experience_text:
                        found = True
                        matching_keyword = kw
                        for s in sentences:
                            if kw in s.lower():
                                matching_sentence = clean_evidence(s.strip(), kw)
                                break
                        break
                    
                    # Singular check
                    if kw.endswith('s') and len(kw) > 3 and kw[:-1] in experience_text:
                        found = True
                        matching_keyword = kw[:-1]
                        for s in sentences:
                            if kw[:-1] in s.lower():
                                matching_sentence = clean_evidence(s.strip(), kw[:-1])
                                break
                        break
                        
                    # Flexible sub-word check for multi-word concepts
                    sub_words = [w.strip() for w in kw.split() if len(w.strip()) > 1]
                    if len(sub_words) > 1 and all(w in experience_text for w in sub_words):
                        found = True
                        matching_keyword = sub_words[0]
                        for s in sentences:
                            if any(w in s.lower() for w in sub_words):
                                matching_sentence = clean_evidence(s.strip(), sub_words[0])
                                break
                        break
            
            if found:
                matched_skills.append(req_name)
                if matching_sentence and matching_sentence not in matched_sentences:
                    matched_sentences.append(matching_sentence)
                requirements_analysis.append({
                    "requirement": req_name,
                    "status": "met",
                    "exact_matching_keyword": matching_keyword,
                    "evidence": matching_sentence,
                    "years_of_experience": 0,   # placeholder — will be filled by AI below
                    "is_mandatory": is_mandatory
                })
            else:
                requirements_analysis.append({
                    "requirement": req_name,
                    "status": "not_met",
                    "exact_matching_keyword": "NOT_FOUND",
                    "evidence": "Required keywords not found in scraped experience.",
                    "years_of_experience": 0,
                    "is_mandatory": is_mandatory
                })
        
        # 3b. Single batched AI call to calculate years of experience for MET skills only
        if matched_skills and experience_text:
            from datetime import datetime
            current_year = datetime.now().year
            years_prompt = f"""
You are a strict date calculator. Your job is to calculate how many years of experience a candidate has with specific skills, based ONLY on explicit date ranges found in their resume/profile text.

STRICT RULES (to prevent hallucination):
1. ONLY count years from explicit date ranges like "Jan 2020 - Dec 2022", "2019 - Present", "Jul '18 to Mar '22". 
2. If "Present" or "Current" appears, treat it as the year {current_year}.
3. Do NOT count overlapping periods twice. If two jobs overlap in dates, count only unique time.
4. If a skill is mentioned but NO date range is nearby or attributable to it, return 0. Do NOT guess.
5. If a date says only a year (e.g. "2021-2022") with no months, assume exactly 1 year.
6. Do NOT use general statements like "5+ years of experience" — only use actual date ranges.
7. Round to nearest 0.5 years.

Skills to calculate (ONLY these, already confirmed present in the text):
{', '.join(matched_skills)}

Resume/Profile Text:
{experience_text[:3000]}

Return ONLY valid JSON in this exact format. No extra text:
{{
    "skill_years": {{
        "SkillName": years_as_number,
        "AnotherSkill": years_as_number
    }}
}}
"""
            try:
                payload = {"model": MODEL_NAME, "prompt": years_prompt, "stream": False, "format": "json"}
                response = requests.post(OLLAMA_API_URL, json=payload, timeout=25)
                raw = response.json().get('response', '')
                parsed = extract_json(raw)
                if parsed and 'skill_years' in parsed:
                    skill_years_map = parsed['skill_years']
                    # Patch the years_of_experience into the requirements_analysis entries
                    for req_entry in requirements_analysis:
                        if req_entry['status'] == 'met':
                            skill_name = req_entry['requirement']
                            # Case-insensitive lookup
                            for key, val in skill_years_map.items():
                                if key.lower().strip() == skill_name.lower().strip():
                                    req_entry['years_of_experience'] = val if isinstance(val, (int, float)) and val >= 0 else 0
                                    break
                    print(f"✅ AI year calculation complete for {len(matched_skills)} met skills.", flush=True)
            except Exception as yr_err:
                print(f"⚠️ AI year calculation failed (non-fatal): {yr_err}", flush=True)
                # Leave years_of_experience as 0 — non-fatal, matching still works
        

        # 4. Calculate Mathematical Arithmetic Match Score (Zero-Tolerance)
        mandatory_reqs = [r for r in requirements if r.get('mandatory', False)]
        if mandatory_reqs:
            met_mandatory_count = sum(
                1 for req_name in matched_skills 
                if any(r.get('display_name') == req_name and r.get('mandatory', False) for r in mandatory_reqs)
            )
            calc_score = round((met_mandatory_count / len(mandatory_reqs)) * 10)
            match_percentage = calc_score * 10
        elif requirements:
            met_count = sum(1 for req_name in matched_skills if any(r.get('display_name') == req_name for r in requirements))
            calc_score = round((met_count / len(requirements)) * 10)
            match_percentage = calc_score * 10
        else:
            match_percentage = 50 # Default fallback
            
        # 5. Use AI to extract structured project_insights (same as internal screening)
        exp_text_full = lead.get('experience_text', '')
        project_insights = []
        context_evidence = "No direct project or work experience found for mandatory technical requirements."

        # Get the most relevant section of the resume to parse
        if "=== ATTACHED RESUME ===" in exp_text_full:
            resume_section = exp_text_full.split("=== ATTACHED RESUME ===")[-1].strip()
        elif "=== PROJECTS ===" in exp_text_full:
            resume_section = exp_text_full.split("=== WORK EXPERIENCE ===")[-1].strip() if "=== WORK EXPERIENCE ===" in exp_text_full else exp_text_full
        elif "=== WORK EXPERIENCE ===" in exp_text_full:
            resume_section = exp_text_full.split("=== WORK EXPERIENCE ===")[-1].strip()
        else:
            resume_section = exp_text_full.strip()

        if resume_section and matched_skills:
            # AI extracts structured project list (identical to internal screening)
            project_prompt = f"""
            Act as a Technical Recruiter analyzing a candidate's resume/profile text.
            Extract all distinct projects or work assignments mentioned in the text below.

            STRICT RULES:
            1. Each project must have a clear name and a 1-2 sentence description based ONLY on the text.
            2. Do NOT invent or assume any details not present in the text.
            3. Return ONLY valid JSON.

            JSON FORMAT:
            {{
                "project_insights": [
                    {{"name": "Project or Role Name", "description": "What they did, technologies used, based strictly on the text."}}
                ]
            }}

            Resume/Profile Text:
            {resume_section[:3000]}
            """/api/analyze
            try:
                payload = {"model": MODEL_NAME, "prompt": project_prompt, "stream": False, "format": "json"}
                response = requests.post(OLLAMA_API_URL, json=payload, timeout=30)
                raw = response.json().get('response', '')
                parsed = extract_json(raw)
                if parsed and parsed.get('project_insights'):
                    project_insights = parsed['project_insights']
            except Exception as ai_err:
                print(f"Error calling AI for project insights: {ai_err}")

        if not project_insights and resume_section:
            project_insights = [{"name": "Experience from Profile", "description": resume_section[:500] + ("..." if len(resume_section) > 500 else "")}]

        # Parse experience years for risk checking
        def parse_exp_years(exp_str):
            if not exp_str or exp_str == "N/A":
                return 0
            m = re.search(r'(\d+(?:\.\d+)?)\s*(?:yrs?|years?|yr\b|y\b)', exp_str, re.IGNORECASE)
            if m:
                return int(float(m.group(1)))
            m2 = re.search(r'(\d+)', exp_str)
            return int(m2.group(1)) if m2 else 0

        exp_years = parse_exp_years(lead.get('experience', ''))
        jd_min_exp = keywords.get('min_exp', 2)

        # ── Calculate deterministic feedback signals ──
        signals = generate_feedback_signals(
            requirements_analysis=requirements_analysis,
            match_percentage=match_percentage,
            jd_min_exp=jd_min_exp,
            experience_years=exp_years,
            domain_experience=None,
            active_status=lead.get('active_status', ''),
            notice_period=lead.get('notice_period', '')
        )

        # ── Summarize overall narrative via lightweight Ollama ──
        summary = generate_feedback_summary(
            jd_summary=jd[:300], 
            matched_skills=matched_skills,
            requirements_analysis=requirements_analysis,
            project_insights=project_insights,
            missing_skills=signals['missing_skills'],
            risk_areas=signals['risk_areas']
        )

        context_evidence = f"Verified experience in: {', '.join(matched_skills[:3]) if matched_skills else 'domain'}."

        lead.update({
            "match_percentage": match_percentage,
            "matched_skills": matched_skills,
            "context_evidence": context_evidence,
            "project_insights": project_insights,
            "requirements_analysis": requirements_analysis,
            "scoring_logic": f"Deterministically matched {match_percentage}% of mandatory requirements from Resdex profile.",
            "feedback": {
                "evaluation_bullets": summary.get('evaluation_bullets', [])
            }
        })
        return lead

    print(f"Analyzing {len(raw_leads)} candidates in parallel...", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        analyzed_leads = list(executor.map(analyze_lead, raw_leads))
    
    results = sourcing_agent.simulate_naukri_search(keywords)
    results["simulated_leads"] = analyzed_leads
    results["other_candidates"] = other_candidates
    results["status"] = f"Found and analyzed {len(analyzed_leads)} candidates on page {page_num}."
    
    return jsonify(results)


@app.route('/api/market-analysis', methods=['POST'])
# @jwt_required()
def market_analysis():

    # user_id = get_jwt_identity()
    user_id = 1
    print(f"Source request from user {user_id}")
    data = request.get_json()
    jd = data.get('jd', '').strip()
    if not jd:
        return jsonify({'error': 'No JD provided'}), 400

    # Get search keywords from JD
    keywords_data = sourcing_agent.get_search_keywords(jd, for_market_analysis=True)
    query = keywords_data.get('boolean_query', ' '.join(keywords_data.get('primary_keywords', [])))
    jd_min_exp = keywords_data.get('min_exp', 2)
    jd_max_exp = keywords_data.get('max_exp', 10)

    # ⚠️ Market Analysis: scan ALL experience levels (0-25y) to get the full market picture.
    # The JD's target range is shown as reference — NOT used to filter Naukri results.
    MARKET_MIN_EXP = 0
    MARKET_MAX_EXP = 25

    print(f"📊 Starting AI Talent Market Intelligence Engine scan. Query: {query} | Full range: {MARKET_MIN_EXP}-{MARKET_MAX_EXP}y | JD target: {jd_min_exp}-{jd_max_exp}y", flush=True)

    # Acquire the browser lock — Naukri only allows ONE session at a time
    if not naukri_browser_lock.acquire(blocking=False):
        busy_by = naukri_browser_in_use.get('by', 'another task')
        return jsonify({'error': f'Naukri browser is currently busy ({busy_by}). Please wait for it to finish and try again.'}), 429

    naukri_browser_in_use['by'] = 'Market Analysis'
    try:
        # Scan up to 15 pages (600 candidates) to capture the complete market talent pool
        candidates = asyncio.run(sourcing_agent.market_scan_search(keywords_data, MARKET_MIN_EXP, MARKET_MAX_EXP, max_pages=15))
    except Exception as e:
        print(f"Market scan error: {e}", flush=True)
        candidates = []
    finally:
        naukri_browser_in_use['by'] = None
        naukri_browser_lock.release()

    if not candidates:
        return jsonify({'error': 'No candidates found. Check Naukri session.'}), 404

    # ── Parse Requirements from JD (for scoring) ───────────────────────────
    try:
        # Reuse existing sourcing agent logic
        structured_jd = extract_jd_structure(jd)
        requirements = structured_jd.get('requirements', [])

    except Exception as jd_err:
        print(f"Ollama requirements extraction error: {jd_err}")
        requirements = []

    # FALLBACK: If Ollama fails, build requirements from search keywords!
    if not requirements:
        print("Ollama extraction failed. Building requirements from search keywords...", flush=True)
        primary_kws = keywords_data.get('primary_keywords', [])
        secondary_kws = keywords_data.get('secondary_keywords', [])
        for kw in primary_kws:
            requirements.append({
                "display_name": kw,
                "keywords": [kw],
                "mandatory": True
            })
        for kw in secondary_kws:
            requirements.append({
                "display_name": kw,
                "keywords": [kw],
                "mandatory": False
            })

    # ── Parallelized Deterministic Scoring ─────────────────────────────────
    scored_candidates = []
    print(f"⚡ Parallel scoring {len(candidates)} candidates using ThreadPoolExecutor...", flush=True)
    with ThreadPoolExecutor(max_workers=5) as p_executor:
        futures = {p_executor.submit(market_analyze_candidate, c, requirements, jd_min_exp, jd_max_exp): c for c in candidates}

        for future in concurrent.futures.as_completed(futures):
            try:
                res = future.result()
                scored_candidates.append(res)
            except Exception as score_err:
                print(f"Error scoring individual candidate: {score_err}")

    # Calculate summary stats across ALL experience levels
    def parse_exp_years(exp_str):
        if not exp_str or exp_str == "N/A":
            return None
        m = re.search(r'(\d+(?:\.\d+)?)\s*(?:yrs?|years?|yr\b|y\b)', exp_str, re.IGNORECASE)
        if m:
            return int(float(m.group(1)))
        m2 = re.search(r'(\d+)', exp_str)
        return int(m2.group(1)) if m2 else None

    # KPI Accumulators
    buckets = {"0-3y": 0, "3-5y": 0, "5-7y": 0, "7-9y": 0, "9-12y": 0, "12y+": 0}
    match_distribution = {"90-100": 0, "80-89": 0, "70-79": 0, "60-69": 0, "<60": 0}
    
    active_30 = sum(1 for c in scored_candidates if c.get('is_active_30d') is True)
    notice_30 = sum(1 for c in scored_candidates if '30' in str(c.get('notice_period', '')) or 'immediate' in str(c.get('notice_period', '')).lower())
    in_target = 0
    total_match_score = 0
    high_quality_pool = 0
    active_high_quality_pool = 0
    immediate_joiner_pool = 0
    
    # Skill aggregation
    skill_counts = {}

    for c in scored_candidates:
        yrs = parse_exp_years(c['experience'])
        c['in_target_range'] = False
        if yrs is not None:
            c['in_target_range'] = jd_min_exp <= yrs <= jd_max_exp
            if c['in_target_range']:
                in_target += 1
            # Bucket
            if yrs < 3:    buckets["0-3y"] += 1
            elif yrs < 5:  buckets["3-5y"] += 1
            elif yrs < 7:  buckets["5-7y"] += 1
            elif yrs < 9:  buckets["7-9y"] += 1
            elif yrs < 12: buckets["9-12y"] += 1
            else:          buckets["12y+"] += 1

        # Match percentage metrics
        mp = c.get('match_percentage', 0)
        total_match_score += mp
        
        # Match Distribution Buckets
        if mp >= 90:   match_distribution["90-100"] += 1
        elif mp >= 80: match_distribution["80-89"] += 1
        elif mp >= 70: match_distribution["70-79"] += 1
        elif mp >= 60: match_distribution["60-69"] += 1
        else:          match_distribution["<60"] += 1

        # Quality pools
        if mp >= 80:
            high_quality_pool += 1
            if c.get('is_active_30d') is True:
                active_high_quality_pool += 1
        
        # Immediate Joiner Pool (60%+ match + short notice)
        is_short_notice = '30' in str(c.get('notice_period', '')) or 'immediate' in str(c.get('notice_period', '')).lower()
        if mp >= 60 and is_short_notice:
            immediate_joiner_pool += 1

        # Skills Aggregation & Normalization
        c_skills = c.get('skills', '') or ''
        # Naukri skills are piped/comma separated
        raw_skills_list = re.split(r'[|,\n]', c_skills)
        for s_raw in raw_skills_list:
            s_clean = s_raw.replace('Key skills', '').strip()
            if s_clean and s_clean.lower() != 'n/a':
                norm = normalize_skill(s_clean)
                
                # Keep the candidate's exact original capitalization (e.g., 'CATIA V5', 'AutoCAD')
                display_name = s_clean
                
                # Automatically capitalize short abbreviations or acronyms (e.g. 'cad' -> 'CAD', 'hvac' -> 'HVAC')
                if len(display_name) <= 4:
                    display_name = display_name.upper()

                
                skill_counts[norm] = skill_counts.get(norm, {"name": display_name, "count": 0})
                skill_counts[norm]["count"] += 1

    total = len(scored_candidates)
    avg_match_score = round(total_match_score / total) if total else 0

    # Deduplicated Top Skills list
    top_skills = sorted(skill_counts.values(), key=lambda x: x['count'], reverse=True)[:10]

    # ── Market Intelligence Calculations ────────────────────────────────────
    from collections import Counter

    # Availability Score (0-100): weighted by active + short notice + target match
    active_pct  = (active_30 / total * 100) if total else 0
    notice_pct  = (notice_30 / total * 100) if total else 0
    target_pct  = (in_target / total * 100) if total else 0
    availability_score = round(min(100, (active_pct * 0.5 + notice_pct * 0.3 + target_pct * 0.2)))

    # Supply Tightness
    if in_target >= 30:   tightness = "High Supply"
    elif in_target >= 12: tightness = "Moderate Supply"
    elif in_target >= 5:  tightness = "Low Supply"
    else:                 tightness = "Scarce"

    # Market Health Classification
    if total >= 100 and high_quality_pool >= 20:   market_health = "Strong"
    elif total >= 50 and high_quality_pool >= 10:   market_health = "Moderate"
    elif total >= 20 and high_quality_pool >= 3:    market_health = "Tight"
    else:                                           market_health = "Scarce"

    # Hiring Difficulty
    if active_high_quality_pool >= 15:    hiring_difficulty = "Low"
    elif active_high_quality_pool >= 5:     hiring_difficulty = "Medium"
    elif active_high_quality_pool >= 1:     hiring_difficulty = "High"
    else:                                   hiring_difficulty = "Very High"

    # Top companies (parse from 'current' field e.g. "Senior Engineer at Capgemini")
    company_names = []
    for c in scored_candidates:
        cur = c.get('current', '')
        if ' at ' in cur:
            company_names.append(cur.split(' at ')[-1].strip())
        elif cur and cur != 'N/A':
            company_names.append(cur.strip())
    top_companies = [{"name": k, "count": v} for k, v in Counter(company_names).most_common(6) if k]

    # Top cities
    city_names = [c.get('location', '').split(',')[0].strip() for c in scored_candidates if c.get('location') and c.get('location') != 'N/A']
    top_cities = [{"name": k, "count": v} for k, v in Counter(city_names).most_common(6) if k]

    # ── AI Narrative via Ollama ──────────────────────────────────────────────
    dist_text = ", ".join([f"{k}: {v}" for k, v in buckets.items() if v > 0])
    company_text = ", ".join([f"{c['name']} ({c['count']})" for c in top_companies[:4]])
    city_text = ", ".join([f"{c['name']} ({c['count']})" for c in top_cities[:4]])

    narrative_prompt = f"""You are a Senior Talent Market Analyst. Write a 4-5 sentence professional market intelligence brief.

Data:
- Role requirement: {jd[:120]}
- Total candidates found with relevant skills: {total}
- JD target experience: {jd_min_exp}-{jd_max_exp} years → {in_target} candidates match ({round(target_pct)}%)
- Active in last 30 days: {active_30} ({round(active_pct)}%)
- Available with short notice (≤30 days): {notice_30}
- Experience distribution: {dist_text}
- Top hiring companies (candidate sources): {company_text}
- Top cities: {city_text}
- Availability Score: {availability_score}/100
- Market Tightness: {tightness}
- Market Health: {market_health}
- Hiring Difficulty: {hiring_difficulty}

Write ONLY the brief paragraph. Be direct, analytical, and professional. Use concrete numbers. Include a hiring recommendation."""

    narrative = call_ollama(narrative_prompt).strip()
    if not narrative:
        narrative = (f"The talent pool for this role shows {total} candidates with relevant skills on Naukri. "
                     f"Of these, {in_target} ({round(target_pct)}%) fall within the target {jd_min_exp}-{jd_max_exp} year experience range. "
                     f"Market availability is {'high' if availability_score > 60 else 'moderate' if availability_score > 35 else 'tight'} "
                     f"with {active_30} candidates active in the last 30 days.")

    # Sort Candidates for display: High Match first, then active
    sorted_candidates = sorted(
        scored_candidates,
        key=lambda x: (x.get('match_percentage', 0), 1 if x.get('is_active_30d') else 0),
        reverse=True
    )

    # Return all matched candidates to display in the UI list, sorted by match percentage
    top_display_candidates = sorted_candidates

    return jsonify({
        "top_candidates": top_display_candidates,
        "candidates": sorted_candidates,

        "summary": {
            "total": total,
            "active_30d": active_30,
            "notice_30d": notice_30,
            "in_target_range": in_target,
            "exp_distribution": buckets,
            "query": query,
            "jd_target_range": f"{jd_min_exp}-{jd_max_exp} years",
            "generated": datetime.now().strftime('%d %b %Y %H:%M'),
            "availability_score": availability_score,
            "tightness": tightness,
            "top_companies": top_companies,
            "top_cities": top_cities,
            "narrative": narrative,
            
            # New Intelligence Fields
            "avg_match_score": avg_match_score,
            "high_quality_pool": high_quality_pool,
            "active_high_quality_pool": active_high_quality_pool,
            "immediate_joiner_pool": immediate_joiner_pool,
            "market_health": market_health,
            "hiring_difficulty": hiring_difficulty,
            "match_distribution": match_distribution,
            "top_skills": top_skills
        }
    })



@app.route('/api/export-market-excel', methods=['POST'])
def export_market_excel():
    """Accepts candidate data from frontend and returns a styled Excel file."""
    data = request.get_json()
    candidates = data.get('candidates', [])
    summary = data.get('summary', {})
    jd_snippet = data.get('jd_snippet', '')

    if not candidates:
        return jsonify({'error': 'No data to export'}), 400

    wb = openpyxl.Workbook()
    HEADER_BG = "1F3864"; HEADER_FG = "FFFFFF"
    ACTIVE_BG = "E2EFDA"; INACTIVE_BG = "FCE4D6"; ALT_ROW_BG = "F2F2F2"; ACCENT_BG = "BDD7EE"
    thin = Side(style='thin', color='CCCCCC')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    def hdr_cell(ws, row, col, value, width=20):
        c = ws.cell(row=row, column=col, value=value)
        c.font = Font(bold=True, color=HEADER_FG, size=11)
        c.fill = PatternFill('solid', fgColor=HEADER_BG)
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        c.border = border
        ws.column_dimensions[get_column_letter(col)].width = width
        return c

    def data_cell(ws, row, col, value, bg=None, bold=False, link=None):
        c = ws.cell(row=row, column=col, value=value)
        c.font = Font(bold=bold, color="0563C1" if link else "000000", underline="single" if link else None, size=10)
        if bg: c.fill = PatternFill('solid', fgColor=bg)
        c.alignment = Alignment(vertical='center', wrap_text=True)
        c.border = border
        if link: c.hyperlink = link
        return c

    # Sheet 1: Candidate Pool
    ws1 = wb.active
    ws1.title = "Candidate Pool"
    ws1.row_dimensions[1].height = 40
    ws1.merge_cells('A1:K1')
    title_cell = ws1['A1']
    title_cell.value = f"📊 Market Analysis  |  {jd_snippet}  |  {summary.get('generated', '')}"
    title_cell.font = Font(bold=True, size=12, color=HEADER_FG)
    title_cell.fill = PatternFill('solid', fgColor=HEADER_BG)
    title_cell.alignment = Alignment(horizontal='center', vertical='center')

    headers = ["#", "Name", "Match %", "Email", "Experience", "Active Status", "Notice Period", "Current Company / Role", "Location", "Key Skills", "Profile Link"]
    widths  = [4,   22,     10,        28,      12,            16,              15,              30,                       18,         35,          20]
    for i, (h, w) in enumerate(zip(headers, widths), 1):
        hdr_cell(ws1, 2, i, h, w)
    ws1.freeze_panes = 'A3'

    for idx, c in enumerate(candidates, 1):
        row = idx + 2
        is_active = c.get('is_active_30d')
        bg = ACTIVE_BG if is_active is True else (INACTIVE_BG if is_active is False else (ALT_ROW_BG if idx % 2 == 0 else None))
        
        mp = c.get('match_percentage')
        mp_display = f"{mp}%" if mp is not None else "N/A"

        data_cell(ws1, row, 1, idx, bg)
        data_cell(ws1, row, 2, c['name'], bg, bold=True)
        data_cell(ws1, row, 3, mp_display, bg)
        data_cell(ws1, row, 4, c.get('email', ''), bg)
        data_cell(ws1, row, 5, c.get('experience', ''), bg)
        data_cell(ws1, row, 6, c.get('active_status', ''), bg)
        data_cell(ws1, row, 7, c.get('notice_period', ''), bg)
        data_cell(ws1, row, 8, c.get('current', ''), bg)
        data_cell(ws1, row, 9, c.get('location', ''), bg)
        data_cell(ws1, row, 10, c.get('skills', ''), bg)
        link = c.get('profile_link', '')
        data_cell(ws1, row, 11, "Open Profile" if link else "", bg, link=link or None)
        ws1.row_dimensions[row].height = 20

    # Sheet 2: Market Summary
    ws2 = wb.create_sheet("Market Summary")
    ws2.column_dimensions['A'].width = 30
    ws2.column_dimensions['B'].width = 18

    exp_dist = summary.get('exp_distribution', {})
    summary_rows = [
        ("📊 MARKET SUMMARY", ""),
        ("Total Candidates Found", summary.get('total', 0)),
        ("Active in Last 30 Days", f"{summary.get('active_30d', 0)} ({round(summary.get('active_30d', 0)/max(summary.get('total', 1), 1)*100)}%)"),
        ("Notice Period ≤ 30 Days", summary.get('notice_30d', 0)),
        ("", ""),
        ("📈 EXPERIENCE DISTRIBUTION", ""),
    ] + [(k, v) for k, v in exp_dist.items()] + [
        ("", ""),
        ("🔍 Search Query", summary.get('query', '')),
        ("Experience Filter", summary.get('exp_range', '')),
        ("Report Date", summary.get('generated', '')),
    ]

    for r, (label, value) in enumerate(summary_rows, 1):
        cl = ws2.cell(row=r, column=1, value=label)
        cv = ws2.cell(row=r, column=2, value=value)
        if str(label).startswith(("📊", "📈", "🔍")):
            cl.font = Font(bold=True, size=12, color=HEADER_FG)
            cl.fill = PatternFill('solid', fgColor=HEADER_BG)
            cv.fill = PatternFill('solid', fgColor=HEADER_BG)
        else:
            cl.font = Font(bold=True, size=11)
            cl.fill = PatternFill('solid', fgColor=ACCENT_BG)
            cv.font = Font(size=11)
        cl.alignment = Alignment(vertical='center')
        cv.alignment = Alignment(vertical='center')
        ws2.row_dimensions[r].height = 22

    excel_buffer = io.BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)

    filename = f"Market_Analysis_{datetime.now().strftime('%d%b%Y_%H%M')}.xlsx"
    return send_file(
        excel_buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
