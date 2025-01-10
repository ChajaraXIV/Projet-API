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
    payment_type payment_type_enum NOT NULL
);

INSERT INTO payments (user_name, amount, payment_type) VALUES
('Jadkab', 100.0,'depot'),
('HatimFil', 200.0,'pari'),
('IkramBad', 250.0,'depot'),
('AchrafMagh', 150.0,'retrait');