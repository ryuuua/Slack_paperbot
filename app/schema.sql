CREATE TABLE IF NOT EXISTS papers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT UNIQUE,
  source TEXT,            -- 'arxiv' | 'doi' | 'acl' | 'openreview' | ...
  title TEXT,
  authors TEXT,           -- "A; B; C"
  year INTEGER,
  venue TEXT,
  added_by TEXT,          -- user id
  ts INTEGER              -- epoch seconds
);