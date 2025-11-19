-- ===============================================
-- ================================================

-- Table 1 : Utilisateur
CREATE TABLE utilisateurs (
    id_user SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- Table 2 : Fichier_Audio
CREATE TABLE fichiers_audio (
    id_audio SERIAL PRIMARY KEY,
    id_user INTEGER NOT NULL REFERENCES utilisateurs(id_user) ON DELETE CASCADE,
    
    title VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    
    file_path VARCHAR(500) NOT NULL  -- OBLIGATOIRE pour accéder au fichier
);

-- Table 3 : Transcription
CREATE TABLE transcriptions (
    id_transcription SERIAL PRIMARY KEY,
    id_audio INTEGER NOT NULL REFERENCES fichiers_audio(id_audio) ON DELETE CASCADE,
    
    text_brut TEXT NOT NULL,
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    speaker VARCHAR(50),
    
    sequence_number INTEGER NOT NULL  -- OBLIGATOIRE pour l'ordre des segments!
);

-- Table 4 : Résumé
CREATE TABLE resumes (
    id_resume SERIAL PRIMARY KEY,
    id_audio INTEGER NOT NULL REFERENCES fichiers_audio(id_audio) ON DELETE CASCADE,
    
    summary_text TEXT NOT NULL,
    
    type_resume VARCHAR(50) NOT NULL,  -- OBLIGATOIRE : 'general' ou 'par_speaker'
    speaker VARCHAR(50)                 -- OBLIGATOIRE si type='par_speaker'
);

-- Index minimum
CREATE INDEX idx_fichiers_audio_user ON fichiers_audio(id_user);
CREATE INDEX idx_transcriptions_audio ON transcriptions(id_audio, sequence_number);
CREATE INDEX idx_resumes_audio ON resumes(id_audio);

-- Ajouter la colonne num_speakers à la table existante
ALTER TABLE fichiers_audio ADD COLUMN num_speakers INTEGER;
ALTER TABLE fichiers_audio ADD COLUMN duration FLOAT;


-- Ajouter la colonne
ALTER TABLE fichiers_audio ADD COLUMN date_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Mettre à jour les lignes existantes
UPDATE fichiers_audio SET date_upload = CURRENT_TIMESTAMP WHERE date_upload IS NULL;


SELECT * FROM utilisateurs;
SELECT * FROM fichiers_audio;
SELECT * FROM transcriptions;
SELECT * FROM resumes;