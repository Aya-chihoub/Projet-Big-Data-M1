"""
Script pour créer automatiquement la base de données et le schéma
Fonctionne sur Windows/PowerShell sans problème
"""

import mysql.connector
from mysql.connector import Error
import os

def create_database_and_schema():
    """Créer la base de données et exécuter le schéma SQL"""
    
    def _parse_sql_commands(sql_text):
        """Parser les commandes SQL en ignorant les commentaires"""
        commands = []
        current_command = []
        
        for line in sql_text.split('\n'):
            # Ignorer les commentaires
            if line.strip().startswith('--') or line.strip().startswith('#'):
                continue
            
            # Ignorer les lignes vides
            if not line.strip():
                continue
            
            # Ignorer DELIMITER, USE, SHOW
            if any(line.strip().upper().startswith(x) for x in ['DELIMITER', 'USE ', 'SHOW ']):
                continue
            
            current_command.append(line)
            
            # Si la ligne se termine par ';', c'est la fin de la commande
            if line.strip().endswith(';'):
                command = '\n'.join(current_command)
                commands.append(command)
                current_command = []
        
        return commands
    
    print("=" * 70)
    print("  CRÉATION AUTOMATIQUE DE LA BASE DE DONNÉES")
    print("=" * 70)
    
    # Configuration
    host = "localhost"
    user = "root"
    password = input("\nEntrez le mot de passe MySQL root: ")
    database = "asl_recognition"
    schema_file = "database/schema.sql"
    
    # Vérifier que le fichier SQL existe
    if not os.path.exists(schema_file):
        print(f"\n❌ Fichier {schema_file} non trouvé!")
        print(f"   Assurez-vous que schema.sql est dans le même dossier")
        return False
    
    try:
        # Étape 1: Connexion au serveur MySQL
        print("\n[1/4] Connexion au serveur MySQL...")
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        
        if connection.is_connected():
            print(f"✅ Connecté au serveur MySQL")
            cursor = connection.cursor()
            
            # Étape 2: Créer la base de données
            print(f"\n[2/4] Création de la base '{database}'...")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
            print(f"✅ Base de données créée/vérifiée")
            
            # Étape 3: Utiliser la base
            print(f"\n[3/4] Sélection de la base '{database}'...")
            cursor.execute(f"USE {database}")
            print(f"✅ Base sélectionnée")
            
            # Étape 4: Lire et exécuter le fichier SQL
            print(f"\n[4/4] Exécution du schéma SQL...")
            
            with open(schema_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Séparer le contenu en sections
            # 1. Tables et vues (avant DELIMITER)
            # 2. Procédures stockées (entre DELIMITER // et DELIMITER ;)
            
            parts = sql_content.split('DELIMITER //')
            
            # Partie 1: Tables et vues
            print("   Création des tables et vues...")
            if parts[0]:
                commands = _parse_sql_commands(parts[0])
                commands_executed = 0
                for cmd in commands:
                    if cmd:
                        try:
                            cursor.execute(cmd)
                            commands_executed += 1
                        except Error as e:
                            if "already exists" not in str(e).lower():
                                print(f"   ⚠️  Erreur: {str(e)[:80]}")
                
                connection.commit()
                print(f"   ✅ {commands_executed} commandes exécutées")
            
            # Partie 2: Procédures stockées
            if len(parts) > 1:
                print("   Création des procédures stockées...")
                procedure_section = parts[1].split('DELIMITER ;')[0]
                
                # Séparer les procédures par '//'
                procedures = [p.strip() for p in procedure_section.split('//') if p.strip()]
                
                proc_count = 0
                for proc in procedures:
                    if proc and ('CREATE PROCEDURE' in proc.upper() or 'CREATE FUNCTION' in proc.upper()):
                        try:
                            cursor.execute(proc)
                            proc_count += 1
                        except Error as e:
                            if "already exists" not in str(e).lower():
                                print(f"   ⚠️  Erreur procédure: {str(e)[:80]}")
                
                connection.commit()
                print(f"   ✅ {proc_count} procédures créées")
            
            print(f"✅ Schéma SQL exécuté avec succès")
            
            # Vérifier les tables créées
            print("\n📊 Tables créées:")
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            if tables:
                for table in tables:
                    print(f"   ✅ {table[0]}")
            else:
                print("   ⚠️  Aucune table trouvée")
            
            # Vérifier les vues
            print("\n👁️  Vues créées:")
            cursor.execute("SHOW FULL TABLES WHERE Table_type = 'VIEW'")
            views = cursor.fetchall()
            
            if views:
                for view in views:
                    print(f"   ✅ {view[0]}")
            else:
                print("   ℹ️  Aucune vue trouvée")
            
            # Vérifier les procédures stockées
            print("\n⚙️  Procédures stockées:")
            cursor.execute("SHOW PROCEDURE STATUS WHERE Db = %s", (database,))
            procedures = cursor.fetchall()
            
            if procedures:
                for proc in procedures:
                    print(f"   ✅ {proc[1]}")
            else:
                print("   ℹ️  Aucune procédure trouvée")
            
            cursor.close()
            connection.close()
            
            print("\n" + "=" * 70)
            print("✅ BASE DE DONNÉES CRÉÉE AVEC SUCCÈS!")
            print("=" * 70)
            print(f"\nVous pouvez maintenant:")
            print(f"1. Exécuter: python populate_database_v2.py")
            print(f"2. Ou tester: python test_mysql.py")
            
            return True
            
    except Error as e:
        print(f"\n❌ ERREUR MySQL: {e}")
        print(f"\n🔧 SOLUTIONS:")
        print(f"1. Vérifiez votre mot de passe")
        print(f"2. Vérifiez que MySQL est démarré (net start MySQL80)")
        print(f"3. Consultez DEPANNAGE_MYSQL.md")
        return False
    
    except FileNotFoundError:
        print(f"\n❌ Fichier {schema_file} non trouvé!")
        return False
    
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {e}")
        return False


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║           CRÉATION AUTOMATIQUE DE LA BASE DE DONNÉES                ║
    ║                Compatible PowerShell Windows                         ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    create_database_and_schema()
    
    input("\nAppuyez sur Entrée pour quitter...")