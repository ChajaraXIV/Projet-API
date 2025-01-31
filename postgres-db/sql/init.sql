-- Création payment
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'payment_type_enum') THEN
        CREATE TYPE payment_type_enum AS ENUM ('depot', 'pari', 'retrait','gains','pertes');
    END IF;
END $$;


-- Création table teams 
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(255) NOT NULL
);

INSERT INTO teams (name, country)
VALUES
    ('Arsenal', 'ENG'),
    ('Aston Villa', 'ENG'),
    ('Liverpool', 'ENG'),
    ('Manchester City', 'ENG'),
    ('Atlético de Madrid', 'ESP'),
    ('Barcelona', 'ESP'),
    ('Girona', 'ESP'),
    ('Real Madrid', 'ESP'),
    ('Bayern Munich', 'GER'),
    ('Borussia Dortmund', 'GER'),
    ('RB Leipzig', 'GER'),
    ('Bayer Leverkusen', 'GER'),
    ('Stuttgart', 'GER'),
    ('Atalanta', 'ITA'),
    ('Bologna', 'ITA'),
    ('Inter Milan', 'ITA'),
    ('Juventus', 'ITA'),
    ('AC Milan', 'ITA'),
    ('Brest', 'FRA'),
    ('Lille', 'FRA'),
    ('Monaco', 'FRA'),
    ('Paris Saint-Germain', 'FRA'),
    ('Salzburg', 'AUT'),
    ('Sturm Graz', 'AUT'),
    ('Feyenoord', 'NED'),
    ('PSV Eindhoven', 'NED'),
    ('Benfica', 'POR'),
    ('Sporting CP', 'POR'),
    ('Club Brugge', 'BEL'),
    ('Dinamo Zagreb', 'CRO'),
    ('Sparta Prague', 'CZE'),
    ('Celtic', 'SCO'),
    ('Red Star Belgrade', 'SRB'),
    ('Slovan Bratislava', 'SVK'),
    ('Young Boys', 'SUI'),
    ('Shakhtar Donetsk', 'UKR');    
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


ALTER TABLE odds ADD COLUMN IF NOT EXISTS team1_id INT REFERENCES teams(id) ON DELETE CASCADE;
ALTER TABLE odds ADD COLUMN IF NOT EXISTS team2_id INT REFERENCES teams(id) ON DELETE CASCADE;


--Creation table card 
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'card_type_enum') THEN
        CREATE TYPE card_type_enum AS ENUM ('Visa', 'Mastercard', 'Amex', 'Discover');
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS card (
    id SERIAL PRIMARY KEY,  
    full_name VARCHAR(255) NOT NULL,            
    numbers BIGINT NOT NULL,               
    card_type card_type_enum NOT NULL,       
    validity DATE NOT NULL,               
    crypto INT NOT NULL               
);

-- Insertions de données dans la table card
INSERT INTO card (full_name, numbers, card_type, validity, crypto)
VALUES 
('John Doe', 1234567812345678, 'Visa', '2025-12-31', 123),
('Jane Smith', 8765432187654321, 'Mastercard', '2026-06-30', 456),
('Alice Johnson', 5678901256789012, 'Amex', '2024-09-15', 789),
('Bob Brown', 4321876543218765, 'Discover', '2027-03-01', 321),
('Charlie Davis', 1029384756102938, 'Visa', '2025-08-20', 654),
('Emily White', 5647382910564738, 'Mastercard', '2026-11-05', 987);


-- Création de la table bookmakers
CREATE TABLE bookmakers (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL
);

INSERT INTO bookmakers (first_name, last_name) VALUES ('John', 'Doe');

          

-- Table users pour le service Auth
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    user_role VARCHAR(255) NOT NULL,
    connected BOOLEAN NOT NULL DEFAULT FALSE,
    registration_token VARCHAR(500),
    signin_allowed BOOLEAN NOT NULL DEFAULT FALSE
);

INSERT INTO users (email, password_hash, user_role, connected, registration_token, signin_allowed)
VALUES ('test@example.com', 'hashed_password', 'user', FALSE, NULL, TRUE)
RETURNING id;

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
    username VARCHAR(50) PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    firstname VARCHAR(100) NOT NULL,
    lastname VARCHAR(100) NOT NULL,
    Birth_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount FLOAT NOT NULL,
    payment_type payment_type_enum NOT NULL,
    time TIMESTAMP NOT NULL
);

-- INSERT INTO payments (user_name, amount, payment_type, time) VALUES
--      ('Jadkab', 100.0, 'depot', '2025-01-10 17:45:00'),
--      ('HatimFil', 200.0, 'pari', '2025-01-10 17:46:00'),
--      ('IkramBad', 250.0, 'depot', '2025-01-10 17:47:00'),
--      ('AchrafMagh', 150.0, 'retrait', '2025-01-10 17:48:00');


-- Création bets
-- DO $$ 
-- BEGIN
--     IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'odds_type_enum') THEN
--         CREATE TYPE odds_type_enum AS ENUM ('Simple', 'Combine');
--     END IF;
-- END $$;

-- CREATE TABLE IF NOT EXISTS bets (
--     id SERIAL PRIMARY KEY,
--     amount FLOAT NOT NULL,
--     odds FLOAT NOT NULL,
--     odds_type odds_type_enum NOT NULL,
--     time TIMESTAMP NOT NULL,
--     winnings FLOAT NOT NULL
-- );

-- INSERT INTO bets(amount,odds,odds_type,time,winnings)
-- VALUES 
-- (25,3.5, 'Simple','2025-01-12 18:00:00',87.5),
-- (30,1.01, 'Combine','2025-01-12 18:00:00',30.3),
-- (10,1, 'Combine','2025-01-12 18:00:00',10),
-- (47,9.9, 'Simple','2025-01-12 18:00:00',465.3);

-- Vérification et création du type ENUM odds_type_enum si non existant
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'odds_type_enum') THEN
        CREATE TYPE odds_type_enum AS ENUM ('Simple', 'Combine');
    END IF;
END $$;

-- Création de la table bets avec les clés étrangères
CREATE TABLE IF NOT EXISTS bets (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    match_id INT NOT NULL REFERENCES odds(id) ON DELETE CASCADE,
    amount FLOAT NOT NULL CHECK (amount > 0),
    odds FLOAT NOT NULL CHECK (odds > 0),
    odds_type odds_type_enum NOT NULL,
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    winnings FLOAT NOT NULL CHECK (winnings >= 0)
);

ALTER TABLE bets DROP COLUMN IF EXISTS match_id;
ALTER TABLE bets ADD COLUMN IF NOT EXISTS match_ids TEXT NOT NULL;
ALTER TABLE bets ADD COLUMN IF NOT EXISTS odds_list TEXT NOT NULL;
ALTER TABLE bets ADD COLUMN IF NOT EXISTS odds FLOAT NOT NULL;


-- Ajout de quelques paris pour tester
INSERT INTO bets (user_id, match_id, amount, odds, odds_type, time, winnings)
VALUES
    (1, 1, 25.0, 3.5, 'Simple', '2025-01-12 18:00:00', 87.5),
    (34, 2, 30.0, 1.01, 'Combine', '2025-01-12 18:00:00', 30.3),
    (3, 3, 10.0, 1.0, 'Combine', '2025-01-12 18:00:00', 10.0),
    (4, 1, 47.0, 9.9, 'Simple', '2025-01-12 18:00:00', 465.3);
