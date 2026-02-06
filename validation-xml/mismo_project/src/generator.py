
from lxml import etree
from datetime import datetime

MISMO_NAMESPACE = "http://www.mismo.org/residential/2009/schemas"
XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"

def create_element(tag, text=None, nsmap=None):
    """Helper to create elements with namespace."""
    if nsmap:
         elem = etree.Element(f"{{{MISMO_NAMESPACE}}}{tag}", nsmap=nsmap)
    else:
        elem = etree.Element(f"{{{MISMO_NAMESPACE}}}{tag}")
        
    if text:
        elem.text = str(text)
    return elem

def generate_mismo_xml(canonical: dict) -> str:
    """
    Generates MISMO v3.6 XML from canonical data.
    """
    
    # Define Namespaces
    nsmap = {
        'mismo': MISMO_NAMESPACE,
        'xlink': XLINK_NAMESPACE
    }
    
    # 1. MESSAGE (Root)
    root = etree.Element(f"{{{MISMO_NAMESPACE}}}MESSAGE", nsmap=nsmap)
    
    # 2. ABOUT_VERSIONS (Standard Header)
    # Skipped for brevity, focusing on Payload
    
    # 3. DEAL_SETS -> DEAL_SET -> DEALS -> DEAL
    deal_sets = etree.SubElement(root, f"{{{MISMO_NAMESPACE}}}DEAL_SETS")
    deal_set = etree.SubElement(deal_sets, f"{{{MISMO_NAMESPACE}}}DEAL_SET")
    deals = etree.SubElement(deal_set, f"{{{MISMO_NAMESPACE}}}DEALS")
    deal = etree.SubElement(deals, f"{{{MISMO_NAMESPACE}}}DEAL")
    
    # 4. PARTIES
    # Note: XSD might require LOANS before PARTIES if LOANS is present.
    # If we have no loan data, we skip LOANS (minOccurs=0 usually).
    parties = etree.SubElement(deal, f"{{{MISMO_NAMESPACE}}}PARTIES")
    party = etree.SubElement(parties, f"{{{MISMO_NAMESPACE}}}PARTY")
    
    # INDIVIDUAL
    individual = etree.SubElement(party, f"{{{MISMO_NAMESPACE}}}INDIVIDUAL")
    name = etree.SubElement(individual, f"{{{MISMO_NAMESPACE}}}NAME")
    full_name = canonical.get('borrower', {}).get('full_name', 'Unknown')
    etree.SubElement(name, f"{{{MISMO_NAMESPACE}}}FullName").text = full_name
    
    # ADDRESSES
    addresses = etree.SubElement(party, f"{{{MISMO_NAMESPACE}}}ADDRESSES")
    address = etree.SubElement(addresses, f"{{{MISMO_NAMESPACE}}}ADDRESS")
    addr_data = canonical.get('borrower', {}).get('address', {})
    
    # Address Sequence: Line -> City -> Postal -> State (Alphabeticalish? Check XSD)
    # XSD says: Expected is ( ... StateName, StreetName ... ) after PostalCode.
    # So PostalCode is before StateCode.
    etree.SubElement(address, f"{{{MISMO_NAMESPACE}}}AddressLineText").text = addr_data.get('street')
    etree.SubElement(address, f"{{{MISMO_NAMESPACE}}}CityName").text = addr_data.get('city')
    etree.SubElement(address, f"{{{MISMO_NAMESPACE}}}PostalCode").text = addr_data.get('zip')
    etree.SubElement(address, f"{{{MISMO_NAMESPACE}}}StateCode").text = addr_data.get('state')
    
    # ROLES
    roles = etree.SubElement(party, f"{{{MISMO_NAMESPACE}}}ROLES")
    role = etree.SubElement(roles, f"{{{MISMO_NAMESPACE}}}ROLE")
    
    # Sequence: Choice (BORROWER) -> LICENSES -> IDENTIFIERS -> ROLE_DETAIL
    
    # 1. BORROWER (Choice)
    borrower = etree.SubElement(role, f"{{{MISMO_NAMESPACE}}}BORROWER")
    bor_detail = etree.SubElement(borrower, f"{{{MISMO_NAMESPACE}}}BORROWER_DETAIL")
    
    # Income (CURRENT_INCOME -> CURRENT_INCOME_ITEMS -> ITEM -> DETAIL)
    income_data = canonical.get('income', {})
    if income_data:
        current_income = etree.SubElement(borrower, f"{{{MISMO_NAMESPACE}}}CURRENT_INCOME")
        income_items = etree.SubElement(current_income, f"{{{MISMO_NAMESPACE}}}CURRENT_INCOME_ITEMS")
        pay_item = etree.SubElement(income_items, f"{{{MISMO_NAMESPACE}}}CURRENT_INCOME_ITEM")
        
        # Detail Container
        pay_detail = etree.SubElement(pay_item, f"{{{MISMO_NAMESPACE}}}CURRENT_INCOME_ITEM_DETAIL")
        
        earnings = income_data.get('earnings', {})
        amt = earnings.get('current_gross_pay')
        if amt:
             etree.SubElement(pay_detail, f"{{{MISMO_NAMESPACE}}}CurrentIncomeMonthlyTotalAmount").text = str(amt)

        etree.SubElement(pay_detail, f"{{{MISMO_NAMESPACE}}}IncomeType").text = "Base"

    # Employment (EMPLOYERS -> EMPLOYER)
    emp_data = canonical.get('borrower', {}).get('employment', {})
    if emp_data:
        employers = etree.SubElement(borrower, f"{{{MISMO_NAMESPACE}}}EMPLOYERS")
        employer = etree.SubElement(employers, f"{{{MISMO_NAMESPACE}}}EMPLOYER")
        
        # Employer Name -> LegalEntity -> LegalEntityDetail -> FullName (as per error suggestion)
        legal_entity = etree.SubElement(employer, f"{{{MISMO_NAMESPACE}}}LEGAL_ENTITY")
        le_detail = etree.SubElement(legal_entity, f"{{{MISMO_NAMESPACE}}}LEGAL_ENTITY_DETAIL")
        etree.SubElement(le_detail, f"{{{MISMO_NAMESPACE}}}FullName").text = emp_data.get('employer_name')
        
        # Employment Info
        billing_emp = etree.SubElement(employer, f"{{{MISMO_NAMESPACE}}}EMPLOYMENT")
        etree.SubElement(billing_emp, f"{{{MISMO_NAMESPACE}}}EmploymentPositionDescription").text = emp_data.get('job_title')

    # 4. ROLE_DETAIL
    role_detail = etree.SubElement(role, f"{{{MISMO_NAMESPACE}}}ROLE_DETAIL")
    etree.SubElement(role_detail, f"{{{MISMO_NAMESPACE}}}PartyRoleType").text = "Borrower"

    # Generate String
    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8").decode('utf-8')


    # Generate String
    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8").decode('utf-8')

if __name__ == "__main__":
    # Test stub
    pass

