"""
Data Validator — Post-assembly quality gate.

Runs after CanonicalAssembler and before RelationalTransformer.
Checks for missing critical fields, logical inconsistencies,
and data format violations.

Returns the (potentially cleaned) data AND a list of error strings.

Dependencies: stdlib only (no AI libraries)
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.utils.logging import logger


class DataValidator:
    """Validates canonical JSON for quality and logical sanity."""

    # Critical fields that should be present for a complete loan file.
    # Each tuple: (human_label, dotted_path)
    _CRITICAL_FIELDS = [
        ("Borrower Name",      "deal.parties.0.individual.full_name"),
        ("Borrower SSN",       "deal.parties.0.individual.ssn"),
        ("Loan Amount",        "deal.transaction_information.final_loan_amount"),
        ("Loan Purpose",       "deal.transaction_information.loan_purpose.value"),
        ("Property Address",   "deal.collateral.subject_property.address"),
    ]

    # SSN pattern: XXX-XX-XXXX
    _SSN_RE = re.compile(r"^\d{3}-\d{2}-\d{4}$")

    # Date pattern: MM/DD/YYYY or YYYY-MM-DD
    _DATE_RE = re.compile(
        r"^(?:\d{2}[/-]\d{2}[/-]\d{4}|\d{4}-\d{2}-\d{2})$"
    )

    def validate(
        self, canonical_data: dict
    ) -> Tuple[dict, List[str]]:
        """Validate canonical JSON data quality and logical sanity.

        Args:
            canonical_data: Deep canonical JSON from CanonicalAssembler.

        Returns:
            Tuple of (data, errors) where data is the input (unchanged)
            and errors is a list of validation error strings.
        """
        errors: List[str] = []

        deal = canonical_data.get("deal", {})
        if not deal:
            errors.append("CRITICAL: No 'deal' section found in canonical data.")
            return canonical_data, errors

        parties = deal.get("parties", [])

        # ── Quality checks (missing critical fields) ───────────
        self._check_critical_fields(canonical_data, errors)

        # ── Per-party validation ───────────────────────────────
        for idx, party in enumerate(parties):
            party_label = f"parties[{idx}]"
            role = (party.get("party_role") or {}).get("value", "Unknown")

            # Skip lender parties
            if role == "Lender":
                continue

            individual = party.get("individual", {})

            # SSN format
            ssn = individual.get("ssn")
            if ssn and not self._SSN_RE.match(ssn):
                errors.append(
                    f"FORMAT: {party_label}.individual.ssn "
                    f"'{ssn}' does not match XXX-XX-XXXX pattern."
                )

            # Date of birth format
            dob = individual.get("dob")
            if dob and not self._DATE_RE.match(str(dob)):
                errors.append(
                    f"FORMAT: {party_label}.individual.dob "
                    f"'{dob}' is not a valid date format."
                )

            # Employment validation
            for emp_idx, emp in enumerate(party.get("employment", [])):
                emp_label = f"{party_label}.employment[{emp_idx}]"
                self._validate_employment(emp, emp_label, errors)

            # Income validation
            for mi_idx, emp in enumerate(party.get("employment", [])):
                mi = emp.get("monthly_income", {})
                for inc_type, amount in mi.items():
                    if inc_type == "total":
                        continue
                    if amount is not None and not isinstance(amount, (int, float)):
                        errors.append(
                            f"TYPE: {party_label}.employment[{mi_idx}]"
                            f".monthly_income.{inc_type} is not numeric."
                        )
                    elif amount is not None and amount < 0:
                        errors.append(
                            f"LOGIC: {party_label}.employment[{mi_idx}]"
                            f".monthly_income.{inc_type} = {amount} "
                            f"(negative income)."
                        )

        # ── Transaction validation ─────────────────────────────
        tx = deal.get("transaction_information", {})
        self._validate_transaction(tx, errors)

        # ── Collateral validation ──────────────────────────────
        collateral = deal.get("collateral", {})
        subject = collateral.get("subject_property", {})
        valuation = subject.get("valuation", {})
        sales_price = valuation.get("sales_price")
        if sales_price is not None and isinstance(sales_price, (int, float)):
            if sales_price <= 0:
                errors.append(
                    f"LOGIC: collateral.subject_property.valuation"
                    f".sales_price = {sales_price} (must be > 0)."
                )

        # ── Summary log ────────────────────────────────────────
        if errors:
            logger.warning(
                f"DataValidator: {len(errors)} issue(s) found"
            )
        else:
            logger.info("DataValidator: All checks passed")

        return canonical_data, errors

    # ================================================================
    #  INTERNAL CHECKS
    # ================================================================

    def _check_critical_fields(
        self, data: dict, errors: List[str]
    ) -> None:
        """Check that critical fields are present and non-empty."""
        for label, path in self._CRITICAL_FIELDS:
            val = self._deep_get(data, path)
            if val is None or (isinstance(val, str) and not val.strip()):
                errors.append(
                    f"CRITICAL: Missing required field [{path}] "
                    f"({label}) - Document may be unclear."
                )

    def _validate_employment(
        self, emp: dict, label: str, errors: List[str]
    ) -> None:
        """Validate a single employment record."""
        # Employer name should exist
        if not emp.get("employer_name"):
            errors.append(
                f"QUALITY: {label}.employer_name is missing."
            )

        # Start date / end date ordering
        start = emp.get("start_date")
        end = emp.get("end_date")
        if start and end:
            start_dt = self._parse_date(start)
            end_dt = self._parse_date(end)
            if start_dt and end_dt and start_dt > end_dt:
                errors.append(
                    f"LOGIC: {label}.start_date ({start}) is after "
                    f"end_date ({end})."
                )

    def _validate_transaction(
        self, tx: dict, errors: List[str]
    ) -> None:
        """Validate transaction/loan fields."""
        loan_amount = tx.get("final_loan_amount")
        if loan_amount is not None and isinstance(loan_amount, (int, float)):
            if loan_amount <= 0:
                errors.append(
                    f"LOGIC: transaction_information.final_loan_amount "
                    f"= {loan_amount} (must be > 0)."
                )

        # Application date format
        app_date = tx.get("application_date")
        if app_date and not self._DATE_RE.match(str(app_date)):
            errors.append(
                f"FORMAT: transaction_information.application_date "
                f"'{app_date}' is not a valid date format."
            )

    # ================================================================
    #  HELPERS
    # ================================================================

    @staticmethod
    def _deep_get(data: Any, dotted_path: str) -> Any:
        """Get a value from nested dict using dot notation."""
        parts = dotted_path.split(".")
        current = data
        for part in parts:
            if current is None:
                return None
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    current = current[int(part)]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        return current

    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
        """Try to parse a date string in common formats."""
        for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"):
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except (ValueError, AttributeError):
                continue
        return None
