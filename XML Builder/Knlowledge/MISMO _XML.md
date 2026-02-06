# How to Build a MISMO XML File from a Supabase Database

## Purpose

This document explains the **complete, practical process** for generating a MISMO XML file when your loan data is already stored inside a Supabase (PostgreSQL) database.

It focuses on clarity and execution — no unnecessary architecture patterns, no over-engineering, and no confusing theory.

After reading this, an agent or developer should clearly understand:

✅ What MISMO is
✅ Why the database is used
✅ How to fetch the data
✅ How to map it correctly
✅ How to generate XML using Python
✅ What must be validated before sending

---

# 1. What is MISMO?

**MISMO (Mortgage Industry Standards Maintenance Organization)** defines a standard XML format used by lenders to exchange loan data with:

* Automated Underwriting Systems (AUS)
* Investors
* Compliance platforms
* Servicers

Think of MISMO as a **structured export of a loan file.**

👉 It is **not a database**
👉 It is **not a storage format**

It is simply a standardized way to transmit loan data.

---

# 2. Why Generate MISMO from the Database?

Your Supabase database is the **final and trusted version of the loan.**

Even if documents were parsed earlier, the database should always be treated as the **source of truth** because:

* Loan officers may edit data
* Underwriters may adjust income
* Assets or liabilities may change
* Errors may be corrected

If MISMO were generated directly from documents, it could send outdated or incorrect information.

✅ Therefore:

> Always generate MISMO from the database — never directly from parsed documents.

---

# 3. Overall Process

The workflow is straightforward:

```
Supabase Database
        ↓
Fetch Loan Data
        ↓
Organize into One Loan Object
        ↓
Map Database Values to MISMO Tags
        ↓
Generate XML using Python
        ↓
Validate XML
        ↓
Send or Store the File
```

Each step is explained below.

---

# 4. Step One — Fetch the Loan Data

Start by retrieving all information related to a single loan.

Typically this includes:

* Application data
* Borrower details
* Property information
* Income
* Assets
* Liabilities

### Example SQL Queries

```sql
SELECT * FROM applications WHERE id = 'loan_id';

SELECT * FROM borrowers WHERE application_id = 'loan_id';

SELECT * FROM properties WHERE application_id = 'loan_id';
```

Using the Supabase Python client:

```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

application = supabase.table("applications") \
    .select("*") \
    .eq("id", loan_id) \
    .execute()

borrowers = supabase.table("borrowers") \
    .select("*") \
    .eq("application_id", loan_id) \
    .execute()
```

---

# 5. Step Two — Organize Data into One Loan Object

Instead of working with many separate query results, combine everything into a single structure.

### Example:

```python
loan_data = {
    "application": application.data[0],
    "borrowers": borrowers.data,
    "property": property.data[0]
}
```

This makes XML generation much easier because all loan information is now in one place.

---

# 6. Step Three — Map Database Values to MISMO Values

Database values often do NOT exactly match MISMO text.

For example:

| Database Value | MISMO Value      |
| -------------- | ---------------- |
| PURCHASE       | Purchase         |
| REFINANCE      | Refinance        |
| PRIMARY        | PrimaryResidence |

Create small mapping functions to convert them.

### Example:

```python
def map_loan_purpose(value):
    mapping = {
        "PURCHASE": "Purchase",
        "REFINANCE": "Refinance"
    }
    return mapping.get(value)
```

This prevents schema errors later.

---

# 7. Step Four — Generate the MISMO XML Using Python

Install the XML library:

```
pip install lxml
```

### Example Code

```python
from lxml import etree

def build_mismo_xml(loan):

    root = etree.Element("MESSAGE")

    deal_sets = etree.SubElement(root, "DEAL_SETS")
    deal_set = etree.SubElement(deal_sets, "DEAL_SET")
    deals = etree.SubElement(deal_set, "DEALS")
    deal = etree.SubElement(deals, "DEAL")

    loans = etree.SubElement(deal, "LOANS")
    loan_el = etree.SubElement(loans, "LOAN")

    loan_detail = etree.SubElement(loan_el, "LOAN_DETAIL")

    purpose = etree.SubElement(loan_detail, "LoanPurposeType")
    purpose.text = map_loan_purpose(
        loan["application"]["loan_purpose"]
    )

    property_el = etree.SubElement(loan_el, "PROPERTY")
    address = etree.SubElement(property_el, "ADDRESS")

    etree.SubElement(address, "CityName").text = \
        loan["property"]["city"]

    etree.SubElement(address, "StateCode").text = \
        loan["property"]["state"]

    return etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8"
    )
```

---

# 8. Step Five — Validate Before Using the File

Before sending the XML anywhere, confirm that required data exists.

### Example Checks:

✔ At least one borrower is present
✔ Property address is not empty
✔ Loan purpose exists

Example:

```python
if not loan["borrowers"]:
    raise Exception("MISMO generation failed: borrower missing.")
```

Validation prevents downstream rejection.

---

# 9. Step Six — Save the XML File

```python
xml_data = build_mismo_xml(loan_data)

with open("mismo.xml", "wb") as f:
    f.write(xml_data)
```

The file is now ready for transmission or storage.

---

# Example Summary

## Input (Database)

```
applications.loan_purpose = "PURCHASE"
properties.city = "Austin"
properties.state = "TX"
```

## Output (MISMO XML)

```xml
<LoanPurposeType>Purchase</LoanPurposeType>
<CityName>Austin</CityName>
<StateCode>TX</StateCode>
```

The database values were fetched, mapped, and converted into MISMO format.

---

# Key Takeaways

✅ Always generate MISMO from the Supabase database
✅ Gather all loan data first
✅ Convert database values to MISMO-compatible values
✅ Use Python with an XML library like `lxml`
✅ Validate required fields before generating

---

# Final Understanding

The process is simple:

> **Stored Loan Data → Fetch → Map → Build XML**

Once implemented, this becomes a repeatable workflow for every loan.
