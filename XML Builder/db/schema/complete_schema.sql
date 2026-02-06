-- ============================================
-- COMPLETELY CONSOLIDATED SCHEMA
-- ============================================

-- ============================================
-- 1. USERS TABLE (Reference)
-- ============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID,
    email TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    phone_number TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT users_email_unique UNIQUE (email)
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_organization_id ON users(organization_id);

-- ============================================
-- 2. LENDING TABLES (New)
-- ============================================

-- Applications
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID,
    loan_purpose TEXT, 
    loan_amount NUMERIC(15, 2),
    interest_rate NUMERIC(5, 4),
    term_months INTEGER,
    application_date DATE DEFAULT CURRENT_DATE,
    status TEXT DEFAULT 'Draft',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_applications_org ON applications(organization_id);

-- Properties
CREATE TABLE properties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    address_line TEXT,
    unit_number TEXT,
    city TEXT,
    state TEXT, 
    zip_code TEXT,
    property_type TEXT,
    estimated_value NUMERIC(15, 2),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_properties_app ON properties(application_id);

-- Application Borrowers
CREATE TABLE application_borrowers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role TEXT,
    is_primary BOOLEAN DEFAULT false,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(application_id, user_id)
);
CREATE INDEX idx_app_borrowers_app ON application_borrowers(application_id);
CREATE INDEX idx_app_borrowers_user ON application_borrowers(user_id);

-- ============================================
-- 3. VERSIONED ENTITY TABLES (Original)
-- ============================================

-- Incomes
CREATE TABLE incomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    income_type TEXT NOT NULL,
    monthly_amount NUMERIC(12, 2) NOT NULL,
    version_number INTEGER NOT NULL DEFAULT 1,
    is_current BOOLEAN NOT NULL DEFAULT true,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ,
    CONSTRAINT fk_incomes_customer FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX idx_incomes_customer_id ON incomes(customer_id);
CREATE INDEX idx_incomes_is_current ON incomes(is_current) WHERE is_current = true;
CREATE INDEX idx_incomes_logical_identity ON incomes(customer_id, income_type);

-- Employments
CREATE TABLE employments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    employer_name TEXT NOT NULL,
    employment_type TEXT NOT NULL,
    version_number INTEGER NOT NULL DEFAULT 1,
    is_current BOOLEAN NOT NULL DEFAULT true,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ,
    CONSTRAINT fk_employments_customer FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX idx_employments_customer_id ON employments(customer_id);
CREATE INDEX idx_employments_is_current ON employments(is_current) WHERE is_current = true;
CREATE INDEX idx_employments_logical_identity ON employments(customer_id, employer_name);

-- Assets
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    application_id UUID,
    asset_type TEXT NOT NULL,
    asset_value NUMERIC(15, 2) NOT NULL,
    version_number INTEGER NOT NULL DEFAULT 1,
    is_current BOOLEAN NOT NULL DEFAULT true,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ,
    CONSTRAINT fk_assets_customer FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX idx_assets_customer_id ON assets(customer_id);
CREATE INDEX idx_assets_application_id ON assets(application_id);
CREATE INDEX idx_assets_is_current ON assets(is_current) WHERE is_current = true;
CREATE INDEX idx_assets_logical_identity ON assets(customer_id, asset_type);

-- Liabilities
CREATE TABLE liabilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    application_id UUID,
    liability_type TEXT NOT NULL,
    monthly_payment NUMERIC(12, 2) NOT NULL,
    version_number INTEGER NOT NULL DEFAULT 1,
    is_current BOOLEAN NOT NULL DEFAULT true,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ,
    CONSTRAINT fk_liabilities_customer FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX idx_liabilities_customer_id ON liabilities(customer_id);
CREATE INDEX idx_liabilities_application_id ON liabilities(application_id);
CREATE INDEX idx_liabilities_is_current ON liabilities(is_current) WHERE is_current = true;
CREATE INDEX idx_liabilities_logical_identity ON liabilities(customer_id, liability_type);
