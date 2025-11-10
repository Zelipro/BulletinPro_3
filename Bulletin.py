import flet as ft
from Zeli_Dialog import ZeliDialog2
import sqlite3
from datetime import datetime
from weasyprint import HTML
from jinja2 import Template
import os
from pathlib import Path

def Generation_Bulletin(page, Donner):
    """Génération des bulletins scolaires avec HTML/CSS"""
    Dialog = ZeliDialog2(page)
    
    if Donner.get("role") not in ["admin", "prof"]:
        Dialog.alert_dialog(title="Accès refusé", message="Vous n'avez pas les permissions nécessaires.")
        return
    
    def get_documents_folder():
        """Retourne le chemin du dossier Documents selon la plateforme"""
        home = Path.home()
        
        # Windows
        if os.name == 'nt':
            documents = home / "Documents"
        # macOS et Linux
        else:
            documents = home / "Documents"
            # Si le dossier Documents n'existe pas, utiliser le home
            if not documents.exists():
                documents = home / "documents"  # Essayer en minuscule
                if not documents.exists():
                    documents = home  # Fallback sur home
        
        return documents
    
    def Return(Ident):
        con = None
        try:
            con = sqlite3.connect("base.db")
            cur = con.cursor()
            cur.execute(f"SELECT {Ident} FROM User WHERE identifiant = ? AND titre = ? AND passwords = ?",
                (Donner.get("ident"), Donner.get("role"), Donner.get("pass")))
            donne = cur.fetchall()
            cur.close()
            return donne
        except Exception as e:
            Dialog.error_toast(f"Erreur: {str(e)}")
            return []
        finally:
            if con:
                con.close()
    
    def init_trimestre_table():
        con = None
        try:
            con = sqlite3.connect("base.db")
            cur = con.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS Trimestre_moyen_save (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matricule TEXT NOT NULL,
                moyenne REAL NOT NULL,
                annee_scolaire TEXT NOT NULL,
                periode TEXT NOT NULL,
                UNIQUE(matricule, annee_scolaire, periode))""")
            con.commit()
        except:
            pass
        finally:
            if con:
                con.close()
    
    def calculate_moyenne_matiere(note_interro, note_devoir, note_compo):
        try:
            interro, devoir, compo = float(note_interro), float(note_devoir), float(note_compo)
            return round((((interro + devoir) / 2) + compo) / 2, 2)
        except:
            return 0.0
    
    def calculate_moyenne_generale(notes):
        try:
            total_points, total_coef = 0, 0
            for note in notes:
                moyenne_matiere = calculate_moyenne_matiere(note[5], note[6], note[7])
                coef = float(note[4])
                total_points += moyenne_matiere * coef
                total_coef += coef
            return round(total_points / total_coef, 2) if total_coef > 0 else 0.0
        except:
            return 0.0
    
    def get_appreciation(moyenne):
        if moyenne >= 18: return "Excellent"
        elif moyenne >= 16: return "Très bien"
        elif moyenne >= 14: return "Bien"
        elif moyenne >= 12: return "Assez bien"
        elif moyenne >= 10: return "Passable"
        elif moyenne >= 8: return "Insuffisant"
        else: return "Très insuffisant"
    
    def get_matiere_info(matiere_nom, etablissement):
        """Récupère les informations complètes d'une matière"""
        con = None
        try:
            con = sqlite3.connect("base.db")
            cur = con.cursor()
            
            # Normaliser le nom de la matière recherchée
            matiere_search = matiere_nom.strip().lower()
            
            # Recherche exacte d'abord
            cur.execute("""
                SELECT nom, genre 
                FROM Matieres 
                WHERE LOWER(TRIM(nom)) = ? 
                AND etablissement = ?
            """, (matiere_search, etablissement))
            
            result = cur.fetchone()
            
            # Si pas trouvé, recherche approximative
            if not result:
                cur.execute("""
                    SELECT nom, genre 
                    FROM Matieres 
                    WHERE LOWER(TRIM(nom)) LIKE ? 
                    AND etablissement = ? 
                    LIMIT 1
                """, (f"%{matiere_search}%", etablissement))
                result = cur.fetchone()
            
            # Si toujours pas trouvé, chercher sans l'établissement
            if not result:
                cur.execute("""
                    SELECT nom, genre 
                    FROM Matieres 
                    WHERE LOWER(TRIM(nom)) = ?
                    LIMIT 1
                """, (matiere_search,))
                result = cur.fetchone()
            
            if result:
                nom_complet = result[0].strip()
                genre = result[1].strip().lower() if result[1] else ""
                
                # Déterminer la catégorie selon le genre
                if any(keyword in genre for keyword in ["scien", "science", "scientifique"]):
                    categorie = "Scientifique"
                elif any(keyword in genre for keyword in ["litt", "littérature", "littéraire"]):
                    categorie = "Littéraire"
                elif any(keyword in genre for keyword in ["art", "artistique"]):
                    categorie = "Facultative"
                else:
                    categorie = "Facultative"
                
                return nom_complet, categorie
            
            # Si aucune matière trouvée, retourner les valeurs par défaut
            print(f"⚠️ Matière non trouvée: {matiere_nom}")
            return matiere_nom, "Facultative"
            
        except Exception as e:
            print(f"❌ Erreur get_matiere_info: {e}")
            return matiere_nom, "Facultative"
        finally:
            if con:
                con.close()    
    
    def calculate_matiere_rank(matiere, classe, moyenne_eleve):
        con = None
        try:
            con = sqlite3.connect("base.db")
            cur = con.cursor()
            cur.execute("SELECT matricule, note_interrogation, note_devoir, note_composition FROM Notes WHERE classe = ? AND matiere = ?",
                (classe, matiere))
            notes_matiere = cur.fetchall()
            moyennes = [(n[0], calculate_moyenne_matiere(n[1], n[2], n[3])) for n in notes_matiere]
            moyennes.sort(key=lambda x: x[1], reverse=True)
            for i, (mat, moy) in enumerate(moyennes, 1):
                if abs(moy - moyenne_eleve) < 0.01:
                    return f"{i}er" if i == 1 else f"{i}e"
            return "N/A"
        except:
            return "N/A"
        finally:
            if con:
                con.close()
    
    def save_trimestre_moyenne(matricule, moyenne, annee_scolaire, periode):
        con = None
        try:
            con = sqlite3.connect("base.db")
            cur = con.cursor()
            cur.execute("INSERT OR REPLACE INTO Trimestre_moyen_save (matricule, moyenne, annee_scolaire, periode) VALUES (?, ?, ?, ?)",
                (matricule, moyenne, annee_scolaire, periode))
            con.commit()
        except:
            pass
        finally:
            if con:
                con.close()
    
    def get_previous_moyennes(matricule, annee_scolaire, periode_actuelle):
        con = None
        try:
            con = sqlite3.connect("base.db")
            cur = con.cursor()
            cur.execute("SELECT periode, moyenne FROM Trimestre_moyen_save WHERE matricule = ? AND annee_scolaire = ? AND periode != ? ORDER BY id",
                (matricule, annee_scolaire, periode_actuelle))
            return cur.fetchall()
        except:
            return []
        finally:
            if con:
                con.close()
    
    def load_classes_with_students():
        Etat = Return("etablissement")
        if not Etat:
            return []
        con = None
        try:
            con = sqlite3.connect("base.db")
            cur = con.cursor()
            cur.execute("SELECT DISTINCT classe, COUNT(*) as effectif FROM Students WHERE etablissement = ? GROUP BY classe ORDER BY classe",
                (Etat[0][0],))
            return cur.fetchall()
        except:
            return []
        finally:
            if con:
                con.close()
    
    def load_students_by_class(classe_nom):
        Etat = Return("etablissement")
        if not Etat:
            return []
        con = None
        try:
            con = sqlite3.connect("base.db")
            cur = con.cursor()
            cur.execute("SELECT * FROM Students WHERE classe = ? AND etablissement = ? ORDER BY nom, prenom",
                (classe_nom, Etat[0][0]))
            return cur.fetchall()
        except:
            return []
        finally:
            if con:
                con.close()
    
    def get_student_notes(matricule, classe):
        con = None
        try:
            con = sqlite3.connect("base.db")
            cur = con.cursor()
            cur.execute("SELECT * FROM Notes WHERE matricule = ? AND classe = ? ORDER BY matiere", (matricule, classe))
            return cur.fetchall()
        except:
            return []
        finally:
            if con:
                con.close()
    
    def get_teacher_by_subject(matiere, etablissement):
        con = None
        try:
            con = sqlite3.connect("base.db")
            cur = con.cursor()
            cur.execute("SELECT u.nom FROM Teacher t JOIN User u ON t.ident = u.identifiant WHERE t.matiere = ? AND u.etablissement = ? LIMIT 1",
                (matiere, etablissement))
            result = cur.fetchone()
            return result[0] if result else "N/A"
        except:
            return "N/A"
        finally:
            if con:
                con.close()
    
    def calculate_class_rank(moyenne, classe, annee, notes_list):
        con = None
        try:
            con = sqlite3.connect("base.db")
            cur = con.cursor()
            cur.execute("SELECT DISTINCT matricule FROM Notes WHERE classe = ?", (classe,))
            matricules = cur.fetchall()
            moyennes = []
            for (mat,) in matricules:
                cur.execute("SELECT * FROM Notes WHERE matricule = ? AND classe = ?", (mat, classe))
                notes_eleve = cur.fetchall()
                moy = calculate_moyenne_generale(notes_eleve)
                moyennes.append((mat, moy))
            moyennes.sort(key=lambda x: x[1], reverse=True)
            for i, (mat, moy) in enumerate(moyennes, 1):
                if abs(moy - moyenne) < 0.01:
                    return f"{i}e" if i > 1 else "1er"
            return "N/A"
        except:
            return "N/A"
        finally:
            if con:
                con.close()
    
    def calculate_class_stats(classe):
        con = None
        try:
            con = sqlite3.connect("base.db")
            cur = con.cursor()
            cur.execute("SELECT DISTINCT matricule FROM Notes WHERE classe = ?", (classe,))
            matricules = cur.fetchall()
            moyennes = []
            for (mat,) in matricules:
                cur.execute("SELECT * FROM Notes WHERE matricule = ? AND classe = ?", (mat, classe))
                notes_eleve = cur.fetchall()
                moy = calculate_moyenne_generale(notes_eleve)
                moyennes.append(moy)
            if moyennes:
                return {'plus_forte': round(max(moyennes), 2), 'plus_faible': round(min(moyennes), 2),
                        'moyenne_classe': round(sum(moyennes) / len(moyennes), 2)}
            return {'plus_forte': 0, 'plus_faible': 0, 'moyenne_classe': 0}
        except:
            return {'plus_forte': 0, 'plus_faible': 0, 'moyenne_classe': 0}
        finally:
            if con:
                con.close()
    
    def get_bulletin_html_template():
        return """<!DOCTYPE html><html><head><meta charset="UTF-8"><style>@page{size:A4;margin:1cm}body{font-family:Arial,sans-serif;font-size:9pt;background-color:#d4e8d4;color:#000;position:relative}body::before{content:"";position:fixed;top:-10%;left:-10%;width:120%;height:120%;background-image:url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200"><text x="10" y="30" font-family="Arial" font-size="16" fill="rgba(0,0,0,0.03)" transform="rotate(-30 200 100)">{{ etablissement }}</text></svg>');background-repeat:repeat;z-index:-1;pointer-events:none}.container{background-color:#d4e8d4;padding:10px}.header-row{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:3px}.header-left{text-align:left;flex:1;padding-right:15px}.header-center{text-align:center;flex:0.5;display:flex;justify-content:center;align-items:center}.header-right{text-align:right;flex:1;padding-left:15px}.title{background-color:#4CAF50;color:white;text-align:center;padding:8px;font-size:11pt;font-weight:bold;margin:10px 0}.info-section{background-color:#e8f5e9;padding:8px;margin-bottom:10px;border:1px solid #999}.info-row{display:flex;justify-content:space-between;margin-bottom:3px}table{width:100%;border-collapse:collapse;margin-bottom:10px;font-size:7.5pt}th{background-color:#a8d5ba;border:1px solid #666;padding:4px 2px;text-align:center;font-weight:bold}td{border:1px solid #666;padding:3px 2px;text-align:center}.section-title{background-color:#e8f5e9;font-weight:bold;text-align:left;padding-left:5px}.subtotal-row{background-color:#f0f0f0;font-weight:bold}.total-row{background-color:#fff9e6;font-weight:bold}.decision-section{background-color:#fff9e6;border:1px solid #666;padding:8px;margin-top:10px}.decision-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.signature-space{height:40px;border-bottom:1px solid #999;margin-top:10px}.footer{text-align:center;font-size:7pt;margin-top:10px;color:#666}.matiere-name{text-align:left!important;padding-left:5px}.prof-name{font-size:7pt}.header-spacing{line-height:1.4;margin-bottom:3px}</style></head><body><div class="container"><div class="header-row"><div class="header-left"><div class="header-spacing">MINISTÈRE DES ENSEIGNEMENTS PRIMAIRE,</div><div class="header-spacing">SECONDAIRE, TECHNIQUE ET DE L'ARTISANAT</div><div style="margin-top:8px">&nbsp;</div><div class="header-spacing"><strong>{{etablissement}}</strong></div><div class="header-spacing" style="font-size:7pt">{{contact_etablissement}}</div></div><div class="header-center">{%if logo_base64%}<img src="{{logo_base64}}" alt="Logo" style="max-width:80px;max-height:60px">{%endif%}</div><div class="header-right"><div class="header-spacing"><strong>RÉPUBLIQUE TOGOLAISE</strong></div><div class="header-spacing">Travail-Liberté-Patrie</div><div style="margin-top:8px">&nbsp;</div><div class="header-spacing" style="font-weight:bold;color:#2E7D32;font-size:9pt">{{devise_etablissement}}</div><div class="header-spacing" style="margin-top:5px">Année scolaire : {{annee_scolaire}}</div></div></div><div class="title">BULLETIN DE NOTES DU {{periode|upper}}</div><div class="info-section"><div class="info-row"><div>Classe : {{classe}}</div><div>Effectif : {{effectif}}</div></div><div class="info-row"><div>NOM ET PRENOMS DE L'ELEVE : {{nom}} {{prenom}}</div><div>Né(e) le : {{date_naissance}}</div></div><div class="info-row"><div>N° Mle : {{matricule}}</div><div>Sexe : {{sexe}}</div></div></div><table><thead><tr><th>Matières</th><th>Inter.</th><th>Dev.</th><th>M. Clas</th><th>Compo.</th><th>Note<br>/20</th><th>Coef.</th><th>Note<br>coef.</th><th>Rg</th><th>Professeur</th><th>Apprécia*</th><th>Signature</th></tr></thead><tbody>{%if matieres_litteraires%}<tr><td colspan="12" class="section-title">MATIÈRES LITTÉRAIRES</td></tr>{%for matiere in matieres_litteraires%}<tr><td class="matiere-name">{{matiere.nom}}</td><td>{{matiere.interro}}</td><td>{{matiere.devoir}}</td><td>{{matiere.compo}}</td><td>{{matiere.compo}}</td><td>{{matiere.moyenne}}</td><td>{{matiere.coef}}</td><td>{{matiere.note_coef}}</td><td>{{matiere.rang}}</td><td class="prof-name">{{matiere.professeur}}</td><td>{{matiere.appreciation}}</td><td></td></tr>{%endfor%}<tr class="subtotal-row"><td colspan="6"></td><td>{{total_coef_litt}}</td><td>{{total_points_litt}}</td><td colspan="4"></td></tr>{%endif%}{%if matieres_scientifiques%}<tr><td colspan="12" class="section-title">MATIÈRES SCIENTIFIQUES</td></tr>{%for matiere in matieres_scientifiques%}<tr><td class="matiere-name">{{matiere.nom}}</td><td>{{matiere.interro}}</td><td>{{matiere.devoir}}</td><td>{{matiere.compo}}</td><td>{{matiere.compo}}</td><td>{{matiere.moyenne}}</td><td>{{matiere.coef}}</td><td>{{matiere.note_coef}}</td><td>{{matiere.rang}}</td><td class="prof-name">{{matiere.professeur}}</td><td>{{matiere.appreciation}}</td><td></td></tr>{%endfor%}<tr class="subtotal-row"><td colspan="6"></td><td>{{total_coef_sci}}</td><td>{{total_points_sci}}</td><td colspan="4"></td></tr>{%endif%}{%if matieres_facultatives%}<tr><td colspan="12" class="section-title">MATIÈRES FACULTATIVES</td></tr>{%for matiere in matieres_facultatives%}<tr><td class="matiere-name">{{matiere.nom}}</td><td>{{matiere.interro}}</td><td>{{matiere.devoir}}</td><td>{{matiere.compo}}</td><td>{{matiere.compo}}</td><td>{{matiere.moyenne}}</td><td>{{matiere.coef}}</td><td>{{matiere.note_coef}}</td><td></td><td class="prof-name">{{matiere.professeur}}</td><td>{{matiere.appreciation}}</td><td></td></tr>{%endfor%}{%if moyenne_fac%}<tr><td colspan="6" style="text-align:left;padding-left:5px">Moyenne des Matières Facultatives</td><td>1</td><td>{{moyenne_fac}}</td><td colspan="4"></td></tr>{%endif%}{%endif%}<tr class="total-row"><td colspan="5"></td><td><strong>TOTAL</strong></td><td>{{total_coef}}</td><td>{{total_points}}</td><td colspan="4"></td></tr><tr class="total-row"><td colspan="2">{{periode}}:</td><td><strong>{{moyenne_generale}}</strong></td><td>Rg : {{rang}}</td><td colspan="2">Moyennes :</td><td colspan="3"></td><td colspan="2">Retards : 0 fois</td><td></td></tr><tr class="total-row"><td colspan="5">Moyenne du {{type_periode_lower}}</td><td><strong>{{moyenne_generale}}</strong></td><td colspan="2">Plus forte moyenne : {{stats.plus_forte}}</td><td colspan="3">Absences : 0 Heures</td><td></td></tr>{%if moyennes_precedentes%}<tr class="total-row"><td colspan="5">Moyennes précédentes</td><td colspan="3">{{moyennes_precedentes_text}}</td><td colspan="3">Plus faible moyenne : {{stats.plus_faible}}</td><td></td></tr>{%endif%}<tr class="total-row"><td colspan="5">Décision du conseil de classe</td><td colspan="6">Moyenne de la classe : {{stats.moyenne_classe}}</td><td></td></tr></tbody></table><div class="decision-section"><div class="decision-grid"><div><div><strong>DÉCISION DU CONSEIL DES PROFESSEURS</strong></div><div style="margin-top:5px"><strong>Distinctions spéciales</strong></div>{%if tableau_honneur=='OUI'%}<div>Tableau d'honneur: OUI</div>{%endif%}{%if encouragement=='OUI'%}<div>Encouragement: OUI</div>{%endif%}{%if felicitation=='OUI'%}<div>Félicitation: OUI</div>{%endif%}<div style="margin-top:10px"><strong>APPRECIATION DU CHEF D'ETABLISSEMENT</strong></div><div>{{appreciation}}</div></div><div><div>Signature du titulaire de classe</div><div class="signature-space"></div><div style="margin-top:10px">Lomé le {{date_actuelle}}</div><div style="margin-top:8px">Le {{type_responsable}}</div><div style="margin-top:3px;font-size:9pt;font-weight:bold">{{nom_responsable}}</div><div class="signature-space"></div></div></div></div><div class="footer">Édité le {{date_edition}}</div></div></body></html>"""
    
    def generate_bulletin_html(student, classe, notes, etablissement, annee, appreciation, moyenne_gen, rang,
                           periode, type_periode, effectif, devise_etablissement, logo_path, bp_info, type_responsable):
        logo_base64 = None
        if logo_path and os.path.exists(logo_path):
            try:
                import base64
                with open(logo_path, 'rb') as f:
                    logo_data = base64.b64encode(f.read()).decode()
                    ext = os.path.splitext(logo_path)[1].lower()
                    mime_type = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.svg': 'image/svg+xml'}.get(ext, 'image/png')
                    logo_base64 = f"data:{mime_type};base64,{logo_data}"
            except:
                pass
        
        # Récupérer le nom et prénom de l'admin
        admin_nom_complet = "Non disponible"
        con = None
        try:
            con = sqlite3.connect("base.db")
            cur = con.cursor()
            cur.execute(
                "SELECT nom, prenom FROM User WHERE etablissement = ? AND titre = 'admin' LIMIT 1",
                (etablissement,)
            )
            result = cur.fetchone()
            if result:
                admin_nom_complet = f"{result[0]} {result[1]}"
        except:
            pass
        finally:
            if con:
                con.close()
        
        notes_litt, notes_sci, notes_fac = [], [], []
        
        for note in notes:
            matiere_courte = str(note[3]).strip()
            matiere_nom_complet, categorie = get_matiere_info(matiere_courte, etablissement)
            moyenne_mat = calculate_moyenne_matiere(note[5], note[6], note[7])
            note_coef = moyenne_mat * float(note[4])
            prof = get_teacher_by_subject(matiere_courte, etablissement)
            apprec = get_appreciation(moyenne_mat)
            rang_mat = calculate_matiere_rank(matiere_courte, classe, moyenne_mat)
            
            matiere_data = {'nom': matiere_nom_complet, 'interro': note[5], 'devoir': note[6], 'compo': note[7],
                'moyenne': f"{moyenne_mat:.2f}", 'coef': note[4], 'note_coef': f"{note_coef:.2f}",
                'rang': rang_mat, 'professeur': prof, 'appreciation': apprec}
            
            if categorie == "Littéraire": notes_litt.append(matiere_data)
            elif categorie == "Scientifique": notes_sci.append(matiere_data)
            else: notes_fac.append(matiere_data)
        
        total_coef_litt = sum(float(m['coef']) for m in notes_litt)
        total_points_litt = sum(float(m['note_coef']) for m in notes_litt)
        total_coef_sci = sum(float(m['coef']) for m in notes_sci)
        total_points_sci = sum(float(m['note_coef']) for m in notes_sci)
        total_coef = sum(float(n[4]) for n in notes)
        total_points = sum(calculate_moyenne_matiere(n[5], n[6], n[7]) * float(n[4]) for n in notes)
        
        moyenne_fac = None
        if notes_fac:
            total_fac = sum(float(m['note_coef']) for m in notes_fac)
            coef_fac = sum(float(m['coef']) for m in notes_fac)
            if coef_fac > 0:
                moyenne_fac = f"{total_fac / coef_fac:.2f}"
        
        stats = calculate_class_stats(classe)
        moyennes_prec = get_previous_moyennes(student[2], annee, periode)
        moyennes_prec_text = "  ".join([f"{p}: {m:.2f}" for p, m in moyennes_prec]) if moyennes_prec else ""
        user_data = Return("telephone")
        contact = user_data[0][0] if user_data else "22 50 28 53"
        
        if bp_info and bp_info.strip():
            contact_info = f"{bp_info} Tel : {contact}"
        else:
            contact_info = f"Tel : {contact}"
        
        date_naissance = student[3] if len(student) > 3 and student[3] else "N/A"
        
        context = {
            'etablissement': etablissement, 
            'contact_etablissement': contact_info,
            'devise_etablissement': devise_etablissement, 
            'logo_base64': logo_base64, 
            'annee_scolaire': annee,
            'periode': periode, 
            'classe': classe, 
            'effectif': effectif, 
            'nom': student[0], 
            'prenom': student[1],
            'matricule': student[2], 
            'date_naissance': date_naissance, 
            'sexe': student[4],
            'matieres_litteraires': notes_litt, 
            'matieres_scientifiques': notes_sci, 
            'matieres_facultatives': notes_fac,
            'total_coef_litt': int(total_coef_litt) if notes_litt else 0,
            'total_points_litt': f"{total_points_litt:.2f}" if notes_litt else "0.00",
            'total_coef_sci': int(total_coef_sci) if notes_sci else 0,
            'total_points_sci': f"{total_points_sci:.2f}" if notes_sci else "0.00",
            'moyenne_fac': moyenne_fac, 
            'total_coef': int(total_coef), 
            'total_points': f"{total_points:.2f}",
            'moyenne_generale': f"{moyenne_gen:.2f}", 
            'rang': rang, 
            'type_periode_lower': type_periode.lower(),
            'stats': stats, 
            'moyennes_precedentes': len(moyennes_prec) > 0, 
            'moyennes_precedentes_text': moyennes_prec_text,
            'tableau_honneur': 'OUI' if moyenne_gen >= 10 else 'NON',
            'encouragement': 'OUI' if moyenne_gen >= 12 and moyenne_gen < 14 else 'NON',
            'felicitation': 'OUI' if moyenne_gen >= 14 else 'NON',
            'appreciation': appreciation, 
            'date_actuelle': datetime.now().strftime("%d %B %Y"),
            'date_edition': datetime.now().strftime("%d/%m/%Y"),
            'type_responsable': type_responsable,
            'nom_responsable': admin_nom_complet
        }
        
        template = Template(get_bulletin_html_template())
        return template.render(**context)
    
    def save_bulletin_pdf(html_content, filename):
        try:
            HTML(string=html_content).write_pdf(filename)
            return True
        except Exception as e:
            print(f"Erreur PDF: {e}")
            return False
    
    def open_folder(path):
        """Ouvre le dossier selon la plateforme"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(path)
            elif os.uname().sysname == 'Darwin':  # macOS
                os.system(f'open "{path}"')
            else:  # Linux
                os.system(f'xdg-open "{path}"')
        except Exception as e:
            print(f"Erreur ouverture dossier: {e}")
    
    def select_periode_and_classe():
        init_trimestre_table()
        type_periode = ft.Dropdown(label="Type de période", options=[ft.dropdown.Option("Trimestre"), ft.dropdown.Option("Semestre")],
            value="Trimestre", width=250)
        periode_dropdown = ft.Dropdown(label="Période", options=[ft.dropdown.Option("Premier Trimestre"),
            ft.dropdown.Option("Deuxième Trimestre"), ft.dropdown.Option("Troisième Trimestre")],
            value="Premier Trimestre", width=250)
        
        def update_periode_options(e):
            if type_periode.value == "Semestre":
                periode_dropdown.options = [ft.dropdown.Option("Premier Semestre"), ft.dropdown.Option("Deuxième Semestre")]
                periode_dropdown.value = "Premier Semestre"
            else:
                periode_dropdown.options = [ft.dropdown.Option("Premier Trimestre"), ft.dropdown.Option("Deuxième Trimestre"),
                    ft.dropdown.Option("Troisième Trimestre")]
                periode_dropdown.value = "Premier Trimestre"
            page.update()
        
        type_periode.on_change = update_periode_options
        annee_field = ft.TextField(label="Année scolaire", value="2023/2024", text_align="center", width=250)
        devise_field = ft.TextField(label="Devise", value="DISCIPLINE - TRAVAIL - RÉUSSITE", text_align="center", width=250)
        bp_field = ft.TextField(label="BP (Boîte Postale) - Optionnel", hint_text="Ex: 04 BP 87 LOME TOGO", text_align="center", width=250)
        
        # Choix Directeur/Proviseur
        responsable_dropdown = ft.Dropdown(
            label="Type de responsable",
            hint_text="Sélectionnez",
            options=[
                ft.dropdown.Option("Directeur"),
                ft.dropdown.Option("Proviseur"),
            ],
            value="Proviseur",
            width=250
        )
        
        logo_path_field = ft.TextField(label="Logo (optionnel)", text_align="center", width=250, read_only=True)
        selected_logo = {"path": None}
        
        def pick_logo(e):
            file_picker = ft.FilePicker(on_result=lambda r: handle_logo_selection(r))
            page.overlay.append(file_picker)
            page.update()
            file_picker.pick_files(allowed_extensions=["png", "jpg", "jpeg", "svg"], dialog_title="Logo")
        
        def handle_logo_selection(result):
            if result.files:
                selected_logo["path"] = result.files[0].path
                logo_path_field.value = result.files[0].name
                page.update()
        
        def valider_periode(e):
            if not all([type_periode.value, periode_dropdown.value, annee_field.value, devise_field.value, responsable_dropdown.value]):
                Dialog.error_toast("Champs obligatoires manquants")
                return
            Dialog.close_dialog(periode_dialog)
            show_classes_selection(
                type_periode.value, 
                periode_dropdown.value, 
                annee_field.value, 
                devise_field.value, 
                selected_logo["path"], 
                bp_field.value,
                responsable_dropdown.value
            )
        
        periode_dialog = Dialog.custom_dialog(title="📅 Configuration", content=ft.Column([
            ft.Icon(ft.Icons.CALENDAR_MONTH, size=50, color=ft.Colors.BLUE),
            ft.Text("Configurez les paramètres", size=14, text_align=ft.TextAlign.CENTER), 
            ft.Divider(),
            ft.Text("Période scolaire", size=12, weight=ft.FontWeight.BOLD), 
            type_periode, 
            periode_dropdown, 
            annee_field, 
            ft.Divider(),
            ft.Text("Personnalisation", size=12, weight=ft.FontWeight.BOLD), 
            devise_field, 
            bp_field,
            ft.Divider(),
            ft.Text("Responsable de l'établissement", size=12, weight=ft.FontWeight.BOLD),
            responsable_dropdown,
            ft.Text("💡 Le nom sera récupéré automatiquement", size=10, italic=True, color=ft.Colors.GREY_600),
            ft.Divider(),
            ft.Row([logo_path_field, ft.IconButton(icon=ft.Icons.UPLOAD_FILE, tooltip="Logo", on_click=pick_logo, bgcolor=ft.Colors.BLUE_100)], spacing=5),
            ft.Text("💡 Logo et BP optionnels", size=10, italic=True, color=ft.Colors.GREY_600)
        ], width=450, height=650, spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Annuler", icon=ft.Icons.CLOSE, on_click=lambda e: Dialog.close_dialog(periode_dialog)),
                ft.ElevatedButton("Suivant", icon=ft.Icons.ARROW_FORWARD, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE, on_click=valider_periode)
            ])
    
    def show_classes_selection(type_periode, periode, annee_scolaire, devise_etablissement, logo_path, bp_info, type_responsable):
        classes = load_classes_with_students()
        
        def create_class_card(classe):
            classe_nom, effectif = classe[0], classe[1]
            con = None
            students_with_notes = 0
            try:
                con = sqlite3.connect("base.db")
                cur = con.cursor()
                cur.execute("SELECT COUNT(DISTINCT matricule) FROM Notes WHERE classe = ?", (classe_nom,))
                result = cur.fetchone()
                students_with_notes = result[0] if result else 0
            except:
                pass
            finally:
                if con:
                    con.close()
            
            pourcentage = int((students_with_notes / effectif * 100)) if effectif > 0 else 0
            
            return ft.Container(content=ft.Column([
                ft.Icon(ft.Icons.CLASS_, color=ft.Colors.PURPLE, size=40),
                ft.Text(classe_nom, size=20, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Container(height=5),
                ft.Row([ft.Icon(ft.Icons.PEOPLE, color=ft.Colors.BLUE, size=20), ft.Text(f"{effectif} élève(s)", size=14)],
                    alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=5),
                ft.Column([ft.Text(f"{students_with_notes}/{effectif} avec notes", size=12, color=ft.Colors.GREY_700),
                    ft.ProgressBar(value=pourcentage / 100, color=ft.Colors.GREEN if pourcentage == 100 else ft.Colors.ORANGE,
                        bgcolor=ft.Colors.GREY_300, height=8),
                    ft.Text(f"{pourcentage}%", size=12, weight=ft.FontWeight.BOLD)],
                    spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER)],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                border=ft.border.all(2, ft.Colors.PURPLE_200), border_radius=15, padding=20, margin=10, width=220, height=220, ink=True,
                on_click=lambda e, c=classe_nom, ef=effectif: show_student_selection_with_checkboxes(
                    c, ef, type_periode, periode, annee_scolaire, devise_etablissement, logo_path, bp_info, type_responsable))
        
        class_cards = [create_class_card(classe) for classe in classes]
        if not class_cards:
            class_cards.append(ft.Container(content=ft.Column([
                ft.Icon(ft.Icons.CLASS_, size=60, color=ft.Colors.GREY_400),
                ft.Text("Aucune classe disponible", size=16, color=ft.Colors.GREY_600)],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10), padding=30))
        
        classes_dialog = Dialog.custom_dialog(title=f"📚 Sélection classe - {periode}", content=ft.Column([
            ft.Container(content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.INFO, color=ft.Colors.BLUE),
                    ft.Text(f"Période: {periode} ({annee_scolaire})", size=14, weight=ft.FontWeight.W_500)], spacing=10),
                ft.Text(f"Devise: {devise_etablissement}", size=11, italic=True),
                ft.Text(f"Responsable: {type_responsable}", size=11, italic=True, color=ft.Colors.PURPLE)
            ]),
                bgcolor=ft.Colors.BLUE_50, padding=15, border_radius=10),
            ft.Divider(), 
            ft.Text("Sélectionnez une classe", size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            ft.Container(height=10),
            ft.Container(content=ft.GridView(controls=class_cards, runs_count=2, max_extent=240, child_aspect_ratio=1.0,
                spacing=10, run_spacing=10), height=400)],
            width=600, height=600, spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[
                ft.TextButton("Retour", icon=ft.Icons.ARROW_BACK,
                    on_click=lambda e: (Dialog.close_dialog(classes_dialog), select_periode_and_classe())),
                ft.TextButton("Fermer", icon=ft.Icons.CLOSE, on_click=lambda e: Dialog.close_dialog(classes_dialog))
            ])
    
    def show_student_selection_with_checkboxes(classe_nom, effectif, type_periode, periode, annee_scolaire, devise_etablissement, logo_path, bp_info, type_responsable):
        students = load_students_by_class(classe_nom)
        etablissement_data = Return("etablissement")
        etablissement = etablissement_data[0][0] if etablissement_data else "N/A"
        student_checkboxes = {}
        student_rows = []
        
        for student in students:
            notes = get_student_notes(student[2], classe_nom)
            has_notes = len(notes) > 0
            
            if has_notes:
                moyenne = calculate_moyenne_generale(notes)
                moy_text = f"{moyenne:.2f}/20"
                moy_color = ft.Colors.GREEN if moyenne >= 10 else ft.Colors.ORANGE
            else:
                moy_text = "Aucune note"
                moy_color = ft.Colors.GREY
            
            checkbox = ft.Checkbox(value=False, disabled=not has_notes)
            student_checkboxes[student[2]] = checkbox
            
            row = ft.Container(content=ft.Row([checkbox,
                ft.Container(content=ft.Text(student[0][0].upper(), size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    width=35, height=35, border_radius=17.5,
                    bgcolor=ft.Colors.BLUE_400 if 'M' in str(student[4]) else ft.Colors.PINK_400, alignment=ft.alignment.center),
                ft.Column([ft.Text(f"{student[0]} {student[1]}", size=13, weight=ft.FontWeight.W_500),
                    ft.Text(f"Mat: {student[2]}", size=10, color=ft.Colors.GREY_700)], spacing=2, expand=True),
                ft.Text(moy_text, size=12, color=moy_color, weight=ft.FontWeight.BOLD),
                ft.Icon(ft.Icons.CHECK_CIRCLE if has_notes else ft.Icons.WARNING,
                    color=ft.Colors.GREEN if has_notes else ft.Colors.ORANGE, size=18)],
                spacing=10), padding=10, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=8)
            
            student_rows.append(row)
        
        if not student_rows:
            student_rows.append(ft.Container(content=ft.Column([
                ft.Icon(ft.Icons.PEOPLE, size=60, color=ft.Colors.GREY_400),
                ft.Text("Aucun élève dans cette classe", size=16, color=ft.Colors.GREY_600)],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10), padding=30))
        
        def toggle_all(e):
            select_all = e.control.value
            for checkbox in student_checkboxes.values():
                if not checkbox.disabled:
                    checkbox.value = select_all
            page.update()
        
        select_all_checkbox = ft.Checkbox(label="Sélectionner tous les élèves avec notes", value=False, on_change=toggle_all)
        
        def generate_selected_bulletins(e):
            selected = [matricule for matricule, cb in student_checkboxes.items() if cb.value]
            if not selected:
                Dialog.error_toast("Veuillez sélectionner au moins un élève")
                return
            Dialog.close_dialog(selection_dialog)
            selected_student_data = [s for s in students if s[2] in selected]
            generate_all_bulletins_batch(classe_nom, selected_student_data, etablissement, annee_scolaire,
                periode, type_periode, effectif, devise_etablissement, logo_path, bp_info, type_responsable)
        
        selection_dialog = Dialog.custom_dialog(title=f"📋 {classe_nom} - Sélection des élèves", content=ft.Column([
            ft.Container(content=ft.Row([ft.Icon(ft.Icons.INFO, color=ft.Colors.BLUE),
                ft.Text(f"{periode} ({annee_scolaire})", size=13, italic=True)], spacing=10),
                bgcolor=ft.Colors.BLUE_50, padding=10, border_radius=5),
            ft.Divider(), 
            select_all_checkbox, 
            ft.Divider(),
            ft.Container(content=ft.Column(controls=student_rows, spacing=8, scroll=ft.ScrollMode.AUTO), height=350)],
            width=600, height=550, spacing=10),
            actions=[
                ft.TextButton("Retour", icon=ft.Icons.ARROW_BACK,
                    on_click=lambda e: (Dialog.close_dialog(selection_dialog),
                        show_classes_selection(type_periode, periode, annee_scolaire, devise_etablissement, logo_path, bp_info, type_responsable))),
                ft.ElevatedButton("Générer les bulletins sélectionnés", icon=ft.Icons.PICTURE_AS_PDF,
                    bgcolor=ft.Colors.RED, color=ft.Colors.WHITE, on_click=generate_selected_bulletins)
            ])
    
    def generate_all_bulletins_batch(classe_nom, students, etablissement, annee, periode, type_periode, effectif, devise_etablissement, logo_path, bp_info, type_responsable):
        loading_dialog = Dialog.loading_dialog(title="Génération en cours...", message=f"Génération de {len(students)} bulletin(s)...")
        
        try:
            # Utiliser le dossier Documents de l'utilisateur
            documents_folder = get_documents_folder()
            bulletins_dir = documents_folder / "Bulletins_Scolaires" / classe_nom / periode.replace(' ', '_')
            
            # Créer le dossier s'il n'existe pas
            bulletins_dir.mkdir(parents=True, exist_ok=True)
            
            success_count = 0
            for student in students:
                notes = get_student_notes(student[2], classe_nom)
                if notes:
                    moyenne_gen = calculate_moyenne_generale(notes)
                    rang = calculate_class_rank(moyenne_gen, classe_nom, annee, notes)
                    filename = bulletins_dir / f"Bulletin_{student[0]}_{student[1]}.pdf"
                    html_content = generate_bulletin_html(student, classe_nom, notes, etablissement, annee,
                        "Bon Travail", moyenne_gen, rang, periode, type_periode, effectif, devise_etablissement, logo_path, bp_info, type_responsable)
                    if save_bulletin_pdf(html_content, str(filename)):
                        save_trimestre_moyenne(student[2], moyenne_gen, annee, periode)
                        success_count += 1
            
            Dialog.close_dialog(loading_dialog)
            success_dialog = Dialog.custom_dialog(title="✅ Génération terminée", content=ft.Column([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=60),
                ft.Text(f"{success_count} bulletin(s) généré(s) !", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                ft.Text(f"Dossier: {bulletins_dir}", size=13),
                ft.ElevatedButton("Ouvrir le dossier", icon=ft.Icons.FOLDER_OPEN,
                    on_click=lambda e: open_folder(str(bulletins_dir)))],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15, width=400, height=250),
                actions=[ft.ElevatedButton("OK", bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE,
                    on_click=lambda e: Dialog.close_dialog(success_dialog))])
        except Exception as ex:
            Dialog.close_dialog(loading_dialog)
            Dialog.error_toast(f"Erreur: {str(ex)}")
            print(f"Erreur: {ex}")
    
    select_periode_and_classe()
