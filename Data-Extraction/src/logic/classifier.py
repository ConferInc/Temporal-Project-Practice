import os
import re
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field

from src.extractors.doctr_tool import extract_with_doctr
from src.utils.logging import logger
from src.utils.file_utils import is_pdf, is_image

# --- Schemas ---

class FileType(str, Enum):
    PDF = "pdf"
    IMAGE = "image"
    UNKNOWN = "unknown"

class PDFType(str, Enum):
    DIGITAL = "digital"
    SCANNED = "scanned"
    NOT_PDF = "not_pdf"

class DocumentType(str, Enum):
    UNKNOWN = "Unknown"
    # Application Core
    URLA = "URLA (Form 1003)"
    URLA_UNMARRIED_ADDENDUM = "URLA - Unmarried Addendum"
    URLA_CONTINUATION_SHEET = "URLA - Continuation Sheet"
    # Supplemental
    SCIF = "SCIF (Form 1103)"
    # Income & Tax
    PAY_STUBS = "Pay Stub"
    W2_FORMS = "W-2 Form"
    TAX_RETURNS_1040 = "Tax Return (1040)"
    IRS_FORM_4506C = "IRS Form 4506-C"
    MILITARY_LES = "Military LES"
    # Assets & Funds
    BANK_STATEMENTS = "Bank Statement"
    GIFT_LETTER = "Gift Letter"
    INVESTMENT_STATEMENTS = "Investment Statement"
    # Property
    APPRAISAL = "Appraisal (Form 1004)"
    SALES_CONTRACT = "Sales Contract"
    PROOF_OF_INSURANCE = "Proof of Insurance"
    LEASE_AGREEMENTS = "Lease Agreement"
    # Identity
    GOVERNMENT_ID = "Government ID"
    # Government Loans
    VA_FORM_26_1880 = "VA Form 26-1880"
    VA_FORM_26_8937 = "VA Form 26-8937"
    # Disclosures
    LOAN_ESTIMATE = "Loan Estimate"
    CLOSING_DISCLOSURE = "Closing Disclosure"

class ClassificationResult(BaseModel):
    file_type: FileType
    pdf_type: PDFType
    document_category: DocumentType
    recommended_tool: str
    confidence: float
    reasoning: str

# --- Service ---

class ClassificationService:
    @staticmethod
    def classify_document(file_path: str) -> Dict[str, Any]:
        """
        Classifies a document based on its content using Doctr.
        Determines:
        1. File Type
        2. Document Category
        3. Recommended Extraction Tool
        """
        logger.info(f"Starting classification for: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # 1. Determine File Type
        if is_pdf(file_path):
            file_type = FileType.PDF
        elif is_image(file_path):
            file_type = FileType.IMAGE
        else:
            file_type = FileType.UNKNOWN

        # 2. Extract content (Using Doctr as requested)
        # Note: Doctr extracts text from both digital and scanned PDFs/Images via OCR.
        # We limit extraction to the first 3 pages for classification efficiency.
        try:
            # Limit extraction to first 3 pages to avoid processing full document
            text_content = extract_with_doctr(file_path, max_pages=3)
        except Exception as e:
            logger.error(f"Error extracting text with Doctr: {e}")
            text_content = ""

        # We are using Doctr, so we treat it as "scanned" in terms of processing method (OCR),
        # but we can't easily distinguish digital/scanned without non-OCR tools.
        # Defaulting to SCANNED as a safe assumption for "OCR-processed".
        pdf_type = PDFType.SCANNED if file_type == FileType.PDF else PDFType.NOT_PDF
        is_scanned = True 

        # 3. Categorize Document (Heuristic / Keyword / Regex based)
        category = DocumentType.UNKNOWN
        confidence = 0.5
        
        # A. Keyword Matching
        keywords = {
            # Application Core
            DocumentType.URLA: ['uniform residential loan application', 'form 1003', 'form 65', 'uniform loan application dataset', 'ulad', 'borrower information'],
            DocumentType.URLA_UNMARRIED_ADDENDUM: ['unmarried addendum', 'domestic partnership', 'community property rights', 'civil union'],
            DocumentType.URLA_CONTINUATION_SHEET: ['continuation sheet', 'form 1003', 'overflow', 'additional information'],
            
            # Supplemental
            DocumentType.SCIF: ['supplemental consumer information', 'form 1103', 'preferred language', 'housing counseling', 'consumer preferences'],
            
            # Income & Tax
            DocumentType.PAY_STUBS: ['pay stub', 'paystubs', 'year-to-date earnings', 'pay period', 'earnings statement', 'pay begin date', 'pay end date', 'hours and earnings', 'net pay', 'total gross', 'fed taxable gross', 'deductions', 'ytd'],
            DocumentType.W2_FORMS: ['w-2', 'wage and tax statement', 'tax withholdings', 'form w-2'],
            DocumentType.TAX_RETURNS_1040: ['form 1040', 'individual income tax return', 'schedule c', 'dividend income', 'adjusted gross income', 'profit or loss'],
            DocumentType.IRS_FORM_4506C: ['form 4506-c', 'request for transcript of tax return', 'ives request'],
            DocumentType.MILITARY_LES: ['leave and earnings statement', 'military pay', 'base pay', 'entitlements', 'defense finance'],
            
            # Assets & Funds
            DocumentType.BANK_STATEMENTS: ['transaction history', 'beginning balance', 'ending balance', 'summary of accounts', 'checking account', 'savings account'],
            DocumentType.GIFT_LETTER: ['gift letter', 'no repayment', 'debt obligation', 'donor', 'gift funds'],
            DocumentType.INVESTMENT_STATEMENTS: ['401(k)', '401k', 'ira', 'stock portfolio', 'brokerage statement', 'retirement account', 'managed account'],
             
            # Property
            DocumentType.APPRAISAL: ['uniform residential appraisal', 'appraisal report', 'appraised value', 'sales comparison approach', 'cost approach', 'income approach', 'subject property', 'reconciliation', 'gross living area'],
            DocumentType.SALES_CONTRACT: ['sales contract', 'purchase agreement', 'terms of sale', 'sales contract price', 'offer to purchase'],
            DocumentType.PROOF_OF_INSURANCE: ['hazard insurance', 'homeowner\'s insurance', 'declaration page', 'collateral protection', 'fire insurance'],
            DocumentType.LEASE_AGREEMENTS: ['lease agreement', 'rental terms', 'monthly rent', 'rental income', 'residential lease'],
            
            # Identity
            DocumentType.GOVERNMENT_ID: ['driver\'s license', 'passport', 'state id', 'identity card', 'government id'],
            
            # Government Loans
            DocumentType.VA_FORM_26_1880: ['form 26-1880', 'certificate of eligibility', 'veterans affairs'],
            DocumentType.VA_FORM_26_8937: ['form 26-8937', 'verification of va benefits'],
            
            # Disclosures
            DocumentType.LOAN_ESTIMATE: ['loan estimate', 'estimated closing costs', 'estimated cash to close', 'projected payments', 'comparisons', 'rate lock'],
            DocumentType.CLOSING_DISCLOSURE: ['closing disclosure', 'loan terms', 'closing costs', 'uniform closing dataset', 'ucd', 'cash to close']
        }
        
        # B. Regex Patterns
        regex_patterns = {
            DocumentType.W2_FORMS: [r'\bW-2\b', r'Form W-2'],
            DocumentType.TAX_RETURNS_1040: [r'Form\s+1040', r'1040\s+U\.S\.'],
            DocumentType.PAY_STUBS: [r'\bYTD\b', r'\bNet Pay\b', r'\bGross Pay\b', r'\d{2}/\d{2}/\d{4}\s*-\s*\d{2}/\d{2}/\d{4}'],
            DocumentType.BANK_STATEMENTS: [r'Account\s+Summary', r'Statement\s+Period'],
            DocumentType.APPRAISAL: [r'Form\s+1004', r'URAR', r'Appraisal\s+Report'],
            DocumentType.LOAN_ESTIMATE: [r'Loan\s+Estimate', r'LOAN\s+ESTIMATE', r'CFPB\s+H-24'],
            DocumentType.IRS_FORM_4506C: [r'Form\s+4506-C'],
            DocumentType.VA_FORM_26_1880: [r'26-1880'],
            DocumentType.VA_FORM_26_8937: [r'26-8937']
        }
        
        if text_content:
            text_lower = text_content.lower()
            
            # Check Keywords (1 point each)
            scores = {cat: 0 for cat in DocumentType}
            
            for cat, words in keywords.items():
                for word in words:
                    if word in text_lower:
                        scores[cat] += 1
            
            # Check Regex (3 points each)
            for cat, patterns in regex_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, text_content, re.IGNORECASE):
                        scores[cat] += 3

            # Find best category
            best_match = max(scores, key=scores.get)
            max_score = scores[best_match]
            
            if best_match and max_score >= 1:
                category = best_match
                # Confidence scales with score, capped at 0.95
                confidence = min(0.5 + (max_score * 0.1), 0.95)

        # 4. Recommend Tool
        complex_types = [
            DocumentType.SCIF, DocumentType.W2_FORMS, DocumentType.TAX_RETURNS_1040,
            DocumentType.IRS_FORM_4506C, DocumentType.BANK_STATEMENTS, DocumentType.PAY_STUBS,
            DocumentType.MILITARY_LES, DocumentType.INVESTMENT_STATEMENTS,
            DocumentType.VA_FORM_26_1880, DocumentType.VA_FORM_26_8937,
            DocumentType.APPRAISAL, DocumentType.LOAN_ESTIMATE, DocumentType.CLOSING_DISCLOSURE
        ]
        
        # URLA documents use OCR instead of Dockling (Dockling can timeout on complex forms)
        urla_types = [
            DocumentType.URLA, DocumentType.URLA_UNMARRIED_ADDENDUM, DocumentType.URLA_CONTINUATION_SHEET
        ]
        
        if category in urla_types:
            recommended_tool = "ocr_document"
            reasoning = f"Document is a URLA form ({category.value}). Using OCR for reliable extraction."
        elif category in complex_types:
            recommended_tool = "parse_document_with_dockling"
            reasoning = f"Document is a complex structured form ({category.value}). Dockling recommended for thorough parsing."
        elif is_scanned:
            recommended_tool = "ocr_document"
            reasoning = f"File is {file_type.value} and appears to be image-based/scanned. OCR is required."
        else:
            recommended_tool = "ocr_document"
            reasoning = "Standard document. Using OCR extraction."
            
        result = ClassificationResult(
            file_type=file_type,
            pdf_type=pdf_type,
            document_category=category,
            recommended_tool=recommended_tool,
            confidence=confidence,
            reasoning=reasoning
        )
        
        logger.info(f"Classification decision: {result.model_dump()}")
        return result.model_dump()

# Wrapper for existing calls
def classify_document(file_path: str) -> dict:
    return ClassificationService.classify_document(file_path)
