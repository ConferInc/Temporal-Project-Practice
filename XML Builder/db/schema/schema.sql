-- ============================================
-- VERSIONED CANONICAL DATA PLATFORM SCHEMA
-- ============================================
-- 
-- This schema implements a temporal, append-only data system
-- for financial and mortgage-related information.
--
-- Core Principles:
-- 1. Users table is a simple reference table (no versioning)
-- 2. Financial entities are fully versioned (incomes, employments, assets, liabilities)
-- 3. Updates create new versions, never overwrite
-- 4. Exactly one row per logical entity has is_current = true
-- ============================================

-- ============================================
-- REFERENCE TABLE (No Versioning)
-- ============================================

-- Users: Simple reference table with persistent UUID
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID,
    email TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure email uniqueness
    CONSTRAINT users_email_unique UNIQUE (email)
);

-- Index for faster lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_organization_id ON users(organization_id);

-- ============================================
-- VERSIONED TABLES
-- ============================================

-- Incomes: User income information over time
CREATE TABLE incomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    income_type TEXT NOT NULL,
    monthly_amount NUMERIC(12, 2) NOT NULL,
    
    -- Versioning columns
    version_number INTEGER NOT NULL DEFAULT 1,
    is_current BOOLEAN NOT NULL DEFAULT true,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ,
    
    -- Foreign key to users
    CONSTRAINT fk_incomes_customer FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for efficient querying
CREATE INDEX idx_incomes_customer_id ON incomes(customer_id);
CREATE INDEX idx_incomes_is_current ON incomes(is_current) WHERE is_current = true;
CREATE INDEX idx_incomes_logical_identity ON incomes(customer_id, income_type);

-- ============================================

-- Employments: Employment details over time
CREATE TABLE employments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    employer_name TEXT NOT NULL,
    employment_type TEXT NOT NULL,
    
    -- Versioning columns
    version_number INTEGER NOT NULL DEFAULT 1,
    is_current BOOLEAN NOT NULL DEFAULT true,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ,
    
    -- Foreign key to users
    CONSTRAINT fk_employments_customer FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for efficient querying
CREATE INDEX idx_employments_customer_id ON employments(customer_id);
CREATE INDEX idx_employments_is_current ON employments(is_current) WHERE is_current = true;
CREATE INDEX idx_employments_logical_identity ON employments(customer_id, employer_name);

-- ============================================

-- Assets: Financial assets over time
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    application_id UUID,
    asset_type TEXT NOT NULL,
    asset_value NUMERIC(15, 2) NOT NULL,
    
    -- Versioning columns
    version_number INTEGER NOT NULL DEFAULT 1,
    is_current BOOLEAN NOT NULL DEFAULT true,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ,
    
    -- Foreign key to users
    CONSTRAINT fk_assets_customer FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for efficient querying
CREATE INDEX idx_assets_customer_id ON assets(customer_id);
CREATE INDEX idx_assets_application_id ON assets(application_id);
CREATE INDEX idx_assets_is_current ON assets(is_current) WHERE is_current = true;
CREATE INDEX idx_assets_logical_identity ON assets(customer_id, asset_type);

-- ============================================

-- Liabilities: Liabilities over time
CREATE TABLE liabilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    application_id UUID,
    liability_type TEXT NOT NULL,
    monthly_payment NUMERIC(12, 2) NOT NULL,
    
    -- Versioning columns
    version_number INTEGER NOT NULL DEFAULT 1,
    is_current BOOLEAN NOT NULL DEFAULT true,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ,
    
    -- Foreign key to users
    CONSTRAINT fk_liabilities_customer FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for efficient querying
CREATE INDEX idx_liabilities_customer_id ON liabilities(customer_id);
CREATE INDEX idx_liabilities_application_id ON liabilities(application_id);
CREATE INDEX idx_liabilities_is_current ON liabilities(is_current) WHERE is_current = true;
CREATE INDEX idx_liabilities_logical_identity ON liabilities(customer_id, liability_type);

-- ============================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================

COMMENT ON TABLE users IS 'Reference table for system users - no versioning';
COMMENT ON TABLE incomes IS 'Versioned income records - preserves all historical versions';
COMMENT ON TABLE employments IS 'Versioned employment records - preserves all historical versions';
COMMENT ON TABLE assets IS 'Versioned asset records - preserves all historical versions';
COMMENT ON TABLE liabilities IS 'Versioned liability records - preserves all historical versions';

COMMENT ON COLUMN incomes.is_current IS 'Exactly one row per (customer_id, income_type) must have is_current = true';
COMMENT ON COLUMN employments.is_current IS 'Exactly one row per (customer_id, employer_name) must have is_current = true';
COMMENT ON COLUMN assets.is_current IS 'Exactly one row per (customer_id, asset_type) must have is_current = true';
COMMENT ON COLUMN liabilities.is_current IS 'Exactly one row per (customer_id, liability_type) must have is_current = true';
