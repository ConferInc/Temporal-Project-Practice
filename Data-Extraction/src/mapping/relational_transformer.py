"""
Relational Transformer — Canonical JSON → Supabase table-organized payload.

Bridges the hierarchical canonical JSON (MISMO-aligned document view) to
a flat relational structure matching the Supabase SQL schema.

Output is a "Database Action Payload": a dict keyed by table name, where
each value is a list of row dicts ready for insertion.  Internal ``_ref``
keys are used for foreign-key resolution (the actual UUIDs are generated
at insert time by the downstream client).

Dependencies: stdlib only (no AI libraries, no Supabase client)
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.utils.logging import logger


class RelationalTransformer:
    """Canonical JSON → Supabase relational table payload."""

    def transform(self, canonical_data: dict) -> dict:
        """Transform canonical JSON into a database action payload.

        Args:
            canonical_data: Deep canonical JSON from CanonicalAssembler
                            (e.g. ``2_canonical.json``)

        Returns:
            Dict keyed by table name, each containing a list of row dicts.
            Row dicts include ``_ref`` keys for internal cross-referencing
            and ``_operation`` to indicate the intended DB operation.
        """
        deal = canonical_data.get("deal", {})
        parties = deal.get("parties", [])
        collateral = deal.get("collateral", {})
        transaction = deal.get("transaction_information", {})
        disclosures = deal.get("disclosures_and_closing", {})
        identifiers = deal.get("identifiers", {})

        # Accumulators per table
        customers: List[dict] = []
        employments: List[dict] = []
        incomes: List[dict] = []
        demographics: List[dict] = []
        residences: List[dict] = []
        assets: List[dict] = []
        liabilities: List[dict] = []
        app_customers: List[dict] = []
        properties: List[dict] = []
        applications: List[dict] = []

        # ── Property from collateral ───────────────────────────────
        prop_ref = None
        subject = collateral.get("subject_property", {})
        if subject:
            prop_row = self._transform_property(subject)
            prop_ref = prop_row["_ref"]
            properties.append(prop_row)

        # ── Application from transaction + disclosures ─────────────
        app_row = self._transform_application(
            transaction, disclosures, identifiers, prop_ref
        )
        app_ref = app_row["_ref"]
        # Occupancy comes from collateral
        occ = subject.get("occupancy_type", {})
        if isinstance(occ, dict):
            occ = occ.get("value")
        if occ:
            app_row["occupancy_type"] = occ
        applications.append(app_row)

        # ── Parties → customers + child tables ─────────────────────
        primary_customer_ref = None

        for idx, party in enumerate(parties):
            role_val = (party.get("party_role") or {}).get("value", "")

            # Skip lender parties — they map to organizations, not customers
            # But preserve lender information in application.key_information
            if role_val == "Lender":
                lender_info = {}
                if party.get("company_name"):
                    lender_info["lender_name"] = party["company_name"]
                individual = party.get("individual", {})
                if individual.get("full_name"):
                    lender_info["loan_officer_name"] = individual["full_name"]
                if individual.get("nmls_id"):
                    lender_info["loan_officer_nmls"] = individual["nmls_id"]
                
                if lender_info:
                    app_row.setdefault("key_information", {})["lender"] = lender_info
                    logger.info(f"Preserved lender information: {lender_info.get('lender_name')}")
                
                continue

            individual = party.get("individual", {})
            has_customer_data = individual or party.get("company_name")
            
            # Create customer if we have individual or company data
            cust_ref = f"customer_{idx}"
            if has_customer_data:
                cust_row = self._transform_customer(individual, cust_ref)
                customers.append(cust_row)

                if primary_customer_ref is None:
                    primary_customer_ref = cust_ref

                # Junction: application_customers
                ac_row = {
                    "_ref": f"app_cust_{idx}",
                    "_operation": "insert",
                    "_application_ref": app_ref,
                    "_customer_ref": cust_ref,
                    "role": role_val or "Borrower",
                    "sequence": idx + 1,
                }
                app_customers.append(ac_row)

                # Demographics
                demo = self._transform_demographics(individual, cust_ref, app_ref)
                if demo:
                    demographics.append(demo)

                # Residences from addresses
                for addr_idx, addr in enumerate(party.get("addresses", [])):
                    res = self._transform_residence(
                        addr, cust_ref, app_ref, addr_idx
                    )
                    if res:
                        residences.append(res)
            else:
                # No customer data, but party may have employment, income, etc.
                # We still process these with a placeholder customer_ref
                logger.warning(f"Party {idx}: No individual/company data, creating placeholder for related records")

            # Employment records (can exist without customer)
            for emp_idx, emp in enumerate(party.get("employment", [])):
                emp_ref = f"employment_{idx}_{emp_idx}"
                emp_row = self._transform_employment(
                    emp, emp_ref, cust_ref, app_ref
                )
                employments.append(emp_row)

                # Income records from monthly_income
                mi = emp.get("monthly_income", {})
                for inc_type, amount in mi.items():
                    if inc_type == "total":
                        continue  # computed, not stored
                    if amount is not None:
                        inc_ref = f"income_{idx}_{emp_idx}_{inc_type}"
                        incomes.append({
                            "_ref": inc_ref,
                            "_operation": "insert",
                            "_customer_ref": cust_ref,
                            "_application_ref": app_ref,
                            "_employment_ref": emp_ref,
                            "income_source": "Employment",
                            "income_type": inc_type.replace("_", " ").title(),
                            "monthly_amount": amount,
                        })

            # Self-employment records
            for self_emp_idx, self_emp in enumerate(party.get("self_employment", [])):
                emp_ref = f"employment_{idx}_self_{self_emp_idx}"
                emp_row = {
                    "_ref": emp_ref,
                    "_operation": "insert",
                    "_customer_ref": cust_ref,
                    "_application_ref": app_ref,
                    "employment_type": "SelfEmployed",
                    "is_self_employed": True,
                    "is_current": True,
                    "start_date": None,  # Required by schema
                }
                
                if self_emp.get("business_name"):
                    emp_row["employer_name"] = self_emp["business_name"]
                
                if self_emp.get("business_phone"):
                    emp_row["employer_phone"] = self_emp["business_phone"]
                
                # Store business address in employer address fields (schema compliant)
                if self_emp.get("business_address_street"):
                    emp_row["employer_street_address"] = self_emp["business_address_street"]
                
                if self_emp.get("business_address_city"):
                    emp_row["employer_city"] = self_emp["business_address_city"]
                
                if self_emp.get("business_address_state"):
                    emp_row["employer_state"] = self_emp["business_address_state"]
                
                if self_emp.get("business_address_zip"):
                    emp_row["employer_zip_code"] = self_emp["business_address_zip"]
                
                employments.append(emp_row)

            # Income streams (1099, self-employment income, etc.)
            for inc_idx, inc in enumerate(party.get("income", [])):
                non_w2 = inc.get("non_w2_income", {})
                for key, val in non_w2.items():
                    if val:
                        incomes.append({
                            "_ref": f"income_{idx}_generic_{inc_idx}_{key}",
                            "_operation": "insert",
                            "_customer_ref": cust_ref,
                            "_application_ref": app_ref,
                            "income_source": "Other",
                            "income_type": key.replace("_", " ").title(),
                            "monthly_amount": str(val),
                            "include_in_qualification": True,
                        })

            # Tax withholding (store in incomes metadata)
            for tax_idx, tax in enumerate(party.get("taxes", [])):
                if tax.get("federal_withheld_amount"):
                    incomes.append({
                        "_ref": f"income_{idx}_tax_{tax_idx}",
                        "_operation": "insert",
                        "_customer_ref": cust_ref,
                        "_application_ref": app_ref,
                        "income_source": "TaxWithholding",
                        "income_type": "Federal Withheld",
                        "monthly_amount": "0",
                        "metadata": {
                            "annual_withheld": tax["federal_withheld_amount"],
                            "is_withholding": True
                        }
                    })

            # Assets
            for asset_idx, asset_data in enumerate(party.get("assets", [])):
                asset_row = self._transform_asset(
                    asset_data, app_ref, idx, asset_idx
                )
                if asset_row:
                    assets.append(asset_row)

            # Liabilities (total from URLA)
            total_liabilities = party.get("total_liabilities")
            total_monthly_pmts = party.get("total_monthly_payments")
            if total_liabilities is not None or total_monthly_pmts is not None:
                liabilities.append({
                    "_ref": f"liability_{idx}_total",
                    "_operation": "insert",
                    "_application_ref": app_ref,
                    "liability_type": "Other",
                    "creditor_name": "URLA Reported Total",
                    "unpaid_balance": total_liabilities,
                    "monthly_payment": total_monthly_pmts or 0,
                })

            # Liabilities (detailed list from Credit Report)
            # If the party has explicit liabilities list (nested mode usually puts them under 'deal'
            # but sometimes they might be associated with a party if we change YAML)
            # Currently CreditBureauReport.yaml targets "deal.liabilities", so it's handled below outside the party loop.
            # But if there are party-specific liabilities... processing them here.
            pass

        # ── Deal-level Liabilities (Credit Report) ─────────────────
        deal_liabilities = deal.get("liabilities", [])
        for liab_idx, liab in enumerate(deal_liabilities):
             liab_ref = f"liability_deal_{liab_idx}"
             row = {
                 "_ref": liab_ref,
                 "_operation": "insert",
                 "_application_ref": app_ref,
                 "liability_type": liab.get("liability_type", {}).get("value", "Other"),
                 "creditor_name": liab.get("creditor_name"),
                 "account_number": liab.get("account_number"),
             }
             if "unpaid_balance" in liab:
                 row["unpaid_balance"] = liab["unpaid_balance"]
             elif "balance_raw" in liab:
                 # Clean generic extraction raw string
                 # (naive cleanup, ideal place is Assembler or RuleEngine transform)
                 row["unpaid_balance"] = self._clean_currency(liab["balance_raw"])

             if "monthly_payment" in liab:
                 row["monthly_payment"] = liab["monthly_payment"]
             else:
                 row["monthly_payment"] = 0 # Required by schema
             
             liabilities.append(row)

             # Implicitly link to primary customer for now if we don't have ownership info
             if primary_customer_ref:
                 # We don't have a 'liability_ownership' accumulator in the standard list above,
                 # but we can add one if the schema requires it.
                 # Looking at schema: liability_ownership table exists.
                 # Looking at output structure lines 44-54: no liability_ownership list init.
                 pass 

        # Set primary customer on application
        if primary_customer_ref:
            app_row["_primary_customer_ref"] = primary_customer_ref

        result = {
            "_metadata": {
                "source": "RelationalTransformer",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "table_count": 0,
                "total_rows": 0,
            },
            "properties": properties,
            "applications": applications,
            "customers": customers,
            "application_customers": app_customers,
            "employments": employments,
            "incomes": incomes,
            "demographics": demographics,
            "residences": residences,
            "assets": assets,
            "liabilities": liabilities,
        }

        # Update metadata counts
        row_count = 0
        table_count = 0
        for key, val in result.items():
            if key.startswith("_"):
                continue
            if val:
                table_count += 1
                row_count += len(val)
        result["_metadata"]["table_count"] = table_count
        result["_metadata"]["total_rows"] = row_count

        # Detect unmapped canonical fields
        self._log_unmapped_fields(canonical_data, result, parties)

        logger.info(
            f"RelationalTransformer: {row_count} rows across "
            f"{table_count} tables"
        )
        return result

    def _log_unmapped_fields(self, canonical_data: dict, result: dict, parties: list) -> None:
        """Log warnings for canonical fields that weren't transformed."""
        deal = canonical_data.get("deal", {})
        
        for idx, party in enumerate(parties):
            # Check for unprocessed arrays
            if party.get("self_employment") and not any(
                e.get("_ref", "").startswith(f"employment_{idx}_self") 
                for e in result.get("employments", [])
            ):
                logger.warning(f"Party {idx}: self_employment data not transformed (check mapping)")
            
            if party.get("income_documents"):
                logger.warning(f"Party {idx}: income_documents metadata not preserved (consider adding to metadata)")
            
            if party.get("taxes") and not any(
                i.get("_ref", "").startswith(f"income_{idx}_tax") 
                for i in result.get("incomes", [])
            ):
                logger.warning(f"Party {idx}: taxes data not transformed")
            
            # Check for income arrays without processing
            if party.get("income") and not any(
                i.get("_ref", "").startswith(f"income_{idx}_generic") 
                for i in result.get("incomes", [])
            ):
                logger.warning(f"Party {idx}: income data exists but not transformed")

    # ================================================================
    #  TABLE-LEVEL TRANSFORMERS
    # ================================================================

    def _transform_property(self, subject: dict) -> dict:
        """collateral.subject_property → properties row."""
        row: Dict[str, Any] = {
            "_ref": "property_0",
            "_operation": "upsert",
        }

        # Parse combined address string into jsonb structure
        raw_addr = subject.get("address", "")
        if raw_addr:
            row["address"] = self._parse_address_to_jsonb(raw_addr)

        if subject.get("number_of_units") is not None:
            row.setdefault("metadata", {})["number_of_units"] = (
                subject["number_of_units"]
            )

        valuation = subject.get("valuation", {})
        if valuation.get("sales_price") is not None:
            row["purchase_price"] = valuation["sales_price"]
        if valuation.get("appraised_value") is not None:
            row["appraised_value"] = valuation["appraised_value"]

        if subject.get("year_built") is not None:
            row["year_built"] = subject["year_built"]
        if subject.get("bedroom_count") is not None:
            row["bedrooms"] = subject["bedroom_count"]
        if subject.get("bathroom_count") is not None:
            row["bathrooms"] = subject["bathroom_count"]
        if subject.get("gross_living_area_sqft") is not None:
            row["square_feet"] = subject["gross_living_area_sqft"]

        # Property type from zoning or occupancy
        if subject.get("zoning_classification"):
            row["property_type"] = subject["zoning_classification"]

        return row

    def _transform_application(
        self,
        transaction: dict,
        disclosures: dict,
        identifiers: dict,
        prop_ref: Optional[str],
    ) -> dict:
        """transaction_information + disclosures → applications row."""
        row: Dict[str, Any] = {
            "_ref": "application_0",
            "_operation": "upsert",
            "status": "imported",
            "stage": "processing",
        }

        if prop_ref:
            row["_property_ref"] = prop_ref

        # Loan amount: prefer final_loan_amount, fallback to principal
        pn = disclosures.get("promissory_note", {})
        loan_amt = transaction.get("final_loan_amount")
        if loan_amt is None:
            loan_amt = pn.get("principal_amount")
        if loan_amt is not None:
            row["loan_amount"] = loan_amt

        # Application number from identifiers
        case_num = identifiers.get("agency_case_number")
        if case_num:
            row["application_number"] = case_num

        # Key information: pack all transaction + disclosure details
        key_info: Dict[str, Any] = {}

        # Transaction fields
        for field, ki_key in [
            ("mortgage_type", "mortgage_type"),
            ("loan_purpose", "loan_purpose"),
            ("amortization_type", "amortization_type"),
        ]:
            val = transaction.get(field)
            if isinstance(val, dict):
                val = val.get("value")
            if val:
                key_info[ki_key] = val

        if transaction.get("application_date"):
            key_info["application_date"] = transaction["application_date"]
            row["submitted_at"] = self._to_iso_date(
                transaction["application_date"]
            )

        for field in [
            "estimated_prepaid_items",
            "estimated_closing_costs",
            "pmi_funding_fee",
        ]:
            if transaction.get(field) is not None:
                key_info[field] = transaction[field]

        # Promissory note
        if pn:
            key_info["promissory_note"] = pn

        # Loan Estimate H-24 details
        h24 = disclosures.get("loan_estimate_h24")
        if h24:
            key_info["loan_estimate_h24"] = h24
            
            # Map date_issued to submitted_at if not already set
            if h24.get("date_issued") and "submitted_at" not in row:
                row["submitted_at"] = self._to_iso_date(h24["date_issued"])
                logger.info(f"Mapped loan estimate date_issued to application.submitted_at")

        # Identifiers
        if identifiers:
            key_info["identifiers"] = identifiers

        if key_info:
            row["key_information"] = key_info

        return row

    def _transform_customer(self, individual: dict, ref: str) -> dict:
        """party.individual → customers row."""
        row: Dict[str, Any] = {
            "_ref": ref,
            "_operation": "upsert",
            "customer_type": "individual",
        }

        # Name splitting
        first, last = self._split_name(
            individual.get("full_name"),
            individual.get("first_name"),
            individual.get("last_name"),
        )
        if first:
            row["first_name"] = first
        if last:
            row["last_name"] = last

        if individual.get("ssn"):
            row["ssn_encrypted"] = individual["ssn"]

        if individual.get("dob"):
            row["date_of_birth"] = self._to_iso_date(individual["dob"])

        if individual.get("home_phone"):
            row["phone_home"] = individual["home_phone"]

        if individual.get("marital_status"):
            row["marital_status"] = individual["marital_status"]

        citizenship = individual.get("citizenship_residency", {})
        if isinstance(citizenship, dict) and citizenship.get("value"):
            row["citizenship_type"] = citizenship["value"]

        return row

    def _transform_employment(
        self,
        emp: dict,
        ref: str,
        customer_ref: str,
        app_ref: str,
    ) -> dict:
        """party.employment[] entry → employments row."""
        row: Dict[str, Any] = {
            "_ref": ref,
            "_operation": "insert",
            "_customer_ref": customer_ref,
            "_application_ref": app_ref,
            "employment_type": "W2",
        }

        if emp.get("employer_name"):
            row["employer_name"] = emp["employer_name"]

        if emp.get("position_title"):
            row["position_title"] = emp["position_title"]

        if emp.get("business_phone"):
            row["employer_phone"] = emp["business_phone"]

        # Note: employer_ein is not stored in employments table
        # It can be added to key_information or a separate employers table
        
        # Employment status
        status = emp.get("employment_status", {})
        if isinstance(status, dict):
            status = status.get("value")
        row["is_current"] = (
            str(status).lower() == "current" if status else True
        )

        # Self-employed detection
        if emp.get("is_self_employed"):
            row["is_self_employed"] = True
            row["employment_type"] = "SelfEmployed"

        # Start date: use pay_period_start as proxy if no explicit date
        if emp.get("start_date"):
            row["start_date"] = self._to_iso_date(emp["start_date"])
        else:
            # Required by schema - will be populated by schema enforcer if missing
            row["start_date"] = None

        return row

    def _transform_demographics(
        self,
        individual: dict,
        customer_ref: str,
        app_ref: str,
    ) -> Optional[dict]:
        """party.individual demographics fields → demographics row."""
        ethnicity = individual.get("ethnicity")
        race = individual.get("race")
        sex = individual.get("sex")

        if not any([ethnicity, race, sex]):
            return None

        row: Dict[str, Any] = {
            "_ref": f"demo_{customer_ref}",
            "_operation": "insert",
            "_customer_ref": customer_ref,
            "_application_ref": app_ref,
            "collection_method": "FaceToFace",
        }

        if ethnicity:
            row["ethnicity"] = [ethnicity] if isinstance(ethnicity, str) else ethnicity
        if race:
            row["race"] = [race] if isinstance(race, str) else race
        if sex:
            row["sex"] = sex

        return row

    def _transform_residence(
        self,
        addr: dict,
        customer_ref: str,
        app_ref: str,
        addr_idx: int,
    ) -> Optional[dict]:
        """party.addresses[] entry → residences row."""
        street = addr.get("street", "")
        if not street:
            return None

        row: Dict[str, Any] = {
            "_ref": f"residence_{customer_ref}_{addr_idx}",
            "_operation": "insert",
            "_customer_ref": customer_ref,
            "_application_ref": app_ref,
            "residence_type": "Current" if addr_idx == 0 else "Prior",
            "street_address": street,
        }

        # Try to parse city_state_zip (handle both field name variants)
        csz = addr.get("city_state_zip") or addr.get("city_state_zip_raw", "")
        if csz:
            city, state, zipcode = self._parse_city_state_zip(csz)
            if city:
                row["city"] = city
            if state:
                row["state"] = state
            if zipcode:
                row["zip_code"] = zipcode
        else:
            # Try parsing from street if it contains full address
            parsed = self._parse_address_to_jsonb(street)
            if parsed.get("city"):
                row["city"] = parsed["city"]
            if parsed.get("state"):
                row["state"] = parsed["state"]
            if parsed.get("zip"):
                row["zip_code"] = parsed["zip"]

        return row

    def _transform_asset(
        self,
        asset_data: dict,
        app_ref: str,
        party_idx: int,
        asset_idx: int,
    ) -> Optional[dict]:
        """party.assets[] entry → assets row."""
        row: Dict[str, Any] = {
            "_ref": f"asset_{party_idx}_{asset_idx}",
            "_operation": "insert",
            "_application_ref": app_ref,
            "asset_category": "LiquidAsset",
        }

        if asset_data.get("institution_name"):
            row["institution_name"] = asset_data["institution_name"]
        if asset_data.get("account_number"):
            row["account_number"] = asset_data["account_number"]

        # Value: ending_balance or cash_or_market_value_amount
        value = (
            asset_data.get("cash_or_market_value_amount")
            or asset_data.get("ending_balance")
            or 0
        )
        row["cash_or_market_value"] = value

        # Asset type
        asset_type = asset_data.get("asset_type", {})
        if isinstance(asset_type, dict):
            asset_type = asset_type.get("value", "CheckingAccount")
        row["asset_type"] = asset_type or "CheckingAccount"

        return row

    # ================================================================
    #  PARSING HELPERS
    # ================================================================

    @staticmethod
    def _split_name(
        full_name: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Split a name into (first, last).

        If first_name and last_name are already provided, use them.
        Otherwise, split full_name on the last space boundary.
        """
        if first_name or last_name:
            return first_name, last_name

        if not full_name:
            return None, None

        full_name = full_name.strip()
        parts = full_name.split()
        if len(parts) == 1:
            return full_name, None
        return parts[0], " ".join(parts[1:])

    @staticmethod
    def _parse_city_state_zip(csz: str) -> Tuple[
        Optional[str], Optional[str], Optional[str]
    ]:
        """Parse 'City, ST 12345' into (city, state, zip)."""
        if not csz:
            return None, None, None

        # Pattern: City, ST 12345 or City, ST 12345-6789
        m = re.match(
            r"^(.+?),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$",
            csz.strip(),
        )
        if m:
            return m.group(1).strip(), m.group(2), m.group(3)

        # Fallback: split on comma
        parts = csz.split(",")
        if len(parts) >= 2:
            city = parts[0].strip()
            rest = parts[-1].strip().split()
            state = rest[0] if rest else None
            zipcode = rest[1] if len(rest) > 1 else None
            return city, state, zipcode

        return csz.strip(), None, None

    @staticmethod
    def _parse_address_to_jsonb(address: str) -> dict:
        """Parse a combined address string into {street, city, state, zip}.

        Handles formats like:
          '748 Thompson Island, Milwaukee, WI 53288'
          '123MainStreet Denver,CO80202'
        """
        if not address:
            return {}

        result: Dict[str, Any] = {}

        # Try standard format: street, city, ST ZIP
        m = re.match(
            r"^(.+?),\s*(.+?),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$",
            address.strip(),
        )
        if m:
            result["street"] = m.group(1).strip()
            result["city"] = m.group(2).strip()
            result["state"] = m.group(3)
            result["zip"] = m.group(4)
            return result

        # Try: street, city ST ZIP (no comma before state)
        m = re.match(
            r"^(.+?),\s*(.+?)\s+([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$",
            address.strip(),
        )
        if m:
            result["street"] = m.group(1).strip()
            result["city"] = m.group(2).strip()
            result["state"] = m.group(3)
            result["zip"] = m.group(4)
            return result

        # Fallback: return full string as street
        result["street"] = address.strip()
        return result

    @staticmethod
    def _to_iso_date(date_str: Optional[str]) -> Optional[str]:
        """Convert MM/DD/YYYY to YYYY-MM-DD (ISO 8601).

        Returns the input unchanged if it doesn't match MM/DD/YYYY.
        """
        if not date_str:
            return None

        m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", date_str.strip())
        if m:
            return f"{m.group(3)}-{m.group(1)}-{m.group(2)}"

        return date_str

    @staticmethod
    def _clean_currency(value: Any) -> float:
        """Parse currency string like '$ 1,234.56' to float 1234.56."""
        if isinstance(value, (int, float)):
            return float(value)
        if not value:
            return 0.0

        s = str(value)
        # Remove '$', space, ','
        s = s.replace("$", "").replace(",", "").strip()
        try:
            return float(s)
        except ValueError:
            return 0.0
