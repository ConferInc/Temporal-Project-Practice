import os
import json
import asyncio
import re  # <--- NEW: Add this import!
from dataclasses import dataclass
from temporalio import activity
from temporalio.exceptions import ApplicationError
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

@dataclass
class LoanData:
    applicant_name: str
    annual_income: int = 0
    credit_score: int = 0
    missing_docs: list[str] = None 
    
    def __post_init__(self):
        if self.missing_docs is None:
            self.missing_docs = []

@activity.defn
async def organize_files(applicant_name: str, file_paths: dict) -> dict:
    activity.logger.info(f"📂 File Clerk starting for: {applicant_name}")
    safe_name = applicant_name.replace(" ", "_").replace("/", "_")
    base_dir = f"uploads/processed/{safe_name}"
    
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)

    new_paths = {}
    for doc_type, old_path in file_paths.items():
        if not old_path:
             continue
             
        if not os.path.exists(old_path): 
            activity.logger.error(f"❌ File missing: {old_path}")
            continue
            
        extension = os.path.splitext(old_path)[1]
        new_filename = f"{safe_name}_{doc_type}{extension}"
        new_full_path = os.path.join(base_dir, new_filename)
        
        # Copy file to new clean location
        # looping to ensure unique if somehow needed, though here we overwrite for MVP consistency
        with open(old_path, 'rb') as src, open(new_full_path, 'wb') as dst:
             dst.write(src.read())
             
        new_paths[doc_type] = new_full_path
        activity.logger.info(f"✅ Filed: {new_filename}")
    
    return new_paths

@activity.defn
async def analyze_document(document_text: str, role: str = "general_analyst") -> LoanData:
    base_url = os.getenv("LITELLM_BASE_URL")
    api_key = os.getenv("LITELLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    model = "gpt-5-nano" # Or os.getenv("LITELLM_MODEL")

    print(f"\n🕵️ CONNECTION DEBUG REPORT:")
    print(f"   -> TARGET URL: '{base_url}'")
    print(f"   -> API KEY: '{api_key[:5]}...{api_key[-4:] if api_key else 'NONE'}'")
    print(f"   -> MODEL: '{model}'")
    
    if not base_url:
        print("   ❌ CRITICAL: BASE_URL is None! AsyncOpenAI will default to official OpenAI!")



    activity.logger.info(f"🕵️ Analyst ({role}) starting analysis...")

    # Define System Prompts based on Role
    system_prompt = "You are a Mortgage Underwriter. Return ONLY valid JSON."
    
    if role == "financial_auditor":
        system_prompt = (
            "You are a Forensic Financial Auditor. Your job is to strictly extract annual income from tax documents. "
            "Ignore credit scores. Return JSON: {\"applicant_name\": str, \"annual_income\": int, \"credit_score\": null, \"missing_docs\": []}."
        )
    elif role == "identity_verifier":
        system_prompt = (
            "You are a Security Officer. Your job is to verify identity and credit scores. "
            "Ignore income. Return JSON: {\"applicant_name\": str, \"annual_income\": null, \"credit_score\": int, \"missing_docs\": []}."
        )
    else:
        system_prompt = (
             "You are a General Underwriter. Extract all available data. "
             "Return JSON: {\"applicant_name\": str, \"annual_income\": int, \"credit_score\": int, \"missing_docs\": [str]}."
        )

    
    # Use environment variables
    # LITELLM_BASE_URL and OPENAI_API_KEY are loaded from .env or docker-compose environment
    client = AsyncOpenAI(
        base_url=os.getenv("LITELLM_BASE_URL"),
        api_key=os.getenv("LITELLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this text: {document_text}"}
            ],
            temperature=0,
        )

        content = response.choices[0].message.content
        print(f"DEBUG: ({role}) Raw LLM Response: '{content}'")

        # --- THE NUCLEAR FIX: REGEX ---
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        
        if not json_match:
             raise ApplicationError("No JSON object found.", non_retryable=False)

        clean_json_string = json_match.group(0)
        data = json.loads(clean_json_string)
        # ------------------------------

        # Role-Specific Validation (Relaxed)
        if role == "financial_auditor" and not data.get("annual_income"):
             pass # Might be missing if doc is bad, but don't crash
        
        activity.logger.info(f"Success! Extracted for {role}.")

        # Robust Conversion
        def to_int(val):
            if val is None: return 0
            try: return int(val)
            except: return 0

        return LoanData(
            applicant_name=data.get("applicant_name") or "Unknown",
            annual_income=to_int(data.get("annual_income")),
            credit_score=to_int(data.get("credit_score")),
            missing_docs=data.get("missing_docs") or []
        )
    except json.JSONDecodeError as e:
         raise ApplicationError("Invalid JSON from LLM", non_retryable=False)

@activity.defn
async def read_pdf_content(file_path: str) -> str:
    activity.logger.info(f"Reading PDF from {file_path}")
    try:
        from pypdf import PdfReader
        
        # Verify file exists
        if not os.path.exists(file_path):
             raise ApplicationError(f"File not found: {file_path}", non_retryable=True)

        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        return text[:5000] # Cap text to avoid token limits for this MVP
    except Exception as e:
        raise ApplicationError(f"Failed to read PDF: {e}", non_retryable=True)

@activity.defn
async def send_email_mock(applicant_name: str, status: str) -> str:
    activity.logger.info(f"Sending email to {applicant_name}: {status}")
    # Simulate email sending
    
    await asyncio.sleep(1)
    return "Email Sent"
