"""
MISMO 3.6 Compliant XML Builder
Constructs MISMO 3.6 XML from LoanSnapshot using modular mappers
Follows MISMO 3.6 Residential Reference Model structure exactly
"""
from lxml import etree
from domain.loan_snapshot import LoanSnapshot
from mapping import (
    application_mapper,
    customer_mapper,
    property_mapper,
    employment_mapper,
    income_mapper,
    asset_mapper,
    liability_mapper
)


def build_mismo_xml(loan: LoanSnapshot) -> bytes:
    """
    Constructs MISMO 3.6 compliant XML tree from a LoanSnapshot object
    Structure follows MISMO 3.6 specification exactly
    """
    
    root = etree.Element("MESSAGE")
    
    deal_sets = etree.SubElement(root, "DEAL_SETS")
    deal_set = etree.SubElement(deal_sets, "DEAL_SET")
    deals = etree.SubElement(deal_set, "DEALS")
    deal = etree.SubElement(deals, "DEAL")
    
    # Add Deal Identifier
    app = loan.application
    if app.get("id"):
        deal.set("DealIdentifier", str(app["id"]))

    # --- LOANS Section ---
    loans = etree.SubElement(deal, "LOANS")
    loan_el = etree.SubElement(loans, "LOAN")
    
    # Loan Amount (direct child of LOAN per MISMO 3.6)
    etree.SubElement(loan_el, "LoanAmount").text = \
        application_mapper.extract_loan_amount(app)
    
    # Occupancy Type
    if app.get("occupancy_type"):
        etree.SubElement(loan_el, "OccupancyType").text = \
            application_mapper.map_occupancy_type(app.get("occupancy_type"))
    
    # Loan Application Identifier
    if app.get("application_number"):
        etree.SubElement(deal, "LoanApplicationIdentifier").text = app["application_number"]
    
    # Loan Application Date
    if app.get("submitted_at"):
        etree.SubElement(deal, "LoanApplicationDate").text = str(app["submitted_at"])

    # --- COLLATERALS Section (Property as SUBJECT_PROPERTY) ---
    if loan.property:
        prop_details = property_mapper.extract_property_details(loan.property)
        
        collaterals = etree.SubElement(deal, "COLLATERALS")
        collateral = etree.SubElement(collaterals, "COLLATERAL")
        
        # Collateral ID
        if loan.property.get("id"):
            collateral.set("CollateralID", str(loan.property["id"]))
        
        subject_property = etree.SubElement(collateral, "SUBJECT_PROPERTY")
        
        # Address
        address = etree.SubElement(subject_property, "ADDRESS")
        addr = prop_details["address"]
        etree.SubElement(address, "AddressLineText").text = addr["street"]
        if addr["unit"]:
            etree.SubElement(address, "AddressUnitIdentifier").text = addr["unit"]
        etree.SubElement(address, "CityName").text = addr["city"]
        etree.SubElement(address, "StateCode").text = property_mapper.format_state_code(addr["state"])
        etree.SubElement(address, "PostalCode").text = addr["zip"]
        if addr["country"]:
            etree.SubElement(address, "CountryCode").text = addr["country"]
        
        # Property Details
        if prop_details["property_type"]:
            etree.SubElement(subject_property, "PropertyType").text = prop_details["property_type"]
        if prop_details["year_built"]:
            etree.SubElement(subject_property, "PropertyYearBuilt").text = str(prop_details["year_built"])
        if prop_details["appraised_value"]:
            etree.SubElement(subject_property, "PropertyEstimatedValueAmount").text = \
                str(prop_details["appraised_value"])

    # --- PARTIES Section ---
    parties = etree.SubElement(deal, "PARTIES")
    
    for customer in loan.customers:
        party = etree.SubElement(parties, "PARTY")
        
        # Party ID
        if customer.get("id"):
            party.set("PartyID", str(customer["id"]))
        
        # ROLES
        roles = etree.SubElement(party, "ROLES")
        role = etree.SubElement(roles, "ROLE")
        role_detail = etree.SubElement(role, "ROLE_DETAIL")
        etree.SubElement(role_detail, "BorrowerRoleType").text = \
            customer_mapper.map_borrower_role(customer.get("role"))
        
        # Customer Type
        customer_type = customer_mapper.map_customer_type(customer.get("customer_type"))
        
        if customer_type == "Individual":
            individual = etree.SubElement(party, "INDIVIDUAL")
            
            # NAME
            name_el = etree.SubElement(individual, "NAME")
            name_parts = customer_mapper.parse_customer_name(customer)
            etree.SubElement(name_el, "FirstName").text = name_parts["first_name"] or "Unknown"
            if name_parts["middle_name"]:
                etree.SubElement(name_el, "MiddleName").text = name_parts["middle_name"]
            etree.SubElement(name_el, "LastName").text = name_parts["last_name"] or "Unknown"
            if name_parts["suffix"]:
                etree.SubElement(name_el, "SuffixName").text = name_parts["suffix"]
            
            # Birth Date
            if customer.get("date_of_birth"):
                etree.SubElement(individual, "BirthDate").text = str(customer["date_of_birth"])
            
            # SSN (Government Identifiers)
            if customer.get("ssn_encrypted"):
                gov_ids = etree.SubElement(individual, "GOVERNMENT_IDENTIFIERS")
                gov_id = etree.SubElement(gov_ids, "GOVERNMENT_IDENTIFIER")
                etree.SubElement(gov_id, "GovernmentIdentifierValue").text = customer["ssn_encrypted"]
            
            # Marital Status
            if customer.get("marital_status"):
                etree.SubElement(individual, "MaritalStatusType").text = \
                    customer_mapper.map_marital_status(customer["marital_status"])
            
            # Dependent Count
            if customer.get("dependent_count") is not None:
                etree.SubElement(individual, "DependentCount").text = str(customer["dependent_count"])
            
            # RESIDENCES (not ADDRESSES per MISMO 3.6)
            current_addr = customer_mapper.get_current_address(customer)
            if current_addr:
                residences = etree.SubElement(party, "RESIDENCES")
                residence = etree.SubElement(residences, "RESIDENCE")
                address_el = etree.SubElement(residence, "ADDRESS")
                etree.SubElement(address_el, "AddressLineText").text = \
                    current_addr.get("street") or current_addr.get("address_line") or ""
                etree.SubElement(address_el, "CityName").text = current_addr.get("city") or ""
                etree.SubElement(address_el, "StateCode").text = \
                    property_mapper.format_state_code(current_addr.get("state") or "")
                etree.SubElement(address_el, "PostalCode").text = \
                    current_addr.get("zip") or current_addr.get("zip_code") or ""
                if current_addr.get("country"):
                    etree.SubElement(address_el, "CountryCode").text = current_addr["country"]
        
        elif customer_type == "Company":
            legal_entity = etree.SubElement(party, "LEGAL_ENTITY")
            name_parts = customer_mapper.parse_customer_name(customer)
            etree.SubElement(legal_entity, "FullName").text = \
                name_parts["company_name"] or "Unknown Company"
        
        # EMPLOYERS (per MISMO 3.6 structure)
        if customer.get("employments"):
            employers = etree.SubElement(party, "EMPLOYERS")
            for employment in customer["employments"]:
                emp_details = employment_mapper.extract_employment_details(employment)
                
                employer = etree.SubElement(employers, "EMPLOYER")
                if employment.get("id"):
                    employer.set("EmployerID", str(employment["id"]))
                
                etree.SubElement(employer, "EmployerName").text = emp_details["employer_name"]
                
                # EMPLOYMENT nested under EMPLOYER
                employment_el = etree.SubElement(employer, "EMPLOYMENT")
                etree.SubElement(employment_el, "EmploymentCurrentIndicator").text = \
                    "true" if emp_details["is_current"] else "false"
                
                if emp_details["start_date"]:
                    etree.SubElement(employment_el, "EmploymentStartDate").text = \
                        str(emp_details["start_date"])
                
                if emp_details["end_date"]:
                    etree.SubElement(employment_el, "EmploymentEndDate").text = \
                        str(emp_details["end_date"])
                
                if emp_details["position_title"]:
                    etree.SubElement(employment_el, "EmploymentPositionDescription").text = \
                        emp_details["position_title"]
                
                etree.SubElement(employment_el, "EmploymentBorrowerSelfEmployedIndicator").text = \
                    "true" if emp_details["is_self_employed"] else "false"
        
        # INCOMES (under PARTY per MISMO 3.6)
        if customer.get("incomes"):
            incomes = etree.SubElement(party, "INCOMES")
            for income in customer["incomes"]:
                inc_details = income_mapper.extract_income_details(income)
                
                income_el = etree.SubElement(incomes, "INCOME")
                etree.SubElement(income_el, "IncomeType").text = inc_details["income_type"]
                etree.SubElement(income_el, "IncomeAmount").text = inc_details["monthly_amount"]
                etree.SubElement(income_el, "IncomeIncludedInQualificationIndicator").text = \
                    "true" if inc_details["include_in_qualification"] else "false"
        
        # ASSETS (under PARTY per MISMO 3.6)
        # Filter assets for this customer via asset_ownership
        customer_assets = [
            asset for asset in loan.assets
            if any(
                owner.get("customer_id") == customer.get("id")
                for owner in asset.get("asset_ownership", [])
            )
        ]
        
        if customer_assets:
            assets = etree.SubElement(party, "ASSETS")
            for asset in customer_assets:
                asset_details = asset_mapper.extract_asset_details(asset)
                
                asset_el = etree.SubElement(assets, "ASSET")
                etree.SubElement(asset_el, "AssetType").text = asset_details["asset_type"]
                etree.SubElement(asset_el, "AssetCashOrMarketValueAmount").text = \
                    asset_details["cash_or_market_value"]
                
                if asset_details["institution_name"]:
                    etree.SubElement(asset_el, "AssetHolderName").text = \
                        asset_details["institution_name"]
                
                etree.SubElement(asset_el, "AssetGiftIndicator").text = \
                    "true" if asset_details["is_gift_or_grant"] else "false"
        
        # LIABILITIES (under PARTY per MISMO 3.6)
        # Filter liabilities for this customer via liability_ownership
        customer_liabilities = [
            liab for liab in loan.liabilities
            if any(
                owner.get("customer_id") == customer.get("id")
                for owner in liab.get("liability_ownership", [])
            )
        ]
        
        if customer_liabilities:
            liabilities = etree.SubElement(party, "LIABILITIES")
            for liability in customer_liabilities:
                liab_details = liability_mapper.extract_liability_details(liability)
                
                liab_el = etree.SubElement(liabilities, "LIABILITY")
                etree.SubElement(liab_el, "LiabilityType").text = liab_details["liability_type"]
                
                if liab_details["creditor_name"]:
                    etree.SubElement(liab_el, "LiabilityHolderName").text = \
                        liab_details["creditor_name"]
                
                if liab_details["account_number"]:
                    etree.SubElement(liab_el, "LiabilityAccountIdentifier").text = \
                        liab_details["account_number"]
                
                etree.SubElement(liab_el, "LiabilityMonthlyPaymentAmount").text = \
                    liab_details["monthly_payment"]
                etree.SubElement(liab_el, "LiabilityUnpaidBalanceAmount").text = \
                    liab_details["unpaid_balance"]
                etree.SubElement(liab_el, "LiabilityExcludedFromDTIIndicator").text = \
                    "true" if liab_details["exclude_from_dti"] else "false"

    return etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8"
    )
