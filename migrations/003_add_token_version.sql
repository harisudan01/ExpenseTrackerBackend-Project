-- Adds the token version used to cancel login tokens (on logout and password reset).
-- Safe to run more than once. The app also adds this column itself at start-up if it is missing.

ALTER TABLE cashexpense_users
    ADD COLUMN IF NOT EXISTS token_version INTEGER NOT NULL DEFAULT 0;
