import sqlite3
import threading
import time
from datetime import datetime
from supabase import create_client, Client
from typing import Optional, Dict, Any, List
import json

from config import SUPABASE_URL, SUPABASE_KEY, LOCAL_DB, SYNC_INTERVAL

class SyncManager:
    """Gestionnaire de synchronisation entre SQLite local et Supabase"""
    
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.local_db = LOCAL_DB
        self.sync_thread: Optional[threading.Thread] = None
        self.is_syncing = False
        self.last_sync: Optional[datetime] = None
        
    # ============ CONNEXION & INITIALISATION ============
    
    def get_local_connection(self):
        """Obtenir une connexion à la base locale"""
        return sqlite3.connect(self.local_db)
    
    def init_local_tables(self):
        """Initialise les tables locales avec structure complète"""
        conn = self.get_local_connection()
        cursor = conn.cursor()
        
        try:
            # Table Users
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS User (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    identifiant TEXT NOT NULL UNIQUE,
                    passwords TEXT NOT NULL,
                    nom TEXT NOT NULL,
                    prenom TEXT NOT NULL,
                    email TEXT NOT NULL,
                    telephone TEXT NOT NULL,
                    etablissement TEXT NOT NULL,
                    titre TEXT NOT NULL,
                    theme TEXT DEFAULT 'light',
                    language TEXT DEFAULT 'fr',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table Students
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Students (
                    nom TEXT NOT NULL,
                    prenom TEXT NOT NULL,
                    matricule TEXT NOT NULL,
                    date_naissance TEXT NOT NULL,
                    sexe TEXT NOT NULL,
                    classe TEXT NOT NULL,
                    etablissement TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(matricule, etablissement)
                )
            """)
            
            # Table Matieres
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Matieres (
                    nom TEXT NOT NULL,
                    genre TEXT NOT NULL,
                    etablissement TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(nom, etablissement)
                )
            """)
            
            # Table Teacher
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Teacher (
                    ident TEXT NOT NULL UNIQUE,
                    pass TEXT NOT NULL,
                    matiere TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table Notes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Notes (
                    classe TEXT NOT NULL,
                    matricule TEXT NOT NULL,
                    matiere TEXT NOT NULL,
                    coefficient TEXT NOT NULL,
                    note_interrogation TEXT NOT NULL,
                    note_devoir TEXT NOT NULL,
                    note_composition TEXT NOT NULL,
                    moyenne TEXT,
                    date_saisie TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(matricule, matiere, classe)
                )
            """)

            # Table Classes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Class (
                    nom TEXT NOT NULL,
                    etablissement TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(nom, etablissement)
                )
            """)
            
            # Table de métadonnées de sync
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_metadata (
                    table_name TEXT PRIMARY KEY,
                    last_sync TIMESTAMP,
                    sync_status TEXT DEFAULT 'pending'
                )
            """)
            
            conn.commit()
            print("✅ Tables locales initialisées")
                
        except Exception as e:
            print(f"❌ Erreur initialisation tables: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    # ============ SYNC AU LOGIN ============
    
    def sync_on_login(self, callback=None):
        """
        Synchronisation lors de la connexion
        1. Charge TOUS les Users
        2. Après login, charge données de l'établissement
        """
        try:
            print("🔄 Sync au login - Chargement Users...")
            
            # Charger tous les users
            self.sync_table_from_supabase("User")
            
            if callback:
                callback("Users chargés")
            
            print("✅ Sync login terminé")
            return True
            
        except Exception as e:
            print(f"❌ Erreur sync login: {e}")
            return False
    
    def sync_etablissement_data(self, etablissement: str, callback=None):
        """
        Charge toutes les données d'un établissement spécifique
        """
        try:
            print(f"🔄 Chargement données: {etablissement}")
            
            # Tables avec colonne etablissement
            tables_with_etablissement = ["Students", "Matieres", "Class"]
            
            for table in tables_with_etablissement:
                if callback:
                    callback(f"Chargement {table}...")
                
                self.sync_table_from_supabase(
                    table, 
                    filter_col="etablissement",
                    filter_val=etablissement
                )
            
            # Teacher : récupérer via les profs de l'établissement
            if callback:
                callback("Chargement Teacher...")
            self._sync_teachers_for_etablissement(etablissement)
            
            # Notes : récupérer via les classes
            if callback:
                callback("Chargement Notes...")
            self._sync_notes_for_etablissement(etablissement)
            
            print(f"✅ Données {etablissement} chargées")
            return True
            
        except Exception as e:
            print(f"❌ Erreur sync établissement: {e}")
            return False
    
    def _sync_teachers_for_etablissement(self, etablissement: str):
        """Synchronise les enseignants d'un établissement"""
        try:
            # Récupérer les identifiants des profs de cet établissement
            conn = self.get_local_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT identifiant FROM User WHERE etablissement = ? AND titre = 'prof'",
                (etablissement,)
            )
            prof_idents = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if not prof_idents:
                print(f"ℹ️ Aucun prof pour {etablissement}")
                return
            
            # Récupérer les teachers depuis Supabase pour ces identifiants
            response = self.supabase.table("Teacher").select("*").in_("ident", prof_idents).execute()
            teachers = response.data
            
            if not teachers:
                print(f"ℹ️ Aucun teacher trouvé pour {etablissement}")
                return
            
            # Insérer/Mettre à jour en local
            conn = self.get_local_connection()
            cursor = conn.cursor()
            
            for teacher in teachers:
                cursor.execute(
                    "SELECT 1 FROM Teacher WHERE ident = ? LIMIT 1",
                    (teacher['ident'],)
                )
                exists = cursor.fetchone()
                
                if exists:
                    # UPDATE
                    cursor.execute(
                        "UPDATE Teacher SET pass = ?, matiere = ?, updated_at = CURRENT_TIMESTAMP WHERE ident = ?",
                        (teacher['pass'], teacher['matiere'], teacher['ident'])
                    )
                else:
                    # INSERT
                    cursor.execute(
                        "INSERT INTO Teacher (ident, pass, matiere) VALUES (?, ?, ?)",
                        (teacher['ident'], teacher['pass'], teacher['matiere'])
                    )
            
            conn.commit()
            conn.close()
            print(f"✅ Teacher: {len(teachers)} enseignants synchronisés")
            
        except Exception as e:
            print(f"❌ Erreur sync teachers: {e}")
    
    def _sync_notes_for_etablissement(self, etablissement: str):
        """Synchronise les notes d'un établissement"""
        try:
            # Récupérer les classes de cet établissement
            conn = self.get_local_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT classe FROM Students WHERE etablissement = ?",
                (etablissement,)
            )
            classes = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if not classes:
                print(f"ℹ️ Aucune classe pour {etablissement}")
                return
            
            # Récupérer les notes depuis Supabase pour ces classes
            response = self.supabase.table("Notes").select("*").in_("classe", classes).execute()
            notes = response.data
            
            if not notes:
                print(f"ℹ️ Aucune note trouvée pour {etablissement}")
                return
            
            # Insérer/Mettre à jour en local
            conn = self.get_local_connection()
            cursor = conn.cursor()
            
            for note in notes:
                cursor.execute(
                    "SELECT 1 FROM Notes WHERE matricule = ? AND matiere = ? AND classe = ? LIMIT 1",
                    (note['matricule'], note['matiere'], note['classe'])
                )
                exists = cursor.fetchone()
                
                if exists:
                    # UPDATE
                    cursor.execute("""
                        UPDATE Notes SET 
                            coefficient = ?, note_interrogation = ?, note_devoir = ?, 
                            note_composition = ?, moyenne = ?, date_saisie = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE matricule = ? AND matiere = ? AND classe = ?
                    """, (
                        note['coefficient'], note['note_interrogation'], note['note_devoir'],
                        note['note_composition'], note.get('moyenne'), note.get('date_saisie'),
                        note['matricule'], note['matiere'], note['classe']
                    ))
                else:
                    # INSERT
                    cursor.execute("""
                        INSERT INTO Notes (classe, matricule, matiere, coefficient, 
                                         note_interrogation, note_devoir, note_composition, 
                                         moyenne, date_saisie)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        note['classe'], note['matricule'], note['matiere'], note['coefficient'],
                        note['note_interrogation'], note['note_devoir'], note['note_composition'],
                        note.get('moyenne'), note.get('date_saisie')
                    ))
            
            conn.commit()
            conn.close()
            print(f"✅ Notes: {len(notes)} notes synchronisées")
            
        except Exception as e:
            print(f"❌ Erreur sync notes: {e}")
    
    # ============ SYNC TABLES ============
    
    def sync_table_from_supabase(self, table_name: str, 
                                  filter_col: str = None, 
                                  filter_val: str = None):
        """
        Synchronise une table depuis Supabase vers local
        """
        try:
            # Récupérer depuis Supabase
            query = self.supabase.table(table_name).select("*")
            
            if filter_col and filter_val:
                query = query.eq(filter_col, filter_val)
            
            response = query.execute()
            remote_data = response.data
            
            if not remote_data:
                print(f"ℹ️ Aucune donnée pour {table_name}")
                return
            
            # Insérer/Mettre à jour en local
            conn = self.get_local_connection()
            cursor = conn.cursor()
            
            for row in remote_data:
                # Supprimer 'id' pour éviter les conflits
                row_data = {k: v for k, v in row.items() if k not in ['id', 'created_at', 'updated_at']}
                
                # Construire la requête INSERT OR REPLACE
                columns = ', '.join(row_data.keys())
                placeholders = ', '.join(['?' for _ in row_data])
                
                # Déterminer la clé unique selon la table
                if table_name == "User":
                    unique_check = "identifiant = ?"
                    unique_val = row_data.get('identifiant')
                elif table_name in ["Students", "Notes"]:
                    unique_check = "matricule = ? AND etablissement = ?" if table_name == "Students" else "matricule = ? AND matiere = ? AND classe = ?"
                    unique_val = (row_data.get('matricule'), row_data.get('etablissement')) if table_name == "Students" else (row_data.get('matricule'), row_data.get('matiere'), row_data.get('classe'))
                elif table_name in ["Matieres", "Class"]:
                    unique_check = "nom = ? AND etablissement = ?"
                    unique_val = (row_data.get('nom'), row_data.get('etablissement'))
                elif table_name == "Teacher":
                    unique_check = "ident = ?"
                    unique_val = row_data.get('ident')
                else:
                    unique_check = None
                
                if unique_check:
                    # Vérifier existence
                    if isinstance(unique_val, tuple):
                        cursor.execute(f"SELECT 1 FROM {table_name} WHERE {unique_check} LIMIT 1", unique_val)
                    else:
                        cursor.execute(f"SELECT 1 FROM {table_name} WHERE {unique_check} LIMIT 1", (unique_val,))
                                    
                    exists = cursor.fetchone()
                    
                    if exists:
                        # UPDATE
                        set_clause = ', '.join([f"{k} = ?" for k in row_data.keys()])
                        values = list(row_data.values())
                        
                        if isinstance(unique_val, tuple):
                            values.extend(unique_val)
                            cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE {unique_check}", values)
                        else:
                            values.append(unique_val)
                            cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE {unique_check}", values)
                    else:
                        # INSERT
                        cursor.execute(
                            f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})",
                            list(row_data.values())
                        )
                else:
                    # INSERT simple
                    cursor.execute(
                        f"INSERT OR REPLACE INTO {table_name} ({columns}) VALUES ({placeholders})",
                        list(row_data.values())
                    )
            
            conn.commit()
            conn.close()
            
            print(f"✅ {table_name}: {len(remote_data)} lignes synchronisées")
            
        except Exception as e:
            print(f"❌ Erreur sync {table_name}: {e}")
    
    def sync_table_to_supabase(self, table_name: str, 
                               filter_col: str = None, 
                               filter_val: str = None):
        """
        Synchronise une table depuis local vers Supabase
        """
        try:
            conn = self.get_local_connection()
            cursor = conn.cursor()
            
            # Récupérer données locales modifiées
            query = f"SELECT * FROM {table_name}"
            params = []
            
            if filter_col and filter_val:
                query += f" WHERE {filter_col} = ?"
                params.append(filter_val)
            
            cursor.execute(query, params)
            columns = [description[0] for description in cursor.description]
            local_data = cursor.fetchall()
            
            conn.close()
            
            if not local_data:
                return
            
            # Préparer les données pour Supabase
            for row in local_data:
                row_dict = dict(zip(columns, row))
                
                # Supprimer 'id', 'created_at', 'updated_at' locaux
                for key in ['id', 'created_at', 'updated_at', 'last_sync']:
                    row_dict.pop(key, None)
                
                # Upsert vers Supabase
                try:
                    self.supabase.table(table_name).upsert(row_dict).execute()
                except Exception as e:
                    print(f"⚠️ Erreur upsert {table_name}: {e}")
            
            print(f"✅ {table_name}: {len(local_data)} lignes envoyées à Supabase")
            
        except Exception as e:
            print(f"❌ Erreur sync vers Supabase {table_name}: {e}")
    
    # ============ SYNC AUTOMATIQUE ============
    
    def start_auto_sync(self, etablissement: str):
        """
        Démarre la synchronisation automatique toutes les 10 minutes
        """
        if self.is_syncing:
            print("⚠️ Sync déjà en cours")
            return
        
        self.is_syncing = True
        
        def sync_loop():
            while self.is_syncing:
                try:
                    print(f"🔄 Sync auto - {datetime.now()}")
                    
                    # Sync User (tous)
                    self.sync_table_from_supabase("User")
                    self.sync_table_to_supabase("User")
                    
                    # Tables avec établissement
                    for table in ["Students", "Matieres", "Class"]:
                        self.sync_table_from_supabase(
                            table,
                            filter_col="etablissement",
                            filter_val=etablissement
                        )
                        self.sync_table_to_supabase(
                            table,
                            filter_col="etablissement",
                            filter_val=etablissement
                        )
                    
                    # Teacher : via les profs de l'établissement
                    self._sync_teachers_for_etablissement(etablissement)
                    self._sync_teachers_to_supabase(etablissement)
                    
                    # Notes : via les classes
                    self._sync_notes_for_etablissement(etablissement)
                    self._sync_notes_to_supabase(etablissement)
                    
                    self.last_sync = datetime.now()
                    print(f"✅ Sync auto terminé - {self.last_sync}")
                    
                except Exception as e:
                    print(f"❌ Erreur sync auto: {e}")
                
                # Attendre 10 minutes
                time.sleep(SYNC_INTERVAL)
        
        self.sync_thread = threading.Thread(target=sync_loop, daemon=True)
        self.sync_thread.start()
        print("✅ Sync automatique démarré (10 min)")
    
    def _sync_teachers_to_supabase(self, etablissement: str):
        """Envoie les teachers vers Supabase"""
        try:
            conn = self.get_local_connection()
            cursor = conn.cursor()
            
            # Récupérer les identifiants des profs
            cursor.execute(
                "SELECT identifiant FROM User WHERE etablissement = ? AND titre = 'prof'",
                (etablissement,)
            )
            prof_idents = [row[0] for row in cursor.fetchall()]
            
            if not prof_idents:
                conn.close()
                return
            
            # Récupérer les teachers locaux
            placeholders = ','.join(['?' for _ in prof_idents])
            cursor.execute(f"SELECT * FROM Teacher WHERE ident IN ({placeholders})", prof_idents)
            columns = [description[0] for description in cursor.description]
            teachers = cursor.fetchall()
            
            conn.close()
            
            for teacher in teachers:
                teacher_dict = dict(zip(columns, teacher))
                teacher_dict.pop('created_at', None)
                teacher_dict.pop('updated_at', None)
                
                try:
                    self.supabase.table("Teacher").upsert(teacher_dict).execute()
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Erreur sync teachers to Supabase: {e}")
    
    def _sync_notes_to_supabase(self, etablissement: str):
        """Envoie les notes vers Supabase"""
        try:
            conn = self.get_local_connection()
            cursor = conn.cursor()
            
            # Récupérer les classes
            cursor.execute(
                "SELECT DISTINCT classe FROM Students WHERE etablissement = ?",
                (etablissement,)
            )
            classes = [row[0] for row in cursor.fetchall()]
            
            if not classes:
                conn.close()
                return
            
            # Récupérer les notes locales
            placeholders = ','.join(['?' for _ in classes])
            cursor.execute(f"SELECT * FROM Notes WHERE classe IN ({placeholders})", classes)
            columns = [description[0] for description in cursor.description]
            notes = cursor.fetchall()
            
            conn.close()
            
            for note in notes:
                note_dict = dict(zip(columns, note))
                note_dict.pop('created_at', None)
                note_dict.pop('updated_at', None)
                
                try:
                    self.supabase.table("Notes").upsert(note_dict).execute()
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Erreur sync notes to Supabase: {e}")
    
    def stop_auto_sync(self):
        """Arrête la synchronisation automatique"""
        self.is_syncing = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        print("🛑 Sync automatique arrêté")


# Instance globale
sync_manager = SyncManager()