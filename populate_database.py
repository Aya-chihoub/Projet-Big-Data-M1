"""
================================================================================
SCRIPT D'INGESTION DE DONNÉES WLASL VERS MySQL
Personne 1 : Base de données & Ingestion
================================================================================
Ce script parse le fichier WLASL_v0.3.json et insère les données dans MySQL
"""

import mysql.connector
from mysql.connector import Error
import json
import os
from datetime import datetime
import random

class WLASLDatabaseManager:
    def __init__(self, host="localhost", user="root", password="", database="asl_recognition"):
        """
        Initialiser la connexion à MySQL
        
        Args:
            host: Hôte MySQL (par défaut localhost)
            user: Utilisateur MySQL (par défaut root)
            password: Mot de passe MySQL
            database: Nom de la base de données
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Établir la connexion à MySQL"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            
            if self.connection.is_connected():
                self.cursor = self.connection.cursor()
                print(f"✅ Connecté à MySQL - Base: {self.database}")
                return True
                
        except Error as e:
            print(f"❌ Erreur de connexion MySQL: {e}")
            return False
    
    def close(self):
        """Fermer la connexion"""
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            print("✅ Connexion MySQL fermée")
    
    def parse_wlasl_json(self, json_file_path):
        """
        Parser le fichier WLASL_v0.3.json
        
        Args:
            json_file_path: Chemin vers le fichier WLASL_v0.3.json
            
        Returns:
            Liste de dictionnaires avec les données parsées
        """
        print(f"\n📄 Parsing du fichier: {json_file_path}")
        
        if not os.path.exists(json_file_path):
            print(f"❌ Fichier non trouvé: {json_file_path}")
            return None
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"✅ JSON parsé avec succès")
            print(f"   Total de mots: {len(data)}")
            
            return data
            
        except Exception as e:
            print(f"❌ Erreur lors du parsing JSON: {e}")
            return None
    
    def insert_words_and_videos(self, wlasl_data):
        """
        Insérer les mots et vidéos dans la base de données
        
        Args:
            wlasl_data: Données parsées du JSON WLASL
        """
        print(f"\n📊 Insertion des données dans MySQL...")
        
        total_words = 0
        total_videos = 0
        skipped_words = 0
        
        try:
            for entry in wlasl_data:
                gloss = entry.get('gloss')
                instances = entry.get('instances', [])
                
                # Vérifier si le mot a des instances
                if instances is None or len(instances) == 0:
                    skipped_words += 1
                    continue
                
                # Insérer le mot dans la table words
                insert_word_query = """
                    INSERT INTO words (gloss, sample_count) 
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE sample_count = %s
                """
                
                sample_count = len(instances)
                self.cursor.execute(insert_word_query, (gloss, sample_count, sample_count))
                word_id = self.cursor.lastrowid
                
                # Si le mot existait déjà, récupérer son ID
                if word_id == 0:
                    self.cursor.execute("SELECT id FROM words WHERE gloss = %s", (gloss,))
                    word_id = self.cursor.fetchone()[0]
                
                total_words += 1
                
                # Insérer les vidéos pour ce mot
                for idx, instance in enumerate(instances):
                    video_id = instance.get('video_id', f"{gloss}_{idx}")
                    url = instance.get('url', '')
                    fps = instance.get('fps')
                    frame_start = instance.get('frame_start')
                    frame_end = instance.get('frame_end')
                    signer_id = instance.get('signer_id')
                    
                    # Calculer la durée estimée si possible
                    duration = None
                    if fps and frame_start is not None and frame_end is not None:
                        duration = (frame_end - frame_start) / fps
                    
                    # Assigner aléatoirement à train/val/test (70/15/15)
                    rand = random.random()
                    if rand < 0.70:
                        split = 'train'
                    elif rand < 0.85:
                        split = 'val'
                    else:
                        split = 'test'
                    
                    insert_video_query = """
                        INSERT INTO videos 
                        (word_id, video_id, video_url, duration_sec, fps, signer_id, split, downloaded, processed)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    self.cursor.execute(insert_video_query, (
                        word_id, 
                        video_id, 
                        url, 
                        duration, 
                        fps, 
                        signer_id, 
                        split, 
                        False, 
                        False
                    ))
                    
                    total_videos += 1
                
                # Commit tous les 100 mots pour éviter les transactions trop longues
                if total_words % 100 == 0:
                    self.connection.commit()
                    print(f"   Progression: {total_words} mots, {total_videos} vidéos insérées...")
            
            # Commit final
            self.connection.commit()
            
            print(f"\n✅ Insertion terminée!")
            print(f"   Mots insérés: {total_words}")
            print(f"   Mots ignorés (sans vidéos): {skipped_words}")
            print(f"   Vidéos insérées: {total_videos}")
            
        except Error as e:
            print(f"❌ Erreur lors de l'insertion: {e}")
            self.connection.rollback()
    
    def get_database_statistics(self):
        """Afficher les statistiques de la base de données"""
        print(f"\n📊 STATISTIQUES DE LA BASE DE DONNÉES")
        print("=" * 60)
        
        try:
            # Statistiques des mots
            self.cursor.execute("SELECT COUNT(*) FROM words")
            word_count = self.cursor.fetchone()[0]
            print(f"Total de mots: {word_count}")
            
            # Statistiques des vidéos
            self.cursor.execute("SELECT COUNT(*) FROM videos")
            video_count = self.cursor.fetchone()[0]
            print(f"Total de vidéos: {video_count}")
            
            # Répartition train/val/test
            self.cursor.execute("""
                SELECT split, COUNT(*) 
                FROM videos 
                GROUP BY split
            """)
            splits = self.cursor.fetchall()
            print(f"\nRépartition des données:")
            for split, count in splits:
                percentage = (count / video_count) * 100 if video_count > 0 else 0
                print(f"  {split}: {count} ({percentage:.1f}%)")
            
            # Top 10 mots avec le plus de vidéos
            self.cursor.execute("""
                SELECT gloss, sample_count 
                FROM words 
                ORDER BY sample_count DESC 
                LIMIT 10
            """)
            top_words = self.cursor.fetchall()
            print(f"\nTop 10 mots avec le plus de vidéos:")
            for gloss, count in top_words:
                print(f"  {gloss}: {count} vidéos")
            
            # Vidéos téléchargées/traitées
            self.cursor.execute("SELECT COUNT(*) FROM videos WHERE downloaded = TRUE")
            downloaded = self.cursor.fetchone()[0]
            print(f"\nVidéos téléchargées: {downloaded}")
            
            self.cursor.execute("SELECT COUNT(*) FROM videos WHERE processed = TRUE")
            processed = self.cursor.fetchone()[0]
            print(f"Vidéos traitées: {processed}")
            
            print("=" * 60)
            
        except Error as e:
            print(f"❌ Erreur lors de la récupération des statistiques: {e}")
    
    def export_connection_info(self, output_file="db_connection_info.txt"):
        """Exporter les informations de connexion pour l'équipe"""
        info = f"""
================================================================================
INFORMATIONS DE CONNEXION - BASE DE DONNÉES ASL RECOGNITION
================================================================================

Hôte: {self.host}
Utilisateur: {self.user}
Base de données: {self.database}
Date de création: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

================================================================================
EXEMPLE DE CONNEXION PYTHON
================================================================================

import mysql.connector

db = mysql.connector.connect(
    host="{self.host}",
    user="{self.user}",
    password="VOTRE_MOT_DE_PASSE",
    database="{self.database}"
)

cursor = db.cursor()
cursor.execute("SELECT * FROM words LIMIT 5")
results = cursor.fetchall()
print(results)

================================================================================
REQUÊTES UTILES
================================================================================

-- Voir tous les mots
SELECT * FROM words LIMIT 10;

-- Voir les vidéos non téléchargées
SELECT * FROM videos_to_download LIMIT 10;

-- Voir les statistiques par mot
SELECT * FROM word_statistics LIMIT 10;

-- Obtenir les statistiques globales
CALL get_database_stats();

-- Mettre à jour les compteurs
CALL update_sample_counts();

================================================================================
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(info)
        
        print(f"\n✅ Informations de connexion exportées vers: {output_file}")


def main():
    """Fonction principale"""
    print("""
    ================================================================================
                        WLASL DATABASE POPULATION SCRIPT
                            Personne 1 - Tâche 1
    ================================================================================
    """)
    
    # Configuration - MODIFIEZ CES VALEURS SELON VOTRE CONFIGURATION
    MYSQL_HOST = "localhost"
    MYSQL_USER = "root"
    MYSQL_PASSWORD = "1234"  # METTEZ VOTRE MOT DE PASSE ICI
    MYSQL_DATABASE = "asl_recognition"
    WLASL_JSON_PATH = "database/WLASL_v0.3.json"  # Chemin vers votre fichier JSON
    
    # Créer l'instance du gestionnaire
    db_manager = WLASLDatabaseManager(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )
    
    # Étape 1: Connexion
    if not db_manager.connect():
        print("❌ Impossible de se connecter à MySQL. Vérifiez vos paramètres.")
        return
    
    # Étape 2: Parser le JSON
    wlasl_data = db_manager.parse_wlasl_json(WLASL_JSON_PATH)
    if wlasl_data is None:
        db_manager.close()
        return
    
    # Étape 3: Insérer les données
    db_manager.insert_words_and_videos(wlasl_data)
    
    # Étape 4: Afficher les statistiques
    db_manager.get_database_statistics()
    
    # Étape 5: Exporter les infos de connexion
    db_manager.export_connection_info()
    
    # Fermer la connexion
    db_manager.close()
    
    print(f"\n✅ PROCESSUS TERMINÉ AVEC SUCCÈS!")
    print(f"   La base de données est prête pour la Personne 2 (PySpark)")


if __name__ == "__main__":
    main()