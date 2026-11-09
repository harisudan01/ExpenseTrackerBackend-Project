-- Adds a unique username so people can sign in with either their email or their username.
-- Safe to run more than once.

ALTER TABLE cashexpense_users
    ADD COLUMN IF NOT EXISTS username VARCHAR(30);

-- Give existing accounts a username based on the part of their email before the "@".
-- If two accounts would get the same one (or it is already taken), the user id is appended.
WITH candidates AS (
    SELECT
        id,
        COALESCE(
            LEFT(NULLIF(regexp_replace(lower(split_part(email, '@', 1)), '[^a-z0-9_.]', '', 'g'), ''), 20),
            'user'
        ) AS base
    FROM cashexpense_users
    WHERE username IS NULL
),
ranked AS (
    SELECT
        c.id,
        c.base,
        row_number() OVER (PARTITION BY c.base ORDER BY c.id) AS rn,
        EXISTS (SELECT 1 FROM cashexpense_users x WHERE x.username = c.base) AS taken
    FROM candidates c
)
UPDATE cashexpense_users u
SET username = CASE WHEN r.rn = 1 AND NOT r.taken THEN r.base ELSE r.base || u.id END
FROM ranked r
WHERE u.id = r.id;

-- Usernames are stored lower-cased, so this makes them unique regardless of case
CREATE UNIQUE INDEX IF NOT EXISTS ix_cashexpense_users_username ON cashexpense_users (username);
