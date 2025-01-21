
-- DO $$ 
-- BEGIN
--     IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'phase_enum') THEN
--         CREATE TYPE phase_enum AS ENUM ('Ligue', 'Plays-off', '8èmes','Quart-finale','Demi-finale','Finale');
--     END IF;
-- END $$;

-- DO $$ 
-- BEGIN
--     IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'state_enum') THEN
--         CREATE TYPE state_enum AS ENUM ('En cours', 'Fini');
--     END IF;
-- END $$;

-- CREATE TABLE IF NOT EXISTS odds (
--     id SERIAL PRIMARY KEY,
--     time TIMESTAMP NOT NULL,
--     phase phase_enum NOT NULL,
--     goals1 INT NOT NULL,
--     goals2 FLOAT NOT NULL,
--     state state_enum NOT NULL,
--     odds1 FLOAT NOT NULL,
--     odds2 FLOAT NOT NULL,
--     oddsx FLOAT NOT NULL
-- );

-- INSERT INTO odds (time, phase, goals1, goals2, state, odds1, odds2, oddsx)
-- VALUES 
-- ('2025-01-11 15:30:00', 'Ligue',1,2,'En cours', 1.8, 3.5, 2.5),
-- ('2025-01-12 18:00:00', 'Quart-finale',0,1, 'Fini', 2.1, 2.8, 3.0),
-- ('2025-01-13 20:45:00', 'Finale',3,3, 'En cours', 1.6, 2.9, 2.7);
