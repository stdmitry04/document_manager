DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS document_groups;

CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT UNIQUE NOT NULL,
    owner VARCHAR(100) NOT NULL,
    file_hash TEXT NOT NULL,
    last_modified_by VARCHAR(100),
    last_modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_modifications INTEGER DEFAULT 1
);

CREATE TABLE document_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    group_name TEXT,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
    UNIQUE(document_id, group_name)
);