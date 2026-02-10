# 📚 GUIDE COMPLET - PERSONNE 1: BASE DE DONNÉES & INGESTION

## 🎯 Objectif
Créer et peupler la base de données MySQL pour le projet de reconnaissance ASL WLASL.

---

## 📋 Prérequis

- ✅ MySQL installé et fonctionnel
- ✅ Python 3.7+ installé
- ✅ Fichier WLASL_v0.3.json téléchargé depuis Kaggle
- ✅ Dossier videos/ (optionnel pour cette étape)

---

## 🚀 ÉTAPES À SUIVRE

### Étape 1: Installer les dépendances Python

```bash
pip install mysql-connector-python tabulate
```

### Étape 2: Configurer MySQL

1. **Démarrer MySQL:**
   ```bash
   # Windows
   net start MySQL80
   
   # Mac/Linux
   sudo service mysql start
   # ou
   mysql.server start
   ```

2. **Se connecter à MySQL:**
   ```bash
   mysql -u root -p
   ```

3. **Créer la base de données:**
   ```sql
   CREATE DATABASE asl_recognition;
   SHOW DATABASES;
   EXIT;
   ```

### Étape 3: Créer le schéma de la base de données

**Option A: Via ligne de commande**
```bash
mysql -u root -p asl_recognition < create_schema.sql
```

**Option B: Via MySQL Workbench**
- Ouvrir MySQL Workbench
- Se connecter à votre serveur
- File → Open SQL Script → Sélectionner `create_schema.sql`
- Exécuter le script (⚡ icône)

**Option C: Via terminal MySQL**
```bash
mysql -u root -p
```
```sql
USE asl_recognition;
SOURCE create_schema.sql;
```

### Étape 4: Vérifier que les tables sont créées

```bash
mysql -u root -p asl_recognition
```
```sql
SHOW TABLES;
DESCRIBE words;
DESCRIBE videos;
```

Vous devriez voir:
```
+------------------------+
| Tables_in_asl_recognition |
+------------------------+
| frames                 |
| landmarks              |
| processing_logs        |
| videos                 |
| word_statistics        |
| words                  |
+------------------------+
```

### Étape 5: Configurer le script Python

Ouvrir `populate_database.py` et modifier les paramètres:

```python
# Configuration - LIGNE 314
MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "VOTRE_MOT_DE_PASSE"  # ⚠️ IMPORTANT: Mettez votre mot de passe
MYSQL_DATABASE = "asl_recognition"
WLASL_JSON_PATH = "WLASL_v0.3.json"  # Chemin vers votre fichier
```

### Étape 6: Exécuter le script d'insertion

```bash
python populate_database.py
```

**Sortie attendue:**
```
================================================================================
                    WLASL DATABASE POPULATION SCRIPT
                        Personne 1 - Tâche 1
================================================================================

✅ Connecté à MySQL - Base: asl_recognition

📄 Parsing du fichier: WLASL_v0.3.json
✅ JSON parsé avec succès
   Total de mots: 2000

📊 Insertion des données dans MySQL...
   Progression: 100 mots, 3500 vidéos insérées...
   Progression: 200 mots, 7000 vidéos insérées...
   ...
   
✅ Insertion terminée!
   Mots insérés: 1999
   Mots ignorés (sans vidéos): 1
   Vidéos insérées: ~12000

📊 STATISTIQUES DE LA BASE DE DONNÉES
============================================================
Total de mots: 1999
Total de vidéos: 12000
...
```

### Étape 7: Vérifier les données

**Option A: Via script Python**
```bash
python database_queries.py
```

**Option B: Via MySQL**
```bash
mysql -u root -p asl_recognition
```
```sql
-- Voir quelques mots
SELECT * FROM words LIMIT 10;

-- Voir quelques vidéos
SELECT * FROM videos LIMIT 10;

-- Statistiques
SELECT COUNT(*) as total_mots FROM words;
SELECT COUNT(*) as total_videos FROM videos;

-- Répartition train/val/test
SELECT split, COUNT(*) FROM videos GROUP BY split;
```

---

## 📊 STRUCTURE DE LA BASE DE DONNÉES

### Table: `words`
Stocke les mots ASL (glosses)
```
id | gloss      | sample_count | created_at
---+------------+--------------+------------
1  | book       | 40           | 2026-02-03
2  | drink      | 35           | 2026-02-03
```

### Table: `videos`
Stocke les métadonnées des vidéos
```
id | word_id | video_url        | split | downloaded | processed
---+---------+------------------+-------+------------+-----------
1  | 1       | https://...      | train | FALSE      | FALSE
2  | 1       | https://...      | val   | FALSE      | FALSE
```

### Table: `frames`
Stocke les images extraites (remplie par Personne 3)
```
id | video_id | frame_number | frame_path
---+----------+--------------+-----------------
1  | 1        | 0            | /data/frames/...
2  | 1        | 1            | /data/frames/...
```

### Table: `landmarks`
Stocke les points de repère MediaPipe (remplie par Personne 3)
```
id | frame_id | landmark_data (JSON) | num_hands
---+----------+----------------------+-----------
1  | 1        | {...}                | 2
```

---

## 🔧 REQUÊTES UTILES POUR L'ÉQUIPE

### Pour la Personne 2 (PySpark)

**Obtenir les vidéos à télécharger:**
```sql
SELECT id, video_url, word_id 
FROM videos 
WHERE downloaded = FALSE
LIMIT 100;
```

**Mettre à jour après téléchargement:**
```sql
UPDATE videos 
SET downloaded = TRUE, local_path = '/data/videos/book/video_001.mp4'
WHERE id = 1;
```

### Statistiques générales

```sql
-- Vue d'ensemble
CALL get_database_stats();

-- Par mot
SELECT * FROM word_statistics ORDER BY total_videos DESC LIMIT 10;

-- Vidéos non téléchargées
SELECT COUNT(*) FROM videos WHERE downloaded = FALSE;
```

---

## 📤 CE QUE VOUS LIVREZ À L'ÉQUIPE

### ✅ Checklist de livraison

- [ ] Base de données MySQL créée et peuplée
- [ ] Fichier `db_connection_info.txt` partagé avec l'équipe
- [ ] Scripts Python fonctionnels:
  - [ ] `create_schema.sql`
  - [ ] `populate_database.py`
  - [ ] `database_queries.py`
- [ ] Documentation complète (ce README)
- [ ] Statistiques de la base affichées
- [ ] Identifiants de connexion partagés (sécurisés)

### 📧 Informations à partager

**Envoyer à Personne 2 (PySpark):**
```
Salut,

La base de données est prête! 🎉

Connexion MySQL:
- Host: localhost
- User: root
- Password: [à définir selon sécurité]
- Database: asl_recognition

Statistiques:
- Mots: 1999
- Vidéos totales: ~12000
- Train: 70%, Val: 15%, Test: 15%

Fichiers utiles:
- database_queries.py (exemples de requêtes)
- db_connection_info.txt (détails connexion)

Prochaine étape: Télécharger les vidéos depuis les URLs!
```

---

## 🐛 DÉPANNAGE

### Problème: "Access denied for user"
**Solution:** Vérifiez votre mot de passe MySQL
```bash
mysql -u root -p
# Entrez le bon mot de passe
```

### Problème: "Database does not exist"
**Solution:** Créez la base
```sql
CREATE DATABASE asl_recognition;
```

### Problème: "Table already exists"
**Solution:** Supprimez et recréez
```sql
DROP DATABASE asl_recognition;
CREATE DATABASE asl_recognition;
# Puis réexécutez create_schema.sql
```

### Problème: "File not found: WLASL_v0.3.json"
**Solution:** Vérifiez le chemin dans le script
```python
WLASL_JSON_PATH = "/chemin/complet/vers/WLASL_v0.3.json"
```

### Problème: Script Python lent
**C'est normal!** L'insertion de 12000 vidéos prend 5-10 minutes.
Le script affiche la progression tous les 100 mots.

---

## ⏱️ TEMPS ESTIMÉ

- Configuration MySQL: 30 min
- Création schéma: 10 min
- Installation dépendances Python: 5 min
- Exécution script d'insertion: 10 min
- Tests et vérification: 15 min
- Documentation: 20 min

**TOTAL: ~1.5 heures**

---

## 📚 RESSOURCES ADDITIONNELLES

### Documentation MySQL
- [MySQL Documentation](https://dev.mysql.com/doc/)
- [MySQL Connector Python](https://dev.mysql.com/doc/connector-python/en/)

### Dataset WLASL
- [Paper original](https://arxiv.org/abs/1910.11006)
- [GitHub officiel](https://github.com/dxli94/WLASL)
- [Kaggle dataset](https://www.kaggle.com/datasets/risangbaskoro/wlasl-processed)

---

## ✅ TÂCHE TERMINÉE!

Une fois que vous avez:
1. ✅ Base de données créée et peuplée
2. ✅ Scripts Python fonctionnels
3. ✅ Documentation partagée
4. ✅ Statistiques vérifiées

**Vous pouvez passer à la recherche de solutions existantes!** 🔍

Voir la section "TÂCHE SUPPLÉMENTAIRE" dans le document original pour les détails sur la recherche comparative.

---

## 🤝 SUPPORT

Si vous rencontrez des problèmes:
1. Vérifiez la section DÉPANNAGE ci-dessus
2. Consultez les logs d'erreur MySQL
3. Testez chaque étape individuellement
4. Contactez votre équipe pour assistance

---

**Créé par: Personne 1**  
**Date: Février 2026**  
**Projet: ASL Recognition - WLASL Dataset**
