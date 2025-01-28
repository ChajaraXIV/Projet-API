-- Création payment
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
    ('AchrafMagh', 150.0, 'retrait', '2025-01-10 17:48:00');


-- Création odds
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'phase_enum') THEN
        CREATE TYPE phase_enum AS ENUM ('Ligue', 'Plays-off', '8èmes','Quart-finale','Demi-finale','Finale');
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'state_enum') THEN
        CREATE TYPE state_enum AS ENUM ('En cours', 'Fini','En attente');
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS odds (
    id SERIAL PRIMARY KEY,
    time TIMESTAMP NOT NULL,
    phase phase_enum NOT NULL,
    goals1 INT NOT NULL,
    goals2 INT NOT NULL,
    state state_enum NOT NULL,
    odds1 FLOAT NOT NULL,
    odds2 FLOAT NOT NULL,
    oddsx FLOAT NOT NULL
);

INSERT INTO odds (time, phase, goals1, goals2, state, odds1, odds2, oddsx)
VALUES 
('2025-01-11 15:30:00', 'Ligue',1,2,'En cours', 1.8, 3.5, 2.5),
('2025-01-12 18:00:00', 'Quart-finale',0,1, 'Fini', 2.1, 2.8, 3.0),
('2025-01-13 20:45:00', 'Finale',3,3, 'En attente', 1.6, 2.9, 2.7);

-- Création bets

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'odds_type_enum') THEN
        CREATE TYPE odds_type_enum AS ENUM ('Simple', 'Combine');
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS bets (
    id SERIAL PRIMARY KEY,
    amount FLOAT NOT NULL,
    odds FLOAT NOT NULL,
    odds_type odds_type_enum NOT NULL,
    time TIMESTAMP NOT NULL,
    winnings FLOAT NOT NULL
);

INSERT INTO bets(amount,odds,odds_type,time,winnings)
VALUES 
(25,3.5, 'Simple','2025-01-12 18:00:00',87.5),
(30,1.01, 'Combine','2025-01-12 18:00:00',30.3),
(47,9.9, 'Simple','2025-01-12 18:00:00',465.3);

-- Table users pour le service Auth
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    user_role VARCHAR(255) NOT NULL,
    connected BOOLEAN NOT NULL DEFAULT FALSE
);

-- Table tokens pour gérer les tokens d'acces et de rafraîchissement
CREATE TABLE IF NOT EXISTS tokens (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) NOT NULL,
    token_type VARCHAR(50) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    valid BOOLEAN NOT NULL
);

-- Table des profils clients
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    firstname VARCHAR(100) NOT NULL,
    lastname VARCHAR(100) NOT NULL,
    Birth_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
