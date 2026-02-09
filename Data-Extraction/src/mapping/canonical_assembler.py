"""
Canonical Assembler — Flat business keys → deep canonical JSON structure.

Converts the flat key-value dicts produced by RuleEngine (output_mode="flat")
into the deep MISMO-aligned canonical JSON used by MismoEmitter.

Each document type has a dedicated strategy that knows how to map
prefixed flat keys into the correct nested structure.

Dependencies: stdlib only (no AI libraries)
"""

from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

from src.utils.logging import logger


class CanonicalAssembler:
    """Flat business keys → deep canonical JSON structure."""

    def assemble(self, flat: dict, doc_type: str) -> dict:
        """Build canonical structure from flat extraction dict.

        Args:
            flat: {business_key: value} dict from RuleEngine flat mode
            doc_type: classifier label (e.g. "W-2 Form", "merged")

        Returns:
            Deep canonical JSON dict (MISMO-aligned)
        """
        strategy = self._STRATEGIES.get(doc_type)
        if strategy is None:
            logger.warning(f"No assembler strategy for '{doc_type}', using generic")
            strategy = self._generic_strategy
        result = strategy(self, flat)
        field_count = self._count_fields(result)
        logger.info(
            f"CanonicalAssembler built {field_count} fields for '{doc_type}'"
        )
        return result

    # ================================================================
    #  STRATEGIES (one per document type)
    # ================================================================

    def _w2_strategy(self, flat: dict) -> dict:
        """W-2: single party (employee), single employer."""
        party = self._build_party(
            ssn=flat.get("w2_employee_ssn"),
            first_name=flat.get("w2_employee_first_name"),
            last_name=flat.get("w2_employee_last_name"),
            full_name=flat.get("w2_employee_full_name"),
            role=flat.get("w2_party_role", "Borrower"),
        )

        # Address
        address = {}
        if flat.get("w2_employee_address"):
            address["street"] = flat["w2_employee_address"]
        if address:
            party["addresses"] = [address]

        # Employment
        employment = self._build_w2_employment(flat)
        if employment:
            party["employment"] = [employment]

        # Income verification fragments
        ivf = self._build_w2_income_fragment(flat)
        if ivf:
            party["income_verification_fragments"] = [ivf]

        result = {"deal": {"parties": [party]}}
        result["document_metadata"] = self._build_metadata(flat, "w2_")
        return result

    def _urla_strategy(self, flat: dict) -> dict:
        """URLA: borrower + optional co-borrower, loan info, property."""
        parties = []

        # Borrower party
        borrower = self._build_party(
            ssn=flat.get("urla_borrower_ssn"),
            full_name=flat.get("urla_borrower_name"),
            role=flat.get("urla_borrower_party_role", "Borrower"),
        )

        # Borrower details
        self._set_if(borrower, "individual", "home_phone", flat.get("urla_borrower_phone"))
        self._set_if(borrower, "individual", "dob", flat.get("urla_borrower_dob"))
        self._set_if(borrower, "individual", "years_school", flat.get("urla_borrower_years_school"))
        self._set_if(borrower, "individual", "marital_status", flat.get("urla_borrower_marital_status"))
        self._set_if(borrower, "individual", "ethnicity", flat.get("urla_borrower_ethnicity"))
        self._set_if(borrower, "individual", "race", flat.get("urla_borrower_race"))
        self._set_if(borrower, "individual", "sex", flat.get("urla_borrower_sex"))

        if flat.get("urla_borrower_us_citizen"):
            borrower.setdefault("individual", {}).setdefault("citizenship_residency", {})["value"] = flat["urla_borrower_us_citizen"]

        if flat.get("urla_borrower_primary_residence_intent"):
            borrower.setdefault("declarations", {})["intent_to_occupy"] = flat["urla_borrower_primary_residence_intent"]

        # Address
        address = {}
        if flat.get("urla_borrower_present_address"):
            address["street"] = flat["urla_borrower_present_address"]
        if flat.get("urla_borrower_city_state_zip"):
            address["city_state_zip"] = flat["urla_borrower_city_state_zip"]
        if address:
            borrower["addresses"] = [address]

        # Employment
        employment = {}
        for field_suffix, emp_key in [
            ("urla_employer_name", "employer_name"),
            ("urla_position_title", "position_title"),
            ("urla_business_phone", "business_phone"),
        ]:
            if flat.get(field_suffix):
                employment[emp_key] = flat[field_suffix]

        monthly_income = {}
        for field_suffix, inc_key in [
            ("urla_base_employment_income", "base"),
            ("urla_overtime_income", "overtime"),
            ("urla_total_monthly_income", "total"),
        ]:
            if flat.get(field_suffix) is not None:
                monthly_income[inc_key] = flat[field_suffix]
        if monthly_income:
            employment["monthly_income"] = monthly_income
        if employment:
            borrower["employment"] = [employment]

        # Assets/Liabilities
        if flat.get("urla_total_assets") is not None:
            borrower["total_assets"] = flat["urla_total_assets"]
        if flat.get("urla_total_liabilities") is not None:
            borrower["total_liabilities"] = flat["urla_total_liabilities"]
        if flat.get("urla_total_monthly_payments") is not None:
            borrower["total_monthly_payments"] = flat["urla_total_monthly_payments"]

        parties.append(borrower)

        # Co-borrower (if present)
        if flat.get("urla_coborrower_name") or flat.get("urla_coborrower_ssn"):
            coborrower = self._build_party(
                ssn=flat.get("urla_coborrower_ssn"),
                full_name=flat.get("urla_coborrower_name"),
                role="CoBorrower",
            )
            parties.append(coborrower)

        # Lender/Originator party
        if flat.get("urla_originator_company"):
            lender = {"company_name": flat["urla_originator_company"]}
            parties.append(lender)

        result = {"deal": {"parties": parties}}

        # Property / Collateral
        collateral = self._build_urla_collateral(flat)
        if collateral:
            result["deal"]["collateral"] = collateral

        # Transaction info
        tx = self._build_urla_transaction(flat)
        if tx:
            result["deal"]["transaction_information"] = tx

        # Disclosures
        disclosures = {}
        pn = {}
        for field_suffix, pn_key in [
            ("urla_loan_amount", "principal_amount"),
            ("urla_interest_rate", "interest_rate"),
            ("urla_loan_term_months", "loan_term_months"),
        ]:
            if flat.get(field_suffix) is not None:
                pn[pn_key] = flat[field_suffix]
        if pn:
            disclosures["promissory_note"] = pn

        # Identifiers
        identifiers = {}
        for field_suffix, id_key in [
            ("urla_agency_case_number", "agency_case_number"),
            ("urla_lender_case_number", "lender_case_number"),
        ]:
            if flat.get(field_suffix):
                identifiers[id_key] = flat[field_suffix]
        if identifiers:
            result["deal"]["identifiers"] = identifiers

        if disclosures:
            result["deal"]["disclosures_and_closing"] = disclosures

        result["document_metadata"] = self._build_metadata(flat, "urla_")
        return result

    def _paystub_strategy(self, flat: dict) -> dict:
        """Pay Stub: single party (employee), single employer, income details."""
        party = self._build_party(
            full_name=flat.get("paystub_employee_name"),
            role="Borrower",
        )

        # Key-value fields stored directly by the key_value handler use the
        # YAML "key" field name (which for key_value rules is the label text).
        # These are stored without prefix in flat mode because key_value rules
        # use the YAML key field (e.g. "Employee Name") as the search key
        # AND the flat key if no separate "key:" is specified.
        # With our new YAML, the key_value rules use the label as "key" in the
        # YAML sense, so we need to check both prefixed and unprefixed.
        employee_name = flat.get("paystub_employee_name") or flat.get("Employee Name")
        if employee_name:
            party.setdefault("individual", {})["full_name"] = employee_name

        employee_id = self._pget(flat, "paystub_employee_id")
        if employee_id:
            party.setdefault("individual", {})["employee_id"] = employee_id

        # Employment
        employment = {}
        for src_key, emp_key in [
            ("paystub_employer_name", "employer_name"),
            ("paystub_employer_business_unit", "employer_business_unit"),
            ("paystub_department", "department"),
            ("paystub_job_title", "position_title"),
            ("paystub_pay_rate", "pay_rate"),
            ("paystub_location", "location"),
            ("paystub_employment_status", "employment_status"),
        ]:
            val = self._pget(flat, src_key)
            if val is not None:
                if emp_key == "employment_status":
                    employment["employment_status"] = {"value": val}
                else:
                    employment[emp_key] = val

        if flat.get("paystub_monthly_income_base") is not None:
            employment.setdefault("monthly_income", {})["base"] = flat["paystub_monthly_income_base"]

        if employment:
            party["employment"] = [employment]

        # Income verification fragments
        ivf = {}
        for src_key, ivf_key in [
            ("paystub_pay_period_start", "pay_period_start"),
            ("paystub_pay_period_end", "pay_period_end"),
            ("paystub_advice_date", "advice_date"),
            ("paystub_federal_tax_status", "federal_tax_status"),
            ("paystub_current_gross_pay", "current_gross_pay"),
            ("paystub_current_fed_taxable_gross", "current_fed_taxable_gross"),
            ("paystub_current_total_taxes", "current_total_taxes"),
            ("paystub_current_total_deductions", "current_total_deductions"),
            ("paystub_current_net_pay", "current_net_pay"),
            ("paystub_ytd_gross_amount", "ytd_gross_amount"),
            ("paystub_ytd_fed_taxable_gross", "ytd_fed_taxable_gross"),
            ("paystub_ytd_total_taxes", "ytd_total_taxes"),
            ("paystub_ytd_total_deductions", "ytd_total_deductions"),
            ("paystub_ytd_net_pay", "ytd_net_pay"),
            ("paystub_verified_monthly_base", "verified_monthly_base"),
            ("paystub_source_doc_type", "source_doc"),
        ]:
            val = self._pget(flat, src_key)
            if val is not None:
                if ivf_key == "source_doc":
                    ivf["source_doc"] = {"value": val}
                else:
                    ivf[ivf_key] = val

        # List-type fields
        for list_key in ["paystub_earnings", "paystub_before_tax_deductions", "paystub_after_tax_deductions"]:
            val = flat.get(list_key)
            if val is not None:
                ivf_name = list_key.replace("paystub_", "")
                ivf[ivf_name] = val

        if ivf:
            party["income_verification_fragments"] = [ivf]

        result = {"deal": {"parties": [party]}}
        result["document_metadata"] = self._build_metadata(flat, "paystub_")
        return result

    def _bank_statement_strategy(self, flat: dict) -> dict:
        """Bank Statement: single party, single asset account."""
        party = self._build_party(
            full_name=flat.get("bank_account_holder"),
            role=flat.get("bank_party_role", "Borrower"),
        )

        # Asset
        asset = {}
        for src_key, asset_key in [
            ("bank_institution_name", "institution_name"),
            ("bank_account_number", "account_number"),
            ("bank_account_type", "account_type"),
            ("bank_statement_period_start", "statement_period_start"),
            ("bank_statement_period_end", "statement_period_end"),
            ("bank_beginning_balance", "beginning_balance"),
            ("bank_ending_balance", "ending_balance"),
            ("bank_cash_or_market_value", "cash_or_market_value_amount"),
            ("bank_total_deposits", "total_deposits"),
            ("bank_total_withdrawals", "total_withdrawals"),
            ("bank_service_fees", "service_fees"),
            ("bank_total_checks", "total_checks"),
            ("bank_average_balance", "average_balance"),
        ]:
            val = flat.get(src_key)
            if val is not None:
                asset[asset_key] = val

        if flat.get("bank_asset_type"):
            asset["asset_type"] = {"value": flat["bank_asset_type"]}

        # Transaction lists
        for list_key, asset_key in [
            ("bank_deposit_transactions", "transactions"),
            ("bank_withdrawal_transactions", "withdrawal_transactions"),
        ]:
            val = flat.get(list_key)
            if val is not None:
                asset[asset_key] = val

        if asset:
            party["assets"] = [asset]

        result = {"deal": {"parties": [party]}}
        result["document_metadata"] = self._build_metadata(flat, "bank_")
        return result

    def _tax_return_strategy(self, flat: dict) -> dict:
        """Tax Return 1040: taxpayer + optional spouse, income line items."""
        parties = []

        # Taxpayer (primary)
        taxpayer = self._build_party(
            ssn=flat.get("tax_taxpayer_ssn"),
            first_name=flat.get("tax_taxpayer_first_name"),
            last_name=flat.get("tax_taxpayer_last_name"),
            role=flat.get("tax_party_role", "Borrower"),
        )

        # Address
        address = {}
        for src_key, addr_key in [
            ("tax_taxpayer_street", "street"),
            ("tax_taxpayer_apt", "apt_number"),
            ("tax_taxpayer_city", "city"),
            ("tax_taxpayer_state", "state"),
            ("tax_taxpayer_zip", "zip_code"),
        ]:
            val = flat.get(src_key)
            if val:
                address[addr_key] = val
        if address:
            taxpayer["addresses"] = [address]

        # Income verification fragments
        ivf = {}
        for src_key, ivf_key in [
            ("tax_year", "tax_year"),
            ("tax_filing_status", "filing_status"),
            ("tax_wages_salaries_tips", "wages_salaries_tips"),
            ("tax_taxable_interest", "taxable_interest"),
            ("tax_ordinary_dividends", "ordinary_dividends"),
            ("tax_capital_gains", "capital_gains"),
            ("tax_other_income", "other_income"),
            ("tax_total_income", "total_income"),
            ("tax_adjustments_to_income", "adjustments_to_income"),
            ("tax_adjusted_gross_income", "adjusted_gross_income"),
            ("tax_deductions", "deductions"),
            ("tax_taxable_income", "taxable_income"),
            ("tax_total_tax", "total_tax"),
            ("tax_total_payments", "total_payments"),
            ("tax_refund_amount", "refund_amount"),
            ("tax_amount_owed", "amount_owed"),
        ]:
            val = flat.get(src_key)
            if val is not None:
                ivf[ivf_key] = val
        if ivf:
            taxpayer["income_verification_fragments"] = [ivf]

        parties.append(taxpayer)

        # Spouse
        if flat.get("tax_spouse_first_name") or flat.get("tax_spouse_ssn"):
            spouse = self._build_party(
                ssn=flat.get("tax_spouse_ssn"),
                first_name=flat.get("tax_spouse_first_name"),
                last_name=flat.get("tax_spouse_last_name"),
                role="CoBorrower",
            )
            parties.append(spouse)

        result = {"deal": {"parties": parties}}
        result["document_metadata"] = self._build_metadata(flat, "tax_")
        return result

    def _appraisal_strategy(self, flat: dict) -> dict:
        """Appraisal 1004: borrower party, property details, valuation."""
        parties = []

        borrower = self._build_party(
            full_name=flat.get("appraisal_borrower_name"),
            role=flat.get("appraisal_party_role", "Borrower"),
        )
        parties.append(borrower)

        # Lender party
        if flat.get("appraisal_lender_name"):
            lender = {"company_name": flat["appraisal_lender_name"]}
            parties.append(lender)

        # Subject property
        prop = {}
        for src_key, prop_key in [
            ("appraisal_property_address", "address"),
            ("appraisal_property_city", "city"),
            ("appraisal_property_state", "state"),
            ("appraisal_property_zip", "zip_code"),
            ("appraisal_property_county", "county"),
            ("appraisal_legal_description", "legal_description"),
            ("appraisal_assessor_parcel", "assessor_parcel_number"),
            ("appraisal_tax_year", "tax_year"),
            ("appraisal_annual_taxes", "annual_taxes"),
            ("appraisal_year_built", "year_built"),
            ("appraisal_effective_age", "effective_age_years"),
            ("appraisal_room_count", "total_room_count"),
            ("appraisal_bedroom_count", "bedroom_count"),
            ("appraisal_bathroom_count", "bathroom_count"),
            ("appraisal_gla_sqft", "gross_living_area_sqft"),
            ("appraisal_stories", "number_of_stories"),
            ("appraisal_design_style", "design_style"),
            ("appraisal_lot_dimensions", "lot_dimensions"),
            ("appraisal_lot_area", "lot_size"),
            ("appraisal_view", "view"),
            ("appraisal_basement_area", "basement_area_sqft"),
            ("appraisal_basement_finish_pct", "basement_finish_percent"),
            ("appraisal_condition_rating", "condition_rating"),
            ("appraisal_occupant_type", "occupancy_status"),
            ("appraisal_neighborhood_name", "neighborhood_name"),
            ("appraisal_zoning", "zoning_classification"),
            ("appraisal_fema_flood_zone", "fema_flood_zone"),
            ("appraisal_fema_map_number", "fema_map_number"),
        ]:
            val = flat.get(src_key)
            if val is not None:
                prop[prop_key] = val

        # Valuation
        valuation = {}
        if flat.get("appraisal_contract_price") is not None:
            valuation["sales_price"] = flat["appraisal_contract_price"]
        if flat.get("appraisal_form_type"):
            valuation["appraisal_form_type"] = flat["appraisal_form_type"]
        if valuation:
            prop["valuation"] = valuation

        result = {"deal": {"parties": parties}}
        if prop:
            result["deal"]["collateral"] = {"subject_property": prop}

        # Identifiers
        if flat.get("appraisal_loan_number"):
            result["deal"]["identifiers"] = {
                "lender_case_number": flat["appraisal_loan_number"]
            }

        result["document_metadata"] = self._build_metadata(flat, "appraisal_")
        return result

    def _loan_estimate_strategy(self, flat: dict) -> dict:
        """Loan Estimate H-24: borrower, lender, loan terms, closing costs."""
        parties = []

        # Borrower
        borrower = self._build_party(
            full_name=flat.get("le_applicant_names"),
            role=flat.get("le_party_role_borrower", "Borrower"),
        )
        parties.append(borrower)

        # Lender
        lender = {}
        if flat.get("le_lender_name"):
            lender["company_name"] = flat["le_lender_name"]
        lender_individual = {}
        if flat.get("le_loan_officer"):
            lender_individual["full_name"] = flat["le_loan_officer"]
        if flat.get("le_loan_officer_nmls"):
            lender_individual["nmls_id"] = flat["le_loan_officer_nmls"]
        if lender_individual:
            lender["individual"] = lender_individual
        if flat.get("le_party_role_lender"):
            lender["party_role"] = {"value": flat["le_party_role_lender"]}
        if lender:
            parties.append(lender)

        result = {"deal": {"parties": parties}}

        # Property / Collateral
        prop = {}
        if flat.get("le_property_address"):
            prop["address"] = flat["le_property_address"]
        if flat.get("le_property_city_state_zip"):
            prop["city_state_zip"] = flat["le_property_city_state_zip"]
        valuation = {}
        if flat.get("le_sale_price") is not None:
            valuation["sales_price"] = flat["le_sale_price"]
        if valuation:
            prop["valuation"] = valuation
        if prop:
            result["deal"]["collateral"] = {"subject_property": prop}

        # Transaction info
        tx = {}
        if flat.get("le_loan_purpose"):
            tx["loan_purpose"] = {"value": flat["le_loan_purpose"]}
        if flat.get("le_loan_type"):
            tx["mortgage_type"] = {"value": flat["le_loan_type"]}
        if tx:
            result["deal"]["transaction_information"] = tx

        # Disclosures & Closing
        disclosures = {}

        # Promissory note
        pn = {}
        for src_key, pn_key in [
            ("le_principal_amount", "principal_amount"),
            ("le_interest_rate", "interest_rate"),
            ("le_interest_rate_raw", "interest_rate_raw"),
            ("le_loan_term_years", "loan_term_years"),
        ]:
            val = flat.get(src_key)
            if val is not None:
                pn[pn_key] = val
        if pn:
            disclosures["promissory_note"] = pn

        # Loan Estimate H-24 details
        h24 = {}
        for src_key, h24_key in [
            ("le_date_issued", "date_issued"),
            ("le_product_description", "product_description"),
            ("le_rate_lock", "rate_lock_indicator"),
            ("le_rate_lock_expiration", "rate_lock_expiration_date"),
            ("le_monthly_pi", "monthly_principal_interest"),
            ("le_prepayment_penalty", "prepayment_penalty"),
            ("le_balloon_payment", "balloon_payment"),
            ("le_total_closing_costs", "total_closing_costs"),
            ("le_estimated_cash_to_close", "estimated_cash_to_close"),
            ("le_origination_charges", "origination_charges"),
            ("le_points_percent", "points_percent"),
            ("le_points_amount", "points_amount"),
            ("le_services_cannot_shop", "services_cannot_shop"),
            ("le_services_can_shop", "services_can_shop"),
            ("le_total_loan_costs", "total_loan_costs"),
            ("le_prepaid_interest_per_day", "prepaid_interest_per_day"),
            ("le_prepaid_interest_days", "prepaid_interest_days"),
            ("le_total_closing_costs_j", "total_closing_costs_j"),
            ("le_down_payment", "down_payment"),
            ("le_earnest_money_deposit", "earnest_money_deposit"),
            ("le_seller_credits", "seller_credits"),
            ("le_cash_to_close_table", "estimated_cash_to_close"),
            ("le_apr", "annual_percentage_rate"),
            ("le_total_interest_percentage", "total_interest_percentage"),
            ("le_five_year_total_paid", "five_year_total_paid"),
            ("le_five_year_principal_reduction", "five_year_principal_reduction"),
        ]:
            val = flat.get(src_key)
            if val is not None:
                h24[h24_key] = val
        if h24:
            disclosures["loan_estimate_h24"] = h24

        if disclosures:
            result["deal"]["disclosures_and_closing"] = disclosures

        # Identifiers
        if flat.get("le_loan_id"):
            result["deal"]["identifiers"] = {
                "lender_case_number": flat["le_loan_id"]
            }

        result["document_metadata"] = self._build_metadata(flat, "le_")
        return result

    def _merged_strategy(self, flat: dict) -> dict:
        """Multi-party aggregation from merged flat dict.

        Instead of delegating to a single doc-type strategy, this:
        1. Scans for all identity prefixes present in the flat dict
        2. Clusters identities by SSN (exact) and name (fuzzy >=80%)
        3. Builds one party per cluster with data from all contributing docs
        4. Assembles deal-level data (collateral, transaction, disclosures)
        """
        # Step 1: Find all identity groups in the flat dict
        identities = self._scan_identities(flat)

        if not identities:
            logger.warning("No identity groups found in merged flat dict")
            return {"deal": {"parties": []}}

        # Step 2: Cluster by SSN/name
        clusters = self._cluster_identities(identities)

        logger.info(
            f"Multi-party resolution: {len(identities)} identity groups "
            f"-> {len(clusters)} parties"
        )

        # Step 3: Build one party per cluster
        parties = []
        urla_borrower_idx = None

        for cluster_idx, cluster in enumerate(clusters):
            party = self._build_merged_party(flat, cluster)
            parties.append(party)
            for identity in cluster:
                if identity["prefix"] == "urla_borrower":
                    urla_borrower_idx = cluster_idx

        # Ensure URLA borrower is parties[0]
        if urla_borrower_idx is not None and urla_borrower_idx > 0:
            parties.insert(0, parties.pop(urla_borrower_idx))

        # Lender party (from URLA originator or Loan Estimate)
        lender = self._build_lender_party(flat)
        if lender:
            parties.append(lender)

        result = {"deal": {"parties": parties}}

        # Step 4: Deal-level data (non-party sections)
        collateral = self._build_urla_collateral(flat)
        if not collateral:
            collateral = self._build_appraisal_collateral(flat)
        if collateral:
            result["deal"]["collateral"] = collateral

        tx = self._build_urla_transaction(flat)
        # Supplement with Loan Estimate transaction data
        if flat.get("le_loan_purpose") and "loan_purpose" not in tx:
            tx["loan_purpose"] = {"value": flat["le_loan_purpose"]}
        if flat.get("le_loan_type") and "mortgage_type" not in tx:
            tx["mortgage_type"] = {"value": flat["le_loan_type"]}
        if tx:
            result["deal"]["transaction_information"] = tx

        disclosures = self._build_merged_disclosures(flat)
        if disclosures:
            result["deal"]["disclosures_and_closing"] = disclosures

        identifiers = self._build_merged_identifiers(flat)
        if identifiers:
            result["deal"]["identifiers"] = identifiers

        return result

    def _generic_strategy(self, flat: dict) -> dict:
        """Fallback: dump all flat keys into a simple structure."""
        result = {"deal": {}, "flat_data": flat}
        return result

    # ================================================================
    #  HELPER METHODS
    # ================================================================

    @staticmethod
    def _build_party(
        ssn: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        full_name: Optional[str] = None,
        role: str = "Borrower",
    ) -> dict:
        """Build a party dict with individual info."""
        party: Dict[str, Any] = {}
        individual: Dict[str, Any] = {}

        if ssn:
            individual["ssn"] = ssn
        if first_name:
            individual["first_name"] = first_name
        if last_name:
            individual["last_name"] = last_name
        if full_name:
            individual["full_name"] = full_name

        if individual:
            party["individual"] = individual

        party["party_role"] = {"value": role}
        return party

    @staticmethod
    def _set_if(party: dict, section: str, key: str, value: Any) -> None:
        """Set a value in party[section][key] if value is not None."""
        if value is not None:
            party.setdefault(section, {})[key] = value

    # Fallback map: RuleEngine key_value rules emit raw label keys for
    # PayStub fields (e.g. "Job Title") while the assembler expects
    # prefixed keys (e.g. "paystub_job_title").  Try prefixed first,
    # then fall back to the raw label.
    _PAYSTUB_KEY_FALLBACKS: Dict[str, str] = {
        "paystub_employer_business_unit": "Business Unit",
        "paystub_department":             "Department",
        "paystub_job_title":              "Job Title",
        "paystub_pay_rate":               "Pay Rate",
        "paystub_location":               "Location",
        "paystub_employee_id":            "Employee ID",
        "paystub_pay_period_start":       "Pay Begin Date",
        "paystub_pay_period_end":         "Pay End Date",
        "paystub_advice_date":            "Advice Date",
        "paystub_federal_tax_status":     "Tax Status",
    }

    @staticmethod
    def _pget(flat: dict, key: str) -> Any:
        """Get value from flat dict, trying prefixed key then raw fallback."""
        val = flat.get(key)
        if val is not None:
            return val
        fallback = CanonicalAssembler._PAYSTUB_KEY_FALLBACKS.get(key)
        if fallback is not None:
            return flat.get(fallback)
        return None

    @staticmethod
    def _build_metadata(flat: dict, prefix: str) -> dict:
        """Build document_metadata from flat keys."""
        meta = {}
        src = flat.get(f"{prefix}source_doc_type")
        if src:
            meta["source_document_type"] = src
        ver = flat.get(f"{prefix}schema_version")
        if ver:
            meta["schema_version"] = ver
        return meta

    @staticmethod
    def _build_w2_employment(flat: dict) -> dict:
        """Build employment dict from W-2 flat keys."""
        emp: Dict[str, Any] = {}
        if flat.get("w2_employer_name"):
            emp["employer_name"] = flat["w2_employer_name"]
        if flat.get("w2_employer_ein"):
            emp["employer_ein"] = flat["w2_employer_ein"]
        if flat.get("w2_income_type"):
            emp["income_type"] = {"value": flat["w2_income_type"]}
        if flat.get("w2_employment_status"):
            emp["employment_status"] = {"value": flat["w2_employment_status"]}
        if flat.get("w2_wages_monthly") is not None:
            emp.setdefault("monthly_income", {})["base"] = flat["w2_wages_monthly"]
        return emp

    @staticmethod
    def _build_w2_income_fragment(flat: dict) -> dict:
        """Build income_verification_fragment from W-2 flat keys."""
        ivf: Dict[str, Any] = {}
        for src_key, ivf_key in [
            ("w2_wages_annual", "w2_wages_annual"),
            ("w2_federal_tax_withheld", "federal_tax_withheld"),
            ("w2_ss_wages", "social_security_wages"),
            ("w2_ss_tax_withheld", "social_security_tax_withheld"),
            ("w2_medicare_wages", "medicare_wages"),
            ("w2_medicare_tax_withheld", "medicare_tax_withheld"),
            ("w2_ss_tips", "social_security_tips"),
            ("w2_dependent_care_benefits", "dependent_care_benefits"),
            ("w2_box12_deferred_comp", "box12_deferred_comp"),
            ("w2_state_code", "state_code"),
            ("w2_state_wages", "state_wages"),
            ("w2_state_income_tax", "state_income_tax"),
            ("w2_tax_year", "tax_year"),
        ]:
            val = flat.get(src_key)
            if val is not None:
                ivf[ivf_key] = val
        return ivf

    @staticmethod
    def _build_urla_collateral(flat: dict) -> dict:
        """Build collateral section from URLA flat keys."""
        prop: Dict[str, Any] = {}
        if flat.get("urla_property_address"):
            prop["address"] = flat["urla_property_address"]
        if flat.get("urla_number_of_units") is not None:
            prop["number_of_units"] = flat["urla_number_of_units"]
        if flat.get("urla_occupancy_type"):
            prop["occupancy_type"] = {"value": flat["urla_occupancy_type"]}
        if flat.get("urla_estate_type"):
            prop["estate_type"] = flat["urla_estate_type"]
        if flat.get("urla_title_held_names"):
            prop["title_held_names"] = flat["urla_title_held_names"]

        valuation = {}
        if flat.get("urla_purchase_price") is not None:
            valuation["sales_price"] = flat["urla_purchase_price"]
        if valuation:
            prop["valuation"] = valuation

        if prop:
            return {"subject_property": prop}
        return {}

    @staticmethod
    def _build_urla_transaction(flat: dict) -> dict:
        """Build transaction_information from URLA flat keys."""
        tx: Dict[str, Any] = {}
        if flat.get("urla_mortgage_type"):
            tx["mortgage_type"] = {"value": flat["urla_mortgage_type"]}
        if flat.get("urla_loan_purpose"):
            tx["loan_purpose"] = {"value": flat["urla_loan_purpose"]}
        if flat.get("urla_amortization_type"):
            tx["amortization_type"] = {"value": flat["urla_amortization_type"]}
        if flat.get("urla_application_date"):
            tx["application_date"] = flat["urla_application_date"]
        for src_key, tx_key in [
            ("urla_estimated_prepaid", "estimated_prepaid_items"),
            ("urla_estimated_closing_costs", "estimated_closing_costs"),
            ("urla_pmi_funding_fee", "pmi_funding_fee"),
            ("urla_final_loan_amount", "final_loan_amount"),
        ]:
            val = flat.get(src_key)
            if val is not None:
                tx[tx_key] = val
        return tx

    # ================================================================
    #  MULTI-PARTY RESOLUTION HELPERS (for _merged_strategy)
    # ================================================================

    # Identity prefix configs: each entry defines one possible "person slot"
    # in the flat dict. SSN and/or name are used for cross-doc matching.
    _IDENTITY_CONFIGS = [
        {"prefix": "urla_borrower",   "ssn_key": "urla_borrower_ssn",   "name_key": "urla_borrower_name",      "doc_type": "URLA (Form 1003)",      "role": "Borrower"},
        {"prefix": "urla_coborrower", "ssn_key": "urla_coborrower_ssn", "name_key": "urla_coborrower_name",     "doc_type": "URLA (Form 1003)",      "role": "CoBorrower"},
        {"prefix": "w2_employee",     "ssn_key": "w2_employee_ssn",     "name_key": "w2_employee_full_name",    "doc_type": "W-2 Form",              "role": "Borrower"},
        {"prefix": "paystub",         "ssn_key": None,                  "name_key": "paystub_employee_name",    "doc_type": "Pay Stub",              "role": "Borrower"},
        {"prefix": "bank",            "ssn_key": None,                  "name_key": "bank_account_holder",      "doc_type": "Bank Statement",        "role": "Borrower"},
        {"prefix": "tax_taxpayer",    "ssn_key": "tax_taxpayer_ssn",    "name_key": None, "name_parts": ["tax_taxpayer_first_name", "tax_taxpayer_last_name"],   "doc_type": "Tax Return (1040)", "role": "Borrower"},
        {"prefix": "tax_spouse",      "ssn_key": "tax_spouse_ssn",      "name_key": None, "name_parts": ["tax_spouse_first_name", "tax_spouse_last_name"],       "doc_type": "Tax Return (1040)", "role": "CoBorrower"},
        {"prefix": "le_applicant",    "ssn_key": None,                  "name_key": "le_applicant_names",       "doc_type": "Loan Estimate",         "role": "Borrower"},
        {"prefix": "appraisal",       "ssn_key": None,                  "name_key": "appraisal_borrower_name",  "doc_type": "Appraisal (Form 1004)", "role": "Borrower"},
    ]

    def _scan_identities(self, flat: dict) -> list:
        """Find all identity groups present in the flat dict."""
        found = []
        for config in self._IDENTITY_CONFIGS:
            ssn = flat.get(config["ssn_key"]) if config.get("ssn_key") else None

            name = None
            if config.get("name_key"):
                name = flat.get(config["name_key"])
            elif config.get("name_parts"):
                parts = [flat.get(k, "") for k in config["name_parts"]]
                parts = [p for p in parts if p]
                name = " ".join(parts) if parts else None

            if ssn or name:
                found.append({
                    "prefix": config["prefix"],
                    "doc_type": config["doc_type"],
                    "role": config["role"],
                    "ssn": ssn,
                    "name": name,
                })
        return found

    @staticmethod
    def _cluster_identities(identities: list) -> list:
        """Group identities by SSN (exact) then name (fuzzy >=80%)."""
        clusters: List[list] = []
        cluster_ssns: List[Optional[str]] = []
        cluster_names: List[Optional[str]] = []

        for identity in identities:
            matched = None
            ssn_clean = (
                identity["ssn"].replace("-", "").replace(" ", "")
                if identity["ssn"] else None
            )

            # SSN exact match
            if ssn_clean:
                for i, c_ssn in enumerate(cluster_ssns):
                    if c_ssn and c_ssn == ssn_clean:
                        matched = i
                        break

            # Name fuzzy match (only if SSN didn't match)
            if matched is None and identity["name"]:
                for i, c_name in enumerate(cluster_names):
                    if c_name:
                        ratio = SequenceMatcher(
                            None,
                            identity["name"].upper().strip(),
                            c_name.upper().strip(),
                        ).ratio()
                        if ratio >= 0.80:
                            matched = i
                            break

            if matched is not None:
                clusters[matched].append(identity)
                if ssn_clean and not cluster_ssns[matched]:
                    cluster_ssns[matched] = ssn_clean
                if identity["name"] and not cluster_names[matched]:
                    cluster_names[matched] = identity["name"]
            else:
                clusters.append([identity])
                cluster_ssns.append(ssn_clean)
                cluster_names.append(identity["name"])

        return clusters

    def _build_merged_party(self, flat: dict, cluster: list) -> dict:
        """Build a single party dict from all identity groups in a cluster.

        Aggregates employment and income data from all contributing
        documents. Lists (employment, income_verification_fragments,
        assets) are APPENDED, never overwritten.
        """
        # Pick best SSN and name from the cluster
        best_ssn = None
        best_name = None
        role = "Borrower"

        for identity in cluster:
            if identity["ssn"] and not best_ssn:
                best_ssn = identity["ssn"]
            if identity["name"] and not best_name:
                best_name = identity["name"]
            if identity["role"] == "CoBorrower":
                role = "CoBorrower"

        party = self._build_party(ssn=best_ssn, full_name=best_name, role=role)

        employments: List[dict] = []
        income_fragments: List[dict] = []

        for identity in cluster:
            prefix = identity["prefix"]
            doc_type = identity["doc_type"]

            if prefix == "urla_borrower":
                self._enrich_urla_borrower_details(party, flat)
                emp = self._build_urla_borrower_employment(flat)
                if emp:
                    employments.append(emp)
                # URLA assets / liabilities
                if flat.get("urla_total_assets") is not None:
                    party["total_assets"] = flat["urla_total_assets"]
                if flat.get("urla_total_liabilities") is not None:
                    party["total_liabilities"] = flat["urla_total_liabilities"]
                if flat.get("urla_total_monthly_payments") is not None:
                    party["total_monthly_payments"] = flat["urla_total_monthly_payments"]

            elif prefix == "urla_coborrower":
                pass  # SSN and name already set via _build_party

            elif doc_type == "W-2 Form":
                emp = self._build_w2_employment(flat)
                if emp:
                    employments.append(emp)
                ivf = self._build_w2_income_fragment(flat)
                if ivf:
                    income_fragments.append(ivf)
                if flat.get("w2_employee_address") and "addresses" not in party:
                    party["addresses"] = [{"street": flat["w2_employee_address"]}]

            elif doc_type == "Pay Stub":
                emp = self._build_paystub_employment(flat)
                if emp:
                    employments.append(emp)
                ivf = self._build_paystub_income_fragment(flat)
                if ivf:
                    income_fragments.append(ivf)

            elif doc_type == "Bank Statement":
                asset = self._build_bank_asset(flat)
                if asset:
                    party.setdefault("assets", []).append(asset)

            elif prefix == "tax_taxpayer":
                ivf = self._build_tax_income_fragment(flat)
                if ivf:
                    income_fragments.append(ivf)
                tax_addr = self._build_tax_address(flat)
                if tax_addr and "addresses" not in party:
                    party["addresses"] = [tax_addr]

            elif prefix == "tax_spouse":
                pass  # shares taxpayer's return data

            elif prefix in ("le_applicant", "appraisal"):
                pass  # deal-level data handled separately

        if employments:
            party["employment"] = employments
        if income_fragments:
            party["income_verification_fragments"] = income_fragments

        return party

    @staticmethod
    def _enrich_urla_borrower_details(party: dict, flat: dict) -> None:
        """Add URLA borrower personal details to an existing party."""
        individual = party.setdefault("individual", {})

        for flat_key, ind_key in [
            ("urla_borrower_phone", "home_phone"),
            ("urla_borrower_dob", "dob"),
            ("urla_borrower_years_school", "years_school"),
            ("urla_borrower_marital_status", "marital_status"),
            ("urla_borrower_ethnicity", "ethnicity"),
            ("urla_borrower_race", "race"),
            ("urla_borrower_sex", "sex"),
        ]:
            val = flat.get(flat_key)
            if val is not None:
                individual[ind_key] = val

        if flat.get("urla_borrower_us_citizen"):
            individual.setdefault("citizenship_residency", {})["value"] = (
                flat["urla_borrower_us_citizen"]
            )

        if flat.get("urla_borrower_primary_residence_intent"):
            party.setdefault("declarations", {})["intent_to_occupy"] = (
                flat["urla_borrower_primary_residence_intent"]
            )

        # URLA address (overwrites any existing)
        address = {}
        if flat.get("urla_borrower_present_address"):
            address["street"] = flat["urla_borrower_present_address"]
        if flat.get("urla_borrower_city_state_zip"):
            address["city_state_zip"] = flat["urla_borrower_city_state_zip"]
        if address:
            party["addresses"] = [address]

    @staticmethod
    def _build_urla_borrower_employment(flat: dict) -> dict:
        """Build employment dict from URLA borrower flat keys."""
        employment: Dict[str, Any] = {}
        for flat_key, emp_key in [
            ("urla_employer_name", "employer_name"),
            ("urla_position_title", "position_title"),
            ("urla_business_phone", "business_phone"),
        ]:
            if flat.get(flat_key):
                employment[emp_key] = flat[flat_key]

        monthly_income: Dict[str, Any] = {}
        for flat_key, inc_key in [
            ("urla_base_employment_income", "base"),
            ("urla_overtime_income", "overtime"),
            ("urla_total_monthly_income", "total"),
        ]:
            if flat.get(flat_key) is not None:
                monthly_income[inc_key] = flat[flat_key]
        if monthly_income:
            employment["monthly_income"] = monthly_income

        return employment

    @staticmethod
    def _build_paystub_employment(flat: dict) -> dict:
        """Build employment dict from PayStub flat keys."""
        _pg = CanonicalAssembler._pget
        employment: Dict[str, Any] = {}
        for src_key, emp_key in [
            ("paystub_employer_name", "employer_name"),
            ("paystub_employer_business_unit", "employer_business_unit"),
            ("paystub_department", "department"),
            ("paystub_job_title", "position_title"),
            ("paystub_pay_rate", "pay_rate"),
            ("paystub_location", "location"),
            ("paystub_employment_status", "employment_status"),
        ]:
            val = _pg(flat, src_key)
            if val is not None:
                if emp_key == "employment_status":
                    employment["employment_status"] = {"value": val}
                else:
                    employment[emp_key] = val

        if flat.get("paystub_monthly_income_base") is not None:
            employment.setdefault("monthly_income", {})["base"] = (
                flat["paystub_monthly_income_base"]
            )

        return employment

    @staticmethod
    def _build_paystub_income_fragment(flat: dict) -> dict:
        """Build income_verification_fragment from PayStub flat keys."""
        _pg = CanonicalAssembler._pget
        ivf: Dict[str, Any] = {}
        for src_key, ivf_key in [
            ("paystub_pay_period_start", "pay_period_start"),
            ("paystub_pay_period_end", "pay_period_end"),
            ("paystub_advice_date", "advice_date"),
            ("paystub_federal_tax_status", "federal_tax_status"),
            ("paystub_current_gross_pay", "current_gross_pay"),
            ("paystub_current_fed_taxable_gross", "current_fed_taxable_gross"),
            ("paystub_current_total_taxes", "current_total_taxes"),
            ("paystub_current_total_deductions", "current_total_deductions"),
            ("paystub_current_net_pay", "current_net_pay"),
            ("paystub_ytd_gross_amount", "ytd_gross_amount"),
            ("paystub_ytd_fed_taxable_gross", "ytd_fed_taxable_gross"),
            ("paystub_ytd_total_taxes", "ytd_total_taxes"),
            ("paystub_ytd_total_deductions", "ytd_total_deductions"),
            ("paystub_ytd_net_pay", "ytd_net_pay"),
            ("paystub_verified_monthly_base", "verified_monthly_base"),
            ("paystub_source_doc_type", "source_doc"),
        ]:
            val = _pg(flat, src_key)
            if val is not None:
                if ivf_key == "source_doc":
                    ivf["source_doc"] = {"value": val}
                else:
                    ivf[ivf_key] = val

        for list_key in [
            "paystub_earnings",
            "paystub_before_tax_deductions",
            "paystub_after_tax_deductions",
        ]:
            val = flat.get(list_key)
            if val is not None:
                ivf[list_key.replace("paystub_", "")] = val

        return ivf

    @staticmethod
    def _build_bank_asset(flat: dict) -> dict:
        """Build a bank account asset dict from flat keys."""
        asset: Dict[str, Any] = {}
        for src_key, asset_key in [
            ("bank_institution_name", "institution_name"),
            ("bank_account_number", "account_number"),
            ("bank_account_type", "account_type"),
            ("bank_statement_period_start", "statement_period_start"),
            ("bank_statement_period_end", "statement_period_end"),
            ("bank_beginning_balance", "beginning_balance"),
            ("bank_ending_balance", "ending_balance"),
            ("bank_cash_or_market_value", "cash_or_market_value_amount"),
            ("bank_total_deposits", "total_deposits"),
            ("bank_total_withdrawals", "total_withdrawals"),
            ("bank_service_fees", "service_fees"),
            ("bank_total_checks", "total_checks"),
            ("bank_average_balance", "average_balance"),
        ]:
            val = flat.get(src_key)
            if val is not None:
                asset[asset_key] = val

        if flat.get("bank_asset_type"):
            asset["asset_type"] = {"value": flat["bank_asset_type"]}

        for list_key, asset_key in [
            ("bank_deposit_transactions", "transactions"),
            ("bank_withdrawal_transactions", "withdrawal_transactions"),
        ]:
            val = flat.get(list_key)
            if val is not None:
                asset[asset_key] = val

        return asset

    @staticmethod
    def _build_tax_income_fragment(flat: dict) -> dict:
        """Build income_verification_fragment from Tax Return flat keys."""
        ivf: Dict[str, Any] = {}
        for src_key, ivf_key in [
            ("tax_year", "tax_year"),
            ("tax_filing_status", "filing_status"),
            ("tax_wages_salaries_tips", "wages_salaries_tips"),
            ("tax_taxable_interest", "taxable_interest"),
            ("tax_ordinary_dividends", "ordinary_dividends"),
            ("tax_capital_gains", "capital_gains"),
            ("tax_other_income", "other_income"),
            ("tax_total_income", "total_income"),
            ("tax_adjustments_to_income", "adjustments_to_income"),
            ("tax_adjusted_gross_income", "adjusted_gross_income"),
            ("tax_deductions", "deductions"),
            ("tax_taxable_income", "taxable_income"),
            ("tax_total_tax", "total_tax"),
            ("tax_total_payments", "total_payments"),
            ("tax_refund_amount", "refund_amount"),
            ("tax_amount_owed", "amount_owed"),
        ]:
            val = flat.get(src_key)
            if val is not None:
                ivf[ivf_key] = val
        return ivf

    @staticmethod
    def _build_tax_address(flat: dict) -> dict:
        """Build address from tax return flat keys."""
        address: Dict[str, Any] = {}
        for src_key, addr_key in [
            ("tax_taxpayer_street", "street"),
            ("tax_taxpayer_apt", "apt_number"),
            ("tax_taxpayer_city", "city"),
            ("tax_taxpayer_state", "state"),
            ("tax_taxpayer_zip", "zip_code"),
        ]:
            val = flat.get(src_key)
            if val:
                address[addr_key] = val
        return address

    @staticmethod
    def _build_appraisal_collateral(flat: dict) -> dict:
        """Build collateral from appraisal flat keys."""
        prop: Dict[str, Any] = {}
        for src_key, prop_key in [
            ("appraisal_property_address", "address"),
            ("appraisal_property_city", "city"),
            ("appraisal_property_state", "state"),
            ("appraisal_property_zip", "zip_code"),
            ("appraisal_property_county", "county"),
            ("appraisal_legal_description", "legal_description"),
            ("appraisal_year_built", "year_built"),
            ("appraisal_gla_sqft", "gross_living_area_sqft"),
            ("appraisal_room_count", "total_room_count"),
            ("appraisal_bedroom_count", "bedroom_count"),
            ("appraisal_bathroom_count", "bathroom_count"),
            ("appraisal_lot_area", "lot_size"),
            ("appraisal_condition_rating", "condition_rating"),
            ("appraisal_zoning", "zoning_classification"),
        ]:
            val = flat.get(src_key)
            if val is not None:
                prop[prop_key] = val

        valuation: Dict[str, Any] = {}
        if flat.get("appraisal_contract_price") is not None:
            valuation["sales_price"] = flat["appraisal_contract_price"]
        if flat.get("appraisal_form_type"):
            valuation["appraisal_form_type"] = flat["appraisal_form_type"]
        if valuation:
            prop["valuation"] = valuation

        if prop:
            return {"subject_property": prop}
        return {}

    @staticmethod
    def _build_lender_party(flat: dict) -> dict:
        """Build lender/originator party from URLA or Loan Estimate data."""
        lender: Dict[str, Any] = {}
        if flat.get("le_lender_name"):
            lender["company_name"] = flat["le_lender_name"]
        elif flat.get("urla_originator_company"):
            lender["company_name"] = flat["urla_originator_company"]

        individual: Dict[str, Any] = {}
        if flat.get("le_loan_officer"):
            individual["full_name"] = flat["le_loan_officer"]
        if flat.get("le_loan_officer_nmls"):
            individual["nmls_id"] = flat["le_loan_officer_nmls"]
        if individual:
            lender["individual"] = individual

        if lender:
            lender["party_role"] = {"value": "Lender"}
            return lender
        return {}

    @staticmethod
    def _build_merged_disclosures(flat: dict) -> dict:
        """Build disclosures from URLA and/or Loan Estimate flat keys."""
        disclosures: Dict[str, Any] = {}

        # Promissory note — URLA first, LE supplements/overrides
        pn: Dict[str, Any] = {}
        for src_key, pn_key in [
            ("urla_loan_amount", "principal_amount"),
            ("urla_interest_rate", "interest_rate"),
            ("urla_loan_term_months", "loan_term_months"),
        ]:
            if flat.get(src_key) is not None:
                pn[pn_key] = flat[src_key]
        for src_key, pn_key in [
            ("le_principal_amount", "principal_amount"),
            ("le_interest_rate", "interest_rate"),
            ("le_interest_rate_raw", "interest_rate_raw"),
            ("le_loan_term_years", "loan_term_years"),
        ]:
            if flat.get(src_key) is not None:
                pn[pn_key] = flat[src_key]
        if pn:
            disclosures["promissory_note"] = pn

        # Loan Estimate H-24 details
        h24: Dict[str, Any] = {}
        for src_key, h24_key in [
            ("le_date_issued", "date_issued"),
            ("le_product_description", "product_description"),
            ("le_rate_lock", "rate_lock_indicator"),
            ("le_rate_lock_expiration", "rate_lock_expiration_date"),
            ("le_monthly_pi", "monthly_principal_interest"),
            ("le_prepayment_penalty", "prepayment_penalty"),
            ("le_balloon_payment", "balloon_payment"),
            ("le_total_closing_costs", "total_closing_costs"),
            ("le_estimated_cash_to_close", "estimated_cash_to_close"),
            ("le_origination_charges", "origination_charges"),
            ("le_points_percent", "points_percent"),
            ("le_points_amount", "points_amount"),
            ("le_services_cannot_shop", "services_cannot_shop"),
            ("le_services_can_shop", "services_can_shop"),
            ("le_total_loan_costs", "total_loan_costs"),
            ("le_prepaid_interest_per_day", "prepaid_interest_per_day"),
            ("le_prepaid_interest_days", "prepaid_interest_days"),
            ("le_total_closing_costs_j", "total_closing_costs_j"),
            ("le_down_payment", "down_payment"),
            ("le_earnest_money_deposit", "earnest_money_deposit"),
            ("le_seller_credits", "seller_credits"),
            ("le_cash_to_close_table", "estimated_cash_to_close"),
            ("le_apr", "annual_percentage_rate"),
            ("le_total_interest_percentage", "total_interest_percentage"),
            ("le_five_year_total_paid", "five_year_total_paid"),
            ("le_five_year_principal_reduction", "five_year_principal_reduction"),
        ]:
            val = flat.get(src_key)
            if val is not None:
                h24[h24_key] = val
        if h24:
            disclosures["loan_estimate_h24"] = h24

        return disclosures

    @staticmethod
    def _build_merged_identifiers(flat: dict) -> dict:
        """Build identifiers from multiple document sources."""
        ids: Dict[str, Any] = {}
        if flat.get("urla_agency_case_number"):
            ids["agency_case_number"] = flat["urla_agency_case_number"]
        if flat.get("urla_lender_case_number"):
            ids["lender_case_number"] = flat["urla_lender_case_number"]
        if flat.get("le_loan_id") and "lender_case_number" not in ids:
            ids["lender_case_number"] = flat["le_loan_id"]
        if flat.get("appraisal_loan_number") and "lender_case_number" not in ids:
            ids["lender_case_number"] = flat["appraisal_loan_number"]
        return ids

    @staticmethod
    def _count_fields(d: Any, _depth: int = 0) -> int:
        """Count leaf values in a nested structure."""
        if isinstance(d, dict):
            return sum(CanonicalAssembler._count_fields(v, _depth + 1) for v in d.values())
        if isinstance(d, list):
            return sum(CanonicalAssembler._count_fields(v, _depth + 1) for v in d)
        return 1 if d is not None else 0

    # ================================================================
    #  STRATEGY DISPATCH
    # ================================================================

    _STRATEGIES: Dict[str, Any] = {}


# Populate after class body
CanonicalAssembler._STRATEGIES = {
    "W-2 Form": CanonicalAssembler._w2_strategy,
    "URLA (Form 1003)": CanonicalAssembler._urla_strategy,
    "Pay Stub": CanonicalAssembler._paystub_strategy,
    "Bank Statement": CanonicalAssembler._bank_statement_strategy,
    "Tax Return (1040)": CanonicalAssembler._tax_return_strategy,
    "Appraisal (Form 1004)": CanonicalAssembler._appraisal_strategy,
    "Loan Estimate": CanonicalAssembler._loan_estimate_strategy,
    "Loan Estimate (H-24)": CanonicalAssembler._loan_estimate_strategy,
    "merged": CanonicalAssembler._merged_strategy,
}
