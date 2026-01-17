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
    annual_income: int
    credit_score: int
    missing_docs: list[str]

@activity.defn
async def analyze_document(document_text: str) -> LoanData:
    activity.logger.info("Analyzing document with AI...")

    client = AsyncOpenAI(
        base_url=os.getenv("LITELLM_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY")
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a Mortgage Underwriter. Return ONLY valid JSON: {\"applicant_name\": str, \"annual_income\": int, \"credit_score\": int, \"missing_docs\": [str]}. if fields are missing, use null."
                },
                {"role": "user", "content": f"Analyze this text: {document_text}"}
            ],
            temperature=0,
        )

        content = response.choices[0].message.content
        print(f"DEBUG: Raw LLM Response: '{content}'")

        # --- THE NUCLEAR FIX: REGEX ---
        # Find the first '{' and the last '}' and take everything in between.
        # This ignores "Here is your JSON:" or markdown backticks completely.
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        
        if not json_match:
             raise ApplicationError("No JSON object found in LLM response.", non_retryable=False)

        clean_json_string = json_match.group(0)
        data = json.loads(clean_json_string)
        # ------------------------------

        if not data.get("applicant_name") or not data.get("annual_income"):
            raise ApplicationError(
                "LLM extraction incomplete (Name or Income missing). Retrying...", 
                non_retryable=False
            )

        activity.logger.info(f"Success! Extracted: {data['applicant_name']}")

        return LoanData(
            applicant_name=data.get("applicant_name"),
            annual_income=data.get("annual_income", 0),
            credit_score=data.get("credit_score", 0),
            missing_docs=data.get("missing_docs") or []
        )

    except json.JSONDecodeError as e:
        print(f"DEBUG: JSON Parse Error: {e}")
        raise ApplicationError("LLM returned invalid JSON. Retrying...", non_retryable=False)

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
