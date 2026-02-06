# Versioned Canonical Data Platform

A temporal, append-only financial data system built on Supabase that preserves all historical versions of user financial information.

## 🎯 Core Principles

- **Temporal Data System**: Updates create new versions instead of overwriting
- **Canonical JSON Contract**: Stable JSON format decoupled from database schema
- **Multi-Entity Batch Processing**: Single payload can contain multiple entities
- **Historical Preservation**: All versions are preserved forever

## 📋 Prerequisites

- Python 3.8+
- Supabase account and project
- pip (Python package manager)

## 🚀 Setup Instructions

### 1. Clone or Navigate to Project Directory

```bash
cd c:\Users\Gaurav Kumar Saha\Desktop\Confer\supa-los-storage
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv
venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and add your Supabase credentials:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   SUPABASE_ANON_KEY=your_anon_key
   ```

### 5. Initialize Database Schema

1. Log in to your Supabase dashboard
2. Go to SQL Editor
3. Copy the contents of `db/schema.sql`
4. Execute the SQL to create all tables

### 6. Run the Application

```bash
python main.py
```

The application will start on `http://localhost:8000`

## 🧪 Using the Testing Interface

1. Open your browser and navigate to `http://localhost:8000`
2. You'll see a simple interface with:
   - **JSON Input Area**: Paste your canonical JSON
   - **Quick Examples**: Click to load example payloads
   - **Submit Button**: Send data to the backend
   - **Response Area**: View results and version numbers

### Example Payloads

**Single Entity (Income):**
```json
{
  "income": {
    "customer_id": "123e4567-e89b-12d3-a456-426614174000",
    "income_type": "salary",
    "monthly_amount": 50000
  }
}
```

**Multi-Entity (First-Time Submission):**
```json
{
  "employment": {
    "customer_id": "123e4567-e89b-12d3-a456-426614174000",
    "employer_name": "Google",
    "employment_type": "full_time"
  },
  "income": {
    "customer_id": "123e4567-e89b-12d3-a456-426614174000",
    "income_type": "salary",
    "monthly_amount": 50000
  }
}
```

**Update (Creates New Version):**
```json
{
  "income": {
    "customer_id": "123e4567-e89b-12d3-a456-426614174000",
    "income_type": "salary",
    "monthly_amount": 65000
  }
}
```

## 📁 Project Structure

```
supa-los-storage/
├── db/
│   ├── schema.sql              # Database schema
│   └── supabase_client.py      # Supabase client configuration
├── mappings/
│   └── entity_column_map.py    # Canonical JSON to DB mapping
├── services/
│   ├── versioning_service.py   # Universal versioning logic
│   ├── user_service.py         # User entity (non-versioned)
│   ├── income_service.py       # Income entity (versioned)
│   ├── employment_service.py   # Employment entity (versioned)
│   ├── asset_service.py        # Asset entity (versioned)
│   └── liability_service.py    # Liability entity (versioned)
├── api/
│   ├── routes.py               # FastAPI routes
│   └── handlers.py             # Request handlers
├── ui/
│   ├── index.html              # Testing interface
│   ├── styles.css              # UI styling
│   └── app.js                  # Client-side logic
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
└── .env.example                # Environment variables template
```

## 🔑 Supported Entities

| Entity Key | Table | Versioned | Logical Identity |
|------------|-------|-----------|------------------|
| `user` | `users` | ❌ | `email` |
| `income` | `incomes` | ✅ | `customer_id, income_type` |
| `employment` | `employments` | ✅ | `customer_id, employer_name` |
| `asset` | `assets` | ✅ | `application_id, asset_type` |
| `liability` | `liabilities` | ✅ | `application_id, liability_type` |

## 🔄 How Versioning Works

1. **First Insert**: Creates version 1 with `is_current = true`
2. **Update**: 
   - Finds current version by logical identity
   - Sets `is_current = false` and `valid_to = now()`
   - Inserts new version with incremented `version_number`
3. **Historical Queries**: All versions remain in the database

## 🛠️ API Endpoints

- `POST /api/ingest` - Ingest canonical JSON data
- `GET /api/health` - Health check

## 📊 Querying Data

### Get Current Version
```sql
SELECT * FROM incomes 
WHERE customer_id = '...' 
  AND income_type = 'salary' 
  AND is_current = true;
```

### Get All Versions (History)
```sql
SELECT * FROM incomes 
WHERE customer_id = '...' 
  AND income_type = 'salary'
ORDER BY version_number DESC;
```

## 🎓 Key Concepts

- **Canonical JSON**: The stable contract between UI, backend, and database
- **Mapping Layer**: Decouples JSON keys from database columns
- **Logical Identity**: Fields that uniquely identify an entity across versions
- **Temporal Data**: Every row represents a fact valid during a time window

## 🚨 Important Notes

- **No Hard Deletes**: Data is never deleted, only versioned
- **One Current Version**: Exactly one row per logical entity has `is_current = true`
- **Append-Only**: Updates create new rows, never modify existing ones
- **Users Table**: Not versioned - simple reference table with persistent UUID

## 📝 License

This is a custom implementation for financial data versioning.
