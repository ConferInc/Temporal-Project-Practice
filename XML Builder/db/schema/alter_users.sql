-- ============================================
-- UPDATE SCRIPT FOR EXISTING USERS TABLE
-- ============================================

ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number TEXT;
