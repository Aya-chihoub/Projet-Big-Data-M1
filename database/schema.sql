-- ================================================================================
-- SCHÉMA DE BASE DE DONNÉES POUR RECONNAISSANCE ASL
-- Personne 1 : Base de données & Ingestion
-- ================================================================================

-- Créer la base de données
CREATE DATABASE IF NOT EXISTS asl_recognition;
USE asl_recognition;

-- ================================================================================
-- TABLE 1: words (mots ASL)
-- ================================================================================
CREATE TABLE IF NOT EXISTS words (
    id INT AUTO_INCREMENT PRIMARY KEY,
    gloss VARCHAR(100) NOT NULL UNIQUE,
    sample_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_gloss (gloss)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ================================================================================
-- TABLE 2: videos
-- ================================================================================
CREATE TABLE IF NOT EXISTS videos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    word_id INT NOT NULL,
    video_id VARCHAR(50),
    video_url VARCHAR(500),
    local_path VARCHAR(500),
    duration_sec FLOAT,
    fps INT,
    signer_id INT,
    split ENUM('train', 'val', 'test') DEFAULT 'train',
    downloaded BOOLEAN DEFAULT FALSE,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE,
    INDEX idx_word_id (word_id),
    INDEX idx_downloaded (downloaded),
    INDEX idx_processed (processed),
    INDEX idx_split (split)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ================================================================================
-- TABLE 3: frames (images extraites des vidéos)
-- ================================================================================
CREATE TABLE IF NOT EXISTS frames (
    id INT AUTO_INCREMENT PRIMARY KEY,
    video_id INT NOT NULL,
    frame_number INT NOT NULL,
    frame_path VARCHAR(500),
    timestamp_sec FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
    INDEX idx_video_id (video_id),
    INDEX idx_frame_number (frame_number),
    UNIQUE KEY unique_video_frame (video_id, frame_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ================================================================================
-- TABLE 4: landmarks (points de repère MediaPipe)
-- ================================================================================
CREATE TABLE IF NOT EXISTS landmarks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    frame_id INT NOT NULL,
    landmark_data JSON,
    num_hands INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (frame_id) REFERENCES frames(id) ON DELETE CASCADE,
    INDEX idx_frame_id (frame_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ================================================================================
-- TABLE 5: processing_logs (logs de traitement)
-- ================================================================================
CREATE TABLE IF NOT EXISTS processing_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    video_id INT,
    status ENUM('pending', 'downloading', 'success', 'failed') DEFAULT 'pending',
    error_message TEXT,
    processing_time_sec FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
    INDEX idx_video_id (video_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ================================================================================
-- VUES UTILES
-- ================================================================================

-- Vue pour voir les statistiques par mot
CREATE OR REPLACE VIEW word_statistics AS
SELECT 
    w.id,
    w.gloss,
    w.sample_count,
    COUNT(v.id) as total_videos,
    SUM(CASE WHEN v.downloaded = TRUE THEN 1 ELSE 0 END) as downloaded_count,
    SUM(CASE WHEN v.processed = TRUE THEN 1 ELSE 0 END) as processed_count,
    SUM(CASE WHEN v.split = 'train' THEN 1 ELSE 0 END) as train_count,
    SUM(CASE WHEN v.split = 'val' THEN 1 ELSE 0 END) as val_count,
    SUM(CASE WHEN v.split = 'test' THEN 1 ELSE 0 END) as test_count
FROM words w
LEFT JOIN videos v ON w.id = v.word_id
GROUP BY w.id, w.gloss, w.sample_count;

-- Vue pour les vidéos non téléchargées
CREATE OR REPLACE VIEW videos_to_download AS
SELECT 
    v.id,
    v.video_id,
    v.video_url,
    w.gloss as word
FROM videos v
JOIN words w ON v.word_id = w.id
WHERE v.downloaded = FALSE
ORDER BY w.gloss;

-- ================================================================================
-- PROCÉDURES STOCKÉES UTILES
-- ================================================================================

DELIMITER //

-- Procédure pour mettre à jour le compteur de samples
CREATE PROCEDURE update_sample_counts()
BEGIN
    UPDATE words w
    SET sample_count = (
        SELECT COUNT(*) 
        FROM videos v 
        WHERE v.word_id = w.id
    );
END //

-- Procédure pour obtenir les statistiques globales
CREATE PROCEDURE get_database_stats()
BEGIN
    SELECT 
        'Total Words' as metric, 
        COUNT(*) as value 
    FROM words
    UNION ALL
    SELECT 
        'Total Videos', 
        COUNT(*) 
    FROM videos
    UNION ALL
    SELECT 
        'Downloaded Videos', 
        COUNT(*) 
    FROM videos 
    WHERE downloaded = TRUE
    UNION ALL
    SELECT 
        'Processed Videos', 
        COUNT(*) 
    FROM videos 
    WHERE processed = TRUE
    UNION ALL
    SELECT 
        'Total Frames', 
        COUNT(*) 
    FROM frames
    UNION ALL
    SELECT 
        'Total Landmarks', 
        COUNT(*) 
    FROM landmarks;
END //

DELIMITER ;

-- ================================================================================
-- FIN DU SCHÉMA
-- ================================================================================

SHOW TABLES;