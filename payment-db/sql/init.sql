-- Création du type ENUM pour payment_type
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'payment_type_enum') THEN
        CREATE TYPE payment_type_enum AS ENUM ('depot', 'pari', 'retrait','gains','pertes');
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR(255) NOT NULL,
    amount FLOAT NOT NULL,
    payment_type payment_type_enum NOT NULL,
    time TIMESTAMP NOT NULL
);

INSERT INTO payments (user_name, amount, payment_type, time) VALUES
    ('Jadkab', 100.0, 'depot', '2025-01-10 17:45:00'),
    ('HatimFil', 200.0, 'pari', '2025-01-10 17:46:00'),
    ('IkramBad', 250.0, 'depot', '2025-01-10 17:47:00'),
    ('AchrafMagh', 150.0, 'retrait', '2025-01-10 17:48:00')