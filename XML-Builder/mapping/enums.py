"""
MISMO XML Enumeration Constants
Comprehensive mapping of database values to MISMO-compliant values
"""

# Loan Purpose Types
LOAN_PURPOSE = {
    "PURCHASE": "Purchase",
    "REFINANCE": "Refinance",
    "CASHOUT_REFINANCE": "CashOutRefinance",
    "CONSTRUCTION": "Construction",
    "CONSTRUCTION_TO_PERMANENT": "ConstructionToPermanent",
    "OTHER": "Other"
}

# Occupancy Types
OCCUPANCY_TYPE = {
    "PRIMARY": "PrimaryResidence",
    "SECONDARY": "SecondHome",
    "INVESTMENT": "Investment",
    "SECOND_HOME": "SecondHome"
}

# Property Types
PROPERTY_TYPE = {
    "SINGLE_FAMILY": "SingleFamily",
    "CONDO": "Condominium",
    "TOWNHOUSE": "Townhouse",
    "COOPERATIVE": "Cooperative",
    "MANUFACTURED_HOME": "ManufacturedHome",
    "MULTI_FAMILY": "MultiFamilyDwelling",
    "PUD": "PUD",
    "COMMERCIAL": "Commercial",
    "MIXED_USE": "MixedUse"
}

# Customer/Borrower Types
CUSTOMER_TYPE = {
    "INDIVIDUAL": "Individual",
    "COMPANY": "Company",
    "TRUST": "Trust",
    "ESTATE": "Estate"
}

# Borrower Roles
BORROWER_ROLE = {
    "BORROWER": "Borrower",
    "CO_BORROWER": "CoBorrower",
    "COBORROWER": "CoBorrower",
    "NON_OCCUPANT_COBORROWER": "NonOccupantCoBorrower"
}

# Marital Status
MARITAL_STATUS = {
    "MARRIED": "Married",
    "UNMARRIED": "Unmarried",
    "SEPARATED": "Separated",
    "CIVIL_UNION": "CivilUnion",
    "DOMESTIC_PARTNERSHIP": "DomesticPartnership",
    "REGISTERED_RECIPROCAL_BENEFICIARY": "RegisteredReciprocalBeneficiaryRelationship"
}

# Citizenship Types
CITIZENSHIP_TYPE = {
    "US_CITIZEN": "USCitizen",
    "PERMANENT_RESIDENT": "PermanentResidentAlien",
    "NON_PERMANENT_RESIDENT": "NonPermanentResidentAlien",
    "FOREIGN_NATIONAL": "ForeignNational"
}

# Employment Types
EMPLOYMENT_TYPE = {
    "EMPLOYED": "Employed",
    "SELF_EMPLOYED": "SelfEmployed",
    "RETIRED": "Retired",
    "UNEMPLOYED": "Unemployed",
    "NOT_EMPLOYED": "NotEmployed",
    "MILITARY": "Military"
}

# Income Types
INCOME_TYPE = {
    "BASE": "Base",
    "OVERTIME": "Overtime",
    "BONUS": "Bonus",
    "COMMISSION": "Commission",
    "MILITARY": "MilitaryBasePay",
    "MILITARY_ALLOWANCE": "MilitaryAllowance",
    "PENSION": "Pension",
    "SOCIAL_SECURITY": "SocialSecurity",
    "DISABILITY": "Disability",
    "UNEMPLOYMENT": "Unemployment",
    "RENTAL": "RentalIncome",
    "INTEREST_DIVIDENDS": "InterestAndDividends",
    "TRUST": "TrustIncome",
    "ALIMONY": "Alimony",
    "CHILD_SUPPORT": "ChildSupport",
    "OTHER": "Other"
}

# Income Sources
INCOME_SOURCE = {
    "EMPLOYMENT": "Employment",
    "SELF_EMPLOYMENT": "SelfEmployment",
    "INVESTMENT": "Investment",
    "RETIREMENT": "Retirement",
    "GOVERNMENT": "Government",
    "OTHER": "Other"
}

# Asset Types
ASSET_TYPE = {
    "CHECKING": "CheckingAccount",
    "SAVINGS": "SavingsAccount",
    "MONEY_MARKET": "MoneyMarketFund",
    "CERTIFICATE_OF_DEPOSIT": "CertificateOfDeposit",
    "MUTUAL_FUND": "MutualFund",
    "STOCKS": "Stock",
    "BONDS": "Bond",
    "RETIREMENT_401K": "RetirementFund",
    "IRA": "IRA",
    "BRIDGE_LOAN": "BridgeLoanNotDeposited",
    "GIFT": "EarnestMoneyCashDepositTowardPurchase",
    "PROCEEDS_FROM_SALE": "ProceedsFromSaleOfNonRealEstateAsset",
    "PROCEEDS_FROM_REAL_ESTATE": "ProceedsFromRealEstatePropertyToBeSOld",
    "CASH_ON_HAND": "CashOnHand",
    "OTHER": "OtherAsset"
}

# Asset Categories
ASSET_CATEGORY = {
    "LIQUID": "Liquid",
    "NON_LIQUID": "NonLiquid",
    "RETIREMENT": "Retirement"
}

# Gift Types
GIFT_TYPE = {
    "CASH_GIFT": "CashGift",
    "EQUITY": "Equity",
    "GRANT": "Grant",
    "GIFT_OF_EQUITY": "GiftOfEquity"
}

# Liability Types
LIABILITY_TYPE = {
    "REVOLVING": "Revolving",
    "INSTALLMENT": "Installment",
    "MORTGAGE": "MortgageLoan",
    "OPEN_30_DAY": "Open30DayChargeAccount",
    "COLLECTIONS": "CollectionsJudgmentsAndLiens",
    "TAXES": "Taxes",
    "CHILD_SUPPORT": "ChildSupport",
    "ALIMONY": "Alimony",
    "OTHER": "Other"
}

# US State Codes (2-letter)
STATE_CODES = {
    "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR",
    "CALIFORNIA": "CA", "COLORADO": "CO", "CONNECTICUT": "CT", "DELAWARE": "DE",
    "FLORIDA": "FL", "GEORGIA": "GA", "HAWAII": "HI", "IDAHO": "ID",
    "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA", "KANSAS": "KS",
    "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME", "MARYLAND": "MD",
    "MASSACHUSETTS": "MA", "MICHIGAN": "MI", "MINNESOTA": "MN", "MISSISSIPPI": "MS",
    "MISSOURI": "MO", "MONTANA": "MT", "NEBRASKA": "NE", "NEVADA": "NV",
    "NEW_HAMPSHIRE": "NH", "NEW_JERSEY": "NJ", "NEW_MEXICO": "NM", "NEW_YORK": "NY",
    "NORTH_CAROLINA": "NC", "NORTH_DAKOTA": "ND", "OHIO": "OH", "OKLAHOMA": "OK",
    "OREGON": "OR", "PENNSYLVANIA": "PA", "RHODE_ISLAND": "RI", "SOUTH_CAROLINA": "SC",
    "SOUTH_DAKOTA": "SD", "TENNESSEE": "TN", "TEXAS": "TX", "UTAH": "UT",
    "VERMONT": "VT", "VIRGINIA": "VA", "WASHINGTON": "WA", "WEST_VIRGINIA": "WV",
    "WISCONSIN": "WI", "WYOMING": "WY", "DISTRICT_OF_COLUMBIA": "DC"
}
