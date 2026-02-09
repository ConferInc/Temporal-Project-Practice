"""
AI Underwriting Schemas

Pydantic models that define the structured outputs of the AI underwriting pipeline.
These schemas are used by:
  - LangGraph nodes for structured LLM output
  - The Temporal activity to persist results to Postgres
  - The frontend ManagerDashboard to render AI analysis
"""
from typing import Optional
from pydantic import BaseModel, Field


class ExtractedFinancials(BaseModel):
    """
    Raw financial data extracted by the LLM from document text.
    This is the output of Node 1 (Extract) in the LangGraph agent.
    """
    applicant_name: Optional[str] = Field(
        default=None,
        description="Full name of the applicant as found in the document"
    )
    annual_income: float = Field(
        default=0.0,
        description="Total annual income extracted from the document"
    )
    pay_stub_income: float = Field(
        default=0.0,
        description="Annualized income derived from pay stub (monthly * 12 or biweekly * 26)"
    )
    tax_return_income: float = Field(
        default=0.0,
        description="Annual income from tax return (AGI or total income line)"
    )
    credit_score: int = Field(
        default=0,
        description="Credit score if found in documents, 0 if not present"
    )
    monthly_debts: float = Field(
        default=0.0,
        description="Total monthly debt obligations (car, student loans, credit cards)"
    )
    employer_name: Optional[str] = Field(
        default=None,
        description="Name of the employer if found in documents"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="LLM's self-assessed confidence in the extraction (0.0 to 1.0)"
    )


class IncomeAnalysis(BaseModel):
    """
    Income verification analysis combining extracted data with deterministic checks.
    This is populated by Node 2 (Reason) in the LangGraph agent.

    Field names align with what the frontend ManagerDashboard.jsx expects:
      - verified_income, stated_income, pay_stub_income, tax_income
      - income_mismatch, confidence, extracted_name, credit_score
    """
    stated_income: float = Field(
        default=0.0,
        description="Income stated by the applicant on the application"
    )
    verified_income: float = Field(
        default=0.0,
        description="Best verified income from documents (max of pay stub and tax)"
    )
    variance_percentage: float = Field(
        default=0.0,
        description="Percentage difference between stated and verified income"
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall confidence in the income verification"
    )
    pay_stub_income: float = Field(
        default=0.0,
        description="Annualized income from pay stub analysis"
    )
    tax_income: float = Field(
        default=0.0,
        description="Annual income from tax return analysis"
    )
    extracted_name: Optional[str] = Field(
        default=None,
        description="Applicant name extracted from documents"
    )
    credit_score: int = Field(
        default=0,
        description="Credit score extracted from documents"
    )
    income_mismatch: bool = Field(
        default=False,
        description="True if verified income is more than 10% below stated income"
    )
    monthly_debts: float = Field(
        default=0.0,
        description="Total monthly debt obligations"
    )
    dti_ratio: Optional[float] = Field(
        default=None,
        description="Debt-to-income ratio if calculable"
    )


class UnderwritingDecision(BaseModel):
    """
    Final structured underwriting decision from the AI agent.
    This is the output of Node 3 (Decide) in the LangGraph agent.
    """
    status: str = Field(
        description="Decision status: 'Approved', 'Rejected', or 'Review'"
    )
    reasoning: str = Field(
        description="Detailed reasoning for the decision in Markdown format"
    )
    risk_factors: list[str] = Field(
        default_factory=list,
        description="List of identified risk factors (e.g., 'High DTI', 'Low Reserves')"
    )
    conditions: list[str] = Field(
        default_factory=list,
        description="Conditions that must be met before closing (e.g., 'Verify employment')"
    )


class UnderwritingResult(BaseModel):
    """
    Complete result combining the decision with its underlying analysis.
    This is what gets persisted to LoanApplication.ai_analysis in Postgres.
    """
    decision: UnderwritingDecision
    analysis: IncomeAnalysis

    def to_frontend_dict(self) -> dict:
        """
        Convert to the flat dict format the frontend ManagerDashboard expects.

        The frontend reads from `analysis.verified_income`, `analysis.confidence`, etc.
        """
        return {
            # Fields the frontend reads directly
            "verified_income": self.analysis.verified_income,
            "stated_income": self.analysis.stated_income,
            "pay_stub_income": self.analysis.pay_stub_income,
            "tax_income": self.analysis.tax_income,
            "income_mismatch": self.analysis.income_mismatch,
            "confidence": self.analysis.confidence_score,
            "extracted_name": self.analysis.extracted_name,
            "credit_score": self.analysis.credit_score,
            # Extended fields from the AI brain
            "variance_percentage": self.analysis.variance_percentage,
            "monthly_debts": self.analysis.monthly_debts,
            "dti_ratio": self.analysis.dti_ratio,
            "ai_decision": {
                "status": self.decision.status,
                "reasoning": self.decision.reasoning,
                "risk_factors": self.decision.risk_factors,
                "conditions": self.decision.conditions,
            },
        }
