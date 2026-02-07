# MISMO 3.6 XML Generator

A production-ready Python application that generates **MISMO 3.6 compliant XML** from a canonical PostgreSQL database for mortgage loan applications.

## Features

✅ **MISMO 3.6 Compliant** - Generates fully compliant MISMO 3.6 Residential Reference Model XML
✅ **Modular Architecture** - 7 table-specific mappers for maintainability
✅ **JSONB Support** - Handles complex address fields stored as JSONB
✅ **Junction Tables** - Supports ownership tracking for assets and liabilities
✅ **Role-Based** - Handles Borrower, CoBorrower, and other party roles
✅ **Comprehensive Validation** - Validates data before XML generation

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database (Supabase)
- Active Supabase project

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd "XML Builder"

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Supabase credentials
```

### Configuration

Create a `.env` file:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### Usage

```bash
# Generate MISMO XML for a loan application
python main.py <APPLICATION_UUID>

# Custom output path
python main.py <APPLICATION_UUID> --output custom/path.xml

# List available applications
python list_applications.py
```

### Example

```bash
python main.py fdd8dfa2-fbc6-468b-997c-d763c1c1ee0e
# Output: output/fdd8dfa2-fbc6-468b-997c-d763c1c1ee0e_mismo.xml
```

## Project Structure

```
XML Builder/
├── db/
│   ├── supabase_client.py      # Database connection
│   └── fetchers.py              # Data retrieval functions
├── domain/
│   └── loan_snapshot.py         # Domain model
├── mapping/
│   ├── enums.py                 # MISMO enumeration constants
│   ├── application_mapper.py    # Loan-level mappings
│   ├── customer_mapper.py       # Borrower mappings
│   ├── property_mapper.py       # Property mappings
│   ├── employment_mapper.py     # Employment mappings
│   ├── income_mapper.py         # Income mappings
│   ├── asset_mapper.py          # Asset mappings
│   └── liability_mapper.py      # Liability mappings
├── xml_gen/
│   └── xml_builder.py           # MISMO 3.6 XML builder
├── validation/
│   └── loan_validator.py        # Data validation
├── output/                      # Generated XML files
├── main.py                      # Main entry point
└── requirements.txt             # Python dependencies
```

## Database Schema

### Core Tables

- `applications` - Loan application master records
- `customers` - Borrower/co-borrower information
- `application_customers` - Links customers to applications with roles
- `properties` - Subject property details (JSONB addresses)
- `employments` - Employment history
- `incomes` - Income sources
- `assets` - Borrower assets
- `asset_ownership` - Asset ownership tracking
- `liabilities` - Borrower debts
- `liability_ownership` - Liability ownership tracking

See `Knlowledge/Schema/schema.sql` for complete schema.

## MISMO 3.6 Compliance

This generator produces XML that conforms to the **MISMO 3.6 Residential Reference Model**:

- ✅ Proper hierarchy: `MESSAGE → DEAL_SETS → DEAL_SET → DEALS → DEAL`
- ✅ Property under `COLLATERALS/COLLATERAL/SUBJECT_PROPERTY`
- ✅ Borrower addresses under `RESIDENCES/RESIDENCE/ADDRESS`
- ✅ Employment under `EMPLOYERS/EMPLOYER/EMPLOYMENT`
- ✅ Incomes, Assets, Liabilities under `PARTY` (per borrower)
- ✅ All required fields included
- ✅ Correct MISMO element names and enumerations

See `MISMO_3.6_End_to_End_Process.md` for complete documentation.

## Mapping Documentation

The canonical database → MISMO 3.6 mapping is documented in:

- `Knlowledge/MISMO Mapping/Mismo_v3.6_mapping.md`

## Example Output

```xml
<MESSAGE>
  <DEAL_SETS>
    <DEAL_SET>
      <DEALS>
        <DEAL DealIdentifier="...">
          <LOANS>
            <LOAN>
              <LoanAmount>340000.0</LoanAmount>
              <OccupancyType>PrimaryResidence</OccupancyType>
            </LOAN>
          </LOANS>
          <COLLATERALS>
            <COLLATERAL>
              <SUBJECT_PROPERTY>
                <ADDRESS>...</ADDRESS>
              </SUBJECT_PROPERTY>
            </COLLATERAL>
          </COLLATERALS>
          <PARTIES>
            <PARTY>
              <ROLES>...</ROLES>
              <INDIVIDUAL>...</INDIVIDUAL>
              <RESIDENCES>...</RESIDENCES>
              <EMPLOYERS>...</EMPLOYERS>
              <INCOMES>...</INCOMES>
              <ASSETS>...</ASSETS>
              <LIABILITIES>...</LIABILITIES>
            </PARTY>
          </PARTIES>
        </DEAL>
      </DEALS>
    </DEAL_SET>
  </DEAL_SETS>
</MESSAGE>
```

- NOTE: The output is based on what fields are actually availabe in the current database

## Dependencies

- `supabase` - Database client
- `lxml` - XML generation
- `python-dotenv` - Environment configuration

See `requirements.txt` for complete list.

## License

[Your License Here]

## Support

For issues or questions, please [open an issue](your-repo-url/issues).

---

**Built with ❤️ for the mortgage industry**
