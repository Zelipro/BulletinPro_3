import flet as ft
from Zeli_Dialog import ZeliDialog2
import sqlite3
import os
import shutil
from pathlib import Path
from time import sleep


def Gestion_Classe(page, Donner):
    Dialog = ZeliDialog2(page)
    
    def Return(Ident):
        """Récupère une information depuis la table User"""
        con = None
        try:
            con = sqlite3.connect("base.db")
            cur = con.cursor()
            cur.execute(
                f"SELECT {Ident} FROM User WHERE identifiant = ? AND titre = ? AND passwords = ?",
                (Donner.get("ident"), Donner.get("role"), Donner.get("pass"))
            )
            donne = cur.fetchall()
            cur.close()
            return donne
        except Exception as e:
            Dialog.error_toast(f"Erreur de récupération: {str(e)}")
            return []
        finally:
            if con:
                con.close()
    
    def load_classes():
        """Charge la liste de toutes les classes de l'établissement"""
        Etat = Return("etablissement")
        
        if not Etat:
            return []
        
        con = None
        try:
            con = sqlite3.connect("base.db")
            cur = con.cursor()
            
            # Créer la table Classes si elle n'existe pas
            cur.execute("""
                CREATE TABLE IF NOT EXISTS Classes(
                    nom TEXT NOT NULL,
                    niveau TEXT NOT NULL,
                    effectif INTEGER DEFAULT 0,
                    etablissement TEXT NOT NULL,
                    PRIMARY KEY (nom, etablissement)
                )
            """)
            con.commit()
            cur.close()
            
            # Récupérer toutes les classes distinctes depuis Students
            cur = con.cursor()
            cur.execute("""
                SELECT DISTINCT classe, COUNT(*) as effectif
                FROM Students 
                WHERE etablissement = ?
                GROUP BY classe
            """, (Etat[0][0],))
            donne = cur.fetchall()
            
            return donne
        except Exception as e:
            Dialog.error_toast(f"Erreur de chargement: {str(e)}")
            return []
        finally:
            if con:
                con.close()
    
    def load_students_by_class(classe_nom):
        """Charge tous les élèves d'une classe spécifique"""
        Etat = Return("etablissement")
        
        if not Etat:
            return []
        
        con = None
        try:
            con = sqlite3.connect("base.db")
            cur = con.cursor()
            cur.execute("""
                SELECT * FROM Students 
                WHERE classe = ? AND etablissement = ?
                ORDER BY nom, prenom
            """, (classe_nom, Etat[0][0]))
            donne = cur.fetchall()
            return donne
        except Exception as e:
            Dialog.error_toast(f"Erreur de chargement: {str(e)}")
            return []
        finally:
            if con:
                con.close()
    
    def search_students(students, search_term):
        """Filtre les élèves selon le terme de recherche"""
        if not search_term:
            return students
        
        search_term = search_term.lower().strip()
        filtered = []
        
        for student in students:
            nom = str(student[0]).lower()
            prenom = str(student[1]).lower()
            matricule = str(student[2]).lower()
            
            if (search_term in nom or 
                search_term in prenom or 
                search_term in matricule):
                filtered.append(student)
        
        return filtered
    
    def show_class_details(classe_nom, effectif):
        """Affiche les détails d'une classe avec la liste des élèves"""
        
        # Charger les élèves de la classe
        all_students = load_students_by_class(classe_nom)
        
        # Container pour afficher les élèves filtrés
        students_container = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
        )
        
        def update_student_list(search_term=""):
            """Met à jour la liste des élèves affichés"""
            filtered_students = search_students(all_students, search_term)
            
            students_container.controls.clear()
            
            if not filtered_students:
                students_container.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.SEARCH_OFF, size=50, color=ft.Colors.GREY_400),
                            ft.Text(
                                "Aucun élève trouvé",
                                size=16,
                                color=ft.Colors.GREY_600
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10
                        ),
                        padding=30
                    )
                )
            else:
                for student in filtered_students:
                    students_container.controls.append(
                        create_student_row(student)
                    )
            
            page.update()
        
        def on_search_change(e):
            """Appelé quand le texte de recherche change"""
            update_student_list(e.control.value)
        
        # Champ de recherche
        search_field = ft.TextField(
            hint_text="Rechercher par nom, prénom ou matricule...",
            prefix_icon=ft.Icons.SEARCH,
            border_color=ft.Colors.BLUE_200,
            focused_border_color=ft.Colors.BLUE_500,
            on_change=on_search_change,
            width=450,
        )
        
        # Initialiser la liste complète
        update_student_list()
        
        # Dialog des détails de classe
        detail_dialog = Dialog.custom_dialog(
            title=f"📚 Classe {classe_nom} - {len(all_students)} élève(s)",
            content=ft.Column([
                # Statistiques rapides
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.PEOPLE, color=ft.Colors.BLUE, size=30),
                                ft.Text(f"{effectif}", size=20, weight=ft.FontWeight.BOLD),
                                ft.Text("Élèves", size=12, color=ft.Colors.GREY_600),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5
                            ),
                            padding=10,
                            border=ft.border.all(1, ft.Colors.BLUE_200),
                            border_radius=10,
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.MALE, color=ft.Colors.GREEN, size=30),
                                ft.Text(
                                    f"{sum(1 for s in all_students if 'M' in str(s[4]))}",
                                    size=20,
                                    weight=ft.FontWeight.BOLD
                                ),
                                ft.Text("Garçons", size=12, color=ft.Colors.GREY_600),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5
                            ),
                            padding=10,
                            border=ft.border.all(1, ft.Colors.GREEN_200),
                            border_radius=10,
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.FEMALE, color=ft.Colors.PINK, size=30),
                                ft.Text(
                                    f"{sum(1 for s in all_students if 'F' in str(s[4]))}",
                                    size=20,
                                    weight=ft.FontWeight.BOLD
                                ),
                                ft.Text("Filles", size=12, color=ft.Colors.GREY_600),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5
                            ),
                            padding=10,
                            border=ft.border.all(1, ft.Colors.PINK_200),
                            border_radius=10,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    spacing=10
                    ),
                    padding=10,
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=10,
                ),
                
                ft.Divider(),
                
                # Barre de recherche
                search_field,
                
                ft.Divider(),
                
                # Liste des élèves
                ft.Container(
                    content=students_container,
                    height=300,
                    width=450,
                ),
            ],
            width=500,
            height=550,
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            actions=[
                ft.TextButton(
                    "Fermer",
                    icon=ft.Icons.CLOSE,
                    on_click=lambda e: Dialog.close_dialog(detail_dialog)
                )
            ]
        )
    
    def create_student_row(student):
        """Crée une ligne pour afficher un élève"""
        return ft.Container(
            content=ft.Row([
                # Avatar avec initiale
                ft.Container(
                    content=ft.Text(
                        student[0][0].upper(),  # Première lettre du nom
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                    ),
                    width=40,
                    height=40,
                    border_radius=20,
                    bgcolor=ft.Colors.BLUE_400 if 'M' in str(student[4]) else ft.Colors.PINK_400,
                    alignment=ft.alignment.center,
                ),
                
                # Informations élève
                ft.Column([
                    ft.Text(
                        f"{student[0]} {student[1]}",
                        size=15,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Row([
                        ft.Icon(ft.Icons.TAG, size=14, color=ft.Colors.GREY_600),
                        ft.Text(
                            f"Matricule: {student[2]}",
                            size=12,
                            color=ft.Colors.GREY_700,
                        ),
                        ft.Text("|", color=ft.Colors.GREY_400),
                        ft.Icon(
                            ft.Icons.MALE if 'M' in str(student[4]) else ft.Icons.FEMALE,
                            size=14,
                            color=ft.Colors.BLUE_400 if 'M' in str(student[4]) else ft.Colors.PINK_400
                        ),
                        ft.Text(
                            student[4],
                            size=12,
                            color=ft.Colors.GREY_700,
                        ),
                    ], spacing=5),
                ], spacing=2, expand=True),
                
                # Bouton détails
                ft.IconButton(
                    icon=ft.Icons.INFO_OUTLINE,
                    icon_color=ft.Colors.BLUE,
                    tooltip="Voir détails",
                    on_click=lambda e, s=student: show_student_detail(s)
                ),
            ], spacing=10),
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            ink=True,
        )
    
    def show_student_detail(student):
        """Affiche les détails complets d'un élève"""
        detail_student_dialog = Dialog.custom_dialog(
            title=f"👤 Détails - {student[0]} {student[1]}",
            content=ft.Column([
                ft.Divider(),
                create_info_row("Nom:", student[0]),
                create_info_row("Prénom:", student[1]),
                create_info_row("Matricule:", student[2]),
                create_info_row("Date de naissance:", student[3]),
                create_info_row("Sexe:", student[4]),
                create_info_row("Classe:", student[5]),
                ft.Divider(),
            ],
            width=400,
            height=300,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            spacing=10,
            ),
            actions=[
                ft.TextButton(
                    "Fermer",
                    icon=ft.Icons.CLOSE,
                    icon_color=ft.Colors.RED,
                    on_click=lambda e: Dialog.close_dialog(detail_student_dialog)
                )
            ]
        )
    
    def add_class():

        def save(d):
            con = None
            #print("============================= 0 =============================")
            try:
                #print("============================= 1 =============================")
                con = sqlite3.connect("base.db")
                cur = con.cursor()
                
                #print("============================= 2 =============================")
                #==== Create la table si elle n'existe pas =====
                cur.execute("CREATE TABLE IF NOT EXISTS Class(nom TEXT NOT NULL , etablissement TEXT NOT NULL)")
                con.commit()
                #===============================================
                cur.close()
                
                #print("============================= 3 =============================")
                #====== Verifier si la classe que l'on veux ajouter existe deja
                cur = con.cursor()
                cur.execute("SELECT * FROM Class WHERE nom = ? AND etablissement = ?",(Classe_field.value , etabl[0][0],))
                #print("============================= 33 =============================")
                if cur.fetchall():
                    Classe_field.error_text = "Cette classe existe déjà"
                    page.update()
                    return
                
                cur.close()
                #===========================================================
                
                #print("============================= 4 =============================")
                cur = con.cursor()
                cur.execute("INSERT INTO Class(nom , etablissement) VALUES (?,?)",(Classe_field.value , etabl[0][0]))
                con.commit()
                
                cur.close()
                
                # NOUVEAU : Sync vers Supabase
                try:
                    from sync_manager import sync_manager
                    sync_manager.sync_table_to_supabase(
                        "Class",
                        filter_col="etablissement",
                        filter_val=etabl[0][0]
                    )
                except Exception as e:
                    Dialog.error_toast(f"⚠️ Erreur sync: {e}")
                    
                #print("============================= 5 =============================")
                Dialog.info_toast(
                    message="Ajout effectuer avec succes !"
                )
                
                d.open = False
                page.update()
            
            except Exception as ex:
                Dialog.error_toast(f"Erreut d'ajout : {ex}")
            
            finally:
                if con:
                    con.close()
                    
        def Close(d):
            d.open = False
            page.update()
            Gestion_Classe(page , Donner)
        etabl = Return("etablissement")
        if not etabl:
            Dialog.error_toast("Erreur de recuperation de l'etablissement")
            return
        
        Classe_field = ft.TextField(label="Classe",hint_text="Ex:Terminal C")
        
        diag = Dialog.custom_dialog(
            title="Classe",
            content=ft.Column(
                [
                    Classe_field,
                    ft.Divider(),
                ],
                height=80,
            ),
            actions=[
                ft.ElevatedButton(
                    icon= ft.Icons.CLOSE,
                    icon_color = "white",
                    text="Annuler",
                    color="white",
                    bgcolor="red",
                    on_click= lambda e : Close(diag)
                ),
                ft.ElevatedButton(
                    icon = ft.Icons.SAVE,
                    icon_color="white",
                    text="Save",
                    color="white",
                    bgcolor="green",
                    on_click= lambda e : save(diag)
                ),
            ]
        )
    
                    
        def Close(d):
            d.open = False
            page.update()
            Gestion_Classe(page , Donner)
        etabl = Return("etablissement")
        if not etabl:
            Dialog.error_toast("Erreur de recuperation de l'etablissement")
            return
        
        Classe_field = ft.TextField(label="Classe",hint_text="Ex:Terminal C")
        
        diag = Dialog.custom_dialog(
            title="Classe",
            content=ft.Column(
                [
                    Classe_field,
                    ft.Divider(),
                ],
                height=80,
            ),
            actions=[
                ft.ElevatedButton(
                    icon = ft.Icons.SAVE,
                    icon_color="white",
                    text="Save",
                    color="white",
                    bgcolor="green",
                    on_click= lambda e : save(diag)
                ),
                ft.ElevatedButton(
                    icon= ft.Icons.CLOSE,
                    icon_color = "white",
                    text="Annuler",
                    color="white",
                    bgcolor="red",
                    on_click= lambda e : Close(diag)
                )
            ]
        )
    
    def create_info_row(label, value):
        """Crée une ligne d'information"""
        return ft.Row([
            ft.Text(label, size=15, weight=ft.FontWeight.BOLD, width=150),
            ft.Text(str(value or "N/A"), size=15, selectable=True, expand=True),
        ], spacing=10)
    
    def create_class_card(classe):
        """Crée une carte pour une classe"""
        classe_nom = classe[0]
        effectif = classe[1]
        
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.CLASS_, color=ft.Colors.GREEN, size=40),
                ft.Text(
                    classe_nom,
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=5),
                ft.Row([
                    ft.Icon(ft.Icons.PEOPLE, color=ft.Colors.BLUE, size=20),
                    ft.Text(f"{effectif} élève(s)", size=14),
                ],
                alignment=ft.MainAxisAlignment.CENTER
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
            ),
            border=ft.border.all(2, ft.Colors.GREEN_200),
            border_radius=15,
            padding=20,
            margin=10,
            width=200,
            height=180,
            ink=True,
            on_click=lambda e, c=classe_nom, ef=effectif: show_class_details(c, ef),
        )
    
    # Chargement des classes
    classes = load_classes()
    class_cards = [create_class_card(classe) for classe in classes]
    
    # Si aucune classe
    if not class_cards:
        class_cards = [
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.CLASS_, size=60, color=ft.Colors.GREY_400),
                    ft.Text(
                        "Aucune classe trouvée",
                        size=16,
                        color=ft.Colors.GREY_600
                    ),
                    ft.Text(
                        "Les classes sont créées automatiquement lors de l'ajout d'élèves",
                        size=12,
                        color=ft.Colors.GREY_500,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10
                ),
                padding=30
            )
        ]
    
    
    # Dialog principal
    main_dialog = Dialog.custom_dialog(
        title=f"📚 Gestion des Classes ({len(classes)} classe(s))",
        content=ft.Column([
            ft.Text(
                "Cliquez sur une classe pour voir ses élèves",
                size=14,
                color=ft.Colors.GREY_600,
                italic=True,
            ),
            ft.Divider(),
            ft.Row(
                [
                    ft.Column(
                        controls= [
                            ft.GridView(
                                controls=class_cards,
                                runs_count = 2,
                                
                            )
                        ],
                        scroll=ft.ScrollMode.AUTO,
                        height=350,
                        width=450,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            ft.Divider(),
            ft.ElevatedButton(
                width = 450,
                bgcolor = "green",
                icon=ft.Icons.ADD,
                icon_color="white",
                text="Ajouter une classe",
                color = "white",
                on_click = lambda e : add_class(),
                
            )
        ],
        width=500,
        height=500,
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        actions=[
            ft.TextButton(
                "Fermer",
                icon=ft.Icons.CLOSE,
                on_click=lambda e: Dialog.close_dialog(main_dialog)
            )
        ]
    )
