"""
AI Underwriting Brain — LangGraph Agent

A 3-node directed graph that processes parsed document text and produces
a structured underwriting decision:

    START -> Extract -> Reason -> Decide -> END

Node 1 (Extract): LLM extracts structured financial data from document text.
Node 2 (Reason):  Deterministic Python — calculates variance, DTI, flags risks.
Node 3 (Decide):  LLM synthesizes analysis into a final UnderwritingDecision.

Adapted from the LangGraph Agents pattern in the Reference Architecture.
"""
import os
import json
import logging
from typing import Optional, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

from app.ai.schemas import (
    ExtractedFinancials,
    IncomeAnalysis,
    UnderwritingDecision,
    UnderwritingResult,
)
from app.ai.ingestion import parse_document

load_dotenv(override=True)
logger = logging.getLogger(__name__)


# =========================================
# Graph State
# =========================================

class GraphState(TypedDict):
    """State that flows through the LangGraph nodes."""
    document_text: str
    stated_income: float
    loan_amount: float
    extracted_data: Optional[dict]
    risk_flags: Optional[list]
    analysis: Optional[dict]
    decision: Optional[dict]


# =========================================
# LLM Factory
# =========================================

def _get_llm() -> ChatOpenAI:
    """
    Build the LLM client using the project's LiteLLM proxy configuration.
    Reads the same env vars as the legacy analyze_document activity.
    """
    return ChatOpenAI(
        base_url=os.getenv("LITELLM_BASE_URL"),
        api_key=os.getenv("LITELLM_API_KEY") or os.getenv("OPENAI_API_KEY"),
        model=os.getenv("LITELLM_MODEL", "gpt-5-nano"),
        temperature=0,
    )


# =========================================
# Node 1: Extract (LLM)
# =========================================

EXTRACT_SYSTEM_PROMPT = """You are a Forensic Financial Auditor for a mortgage lender.
Your job is to extract structured financial data from the provided document text.

Extract the following fields. If a field is not present in the document, use the default (0 or null).
Be precise with dollar amounts — do not round. If you see monthly income, annualize it (* 12).
If you see biweekly income, annualize it (* 26).

Return ONLY valid JSON matching this schema:
{
  "applicant_name": string or null,
  "annual_income": number,
  "pay_stub_income": number (annualized from pay stub if present),
  "tax_return_income": number (from tax return if present),
  "credit_score": integer (0 if not found),
  "monthly_debts": number (total monthly obligations),
  "employer_name": string or null,
  "confidence": number between 0.0 and 1.0
}"""


async def extract_node(state: GraphState) -> dict:
    """
    Node 1: Use the LLM to extract structured financial data from document text.
    """
    logger.info("Node 1 (Extract): Starting LLM extraction...")
    document_text = state["document_text"]

    # Cap document text to avoid token limits
    if len(document_text) > 15000:
        document_text = document_text[:15000]
        logger.warning("Document text truncated to 15,000 chars for LLM context")

    llm = _get_llm()

    try:
        # Try structured output first
        structured_llm = llm.with_structured_output(ExtractedFinancials)
        result: ExtractedFinancials = await structured_llm.ainvoke([
            {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract financial data from this document:\n\n{document_text}"},
        ])
        extracted = result.model_dump()
        logger.info(f"Node 1 (Extract): Structured output succeeded. Income={extracted.get('annual_income')}")
    except Exception as e:
        logger.warning(f"Structured output failed ({e}), falling back to JSON parsing")
        extracted = await _extract_fallback(llm, document_text)

    return {"extracted_data": extracted}


async def _extract_fallback(llm: ChatOpenAI, document_text: str) -> dict:
    """Fallback extraction using raw JSON parsing when structured output is unavailable."""
    import re

    response = await llm.ainvoke([
        {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
        {"role": "user", "content": f"Extract financial data from this document:\n\n{document_text}"},
    ])

    content = response.content
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if not json_match:
        logger.error("No JSON found in LLM response, returning empty extraction")
        return ExtractedFinancials().model_dump()

    try:
        data = json.loads(json_match.group(0))
        validated = ExtractedFinancials(**data)
        return validated.model_dump()
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"JSON parse/validation failed: {e}")
        return ExtractedFinancials().model_dump()


# =========================================
# Node 2: Reason (Deterministic)
# =========================================

def reason_node(state: GraphState) -> dict:
    """
    Node 2: Purely deterministic reasoning over extracted data.

    Checks:
    - Income variance (flag if verified < stated * 0.90, i.e., 10% threshold)
    - DTI ratio (flag if > 43%)
    - Credit score thresholds
    - Loan amount limits
    """
    logger.info("Node 2 (Reason): Running deterministic checks...")
    extracted = state.get("extracted_data") or {}
    stated_income = state.get("stated_income", 0.0)
    loan_amount = state.get("loan_amount", 0.0)

    # Determine verified income (best of pay stub and tax return)
    pay_stub_income = float(extracted.get("pay_stub_income", 0))
    tax_return_income = float(extracted.get("tax_return_income", 0))
    annual_income = float(extracted.get("annual_income", 0))

    # Use max of the individual sources, or fall back to annual_income
    verified_income = max(pay_stub_income, tax_return_income)
    if verified_income == 0:
        verified_income = annual_income

    # Income mismatch check (10% variance threshold from the plan)
    income_mismatch = False
    variance_pct = 0.0
    if verified_income > 0 and stated_income > 0:
        variance_pct = ((stated_income - verified_income) / stated_income) * 100
        income_mismatch = verified_income < stated_income * 0.90

    # DTI calculation
    monthly_debts = float(extracted.get("monthly_debts", 0))
    monthly_income = verified_income / 12 if verified_income > 0 else 0
    dti_ratio = (monthly_debts / monthly_income * 100) if monthly_income > 0 else None

    # Credit score
    credit_score = int(extracted.get("credit_score", 0))

    # Build risk flags
    risk_flags = []
    if income_mismatch:
        risk_flags.append(f"Income Mismatch: stated ${stated_income:,.0f} vs verified ${verified_income:,.0f} ({variance_pct:.1f}% variance)")
    if dti_ratio is not None and dti_ratio > 43:
        risk_flags.append(f"High DTI: {dti_ratio:.1f}% (threshold: 43%)")
    if credit_score > 0 and credit_score < 620:
        risk_flags.append(f"Low Credit Score: {credit_score} (minimum: 620)")
    elif credit_score > 0 and credit_score < 700:
        risk_flags.append(f"Marginal Credit Score: {credit_score} (ideal: 700+)")
    if loan_amount > 1_000_000:
        risk_flags.append(f"Jumbo Loan: ${loan_amount:,.0f} exceeds conforming limit")
    if verified_income == 0:
        risk_flags.append("Unable to verify income from provided documents")

    confidence = float(extracted.get("confidence", 0))

    # Build the analysis object
    analysis = IncomeAnalysis(
        stated_income=stated_income,
        verified_income=verified_income,
        variance_percentage=round(variance_pct, 2),
        confidence_score=confidence,
        pay_stub_income=pay_stub_income,
        tax_income=tax_return_income,
        extracted_name=extracted.get("applicant_name"),
        credit_score=credit_score,
        income_mismatch=income_mismatch,
        monthly_debts=monthly_debts,
        dti_ratio=round(dti_ratio, 2) if dti_ratio is not None else None,
    )

    logger.info(
        f"Node 2 (Reason): verified_income={verified_income}, "
        f"mismatch={income_mismatch}, dti={dti_ratio}, "
        f"risk_flags={len(risk_flags)}"
    )

    return {
        "risk_flags": risk_flags,
        "analysis": analysis.model_dump(),
    }


# =========================================
# Node 3: Decide (LLM)
# =========================================

DECIDE_SYSTEM_PROMPT = """You are a Senior Mortgage Underwriter making a final decision.
You have been provided with a financial analysis and risk assessment.

Based on the data, make one of these decisions:
- "Approved": All criteria met, no significant risk flags.
- "Rejected": Critical disqualifying factors (e.g., cannot verify income, DTI > 50%, credit < 580).
- "Review": Borderline case requiring human underwriter attention.

Return ONLY valid JSON matching this schema:
{
  "status": "Approved" | "Rejected" | "Review",
  "reasoning": "Detailed markdown reasoning explaining your decision",
  "risk_factors": ["list", "of", "risk", "factors"],
  "conditions": ["list of conditions before closing, if approved"]
}"""


async def decide_node(state: GraphState) -> dict:
    """
    Node 3: Use the LLM to synthesize all analysis into a final underwriting decision.
    """
    logger.info("Node 3 (Decide): Starting LLM decision synthesis...")
    analysis = state.get("analysis", {})
    risk_flags = state.get("risk_flags", [])
    loan_amount = state.get("loan_amount", 0)

    context = (
        f"## Loan Analysis Summary\n\n"
        f"**Loan Amount:** ${loan_amount:,.2f}\n"
        f"**Stated Income:** ${analysis.get('stated_income', 0):,.2f}\n"
        f"**Verified Income:** ${analysis.get('verified_income', 0):,.2f}\n"
        f"**Income Mismatch:** {'YES' if analysis.get('income_mismatch') else 'No'}\n"
        f"**Variance:** {analysis.get('variance_percentage', 0):.1f}%\n"
        f"**Credit Score:** {analysis.get('credit_score', 'N/A')}\n"
        f"**DTI Ratio:** {analysis.get('dti_ratio', 'N/A')}%\n"
        f"**Monthly Debts:** ${analysis.get('monthly_debts', 0):,.2f}\n"
        f"**AI Confidence:** {analysis.get('confidence_score', 0):.0%}\n\n"
        f"## Risk Flags\n"
        + ("\n".join(f"- {flag}" for flag in risk_flags) if risk_flags else "- None identified")
    )

    llm = _get_llm()

    try:
        structured_llm = llm.with_structured_output(UnderwritingDecision)
        result: UnderwritingDecision = await structured_llm.ainvoke([
            {"role": "system", "content": DECIDE_SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ])
        decision = result.model_dump()
        logger.info(f"Node 3 (Decide): Decision={decision.get('status')}")
    except Exception as e:
        logger.warning(f"Structured decision output failed ({e}), falling back to JSON parsing")
        decision = await _decide_fallback(llm, context)

    return {"decision": decision}


async def _decide_fallback(llm: ChatOpenAI, context: str) -> dict:
    """Fallback decision parsing when structured output is unavailable."""
    import re

    response = await llm.ainvoke([
        {"role": "system", "content": DECIDE_SYSTEM_PROMPT},
        {"role": "user", "content": context},
    ])

    content = response.content
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if not json_match:
        logger.error("No JSON in decision response, defaulting to Review")
        return UnderwritingDecision(
            status="Review",
            reasoning="AI was unable to produce a structured decision. Manual review required.",
            risk_factors=["AI decision parsing failed"],
            conditions=["Full manual underwriting review required"],
        ).model_dump()

    try:
        data = json.loads(json_match.group(0))
        validated = UnderwritingDecision(**data)
        return validated.model_dump()
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Decision JSON parse/validation failed: {e}")
        return UnderwritingDecision(
            status="Review",
            reasoning=f"AI decision parsing error: {e}. Manual review required.",
            risk_factors=["AI decision parsing failed"],
            conditions=["Full manual underwriting review required"],
        ).model_dump()


# =========================================
# Graph Construction
# =========================================

def _build_graph() -> StateGraph:
    """Build the 3-node underwriting agent graph."""
    builder = StateGraph(GraphState)

    builder.add_node("extract", extract_node)
    builder.add_node("reason", reason_node)
    builder.add_node("decide", decide_node)

    builder.add_edge(START, "extract")
    builder.add_edge("extract", "reason")
    builder.add_edge("reason", "decide")
    builder.add_edge("decide", END)

    return builder


# Compile the graph once at module level
_agent = _build_graph().compile()


# =========================================
# Public API
# =========================================

async def run_underwriter_agent(
    file_path: str,
    stated_income: float = 0.0,
    loan_amount: float = 0.0,
) -> UnderwritingResult:
    """
    Run the full AI underwriting pipeline on a document.

    1. Parses the PDF into Markdown (Docling / pypdf fallback)
    2. Runs the LangGraph agent: Extract -> Reason -> Decide
    3. Returns a structured UnderwritingResult

    Args:
        file_path: Path to the PDF document to analyze.
        stated_income: Income the applicant claimed on the application.
        loan_amount: Requested loan amount.

    Returns:
        UnderwritingResult containing the decision and income analysis.

    Raises:
        No exceptions — on any failure, returns a "Review" decision with error context.
    """
    # Step 1: Parse document
    try:
        document_text = parse_document(file_path)
    except Exception as e:
        logger.error(f"Document parsing failed: {e}")
        return _error_result(f"Document parsing failed: {e}")

    # Step 2: Run the agent
    try:
        initial_state: GraphState = {
            "document_text": document_text,
            "stated_income": stated_income,
            "loan_amount": loan_amount,
            "extracted_data": None,
            "risk_flags": None,
            "analysis": None,
            "decision": None,
        }

        final_state = await _agent.ainvoke(initial_state)

        analysis_data = final_state.get("analysis", {})
        decision_data = final_state.get("decision", {})

        analysis = IncomeAnalysis(**analysis_data)
        decision = UnderwritingDecision(**decision_data)

        return UnderwritingResult(decision=decision, analysis=analysis)

    except Exception as e:
        logger.error(f"Underwriting agent failed: {e}", exc_info=True)
        return _error_result(f"AI agent pipeline error: {e}")


def _error_result(error_message: str) -> UnderwritingResult:
    """Build a safe 'Review Required' result when the pipeline fails."""
    return UnderwritingResult(
        decision=UnderwritingDecision(
            status="Review",
            reasoning=f"Automated analysis could not be completed.\n\n**Error:** {error_message}\n\nA human underwriter must review this application manually.",
            risk_factors=["Automated analysis failed — manual review required"],
            conditions=["Complete manual document review", "Verify all income sources independently"],
        ),
        analysis=IncomeAnalysis(),
    )
