CREATE TABLE IF NOT EXISTS bettings (
    id SERIAL PRIMARY KEY,
    match VARCHAR(255) NOT NULL,
    amount FLOAT NOT NULL,
    odds FLOAT NOT NULL
);
INSERT INTO bettings (match, amount, odds) VALUES
('Match 1', 100.0, 1.5),
('Match 2', 200.0, 2.0),
('Match 3', 150.0, 1.8);
