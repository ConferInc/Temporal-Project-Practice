# 🗺️ Canonical Mapping Examples

## Real-World Mapping Scenarios from Your Project

---

## Table of Contents

1. [Bank Statement Mapping](#bank-statement-mapping)
2. [Pay Stub Mapping](#pay-stub-mapping)
3. [URLA Form Mapping](#urla-form-mapping)
4. [Government ID Mapping](#government-id-mapping)
5. [List Pattern Mapping Deep Dive](#list-pattern-mapping-deep-dive)
6. [Priority-Based Mapping Examples](#priority-based-mapping-examples)

---

## Bank Statement Mapping

### Mapping Rules File
**Location**: `resources/canonical_mappings/BankStatement.json`

### Allowed Sections
```python
DOCUMENT_SCOPE["BankStatement"] = {"transaction", "borrower"}
```

### Complete Mapping Rules

```json
[
  {
    "sourceField": "institutionName",
    "targetPath": "transaction.assets[0].institutionName",
    "priority": 1
  },
  {
    "sourceField": "bankName",
    "targetPath": "transaction.assets[0].institutionName",
    "priority": 2
  },
  {
    "sourceField": "currentBalance",
    "targetPath": "transaction.assets[0].currentBalance",
    "priority": 1
  },
  {
    "sourceField": "endingBalanceAmount",
    "targetPath": "transaction.assets[0].currentBalance",
    "priority": 2
  },
  {
    "sourceField": "accountNumberMasked",
    "targetPath": "transaction.assets[0].accountNumberMasked",
    "priority": 1
  },
  {
    "sourceField": "accountNumber",
    "targetPath": "transaction.assets[0].accountNumberMasked",
    "priority": 2
  },
  {
    "sourceField": "firstName",
    "targetPath": "borrower[0].firstName",
    "priority": 1
  },
  {
    "sourceField": "lastName",
    "targetPath": "borrower[0].lastName",
    "priority": 1
  },
  {
    "sourceField": "customerAddress_street",
    "targetPath": "borrower[0].address.street",
    "priority": 1
  },
  {
    "sourceField": "customerAddress_city",
    "targetPath": "borrower[0].address.city",
    "priority": 1
  },
  {
    "sourceField": "customerAddress_zipCode",
    "targetPath": "borrower[0].address.zipCode",
    "priority": 1
  },
  {
    "sourceField": "customerAddress_country",
    "targetPath": "borrower[0].address.country",
    "priority": 1
  },
  {
    "type": "listPattern",
    "targetPath": "transaction.list",
    "sourcePrefix": "deposits",
    "priority": 1,
    "itemMapping": {
      "amount": "amount",
      "date": "date",
      "description": "description"
    }
  },
  {
    "type": "listPattern",
    "targetPath": "transaction.list",
    "sourcePrefix": "withdrawals",
    "priority": 2,
    "itemMapping": {
      "amount": "amount",
      "date": "date",
      "description": "description"
    }
  }
]
```

### Real Example from Your Test Output

**Input File**: `Test_upload_files/BS.pdf`

**Extracted Fields** (from LLM):
```json
{
  "institutionName": "Bank of America, N.A.",
  "accountNumberMasked": "333 4444 5555",
  "customerAddress_street": "STREET 7-43",
  "customerAddress_city": "BOGOTA",
  "customerAddress_zipCode": "111211",
  "customerAddress_country": "COLOMBIA"
}
```

**Canonical Output** (from `output/pipeline_test/04_canonical_output.json`):
```json
{
  "transaction": {
    "assets": [
      {
        "institutionName": "Bank of America, N.A.",
        "accountNumberMasked": "333 4444 5555"
      }
    ]
  },
  "borrower": [
    {
      "address": {
        "street": "STREET 7-43",
        "city": "BOGOTA",
        "zipCode": "111211",
        "country": "COLOMBIA"
      }
    }
  ]
}
```

### Mapping Flow Diagram

```
Extracted Fields                    Mapping Rules                    Canonical Output
─────────────────                   ──────────────                   ─────────────────

institutionName                     priority 1                       transaction.assets[0]
"Bank of America, N.A."      ──────────────────────────────>        .institutionName
                                                                     "Bank of America, N.A."

accountNumberMasked                 priority 1                       transaction.assets[0]
"333 4444 5555"              ──────────────────────────────>        .accountNumberMasked
                                                                     "333 4444 5555"

customerAddress_street              priority 1                       borrower[0].address
"STREET 7-43"                ──────────────────────────────>        .street
                                                                     "STREET 7-43"

customerAddress_city                priority 1                       borrower[0].address
"BOGOTA"                     ──────────────────────────────>        .city
                                                                     "BOGOTA"
```

---

## Pay Stub Mapping

### Mapping Rules File
**Location**: `resources/canonical_mappings/PayStub.json`

### Allowed Sections
```python
DOCUMENT_SCOPE["PayStub"] = {"financials.incomes", "employment"}
```

### Complete Mapping Rules

```json
[
  {
    "sourceField": "employerName",
    "targetPath": "employment[0].employerName",
    "priority": 1
  },
  {
    "sourceField": "employmentType",
    "targetPath": "employment[0].employmentType",
    "priority": 1
  },
  {
    "sourceField": "payBeginDate",
    "targetPath": "employment[0].startDate",
    "priority": 1
  },
  {
    "sourceField": "totalEarningsCurrent",
    "targetPath": "financials.incomes[0].amount",
    "priority": 1
  },
  {
    "sourceField": "totalEarningsYTD",
    "targetPath": "financials.incomes[0].ytdAmount",
    "priority": 1
  },
  {
    "sourceField": "netPayCurrent",
    "targetPath": "financials.incomes[0].netAmount",
    "priority": 1
  },
  {
    "sourceField": "incomeType",
    "targetPath": "financials.incomes[0].incomeType",
    "priority": 1
  }
]
```

### Example Scenario

**Input**: Pay stub from ABC Corporation

**Extracted Fields**:
```json
{
  "employerName": "ABC Corporation",
  "employmentType": "FullTime",
  "payBeginDate": "2024-01-01",
  "totalEarningsCurrent": 5000,
  "totalEarningsYTD": 60000,
  "netPayCurrent": 3800,
  "incomeType": "Base"
}
```

**Canonical Output**:
```json
{
  "employment": [
    {
      "employerName": "ABC Corporation",
      "employmentType": "FullTime",
      "startDate": "2024-01-01"
    }
  ],
  "financials": {
    "incomes": [
      {
        "amount": 5000,
        "incomeType": "Base"
      }
    ]
  }
}
```

**Note**: Only `employment` and `financials` sections are populated. Even though the canonical schema has `loan`, `parties`, `deal`, etc., they are NOT included because PayStub is scoped to only these two sections.

---

## URLA Form Mapping

### Mapping Rules File
**Location**: `resources/canonical_mappings/URLA.json`

### Allowed Sections
```python
DOCUMENT_SCOPE["URLA"] = {
    "deal", "loan", "parties", "employment", 
    "financials", "collateral", "governmentLoans", "closing"
}
```

### Sample Mapping Rules (Partial - 237 total rules)

```json
[
  {
    "sourceField": "applicationDate",
    "targetPath": "deal.applicationDate",
    "priority": 1
  },
  {
    "sourceField": "loanPurpose",
    "targetPath": "deal.loanPurpose",
    "priority": 1
  },
  {
    "sourceField": "loanAmount",
    "targetPath": "loan.loanAmount",
    "priority": 1
  },
  {
    "sourceField": "interestRate",
    "targetPath": "loan.interestRate",
    "priority": 1
  },
  {
    "sourceField": "borrowerFirstName",
    "targetPath": "parties[0].individual.firstName",
    "priority": 1
  },
  {
    "sourceField": "borrowerLastName",
    "targetPath": "parties[0].individual.lastName",
    "priority": 1
  },
  {
    "sourceField": "borrowerSSN",
    "targetPath": "parties[0].taxpayerIdentifier.value",
    "priority": 1
  },
  {
    "sourceField": "borrowerPhone",
    "targetPath": "parties[0].contact.phone",
    "priority": 1
  },
  {
    "sourceField": "employerName",
    "targetPath": "employment[0].employerName",
    "priority": 1
  },
  {
    "sourceField": "baseIncome",
    "targetPath": "financials.incomes[0].amount",
    "priority": 1
  },
  {
    "sourceField": "propertyStreet",
    "targetPath": "collateral.subjectProperty.address.street",
    "priority": 1
  },
  {
    "sourceField": "vaCOENumber",
    "targetPath": "governmentLoans.va.coeNumber",
    "priority": 1
  },
  {
    "sourceField": "closingDate",
    "targetPath": "closing.closingDate",
    "priority": 1
  }
]
```

### Example Scenario

**Input**: URLA Form 1003

**Extracted Fields**:
```json
{
  "applicationDate": "2024-01-15",
  "loanPurpose": "Purchase",
  "loanAmount": 350000,
  "loanTermMonths": 360,
  "interestRate": 6.5,
  "mortgageType": "Conventional",
  "borrowerFirstName": "John",
  "borrowerLastName": "Doe",
  "borrowerSSN": "123-45-6789",
  "borrowerDOB": "1980-01-15",
  "borrowerPhone": "(555) 123-4567",
  "borrowerEmail": "john.doe@email.com",
  "borrowerStreet": "123 Main St",
  "borrowerCity": "San Francisco",
  "borrowerState": "CA",
  "borrowerZipCode": "94102",
  "employerName": "Tech Corp",
  "employmentType": "FullTime",
  "baseIncome": 120000,
  "propertyStreet": "456 Oak Ave",
  "propertyCity": "San Francisco",
  "propertyState": "CA",
  "propertyZipCode": "94103",
  "purchasePrice": 400000,
  "closingDate": "2024-03-01",
  "monthlyPayment": 2200,
  "cashToClose": 80000
}
```

**Canonical Output**:
```json
{
  "deal": {
    "applicationDate": "2024-01-15",
    "loanPurpose": "Purchase"
  },
  "loan": {
    "loanAmount": 350000,
    "loanTermMonths": 360,
    "interestRate": 6.5,
    "loanPurpose": "Purchase",
    "mortgageType": "Conventional"
  },
  "parties": [
    {
      "individual": {
        "firstName": "John",
        "lastName": "Doe",
        "dateOfBirth": "1980-01-15"
      },
      "taxpayerIdentifier": {
        "value": "123-45-6789"
      },
      "contact": {
        "phone": "(555) 123-4567",
        "email": "john.doe@email.com"
      },
      "currentAddress": {
        "street": "123 Main St",
        "city": "San Francisco",
        "state": "CA",
        "zipCode": "94102"
      }
    }
  ],
  "employment": [
    {
      "employerName": "Tech Corp",
      "employmentType": "FullTime"
    }
  ],
  "financials": {
    "incomes": [
      {
        "amount": 120000
      }
    ]
  },
  "collateral": {
    "subjectProperty": {
      "address": {
        "street": "456 Oak Ave",
        "city": "San Francisco",
        "state": "CA",
        "zipCode": "94103"
      },
      "purchasePrice": 400000
    }
  },
  "closing": {
    "closingDate": "2024-03-01",
    "monthlyPayment": 2200,
    "cashToClose": 80000
  }
}
```

**Note**: URLA has access to ALL sections, so it populates `deal`, `loan`, `parties`, `employment`, `financials`, `collateral`, and `closing`.

---

## Government ID Mapping

### Mapping Rules File
**Location**: `resources/canonical_mappings/GovernmentID.json`

### Allowed Sections
```python
DOCUMENT_SCOPE["GovernmentID"] = {"parties"}
```

### Complete Mapping Rules

```json
[
  {
    "sourceField": "firstName",
    "targetPath": "parties[0].individual.firstName",
    "priority": 1
  },
  {
    "sourceField": "lastName",
    "targetPath": "parties[0].individual.lastName",
    "priority": 1
  },
  {
    "sourceField": "dateOfBirth",
    "targetPath": "parties[0].individual.dateOfBirth",
    "priority": 1
  },
  {
    "sourceField": "idNumber",
    "targetPath": "parties[0].taxpayerIdentifier.value",
    "priority": 1
  },
  {
    "sourceField": "street",
    "targetPath": "parties[0].currentAddress.street",
    "priority": 1
  },
  {
    "sourceField": "city",
    "targetPath": "parties[0].currentAddress.city",
    "priority": 1
  },
  {
    "sourceField": "state",
    "targetPath": "parties[0].currentAddress.state",
    "priority": 1
  },
  {
    "sourceField": "zipCode",
    "targetPath": "parties[0].currentAddress.zipCode",
    "priority": 1
  }
]
```

### Example Scenario

**Input**: Driver's License

**Extracted Fields**:
```json
{
  "firstName": "Jane",
  "lastName": "Smith",
  "dateOfBirth": "1985-05-20",
  "idNumber": "D1234567",
  "street": "789 Elm St",
  "city": "Los Angeles",
  "state": "CA",
  "zipCode": "90001"
}
```

**Canonical Output**:
```json
{
  "parties": [
    {
      "individual": {
        "firstName": "Jane",
        "lastName": "Smith",
        "dateOfBirth": "1985-05-20"
      },
      "taxpayerIdentifier": {
        "value": "D1234567"
      },
      "currentAddress": {
        "street": "789 Elm St",
        "city": "Los Angeles",
        "state": "CA",
        "zipCode": "90001"
      }
    }
  ]
}
```

**Note**: Only `parties` section is populated. No `loan`, `deal`, `financials`, etc.

---

## List Pattern Mapping Deep Dive

### The Problem

Bank statements have multiple transactions (deposits, withdrawals). How do we map them?

### The Solution: List Pattern Mapping

#### Extracted Fields Format

```json
{
  "deposits_1_date": "2024-01-15",
  "deposits_1_amount": 5000,
  "deposits_1_description": "Direct Deposit",
  "deposits_2_date": "2024-01-22",
  "deposits_2_amount": 3000,
  "deposits_2_description": "Transfer",
  "withdrawals_1_date": "2024-01-18",
  "withdrawals_1_amount": -200,
  "withdrawals_1_description": "ATM Withdrawal"
}
```

#### Mapping Rule

```json
{
  "type": "listPattern",
  "targetPath": "transaction.list",
  "sourcePrefix": "deposits",
  "priority": 1,
  "itemMapping": {
    "amount": "amount",
    "date": "date",
    "description": "description"
  }
}
```

#### Processing Logic

1. **Find all keys starting with `deposits_`**
   - `deposits_1_date`
   - `deposits_1_amount`
   - `deposits_1_description`
   - `deposits_2_date`
   - `deposits_2_amount`
   - `deposits_2_description`

2. **Parse index and field name**
   - `deposits_1_date` → index: 1, field: date
   - `deposits_1_amount` → index: 1, field: amount
   - `deposits_2_date` → index: 2, field: date

3. **Group by index**
   ```
   Index 1: {date: "2024-01-15", amount: 5000, description: "Direct Deposit"}
   Index 2: {date: "2024-01-22", amount: 3000, description: "Transfer"}
   ```

4. **Create array**
   ```json
   [
     {
       "date": "2024-01-15",
       "amount": 5000,
       "description": "Direct Deposit"
     },
     {
       "date": "2024-01-22",
       "amount": 3000,
       "description": "Transfer"
     }
   ]
   ```

5. **Set to target path**
   ```json
   {
     "transaction": {
       "list": [
         {
           "date": "2024-01-15",
           "amount": 5000,
           "description": "Direct Deposit"
         },
         {
           "date": "2024-01-22",
           "amount": 3000,
           "description": "Transfer"
         }
       ]
     }
   }
   ```

### Multiple List Patterns with Priority

```json
[
  {
    "type": "listPattern",
    "targetPath": "transaction.list",
    "sourcePrefix": "deposits",
    "priority": 1,
    "itemMapping": {...}
  },
  {
    "type": "listPattern",
    "targetPath": "transaction.list",
    "sourcePrefix": "withdrawals",
    "priority": 2,
    "itemMapping": {...}
  }
]
```

**Logic**: Try `deposits` first (priority 1). If found, use it and stop. If not found, try `withdrawals` (priority 2).

---

## Priority-Based Mapping Examples

### Scenario 1: Institution Name Variations

Different banks use different field names in their statements.

#### Mapping Rules
```json
[
  {
    "sourceField": "institutionName",
    "targetPath": "transaction.assets[0].institutionName",
    "priority": 1
  },
  {
    "sourceField": "bankName",
    "targetPath": "transaction.assets[0].institutionName",
    "priority": 2
  }
]
```

#### Case A: Modern Bank Statement
**Extracted Fields**:
```json
{
  "institutionName": "Chase Bank"
}
```

**Mapping Process**:
1. Check `institutionName` (priority 1) → Found ✅
2. Use value: "Chase Bank"
3. Stop (don't check `bankName`)

**Result**:
```json
{
  "transaction": {
    "assets": [{
      "institutionName": "Chase Bank"
    }]
  }
}
```

#### Case B: Legacy Bank Statement
**Extracted Fields**:
```json
{
  "bankName": "Wells Fargo"
}
```

**Mapping Process**:
1. Check `institutionName` (priority 1) → Not found ❌
2. Check `bankName` (priority 2) → Found ✅
3. Use value: "Wells Fargo"

**Result**:
```json
{
  "transaction": {
    "assets": [{
      "institutionName": "Wells Fargo"
    }]
  }
}
```

#### Case C: Both Fields Present
**Extracted Fields**:
```json
{
  "institutionName": "Bank of America",
  "bankName": "BofA"
}
```

**Mapping Process**:
1. Check `institutionName` (priority 1) → Found ✅
2. Use value: "Bank of America"
3. Stop (ignore `bankName` even though it exists)

**Result**:
```json
{
  "transaction": {
    "assets": [{
      "institutionName": "Bank of America"
    }]
  }
}
```

**Key Point**: Priority 1 always wins when both are present.

---

### Scenario 2: Account Balance Variations

#### Mapping Rules
```json
[
  {
    "sourceField": "currentBalance",
    "targetPath": "transaction.assets[0].currentBalance",
    "priority": 1
  },
  {
    "sourceField": "endingBalanceAmount",
    "targetPath": "transaction.assets[0].currentBalance",
    "priority": 2
  }
]
```

#### Case A: Field Name "currentBalance"
**Extracted Fields**:
```json
{
  "currentBalance": 25000
}
```

**Result**:
```json
{
  "transaction": {
    "assets": [{
      "currentBalance": 25000
    }]
  }
}
```

#### Case B: Field Name "endingBalanceAmount"
**Extracted Fields**:
```json
{
  "endingBalanceAmount": 18500
}
```

**Result**:
```json
{
  "transaction": {
    "assets": [{
      "currentBalance": 18500
    }]
  }
}
```

---

## Scoping Enforcement Examples

### Example 1: Bank Statement Trying to Populate Loan Section

**Extracted Fields**:
```json
{
  "institutionName": "Chase",
  "loanAmount": 350000  // ❌ This shouldn't be in a bank statement
}
```

**Mapping Rules**:
```json
[
  {
    "sourceField": "institutionName",
    "targetPath": "transaction.assets[0].institutionName",
    "priority": 1
  },
  {
    "sourceField": "loanAmount",
    "targetPath": "loan.loanAmount",  // ❌ NOT ALLOWED for BankStatement
    "priority": 1
  }
]
```

**Processing**:
1. Map `institutionName` → `transaction.assets[0].institutionName` ✅ (allowed)
2. Check `loan.loanAmount` against allowed sections for BankStatement
3. Allowed sections: `{"transaction", "borrower"}`
4. `loan` is NOT in allowed sections → Skip ⚠️

**Result**:
```json
{
  "transaction": {
    "assets": [{
      "institutionName": "Chase"
    }]
  }
}
```

**Log Output**:
```
⚠️ Path 'loan.loanAmount' not allowed for this document type. Skipping.
```

---

### Example 2: Pay Stub Trying to Populate Collateral Section

**Document Type**: PayStub  
**Allowed Sections**: `{"financials.incomes", "employment"}`

**Extracted Fields**:
```json
{
  "employerName": "ABC Corp",
  "propertyAddress": "123 Main St"  // ❌ Wrong document type
}
```

**Processing**:
1. Map `employerName` → `employment[0].employerName` ✅
2. Check `propertyAddress` → `collateral.propertyAddress`
3. `collateral` NOT in allowed sections → Skip ⚠️

**Result**:
```json
{
  "employment": [{
    "employerName": "ABC Corp"
  }]
}
```

---

## Summary

### Key Takeaways

1. **Document Scoping**: Each document type has a strict scope of allowed sections
2. **Priority Mapping**: Handles field name variations with fallback logic
3. **List Patterns**: Efficiently maps repeating data structures
4. **No Defaults**: If a field isn't in the source, it won't be in the output
5. **Deterministic**: Same input always produces same output (no LLM in mapping)

### Mapping Flow

```
Extracted Fields → Load Mapping Rules → Apply Scoping → Priority Selection → Canonical Output
```

### Files Reference

- **Schema**: `resources/canonical_schema/schema.json`
- **Mapper**: `tools/canonical_mapper.py`
- **Mappings**: `resources/canonical_mappings/*.json`
- **Test Output**: `output/pipeline_test/04_canonical_output.json`

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-03
