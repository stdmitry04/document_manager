DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS document_groups;

CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT UNIQUE NOT NULL,
    owner VARCHAR(100) NOT NULL,
    file_hash TEXT NOT NULL,
    last_modified_by VARCHAR(100),
    last_modified_at TIMESTAMP,
    total_modifications INTEGER DEFAULT 0
);

CREATE TABLE document_groups (
    document_id INTEGER,
    group_name TEXT,
    FOREIGN KEY(document_id) REFERENCES documents(id),
    PRIMARY KEY(document_id, group_name)
);