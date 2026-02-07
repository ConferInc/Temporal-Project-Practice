"""
MISMO 3.4 XML Emitter — Canonical JSON to MISMO XML.

Builds valid MISMO 3.4 XML from the canonical model produced by the
RuleEngine.  Zero LLM.  Pure xml.etree.ElementTree.

Output structure:
  MESSAGE
    ABOUT_VERSIONS / ABOUT_VERSION
    DEAL_SETS / DEAL_SET / DEALS / DEAL
      PARTIES / PARTY [per party]
        INDIVIDUAL / NAME
        TAXPAYER_IDENTIFIERS / TAXPAYER_IDENTIFIER
        ADDRESSES / ADDRESS
        ROLES / ROLE / ROLE_DETAIL + BORROWER
          EMPLOYERS / EMPLOYER / LEGAL_ENTITY
          CURRENT_INCOME / CURRENT_INCOME_ITEMS / CURRENT_INCOME_ITEM
          DECLARATION / DECLARATION_DETAIL
      COLLATERALS / COLLATERAL / SUBJECT_PROPERTY
        ADDRESS
        PROPERTY_DETAIL
        PROPERTY_VALUATIONS / PROPERTY_VALUATION
      LOANS / LOAN
        AMORTIZATION / AMORTIZATION_RULE
        LOAN_DETAIL
        TERMS_OF_LOAN
        LOAN_PURPOSE
        CLOSING_INFORMATION / CLOSING_INFORMATION_DETAIL
"""

import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from src.utils.logging import logger


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sub(parent: ET.Element, tag: str) -> ET.Element:
    """Create and return a sub-element."""
    return ET.SubElement(parent, tag)


def _sub_text(parent: ET.Element, tag: str, value: Any) -> Optional[ET.Element]:
    """Create a text sub-element only if value is truthy."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    elem = ET.SubElement(parent, tag)
    elem.text = text
    return elem


def _get(data: dict, *keys, default=None):
    """Safe nested dict access."""
    current = data
    for k in keys:
        if isinstance(current, dict):
            current = current.get(k)
        elif isinstance(current, list) and isinstance(k, int) and k < len(current):
            current = current[k]
        else:
            return default
        if current is None:
            return default
    return current


# ---------------------------------------------------------------------------
# Emitter
# ---------------------------------------------------------------------------

class MismoEmitter:
    """
    Converts Canonical JSON -> MISMO 3.4 XML string.

    Usage:
        emitter = MismoEmitter()
        xml_str = emitter.emit(canonical_data)
    """

    MISMO_VERSION = "3.4"
    NAMESPACE = "http://www.mismo.org/residential/2009/schemas"

    def emit(self, canonical: Dict[str, Any]) -> str:
        """Build and return pretty-printed MISMO 3.4 XML."""
        deal = canonical.get("deal", {})
        if not deal:
            logger.warning("MismoEmitter: no 'deal' key in canonical data")
            return ""

        # Root: MESSAGE
        message = ET.Element("MESSAGE")
        message.set("xmlns", self.NAMESPACE)

        # ABOUT_VERSIONS
        about = _sub(message, "ABOUT_VERSIONS")
        av = _sub(about, "ABOUT_VERSION")
        _sub_text(av, "DataVersionIdentifier", self.MISMO_VERSION)

        # DEAL_SETS > DEAL_SET > DEALS > DEAL
        deal_sets = _sub(message, "DEAL_SETS")
        deal_set = _sub(deal_sets, "DEAL_SET")
        deals = _sub(deal_set, "DEALS")
        deal_elem = _sub(deals, "DEAL")

        # --- Build sub-trees ---
        self._build_parties(deal_elem, deal.get("parties", []))
        self._build_collaterals(deal_elem, deal.get("collateral", {}))
        self._build_loans(deal_elem, deal)

        # Pretty-print
        ET.indent(message, space="  ", level=0)
        xml_str = ET.tostring(message, encoding="unicode", xml_declaration=False)
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str

        field_count = self._count_elements(message)
        logger.info(f"MismoEmitter: generated XML with {field_count} data elements")
        return xml_str

    # ================================================================
    #  PARTIES
    # ================================================================

    def _build_parties(self, deal_elem: ET.Element, parties: list):
        if not parties:
            return
        parties_elem = _sub(deal_elem, "PARTIES")

        for party_data in parties:
            party = _sub(parties_elem, "PARTY")
            individual = party_data.get("individual", {})
            employment_list = party_data.get("employment", [])
            addresses = party_data.get("addresses", [])
            party_role = _get(party_data, "party_role", "value")

            # --- INDIVIDUAL ---
            ind_elem = _sub(party, "INDIVIDUAL")

            # NAME
            name_elem = _sub(ind_elem, "NAME")
            full_name = individual.get("full_name", "")
            if full_name:
                parts = full_name.split()
                if len(parts) >= 2:
                    _sub_text(name_elem, "FirstName", parts[0])
                    _sub_text(name_elem, "LastName", parts[-1])
                    if len(parts) > 2:
                        _sub_text(name_elem, "MiddleName", " ".join(parts[1:-1]))
                else:
                    _sub_text(name_elem, "FullName", full_name)
            else:
                _sub_text(name_elem, "FirstName", individual.get("first_name"))
                _sub_text(name_elem, "MiddleName", individual.get("middle_name"))
                _sub_text(name_elem, "LastName", individual.get("last_name"))

            _sub_text(ind_elem, "BirthDate", individual.get("dob"))
            _sub_text(ind_elem, "MaritalStatusType", individual.get("marital_status"))

            # TAXPAYER_IDENTIFIERS
            ssn = individual.get("ssn")
            if ssn:
                tids = _sub(ind_elem, "TAXPAYER_IDENTIFIERS")
                tid = _sub(tids, "TAXPAYER_IDENTIFIER")
                _sub_text(tid, "TaxpayerIdentifierType", "SocialSecurityNumber")
                _sub_text(tid, "TaxpayerIdentifierValue", ssn)

            # CONTACT_POINTS (phone)
            phone = individual.get("home_phone")
            if phone:
                cps = _sub(ind_elem, "CONTACT_POINTS")
                cp = _sub(cps, "CONTACT_POINT")
                cpd = _sub(cp, "CONTACT_POINT_TELEPHONE")
                _sub_text(cpd, "ContactPointTelephoneValue", phone)

            # ADDRESSES
            if addresses:
                addrs_elem = _sub(party, "ADDRESSES")
                for addr_data in addresses:
                    addr = _sub(addrs_elem, "ADDRESS")
                    street = addr_data.get("street", "")
                    csz = addr_data.get("city_state_zip", "")
                    _sub_text(addr, "AddressLineText", street)
                    if csz:
                        # Parse "Syracuse, NY 13224"
                        self._parse_city_state_zip(addr, csz)
                    else:
                        _sub_text(addr, "CityName", addr_data.get("city"))
                        _sub_text(addr, "StateCode", addr_data.get("state"))
                        _sub_text(addr, "PostalCode", addr_data.get("postal_code"))
                    addr_type = _get(addr_data, "address_type", "value")
                    if addr_type:
                        _sub_text(addr, "AddressType", addr_type)

            # ROLES
            roles_elem = _sub(party, "ROLES")
            role_elem = _sub(roles_elem, "ROLE")

            rd = _sub(role_elem, "ROLE_DETAIL")
            _sub_text(rd, "PartyRoleType", party_role or "Borrower")

            # BORROWER (employment + income)
            if party_role in (None, "Borrower", "CoBorrower"):
                borrower = _sub(role_elem, "BORROWER")

                # EMPLOYERS
                if employment_list:
                    employers = _sub(borrower, "EMPLOYERS")
                    for emp in employment_list:
                        employer = _sub(employers, "EMPLOYER")
                        le = _sub(employer, "LEGAL_ENTITY")
                        _sub_text(le, "FullName", emp.get("employer_name"))
                        _sub_text(employer, "EmploymentPositionDescription",
                                  emp.get("position_title"))
                        _sub_text(employer, "EmploymentStatusType",
                                  _get(emp, "employment_status", "value"))
                        _sub_text(employer, "EmploymentSelfEmployedIndicator",
                                  emp.get("self_employed_indicator"))

                        # CURRENT INCOME
                        income = emp.get("monthly_income", {})
                        if income:
                            ci = _sub(borrower, "CURRENT_INCOME")
                            cii = _sub(ci, "CURRENT_INCOME_ITEMS")
                            base = income.get("base")
                            if base is not None:
                                item = _sub(cii, "CURRENT_INCOME_ITEM")
                                _sub_text(item, "CurrentIncomeMonthlyTotalAmount", base)
                                _sub_text(item, "IncomeType", "Base")
                            overtime = income.get("overtime")
                            if overtime is not None:
                                item = _sub(cii, "CURRENT_INCOME_ITEM")
                                _sub_text(item, "CurrentIncomeMonthlyTotalAmount", overtime)
                                _sub_text(item, "IncomeType", "Overtime")
                            bonus = income.get("bonus")
                            if bonus is not None:
                                item = _sub(cii, "CURRENT_INCOME_ITEM")
                                _sub_text(item, "CurrentIncomeMonthlyTotalAmount", bonus)
                                _sub_text(item, "IncomeType", "Bonus")
                            commission = income.get("commission")
                            if commission is not None:
                                item = _sub(cii, "CURRENT_INCOME_ITEM")
                                _sub_text(item, "CurrentIncomeMonthlyTotalAmount", commission)
                                _sub_text(item, "IncomeType", "Commissions")

                # DECLARATION
                declarations = party_data.get("declarations", {})
                citizenship = _get(party_data, "individual", "citizenship_residency", "value")
                if declarations or citizenship:
                    decl = _sub(borrower, "DECLARATION")
                    dd = _sub(decl, "DECLARATION_DETAIL")
                    if citizenship is True or str(citizenship).lower() == "uscitizen":
                        _sub_text(dd, "CitizenshipResidencyType", "USCitizen")
                    elif citizenship:
                        _sub_text(dd, "CitizenshipResidencyType", str(citizenship))
                    _sub_text(dd, "IntentToOccupyType",
                              "Yes" if declarations.get("intent_to_occupy") else None)

    # ================================================================
    #  COLLATERALS
    # ================================================================

    def _build_collaterals(self, deal_elem: ET.Element, collateral: dict):
        if not collateral:
            return
        sp = collateral.get("subject_property", {})
        if not sp:
            return

        collaterals = _sub(deal_elem, "COLLATERALS")
        coll = _sub(collaterals, "COLLATERAL")
        subj = _sub(coll, "SUBJECT_PROPERTY")

        # ADDRESS
        address = sp.get("address", "")
        if address:
            addr = _sub(subj, "ADDRESS")
            _sub_text(addr, "AddressLineText", address)
            # Try to parse city, state, zip from full address
            self._parse_full_address(addr, address)

        # PROPERTY_DETAIL
        pd_elem = _sub(subj, "PROPERTY_DETAIL")
        _sub_text(pd_elem, "PropertyCurrentUsageType",
                  _get(sp, "occupancy_type", "value"))
        _sub_text(pd_elem, "ProjectDesignType",
                  _get(sp, "property_type", "value"))
        _sub_text(pd_elem, "PropertyEstateType",
                  sp.get("estate_type"))
        _sub_text(pd_elem, "FinancedUnitCount",
                  sp.get("number_of_units"))

        # PROPERTY_VALUATIONS
        valuation = sp.get("valuation", {})
        if valuation:
            pvs = _sub(subj, "PROPERTY_VALUATIONS")
            pv = _sub(pvs, "PROPERTY_VALUATION")
            _sub_text(pv, "PropertyValuationAmount",
                      valuation.get("appraised_value"))
            _sub_text(pv, "PropertyEstimatedValueAmount",
                      valuation.get("sales_price"))
            _sub_text(pv, "AppraisalMethodType",
                      _get(valuation, "appraisal_method", "value"))

    # ================================================================
    #  LOANS
    # ================================================================

    def _build_loans(self, deal_elem: ET.Element, deal: dict):
        tx = deal.get("transaction_information", {})
        disc = deal.get("disclosures_and_closing", {})
        note = disc.get("promissory_note", {})
        ids = deal.get("identifiers", {})

        # Only emit LOANS if we have any loan data
        if not tx and not note and not ids:
            return

        loans_elem = _sub(deal_elem, "LOANS")
        loan = _sub(loans_elem, "LOAN")

        # LOAN IDENTIFIERS
        lid = _sub(loan, "LOAN_IDENTIFIERS")
        li = _sub(lid, "LOAN_IDENTIFIER")
        _sub_text(li, "AgencyCaseIdentifier", ids.get("agency_case_number"))
        _sub_text(li, "LenderCaseIdentifier", ids.get("lender_case_number"))

        # AMORTIZATION
        amort_type = _get(tx, "amortization_type", "value")
        if amort_type:
            amort = _sub(loan, "AMORTIZATION")
            ar = _sub(amort, "AMORTIZATION_RULE")
            _sub_text(ar, "AmortizationType", amort_type)

        # LOAN_DETAIL
        ld = _sub(loan, "LOAN_DETAIL")
        _sub_text(ld, "ApplicationReceivedDate", tx.get("application_date"))
        _sub_text(ld, "MortgageType", _get(tx, "mortgage_type", "value"))

        # TERMS_OF_LOAN
        terms = _sub(loan, "TERMS_OF_LOAN")
        _sub_text(terms, "NoteAmount", note.get("principal_amount"))
        _sub_text(terms, "NoteRatePercent", note.get("interest_rate"))
        _sub_text(terms, "LoanMaturityPeriodCount", note.get("loan_term_months"))

        # LOAN_PURPOSE
        loan_purpose = _get(tx, "loan_purpose", "value")
        if loan_purpose:
            lp = _sub(loan, "LOAN_PURPOSE")
            _sub_text(lp, "LoanPurposeType", loan_purpose)

        # CLOSING_INFORMATION
        closing = disc.get("closing_disclosure_h25", {})
        le = disc.get("loan_estimate_h24", {})
        if closing or le:
            ci = _sub(loan, "CLOSING_INFORMATION")
            cid = _sub(ci, "CLOSING_INFORMATION_DETAIL")
            _sub_text(cid, "CashToCloseAmount", closing.get("final_cash_to_close"))
            _sub_text(cid, "ClosingDate", closing.get("disbursement_date"))

    # ================================================================
    #  ADDRESS PARSING HELPERS
    # ================================================================

    def _parse_city_state_zip(self, addr_elem: ET.Element, csz: str):
        """Parse 'Syracuse, NY 13224' into CityName, StateCode, PostalCode."""
        import re
        m = re.match(r"([^,]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)", csz)
        if m:
            _sub_text(addr_elem, "CityName", m.group(1).strip())
            _sub_text(addr_elem, "StateCode", m.group(2))
            _sub_text(addr_elem, "PostalCode", m.group(3))
        else:
            _sub_text(addr_elem, "CityName", csz)

    def _parse_full_address(self, addr_elem: ET.Element, full: str):
        """Parse '748 Thompson Island, Milwaukee, WI 53288'."""
        import re
        m = re.search(r",\s*([^,]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)", full)
        if m:
            _sub_text(addr_elem, "CityName", m.group(1).strip())
            _sub_text(addr_elem, "StateCode", m.group(2))
            _sub_text(addr_elem, "PostalCode", m.group(3))

    # ================================================================
    #  UTILITIES
    # ================================================================

    @staticmethod
    def _count_elements(elem: ET.Element) -> int:
        """Count elements that have text content (data elements)."""
        count = 1 if elem.text and elem.text.strip() else 0
        for child in elem:
            count += MismoEmitter._count_elements(child)
        return count


# ---------------------------------------------------------------------------
# Module-level convenience function
# ---------------------------------------------------------------------------

def emit_mismo_xml(canonical_data: Dict[str, Any]) -> str:
    """One-liner: canonical dict in, MISMO XML string out."""
    emitter = MismoEmitter()
    return emitter.emit(canonical_data)
