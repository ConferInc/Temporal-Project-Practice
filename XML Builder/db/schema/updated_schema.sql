-- ============================================
-- UPDATED SCHEMA: ADDING LENDING TABLES
-- ============================================

-- 1. Applications Table
-- Stores the main loan application data
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID, -- Links to the lender/org
    loan_purpose TEXT, -- Purchase, Refinance, etc.
    loan_amount NUMERIC(15, 2),
    interest_rate NUMERIC(5, 4),
    term_months INTEGER,
    application_date DATE DEFAULT CURRENT_DATE,
    status TEXT DEFAULT 'Draft', -- Draft, Submitted, Processing, etc.
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_applications_org ON applications(organization_id);

-- 2. Properties Table
-- Stores property information linked to an application
CREATE TABLE properties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    address_line TEXT,
    unit_number TEXT,
    city TEXT,
    state TEXT, -- 2-letter code
    zip_code TEXT,
    property_type TEXT, -- SingleFamily, Condo, etc.
    estimated_value NUMERIC(15, 2),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_properties_app ON properties(application_id);

-- 3. App_Borrowers (Junction Table)
-- Links Users (Borrowers) to Applications with a specific role
CREATE TABLE application_borrowers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role TEXT, -- Borrower, CoBorrower
    is_primary BOOLEAN DEFAULT false,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(application_id, user_id)
);

CREATE INDEX idx_app_borrowers_app ON application_borrowers(application_id);
CREATE INDEX idx_app_borrowers_user ON application_borrowers(user_id);

-- ============================================
-- COMMENTS
-- ============================================

COMMENT ON TABLE applications IS 'Main loan application records';
COMMENT ON TABLE properties IS 'Properties associated with loan applications';
COMMENT ON TABLE application_borrowers IS 'Links users to applications as borrowers/co-borrowers';

-- ============================================
-- DATA MIGRATION / SEEDING (OPTIONAL EXAMPLES)
-- ============================================

-- Step 1: Insert a sample application
-- INSERT INTO applications (loan_purpose, loan_amount, status) 
-- VALUES ('Purchase', 350000, 'Active');

-- Step 2: Link an existing user as a borrower
-- INSERT INTO application_borrowers (application_id, user_id, role, is_primary)
-- VALUES ((SELECT id FROM applications LIMIT 1), (SELECT id FROM users LIMIT 1), 'Borrower', true);

-- Step 3: Add a property
-- INSERT INTO properties (application_id, address_line, city, state, zip_code)
-- VALUES ((SELECT id FROM applications LIMIT 1), '123 Main St', 'Austin', 'TX', '78701');
