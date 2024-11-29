DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS passwords;

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    first_name VARCHAR(30),
    last_name VARCHAR(50),
    username VARCHAR(30) UNIQUE NOT NULL,
    email_address VARCHAR(50) UNIQUE NOT NULL,
    user_group VARCHAR(255),
    salt TEXT NOT NULL
);

CREATE TABLE passwords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    password_hash TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);