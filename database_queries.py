"""
================================================================================
REQUÊTES MYSQL UTILES POUR L'ÉQUIPE
Personne 1 : Base de données & Ingestion
================================================================================
"""

import mysql.connector
from tabulate import tabulate

class DatabaseQueryHelper:
    def __init__(self, host="localhost", user="root", password="", database="asl_recognition"):
        self.connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.connection.cursor()
    
    def show_sample_words(self, limit=10):
        """Afficher un échantillon de mots"""
        print(f"\n📚 ÉCHANTILLON DE MOTS (Top {limit}):")
        print("=" * 70)
        
        query = """
            SELECT id, gloss, sample_count 
            FROM words 
            ORDER BY sample_count DESC 
            LIMIT %s
        """
        self.cursor.execute(query, (limit,))
        results = self.cursor.fetchall()
        
        headers = ["ID", "Mot (Gloss)", "Nombre de vidéos"]
        print(tabulate(results, headers=headers, tablefmt="grid"))
    
    def show_videos_for_word(self, gloss, limit=5):
        """Afficher les vidéos pour un mot spécifique"""
        print(f"\n🎥 VIDÉOS POUR LE MOT: '{gloss}'")
        print("=" * 100)
        
        query = """
            SELECT v.id, v.video_id, v.video_url, v.split, v.downloaded, v.processed
            FROM videos v
            JOIN words w ON v.word_id = w.id
            WHERE w.gloss = %s
            LIMIT %s
        """
        self.cursor.execute(query, (gloss, limit))
        results = self.cursor.fetchall()
        
        headers = ["ID", "Video ID", "URL", "Split", "Téléchargé", "Traité"]
        print(tabulate(results, headers=headers, tablefmt="grid"))
    
    def show_download_statistics(self):
        """Afficher les statistiques de téléchargement"""
        print(f"\n📊 STATISTIQUES DE TÉLÉCHARGEMENT:")
        print("=" * 70)
        
        queries = {
            "Total vidéos": "SELECT COUNT(*) FROM videos",
            "Vidéos téléchargées": "SELECT COUNT(*) FROM videos WHERE downloaded = TRUE",
            "Vidéos non téléchargées": "SELECT COUNT(*) FROM videos WHERE downloaded = FALSE",
            "Vidéos traitées": "SELECT COUNT(*) FROM videos WHERE processed = TRUE",
            "Vidéos non traitées": "SELECT COUNT(*) FROM videos WHERE processed = FALSE"
        }
        
        results = []
        for label, query in queries.items():
            self.cursor.execute(query)
            count = self.cursor.fetchone()[0]
            results.append([label, count])
        
        print(tabulate(results, headers=["Métrique", "Valeur"], tablefmt="grid"))
    
    def show_split_distribution(self):
        """Afficher la répartition train/val/test"""
        print(f"\n📈 RÉPARTITION TRAIN/VAL/TEST:")
        print("=" * 70)
        
        query = """
            SELECT 
                split,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM videos), 2) as percentage
            FROM videos
            GROUP BY split
            ORDER BY split
        """
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        
        headers = ["Split", "Nombre", "Pourcentage (%)"]
        print(tabulate(results, headers=headers, tablefmt="grid"))
    
    def get_videos_to_download(self, limit=20):
        """Obtenir la liste des vidéos à télécharger"""
        print(f"\n⬇️  VIDÉOS À TÉLÉCHARGER (Top {limit}):")
        print("=" * 100)
        
        query = """
            SELECT v.id, w.gloss, v.video_url, v.split
            FROM videos v
            JOIN words w ON v.word_id = w.id
            WHERE v.downloaded = FALSE
            LIMIT %s
        """
        self.cursor.execute(query, (limit,))
        results = self.cursor.fetchall()
        
        headers = ["ID", "Mot", "URL", "Split"]
        print(tabulate(results, headers=headers, tablefmt="grid"))
        
        return results
    
    def mark_video_downloaded(self, video_id, local_path):
        """Marquer une vidéo comme téléchargée"""
        query = """
            UPDATE videos 
            SET downloaded = TRUE, local_path = %s, updated_at = NOW()
            WHERE id = %s
        """
        self.cursor.execute(query, (local_path, video_id))
        self.connection.commit()
        print(f"✅ Vidéo {video_id} marquée comme téléchargée")
    
    def get_word_id_by_gloss(self, gloss):
        """Obtenir l'ID d'un mot par son gloss"""
        query = "SELECT id FROM words WHERE gloss = %s"
        self.cursor.execute(query, (gloss,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def close(self):
        """Fermer la connexion"""
        self.cursor.close()
        self.connection.close()


# ================================================================================
# EXEMPLES D'UTILISATION
# ================================================================================

if __name__ == "__main__":
    print("""
    ================================================================================
                            DATABASE QUERY HELPER
                      Requêtes utiles pour l'équipe ASL
    ================================================================================
    """)
    
    # Configuration
    db = DatabaseQueryHelper(
        host="localhost",
        user="root",
        password="1234",  # METTEZ VOTRE MOT DE PASSE
        database="asl_recognition"
    )
    
    # Afficher diverses statistiques
    db.show_sample_words(10)
    db.show_download_statistics()
    db.show_split_distribution()
    db.get_videos_to_download(10)
    
    # Exemple: voir les vidéos pour un mot spécifique
    db.show_videos_for_word("book", limit=5)
    
    # Fermer
    db.close()
    
    print("\n✅ Terminé!")
