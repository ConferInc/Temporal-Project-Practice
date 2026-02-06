from lxml import etree
from domain.loan_snapshot import LoanSnapshot
from mapping import mismo_mapper

def build_mismo_xml(loan: LoanSnapshot) -> bytes:
    """
    Constructs the MISMO XML tree from a LoanSnapshot object.
    Follows structure: MESSAGE -> DEAL_SETS -> DEAL_SET -> DEALS -> DEAL -> LOAN ...
    """
    
    # Namespaces can be added here if needed, keeping it simple for now as requested
    root = etree.Element("MESSAGE")
    
    # --- Header Information (scaled down for simplicity) ---
    # In a real implementation, you'd add AboutVersions, etc.

    deal_sets = etree.SubElement(root, "DEAL_SETS")
    deal_set = etree.SubElement(deal_sets, "DEAL_SET")
    deals = etree.SubElement(deal_set, "DEALS")
    deal = etree.SubElement(deals, "DEAL")

    # --- LOAN Data ---
    loans = etree.SubElement(deal, "LOANS")
    loan_el = etree.SubElement(loans, "LOAN")
    loan_detail = etree.SubElement(loan_el, "LOAN_DETAIL")

    # Map Application Data
    app_data = loan.application
    
    # Loan Purpose
    etree.SubElement(loan_detail, "LoanPurposeType").text = mismo_mapper.map_loan_purpose(app_data.get("loan_purpose"))
    
    # Loan Amount (Example field)
    if "loan_amount" in app_data:
         etree.SubElement(loan_detail, "LoanAmount").text = str(app_data["loan_amount"])

    # --- PROPERTY Data ---
    # Assuming one property for simplicity, but structure allows list
    properties = loan.properties
    if properties:
        prop_data = properties[0] # taking the first one
        property_el = etree.SubElement(loan_el, "PROPERTY")
        
        # Address
        address = etree.SubElement(property_el, "ADDRESS")
        etree.SubElement(address, "AddressLineText").text = prop_data.get("address_line", "")
        etree.SubElement(address, "CityName").text = prop_data.get("city", "")
        etree.SubElement(address, "StateCode").text = mismo_mapper.map_state_code(prop_data.get("state", ""))
        etree.SubElement(address, "PostalCode").text = prop_data.get("zip_code", "")

    # --- PARTIES (Borrowers) ---
    parties = etree.SubElement(deal, "PARTIES")
    
    for borrower in loan.borrowers:
        party = etree.SubElement(parties, "PARTY")
        
        # Role
        roles = etree.SubElement(party, "ROLES")
        role = etree.SubElement(roles, "ROLE")
        etree.SubElement(role, "RoleType").text = "Borrower"
        
        # Individual
        if mismo_mapper.map_borrower_type(borrower.get("type")) == "Individual":
            individual = etree.SubElement(party, "INDIVIDUAL")
            name = etree.SubElement(individual, "NAME")
            # Try to get names, fallback to email parsing or "Unknown"
            first_n = borrower.get("first_name")
            last_n = borrower.get("last_name")
            
            if not first_n and "email" in borrower:
                 # Fallback: Parse email "john.doe@example.com" -> First: John, Last: Doe
                 email_parts = borrower["email"].split("@")[0].split(".")
                 if len(email_parts) > 1:
                     first_n = email_parts[0].capitalize()
                     last_n = email_parts[1].capitalize()
                 else:
                     first_n = email_parts[0].capitalize()
                     last_n = "Unknown"
            
            etree.SubElement(name, "FirstName").text = first_n or "Unknown"
            etree.SubElement(name, "LastName").text = last_n or "Unknown"
            etree.SubElement(name, "SuffixName").text = borrower.get("suffix", "")
        
        # --- ASSETS / LIABILITIES could go here or under LOAN depending on MISMO version ---
        # Keeping it simple as requested

    return etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8"
    )
