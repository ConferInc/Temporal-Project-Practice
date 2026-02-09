"""
Test suite for the two-stage extraction & assembly architecture.

Tests:
  1. Flat mode produces flat keys (no nesting)
  2. CanonicalAssembler produces deep structure from flat keys
  3. Nested mode (backward compat) still works unchanged
  4. DocumentMerger priority-based merging
  5. DocumentMerger party matching (SSN + name)
  6. Round-trip: flat → assemble produces same field count as nested
"""

import os
import sys
import json
import pytest

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.mapping.rule_engine import RuleEngine, extract_with_rules
from src.mapping.canonical_assembler import CanonicalAssembler
from src.logic.merger import DocumentMerger


# ==================================================================
# Sample text fixtures (minimal — just enough to trigger rules)
# ==================================================================

W2_SAMPLE = """
- aEmployee'ssocial securitynumber 999-60-5555
- bEmployeridentification number(EIN)
12-3476543
- cEmployer's name, address, and ZIP code
Butter Builders
- eEmployee's first name and initial Sandy

Last name America
- 1Wages,tips,other compensation 96000
- 2Federal income tax withheld 9867.72
- 3Social security wages 96000
- 4Social security tax withheld 3635.88
- 5Medicare wages and tips 96000
- 6Medicare tax withheld 1392.00
- 15State XN
- 16State wages,tips,etc. 96000
- 17State income tax 2400.00

## W-2 WageandTaxStatement 2020

Department of the Treasury
"""

URLA_SAMPLE = """
Mortgage
XI Conventional
Agency Case Number
999-1234567-001
Lender Case Number
55443
$250,000.00
4.500 % 360
Amortization XI Fixed

Subject Property Address
123 Main Street, Springfield, IL 62704
Legal Description
Lot 12 Block 3

Purpose of
XI Purchase
Property will be
XI Primary

Borrower's Name
Sandy America
Social Security Number
999-60-5555
555-867-5309
01/15/1985
16

Married
XI Married

Present Address
123 Oak Lane
Mailing Address

IV. EMPLOYMENT
Self Employed No
AB1C2D
Best Company Inc
Position/T
Warehouse Manager
555-867-5310
employed

Base Empl. Income* $
5,000.00
Overtime
500.00
Total
a
5,000.00 b
5,500.00 Total

Total Assets a. $
150,000.00
Totall Liabilities a. 50,000.00
TotalMonthly Payments
1,200.00

Purchase Price
250,000.00

Date 01/15/2025
Some Financial Group, LLC
"""


PAYSTUB_SAMPLE = """
## Acme Corporation

Business Unit:

Human Resources

Employee Name:

Sandy America

Employee ID:

E12345

Department:

Engineering

Job Title:

Senior Developer

Pay Rate:

$96,000.00 Annual

Pay Begin Date:

01/01/2025

Pay End Date:

01/15/2025

Advice Date:

01/17/2025

| TOTAL GROSS | FED TAXABLE GROSS | TOTAL TAXES | TOTAL DEDUCTIONS | NET PAY |
|---|---|---|---|---|
| Current | 3,692.31 | 3,492.31 | 923.08 | 500.00 | 2,269.23 |
| YTD | 3,692.31 | 3,492.31 | 923.08 | 500.00 | 2,269.23 |
"""


# ==================================================================
# Test 1: Flat mode produces flat keys
# ==================================================================

class TestFlatMode:
    def test_w2_flat_keys(self):
        engine = RuleEngine()
        flat = engine.extract(W2_SAMPLE, "W-2 Form", output_mode="flat")

        # Should have flat keys, not nested dicts
        assert isinstance(flat, dict)
        assert "w2_employee_ssn" in flat
        assert flat["w2_employee_ssn"] == "999-60-5555"

        # Should NOT have nested structure
        assert "deal" not in flat

        # Check key fields
        assert "w2_employer_ein" in flat
        assert "w2_employer_name" in flat
        assert "w2_employee_first_name" in flat
        assert "w2_wages_annual" in flat or "w2_wages_monthly" in flat
        assert "w2_federal_tax_withheld" in flat
        assert "w2_tax_year" in flat
        assert "w2_source_doc_type" in flat
        assert flat["w2_source_doc_type"] == "W-2"

    def test_urla_flat_keys(self):
        engine = RuleEngine()
        flat = engine.extract(URLA_SAMPLE, "URLA (Form 1003)", output_mode="flat")

        assert isinstance(flat, dict)
        assert "deal" not in flat
        assert "urla_borrower_name" in flat or "urla_borrower_ssn" in flat
        assert "urla_source_doc_type" in flat
        assert flat["urla_source_doc_type"] == "URLA"

    def test_nested_mode_unchanged(self):
        """Verify nested mode (default) still produces deep dicts."""
        engine = RuleEngine()
        nested = engine.extract(W2_SAMPLE, "W-2 Form", output_mode="nested")

        assert isinstance(nested, dict)
        # Should have nested structure
        assert "deal" in nested
        assert "parties" in nested["deal"]


# ==================================================================
# Test 2: CanonicalAssembler produces deep structure
# ==================================================================

class TestCanonicalAssembler:
    def test_w2_assembly(self):
        """W-2 flat → deep canonical."""
        engine = RuleEngine()
        flat = engine.extract(W2_SAMPLE, "W-2 Form", output_mode="flat")

        assembler = CanonicalAssembler()
        canonical = assembler.assemble(flat, "W-2 Form")

        assert "deal" in canonical
        assert "parties" in canonical["deal"]
        assert len(canonical["deal"]["parties"]) >= 1

        party = canonical["deal"]["parties"][0]
        assert "individual" in party
        assert party["individual"]["ssn"] == "999-60-5555"

        assert "employment" in party
        assert len(party["employment"]) >= 1
        assert "employer_ein" in party["employment"][0]

    def test_urla_assembly(self):
        """URLA flat → deep canonical."""
        engine = RuleEngine()
        flat = engine.extract(URLA_SAMPLE, "URLA (Form 1003)", output_mode="flat")

        assembler = CanonicalAssembler()
        canonical = assembler.assemble(flat, "URLA (Form 1003)")

        assert "deal" in canonical
        assert "parties" in canonical["deal"]

    def test_all_strategies_exist(self):
        """Every known doc type has an assembler strategy."""
        assembler = CanonicalAssembler()
        for doc_type in [
            "W-2 Form", "URLA (Form 1003)", "Pay Stub",
            "Bank Statement", "Tax Return (1040)",
            "Appraisal (Form 1004)", "Loan Estimate", "merged",
        ]:
            assert doc_type in assembler._STRATEGIES, \
                f"Missing strategy for {doc_type}"


# ==================================================================
# Test 3: Round-trip field count
# ==================================================================

class TestRoundTrip:
    """Flat → Assemble should produce a comparable structure to nested."""

    def _count_fields(self, d, depth=0):
        if isinstance(d, dict):
            return sum(self._count_fields(v, depth + 1) for v in d.values())
        if isinstance(d, list):
            return sum(self._count_fields(v, depth + 1) for v in d)
        return 1 if d is not None else 0

    def test_w2_round_trip(self):
        """W-2: flat→assemble should have fields >= nested (may differ slightly in structure)."""
        engine = RuleEngine()

        nested = engine.extract(W2_SAMPLE, "W-2 Form", output_mode="nested")
        nested_count = self._count_fields(nested)

        flat = engine.extract(W2_SAMPLE, "W-2 Form", output_mode="flat")
        assembler = CanonicalAssembler()
        assembled = assembler.assemble(flat, "W-2 Form")
        assembled_count = self._count_fields(assembled)

        # Assembled should have at least 80% of nested fields
        # (exact count may differ due to structure differences)
        assert assembled_count >= nested_count * 0.8, \
            f"Assembled ({assembled_count}) has too few fields vs nested ({nested_count})"

    def test_paystub_flat_extraction(self):
        """PayStub: flat mode should produce flat keys."""
        engine = RuleEngine()
        flat = engine.extract(PAYSTUB_SAMPLE, "Pay Stub", output_mode="flat")

        assert isinstance(flat, dict)
        assert "deal" not in flat
        # PayStub has key_value rules that use "key" as the search label
        # The heading rule should produce paystub_employer_name
        assert "paystub_employer_name" in flat


# ==================================================================
# Test 4: DocumentMerger
# ==================================================================

class TestDocumentMerger:
    def test_priority_merge(self):
        """Higher-priority documents overwrite lower-priority."""
        merger = DocumentMerger()

        urla_flat = {
            "urla_borrower_name": "Sandy America",
            "urla_borrower_ssn": "999-60-5555",
        }
        w2_flat = {
            "w2_employee_ssn": "999-60-5555",
            "w2_employee_first_name": "Sandy",
            "w2_wages_annual": 96000.0,
        }

        merged = merger.merge([
            ("URLA (Form 1003)", urla_flat),
            ("W-2 Form", w2_flat),
        ])

        # Both keys should be present
        assert merged["urla_borrower_name"] == "Sandy America"
        assert merged["w2_employee_ssn"] == "999-60-5555"
        assert merged["w2_wages_annual"] == 96000.0

    def test_conflict_resolution(self):
        """When same key appears in multiple docs, higher priority wins."""
        merger = DocumentMerger()

        # Simulate two docs with same key but different values
        low_pri = {"shared_key": "low_value"}
        high_pri = {"shared_key": "high_value"}

        merged = merger.merge([
            ("Loan Estimate", low_pri),  # priority 40
            ("W-2 Form", high_pri),       # priority 90
        ])

        assert merged["shared_key"] == "high_value"

    def test_empty_merge(self):
        merger = DocumentMerger()
        assert merger.merge([]) == {}

    def test_party_matching_ssn(self):
        """SSN-based party matching."""
        merger = DocumentMerger()

        extractions = [
            ("W-2 Form", {"w2_employee_ssn": "999-60-5555", "w2_employee_full_name": "Sandy America"}),
            ("URLA (Form 1003)", {"urla_borrower_ssn": "999-60-5555", "urla_borrower_name": "Sandy America"}),
        ]

        party_map = merger.match_parties(extractions)

        # Both should map to the same party
        assert party_map.get("w2_employee") == party_map.get("urla_borrower")

    def test_party_matching_name_fuzzy(self):
        """Name-based fuzzy party matching."""
        merger = DocumentMerger()

        extractions = [
            ("Pay Stub", {"paystub_employee_name": "SANDY AMERICA"}),
            ("Bank Statement", {"bank_account_holder": "SANDY AMERICA"}),
        ]

        party_map = merger.match_parties(extractions)

        # Should be matched to the same party
        assert "paystub_employee" in party_map or "paystub" in party_map

    def test_two_different_parties(self):
        """Two clearly different people should be separate parties."""
        merger = DocumentMerger()

        extractions = [
            ("URLA (Form 1003)", {
                "urla_borrower_ssn": "999-60-5555",
                "urla_borrower_name": "Sandy America",
                "urla_coborrower_ssn": "888-50-4444",
                "urla_coborrower_name": "John Smith",
            }),
        ]

        party_map = merger.match_parties(extractions)

        # Should have two different parties
        assert party_map.get("urla_borrower") != party_map.get("urla_coborrower")


# ==================================================================
# Test 5: Module-level convenience function
# ==================================================================

class TestExtractWithRules:
    def test_flat_mode_convenience(self):
        """extract_with_rules() with output_mode='flat' should work."""
        flat = extract_with_rules(
            markdown=W2_SAMPLE,
            document_type="W-2 Form",
            output_mode="flat",
        )
        assert isinstance(flat, dict)
        assert "w2_employee_ssn" in flat

    def test_nested_default(self):
        """extract_with_rules() default is nested."""
        nested = extract_with_rules(
            markdown=W2_SAMPLE,
            document_type="W-2 Form",
        )
        assert "deal" in nested


# ==================================================================
# Test 6: Multi-Party Aggregation (_merged_strategy)
# ==================================================================

class TestMultiPartyAggregation:
    """Test that _merged_strategy resolves identities and aggregates data."""

    def _extract_flat(self, text, doc_type):
        engine = RuleEngine()
        return engine.extract(text, doc_type, output_mode="flat")

    def test_same_person_urla_w2_merge(self):
        """URLA + W-2 for same person (same SSN) -> 1 party with both employments."""
        urla_flat = self._extract_flat(URLA_SAMPLE, "URLA (Form 1003)")
        w2_flat = self._extract_flat(W2_SAMPLE, "W-2 Form")

        # Merge
        merger = DocumentMerger()
        merged = merger.merge([
            ("URLA (Form 1003)", urla_flat),
            ("W-2 Form", w2_flat),
        ])

        # Assemble
        assembler = CanonicalAssembler()
        canonical = assembler.assemble(merged, "merged")

        parties = canonical["deal"]["parties"]
        # Filter out lender parties
        borrower_parties = [
            p for p in parties
            if p.get("party_role", {}).get("value") != "Lender"
        ]

        # Same SSN (999-60-5555) -> should be 1 borrower party
        assert len(borrower_parties) == 1, (
            f"Expected 1 borrower party for same SSN, got {len(borrower_parties)}"
        )

        party = borrower_parties[0]
        assert party["individual"]["ssn"] == "999-60-5555"

        # Employment list should have entries from BOTH URLA and W-2
        assert "employment" in party, "Party should have employment data"
        assert len(party["employment"]) >= 2, (
            f"Expected >=2 employments (URLA + W-2), got {len(party['employment'])}"
        )

        # W-2 income verification should be attached
        assert "income_verification_fragments" in party

    def test_different_people_urla_w2_merge(self):
        """URLA (Samuel, SSN 111) + W-2 (Sandy, SSN 999) -> 2 parties."""
        # Build a URLA flat dict for a different person
        urla_flat = {
            "urla_borrower_name": "Samuel Schultz",
            "urla_borrower_ssn": "111-22-3333",
            "urla_mortgage_type": "Conventional",
            "urla_property_address": "456 Elm Street",
            "urla_source_doc_type": "URLA",
        }
        w2_flat = self._extract_flat(W2_SAMPLE, "W-2 Form")

        merger = DocumentMerger()
        merged = merger.merge([
            ("URLA (Form 1003)", urla_flat),
            ("W-2 Form", w2_flat),
        ])

        assembler = CanonicalAssembler()
        canonical = assembler.assemble(merged, "merged")

        parties = canonical["deal"]["parties"]
        borrower_parties = [
            p for p in parties
            if p.get("party_role", {}).get("value") != "Lender"
        ]

        # Different SSNs -> 2 parties
        assert len(borrower_parties) == 2, (
            f"Expected 2 parties for different SSNs, got {len(borrower_parties)}"
        )

        # URLA borrower should be parties[0]
        assert borrower_parties[0]["individual"].get("full_name") == "Samuel Schultz"
        # W-2 employee should be parties[1]
        assert borrower_parties[1]["individual"].get("ssn") == "999-60-5555"

        # W-2 party should have employment
        assert "employment" in borrower_parties[1]

    def test_three_doc_merge_same_person(self):
        """URLA + W-2 + PayStub all same person -> 1 party, multiple employments."""
        urla_flat = self._extract_flat(URLA_SAMPLE, "URLA (Form 1003)")
        w2_flat = self._extract_flat(W2_SAMPLE, "W-2 Form")
        ps_flat = self._extract_flat(PAYSTUB_SAMPLE, "Pay Stub")

        merger = DocumentMerger()
        merged = merger.merge([
            ("URLA (Form 1003)", urla_flat),
            ("W-2 Form", w2_flat),
            ("Pay Stub", ps_flat),
        ])

        assembler = CanonicalAssembler()
        canonical = assembler.assemble(merged, "merged")

        parties = canonical["deal"]["parties"]
        borrower_parties = [
            p for p in parties
            if p.get("party_role", {}).get("value") != "Lender"
        ]

        # All same person (Sandy America / SSN 999-60-5555)
        assert len(borrower_parties) == 1, (
            f"Expected 1 party for same person, got {len(borrower_parties)}"
        )

        party = borrower_parties[0]

        # Employment from URLA, W-2, and PayStub (appended, not overwritten)
        assert "employment" in party
        assert len(party["employment"]) >= 2, (
            f"Expected >=2 employments, got {len(party['employment'])}"
        )

        # Income fragments from W-2 and PayStub
        assert "income_verification_fragments" in party
        assert len(party["income_verification_fragments"]) >= 1

    def test_deal_level_data_preserved(self):
        """Merged mode should still produce deal-level collateral and transaction."""
        urla_flat = self._extract_flat(URLA_SAMPLE, "URLA (Form 1003)")
        w2_flat = self._extract_flat(W2_SAMPLE, "W-2 Form")

        merger = DocumentMerger()
        merged = merger.merge([
            ("URLA (Form 1003)", urla_flat),
            ("W-2 Form", w2_flat),
        ])

        assembler = CanonicalAssembler()
        canonical = assembler.assemble(merged, "merged")

        # URLA collateral should be present
        deal = canonical["deal"]
        assert "collateral" in deal or "transaction_information" in deal, (
            "Merged mode should produce deal-level URLA data"
        )

    def test_employment_lists_appended(self):
        """Employment from different doc types should be in a list, not overwrite."""
        merged = {
            "urla_borrower_name": "Test Person",
            "urla_borrower_ssn": "999-60-5555",
            "urla_employer_name": "URLA Employer",
            "w2_employee_ssn": "999-60-5555",
            "w2_employee_full_name": "Test Person",
            "w2_employer_name": "W-2 Employer",
            "w2_employer_ein": "12-3456789",
        }

        assembler = CanonicalAssembler()
        canonical = assembler.assemble(merged, "merged")

        parties = canonical["deal"]["parties"]
        borrower_parties = [
            p for p in parties
            if p.get("party_role", {}).get("value") != "Lender"
        ]

        assert len(borrower_parties) == 1
        party = borrower_parties[0]

        # Should have 2 employment entries
        assert "employment" in party
        assert len(party["employment"]) == 2, (
            f"Expected 2 employments (URLA + W-2), got {len(party['employment'])}"
        )

        employer_names = [e.get("employer_name") for e in party["employment"]]
        assert "URLA Employer" in employer_names
        assert "W-2 Employer" in employer_names

    def test_empty_merged_flat(self):
        """Empty flat dict should produce empty parties list."""
        assembler = CanonicalAssembler()
        canonical = assembler.assemble({}, "merged")
        assert canonical["deal"]["parties"] == []


# ==================================================================
# Test 7: PayStub raw-key fallback (_pget)
# ==================================================================

class TestPaystubRawKeyFallback:
    """Verify assembler picks up raw label keys emitted by RuleEngine."""

    def test_raw_keys_in_single_doc_strategy(self):
        """_paystub_strategy should resolve 'Job Title' -> position_title."""
        flat = {
            "paystub_employer_name": "ACME Corp",
            "Business Unit": "Engineering",
            "Department": "Platform",
            "Job Title": "Senior Dev",
            "Pay Rate": "$120,000 Annual",
            "Location": "Remote",
            "paystub_employment_status": "Current",
            "paystub_monthly_income_base": 10000.0,
            "Pay Begin Date": "01/01/2025",
            "Pay End Date": "01/15/2025",
            "Advice Date": "01/17/2025",
            "Tax Status": "Single",
            "paystub_current_gross_pay": 5000.0,
            "paystub_current_net_pay": 3500.0,
            "paystub_source_doc_type": "Paystub",
        }

        assembler = CanonicalAssembler()
        canonical = assembler.assemble(flat, "Pay Stub")

        party = canonical["deal"]["parties"][0]

        # Employment should have raw-key data
        assert "employment" in party
        emp = party["employment"][0]
        assert emp["employer_name"] == "ACME Corp"
        assert emp["employer_business_unit"] == "Engineering"
        assert emp["department"] == "Platform"
        assert emp["position_title"] == "Senior Dev"
        assert emp["pay_rate"] == "$120,000 Annual"
        assert emp["location"] == "Remote"

        # Income fragment should have raw-key dates
        assert "income_verification_fragments" in party
        ivf = party["income_verification_fragments"][0]
        assert ivf["pay_period_start"] == "01/01/2025"
        assert ivf["pay_period_end"] == "01/15/2025"
        assert ivf["advice_date"] == "01/17/2025"
        assert ivf["federal_tax_status"] == "Single"

    def test_prefixed_keys_take_precedence(self):
        """When both prefixed and raw keys exist, prefixed wins."""
        flat = {
            "paystub_employer_name": "ACME Corp",
            "paystub_job_title": "Prefixed Title",
            "Job Title": "Raw Title",
            "paystub_department": "Prefixed Dept",
            "Department": "Raw Dept",
        }

        assembler = CanonicalAssembler()
        canonical = assembler.assemble(flat, "Pay Stub")

        emp = canonical["deal"]["parties"][0]["employment"][0]
        assert emp["position_title"] == "Prefixed Title"
        assert emp["department"] == "Prefixed Dept"

    def test_raw_keys_in_merged_mode(self):
        """_build_paystub_employment/income_fragment should also resolve raw keys."""
        flat = {
            "paystub_employee_name": "Sandy America",
            "paystub_employer_name": "ACME Corp",
            "Job Title": "Admin",
            "Location": "HQ",
            "Pay Begin Date": "02/01/2025",
            "Advice Date": "02/05/2025",
            "Tax Status": "Married",
            "paystub_current_gross_pay": 4000.0,
            "paystub_source_doc_type": "Paystub",
        }

        assembler = CanonicalAssembler()
        canonical = assembler.assemble(flat, "merged")

        parties = canonical["deal"]["parties"]
        borrower_parties = [
            p for p in parties
            if p.get("party_role", {}).get("value") != "Lender"
        ]
        assert len(borrower_parties) == 1

        party = borrower_parties[0]
        assert "employment" in party
        emp = party["employment"][0]
        assert emp["position_title"] == "Admin"
        assert emp["location"] == "HQ"

        assert "income_verification_fragments" in party
        ivf = party["income_verification_fragments"][0]
        assert ivf["pay_period_start"] == "02/01/2025"
        assert ivf["advice_date"] == "02/05/2025"
        assert ivf["federal_tax_status"] == "Married"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
