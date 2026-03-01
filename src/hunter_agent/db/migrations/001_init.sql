CREATE TABLE IF NOT EXISTS talent (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  normalized_name TEXT NOT NULL,
  education TEXT,
  institution TEXT,
  grade_or_years TEXT,
  resume_pdf TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_talent_normalized_name ON talent(normalized_name);

CREATE TABLE IF NOT EXISTS talent_contact (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  talent_id INTEGER NOT NULL,
  type TEXT NOT NULL CHECK(type IN ('wechat', 'phone', 'email')),
  value TEXT NOT NULL,
  normalized_value TEXT NOT NULL,
  verified INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(talent_id) REFERENCES talent(id) ON DELETE CASCADE,
  UNIQUE(type, normalized_value)
);

CREATE INDEX IF NOT EXISTS idx_contact_talent_id ON talent_contact(talent_id);

CREATE TABLE IF NOT EXISTS talent_project_tag (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  talent_id INTEGER NOT NULL,
  category TEXT NOT NULL,
  other_text TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(talent_id) REFERENCES talent(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_tag_unique
ON talent_project_tag(talent_id, category, COALESCE(other_text, ''));

CREATE TABLE IF NOT EXISTS paper (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  arxiv_id TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  published_date TEXT,
  categories_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS paper_author_mention (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  paper_id INTEGER NOT NULL,
  talent_name TEXT NOT NULL,
  normalized_name TEXT NOT NULL,
  affiliation TEXT,
  source_date TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(paper_id) REFERENCES paper(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_mention_source_date ON paper_author_mention(source_date);
CREATE INDEX IF NOT EXISTS idx_mention_normalized_name ON paper_author_mention(normalized_name);
