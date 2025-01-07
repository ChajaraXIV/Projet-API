CREATE TABLE IF NOT EXISTS my_table (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    value INTEGER
);
INSERT INTO my_table (name, value)
VALUES ('Alice', 42),
    ('Bob', 36),
    ('Charlie', 28);