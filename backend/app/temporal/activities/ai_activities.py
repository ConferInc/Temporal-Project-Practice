"""
AI Underwriting Activity for Temporal Workflows

This activity bridges the AI module (brain.py) with the Temporal workflow system.
It runs the full GenAI underwriting pipeline and persists results to Postgres.

Usage from a workflow:
    result = await workflow.execute_activity(
        analyze_document_activity,
        args=[file_path, workflow_id, stated_income, loan_amount],
        start_to_close_timeout=timedelta(seconds=120),
    )
"""
from datetime import datetime
from typing import Optional
from temporalio import activity

from app.database import get_session_context
from app.models.application import LoanApplication
from app.ai.brain import run_underwriter_agent
from app.ai.schemas import UnderwritingResult, IncomeAnalysis, UnderwritingDecision


@activity.defn
async def analyze_document_activity(
    file_path: str,
    workflow_id: str,
    stated_income: float = 0.0,
    loan_amount: float = 0.0,
) -> dict:
    """
    Temporal activity that runs the AI underwriting pipeline and updates the database.

    Steps:
    1. Calls run_underwriter_agent() which parses the PDF and runs the LangGraph agent
    2. Converts the result to frontend-compatible format
    3. Updates LoanApplication.ai_analysis and automated_uw_decision in Postgres

    Args:
        file_path: Path to the PDF document to analyze.
        workflow_id: The Temporal workflow ID (used to find the DB record).
        stated_income: Income the applicant stated on the application.
        loan_amount: Requested loan amount.

    Returns:
        dict: Frontend-compatible analysis dict (matches ManagerDashboard.jsx expectations).
    """
    activity.logger.info(
        f"AI Activity: Starting analysis for workflow={workflow_id}, "
        f"file={file_path}, stated_income={stated_income}, loan_amount={loan_amount}"
    )

    # Step 1: Run the AI underwriting pipeline
    try:
        result: UnderwritingResult = await run_underwriter_agent(
            file_path=file_path,
            stated_income=stated_income,
            loan_amount=loan_amount,
        )
    except Exception as e:
        # This should not happen (run_underwriter_agent catches all errors),
        # but we handle it defensively.
        activity.logger.error(f"AI Activity: Unexpected error: {e}")
        result = UnderwritingResult(
            decision=UnderwritingDecision(
                status="Review",
                reasoning=f"Activity-level error: {e}",
                risk_factors=["Activity execution failed"],
                conditions=["Manual review required"],
            ),
            analysis=IncomeAnalysis(
                stated_income=stated_income,
            ),
        )

    # Step 2: Convert to frontend-compatible format
    analysis_dict = result.to_frontend_dict()

    activity.logger.info(
        f"AI Activity: Decision={result.decision.status}, "
        f"verified_income={result.analysis.verified_income}, "
        f"mismatch={result.analysis.income_mismatch}"
    )

    # Step 3: Persist to Postgres
    try:
        with get_session_context() as session:
            loan_app = session.query(LoanApplication).filter(
                LoanApplication.workflow_id == workflow_id
            ).first()

            if loan_app:
                loan_app.ai_analysis = analysis_dict
                loan_app.automated_uw_decision = result.decision.status
                if result.analysis.verified_income > 0:
                    loan_app.risk_score = result.analysis.confidence_score
                loan_app.updated_at = datetime.utcnow()
                session.commit()
                activity.logger.info(f"AI Activity: DB updated for {workflow_id}")
            else:
                activity.logger.warning(
                    f"AI Activity: LoanApplication not found for workflow_id={workflow_id}. "
                    f"Analysis computed but not persisted to DB."
                )
    except Exception as e:
        activity.logger.error(
            f"AI Activity: DB update failed for {workflow_id}: {e}. "
            f"Analysis result is still returned to the workflow."
        )

    return analysis_dict
