"""
Pyramid Architecture: Level 3 - Underwriting MCP Worker

The UnderwritingMCP handles all underwriting operations:
- Verifying borrower signatures
- Evaluating risk based on loan criteria
- DTI calculations
- Credit score checks

This is a mock implementation for development.
In production, integrate with actual underwriting systems.
"""
import os
from dataclasses import dataclass
from temporalio import activity
from datetime import datetime


@dataclass
class UnderwritingMCP:
    """Underwriting MCP - handles risk evaluation"""

    @staticmethod
    def verify_signature(workflow_id: str) -> dict:
        """
        Verify that the borrower has signed the Initial Disclosures.

        Args:
            workflow_id: The loan application workflow ID

        Returns:
            Dict with signature verification status
        """
        timestamp = datetime.utcnow().isoformat()

        # Check if signed PDF exists
        uploads_dir = os.path.join("backend", "uploads", workflow_id)
        if not os.path.exists(uploads_dir):
            uploads_dir = os.path.join("uploads", workflow_id)

        signed_file = os.path.join(uploads_dir, "Initial_Disclosures_SIGNED.pdf")
        signature_verified = os.path.exists(signed_file)

        print(f"[UnderwritingMCP] [{timestamp}] SIGNATURE VERIFICATION")
        print(f"  Workflow ID: {workflow_id}")
        print(f"  Looking for: {signed_file}")
        print(f"  Signature Found: {signature_verified}")

        return {
            "verified": signature_verified,
            "signed_document": signed_file if signature_verified else None,
            "verified_at": timestamp
        }

    @staticmethod
    def evaluate_risk(loan_data: dict) -> dict:
        """
        Evaluate loan risk based on criteria.

        Risk Rules:
        - Loan Amount must be < $1,000,000
        - Credit Score must be > 700 (or estimated from analysis confidence)
        - DTI must be < 43%

        Args:
            loan_data: Dict containing loan information

        Returns:
            Dict with risk evaluation results
        """
        timestamp = datetime.utcnow().isoformat()

        # Extract loan parameters
        loan_amount = float(loan_data.get("loan_amount", 0))
        analysis = loan_data.get("analysis", {})
        credit_score = analysis.get("credit_score", 0)
        verified_income = analysis.get("verified_income", 0)
        income_mismatch = analysis.get("income_mismatch", False)

        # If no credit score, estimate from confidence (mock)
        if credit_score == 0:
            confidence = analysis.get("confidence", 0.5)
            # Map confidence to credit score range (650-800)
            credit_score = int(650 + (confidence * 150))

        # Calculate DTI (Debt-to-Income) - simplified mock
        # Assume monthly loan payment is ~0.5% of loan amount (rough approximation)
        monthly_payment = loan_amount * 0.005
        monthly_income = verified_income / 12 if verified_income > 0 else 1
        dti_ratio = (monthly_payment / monthly_income) * 100 if monthly_income > 0 else 100

        print(f"[UnderwritingMCP] [{timestamp}] RISK EVALUATION")
        print(f"  Loan Amount: ${loan_amount:,.2f}")
        print(f"  Credit Score: {credit_score}")
        print(f"  Verified Income: ${verified_income:,.2f}")
        print(f"  DTI Ratio: {dti_ratio:.1f}%")
        print(f"  Income Mismatch: {income_mismatch}")

        # Evaluate against criteria
        issues = []

        if loan_amount >= 1000000:
            issues.append(f"Loan amount ${loan_amount:,.0f} exceeds $1M limit")

        if credit_score <= 700:
            issues.append(f"Credit score {credit_score} below 700 threshold")

        if dti_ratio > 43:
            issues.append(f"DTI ratio {dti_ratio:.1f}% exceeds 43% limit")

        if income_mismatch:
            issues.append("Income mismatch detected between stated and verified income")

        # Determine decision
        if len(issues) == 0:
            decision = "CLEAR_TO_CLOSE"
            print(f"  Decision: CLEAR_TO_CLOSE")
        else:
            decision = "REFER_TO_HUMAN"
            print(f"  Decision: REFER_TO_HUMAN")
            print(f"  Issues: {issues}")

        return {
            "decision": decision,
            "credit_score": credit_score,
            "dti_ratio": round(dti_ratio, 2),
            "loan_amount": loan_amount,
            "issues": issues,
            "evaluated_at": timestamp
        }


# =========================================
# Temporal Activity Functions
# =========================================

@activity.defn
async def verify_signature(workflow_id: str) -> dict:
    """Temporal Activity: Verify borrower signature via UnderwritingMCP"""
    return UnderwritingMCP.verify_signature(workflow_id)


@activity.defn
async def evaluate_risk(loan_data: dict) -> dict:
    """Temporal Activity: Evaluate loan risk via UnderwritingMCP"""
    return UnderwritingMCP.evaluate_risk(loan_data)
