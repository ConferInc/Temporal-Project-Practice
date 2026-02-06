# 🔄 Canonical Model Change Log (v3.0.0)

**Date:** 2026-02-03  
**Architecture:** MISMO Reference Model v3.x Alignment  
**Status:** Implemented

---

## 🚀 Major Refactoring Summary

This update shifts the canonical model from a **Document-Centric** view (organizing data by where it came from) to a **Logical Data View** (organizing data by what it IS). This aligns with the MISMO standard used by LOS and servicing platforms.

### 1. Structure Changes

| Old Structure (v2) | New Structure (v3) | Reason for Change |
|-------------------|-------------------|-------------------|
| `transaction` (top-level) | Removed / Merged into `assets` | Transactions are evidence; balances are Assets. Aligns with MISMO Asset container. |
| `borrower` (top-level) | `parties` (Role="Borrower") | "Borrower" is a ROLE, not an entity. Creates consistent handling for Co-borrowers and Non-borrowing spouses. |
| `transaction.list` | *Removed from canonical* | Granular transaction history is evidence, not a loan fact. Stored in raw extraction if needed. |
| `financials` (grouped) | Split: `assets`, `liabilities`, `income` | Flattened structure matches MISMO logical containers better than arbitrary grouping. |
| `loan.mortgageType` | `loans[0].mortgageType` | Loan data is array-based to support simultaneous 1st/2nd liens (piggyback loans). |

---

## 2. Responsibility Matrix

Which document types are allowed to populate which canonical sections:

| Document Type | Allowed Canonical Sections (v3) |
|--------------|--------------------------------|
| **Bank Statement** | `assets` (balance), `parties` (basic info) |
| **Pay Stub** | `employment`, `income` |
| **URLA (1003)** | `deal`, `loans`, `parties`, `employment`, `income`, `assets`, `liabilities`, `collateral`, `closing`, `governmentLoan` |
| **Government ID** | `parties` (identity data) |
| **W-2 Form** | `income`, `employment` |
| **Tax Return** | `income` |
| **Sales Contract** | `collateral` (sales price, address) |
| **Closing Disclosure** | `closing`, `loans` |

---

## 3. Canonical → MISMO Concept Map

Mapping internal canonical paths to standard MISMO logical containers:

| Canonical Path | MISMO Logical Concept |
|--------------|----------------------|
| `deal` | `MESSAGE/DEAL_SETS/DEAL_SET/DEALS/DEAL` |
| `parties[]` | `.../DEAL/PARTIES/PARTY` |
| `parties[].individual` | `.../PARTY/INDIVIDUAL` |
| `roles` | `.../PARTY/ROLES/ROLE/ROLE_DETAIL/PartyRoleType` |
| `loans[]` | `.../DEAL/LOANS/LOAN` |
| `collateral[]` | `.../DEAL/COLLATERALS/COLLATERAL/SUBJECT_PROPERTY` |
| `assets[]` | `.../DEAL/ASSETS/ASSET` |
| `liabilities[]` | `.../DEAL/LIABILITIES/LIABILITY` |
| `employment[]` | `.../PARTY/EMPLOYMENT/EMPLOYMENT` |
| `income[]` | `.../DEAL/INCOME_INFORMATION` (Linked to Party) |
| `governmentLoan` | `.../LOAN/GOVERNMENT_LOAN` |

---

## 4. Key Fixes & Improvements

*   **No "Borrower" Object**: Eliminated the ambiguity between the `borrower` object and the `parties` array. Now standardized on `parties`.
*   **Asset Standardization**: Bank Statements now populate the `assets` array directly, normalizing field names like `financialInstitutionName` instead of `institutionName`.
*   **Income/Employment Split**: Income extracted from PayStubs is now clearly separated from Employment history metadata, allowing for multiple income streams per employer.
*   **Scope Enforcement**: The scope definition in the code must be updated to match these new keys.

---
