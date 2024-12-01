DROP TABLE IF EXISTS logs;

CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type VARCHAR(50) NOT NULL,  --user_creation, login, document_creation, document_edit, document_search
    username VARCHAR(30) NOT NULL,
    filename TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);