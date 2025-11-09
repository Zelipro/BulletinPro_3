import flet as ft
from Zeli_Dialog import ZeliDialog2
import sqlite3
import os
import shutil
from pathlib import Path
from time import sleep

def Gestion_Prof(page, Donner):
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
    
    def load_teachers():
        """Charge la liste de tous les enseignants de l'établissement"""
        Etat = Return("etablissement")
        
        if not Etat:
            return []
        
        con = None
        try:
            con = sqlite3.connect("base.db")
            cur = con.cursor()
            cur.execute(
                "SELECT * FROM User WHERE etablissement = ? AND titre = ?",
                (Etat[0][0], "prof")
            )
            donne = cur.fetchall()
            return donne
        except Exception as e:
            Dialog.error_toast(f"Erreur de chargement: {str(e)}")
            return []
        finally:
            if con:
                con.close()
    
    def add_teacher():
        """Ajoute un nouvel enseignant"""
    
        # Fonction pour charger les matières depuis la base de données
        def load_matieres_from_db():
            """Charge les matières depuis la table Matieres"""
            etablissement_data = Return("etablissement")
            if not etablissement_data or not etablissement_data[0]:
                return []
            
            etablissement = etablissement_data[0][0]
            con = None
            try:
                con = sqlite3.connect("base.db")
                cur = con.cursor()
                cur.execute(
                    "SELECT nom FROM Matieres WHERE etablissement = ? ORDER BY nom",
                    (etablissement,)
                )
                matieres = cur.fetchall()
                return [matiere[0] for matiere in matieres]
            except Exception as e:
                print(f"Erreur chargement matières: {e}")
                return []
            finally:
                if con:
                    con.close()
        
        # Charger les matières
        matieres_list = load_matieres_from_db()
        
        # Si aucune matière n'existe, afficher un message
        if not matieres_list:
            Dialog.alert_dialog(
                title="⚠️ Aucune matière",
                message="Veuillez d'abord ajouter des matières dans le système avant de créer un enseignant."
            )
            return
        
        # Champs de saisie
        nom_field = ft.TextField(
            label="Nom",
            hint_text="Entrez le nom",
            autofocus=True,
            capitalization=ft.TextCapitalization.WORDS
        )
        prenom_field = ft.TextField(
            label="Prénom",
            hint_text="Entrez le prénom",
            capitalization=ft.TextCapitalization.WORDS
        )
        email_field = ft.TextField(
            label="Email",
            hint_text="exemple@email.com",
            keyboard_type=ft.KeyboardType.EMAIL
        )
        telephone_field = ft.TextField(
            label="Téléphone",
            hint_text="+228 XX XX XX XX",
            keyboard_type=ft.KeyboardType.PHONE
        )
        
        # Dropdown avec les matières de la base de données
        matiere_dropdown = ft.Dropdown(
            label="Matière principale",
            hint_text="Sélectionnez une matière",
            options=[ft.dropdown.Option(matiere) for matiere in matieres_list],
            width=400
        )
        
        def clear_errors():
            """Efface tous les messages d'erreur"""
            for field in [nom_field, prenom_field, email_field, telephone_field, matiere_dropdown]:
                field.error_text = None
            page.update()
        
        def validate_fields():
            """Valide tous les champs"""
            is_valid = True
            
            # Validation des champs texte
            for field in [nom_field, prenom_field, email_field, telephone_field]:
                if not field.value or not field.value.strip():
                    field.error_text = "Ce champ est obligatoire"
                    is_valid = False
                else:
                    field.error_text = None
            
            # Validation de la matière
            if not matiere_dropdown.value:
                matiere_dropdown.error_text = "Sélectionnez une matière"
                is_valid = False
            else:
                matiere_dropdown.error_text = None
            
            # Validation email
            if email_field.value and "@" not in email_field.value:
                email_field.error_text = "Email invalide"
                is_valid = False
            
            page.update()
            return is_valid
        
        def save_teacher(e):
            """Enregistre l'enseignant"""
            clear_errors()
            
            if not validate_fields():
                return
            
            con = None
            try:
                # Récupération établissement
                etablissement_data = Return("etablissement")
                if not etablissement_data or not etablissement_data[0]:
                    Dialog.error_toast("Impossible de récupérer l'établissement")
                    return
                
                etablissement = etablissement_data[0][0]
                
                # Génération identifiants
                Ident = f"{prenom_field.value[0]}{nom_field.value}".upper().replace(" ", "")
                Pass = f"{prenom_field.value[0].lower()}@prof_{len(nom_field.value) + len(prenom_field.value)}"
                
                con = sqlite3.connect("base.db")
                cur = con.cursor()
                
                # Vérification si existe dans User
                cur.execute(
                    "SELECT * FROM User WHERE identifiant = ? AND passwords = ? AND titre = ?",
                    (Ident, Pass, "prof")
                )
                if cur.fetchone():
                    nom_field.error_text = "Cet utilisateur existe déjà"
                    prenom_field.error_text = "Cet utilisateur existe déjà"
                    page.update()
                    return
                
                # Insertion dans User
                cur.execute("""
                    INSERT INTO User (identifiant, passwords, nom, prenom, email, telephone, etablissement, titre)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'prof')
                """, (
                    Ident, Pass,
                    nom_field.value.strip(),
                    prenom_field.value.strip(),
                    email_field.value.strip(),
                    telephone_field.value.strip(),
                    etablissement
                ))
                con.commit()
                
                # Création table Teacher si nécessaire
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS Teacher (
                        ident TEXT NOT NULL PRIMARY KEY,
                        pass TEXT NOT NULL,
                        matiere TEXT NOT NULL
                    )
                """)
                con.commit()
                
                # Vérification si existe dans Teacher
                cur.execute("SELECT * FROM Teacher WHERE ident = ?", (Ident,))
                if cur.fetchone():
                    nom_field.error_text = "Cet enseignant existe déjà"
                    prenom_field.error_text = "Cet enseignant existe déjà"
                    page.update()
                    return
                
                # Insertion dans Teacher
                cur.execute(
                    "INSERT INTO Teacher (ident, pass, matiere) VALUES (?, ?, ?)",
                    (Ident, Pass, matiere_dropdown.value)
                )
                con.commit()
                
                 # NOUVEAU : Sync vers Supabase
                try:
                    from sync_manager import sync_manager
                    sync_manager.sync_table_to_supabase(
                        "User",
                        filter_col="identifiant",
                        filter_val=Ident
                    )
                    sync_manager.sync_table_to_supabase(
                        "Teacher",
                        filter_col="ident",
                        filter_val=Ident
                    )
                except Exception as e:
                    Dialog.error_toast(f"⚠️ Erreur sync: {e}")
                    
                # Dialog de succès
                success_dialog = Dialog.custom_dialog(
                    title="✅ Succès",
                    content=ft.Column([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=60),
                        ft.Text("Enseignant ajouté avec succès !", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                        ft.Divider(),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text("Nom complet:", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{nom_field.value} {prenom_field.value}", color=ft.Colors.BLUE),
                                ]),
                                ft.Row([
                                    ft.Text("Matière:", weight=ft.FontWeight.BOLD),
                                    ft.Text(matiere_dropdown.value, color=ft.Colors.PURPLE),
                                ]),
                                ft.Divider(),
                                ft.Row([
                                    ft.Text("Identifiant:", weight=ft.FontWeight.BOLD),
                                    ft.Text(Ident, selectable=True, color=ft.Colors.BLUE),
                                ]),
                                ft.Row([
                                    ft.Text("Mot de passe:", weight=ft.FontWeight.BOLD),
                                    ft.Text(Pass, selectable=True, color=ft.Colors.BLUE),
                                ]),
                            ]),
                            bgcolor=ft.Colors.BLUE_50,
                            padding=15,
                            border_radius=10,
                            border=ft.border.all(1, ft.Colors.BLUE_200)
                        ),
                        ft.Text("⚠️ Conservez ces identifiants !", size=12, color=ft.Colors.RED, weight=ft.FontWeight.BOLD),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                    width=450,
                    height=350,
                    ),
                    actions=[
                        ft.ElevatedButton(
                            "Copier les identifiants",
                            icon=ft.Icons.COPY,
                            bgcolor=ft.Colors.BLUE,
                            color=ft.Colors.WHITE,
                            on_click=lambda e: copy_and_close(Ident, Pass, success_dialog, DIag2)
                        ),
                        ft.ElevatedButton(
                            "Fermer",
                            bgcolor=ft.Colors.GREEN,
                            color=ft.Colors.WHITE,
                            on_click=lambda e: close_all_and_refresh(success_dialog, DIag2)
                        )
                    ]
                )
                
            except Exception as ex:
                Dialog.error_toast(f"Erreur d'ajout: {str(ex)}")
                print(f"Erreur détaillée: {ex}")
            finally:
                if con:
                    con.close()
        
        def copy_and_close(ident, password, success_dialog, main_dialog):
            """Copie les identifiants et ferme"""
            page.set_clipboard(f"Identifiant: {ident}\nMot de passe: {password}")
            Dialog.info_toast("Identifiants copiés dans le presse-papiers !")
            Dialog.close_dialog(success_dialog)
            Dialog.close_dialog(main_dialog)
            refresh_display()
        
        def close_all_and_refresh(success_dialog, main_dialog):
            """Ferme tous les dialogs et rafraîchit"""
            Dialog.close_dialog(success_dialog)
            Dialog.close_dialog(main_dialog)
            refresh_display()
        
        # Dialog principal d'ajout
        DIag2 = Dialog.custom_dialog(
            title="➕ Nouvel Enseignant",
            content=ft.Column([
                ft.Text(
                    f"📚 {len(matieres_list)} matière(s) disponible(s)",
                    size=12,
                    italic=True,
                    color=ft.Colors.GREY_700
                ),
                ft.Divider(),
                nom_field,
                prenom_field,
                email_field,
                telephone_field,
                matiere_dropdown,
            ],
            width=450,
            height=400,
            spacing=15,
            scroll=ft.ScrollMode.AUTO
            ),
            actions=[
                ft.TextButton(
                    "Annuler",
                    icon=ft.Icons.CLOSE,
                    on_click=lambda e: Dialog.close_dialog(DIag2)
                ),
                ft.ElevatedButton(
                    "Enregistrer",
                    icon=ft.Icons.SAVE,
                    bgcolor=ft.Colors.GREEN,
                    color=ft.Colors.WHITE,
                    on_click=save_teacher
                ),
            ]
        )
    def show_details(teacher):
        """Affiche les détails d'un enseignant"""
        detail_dialog = Dialog.custom_dialog(
            title=f"📋 Détails - {teacher[3]} {teacher[4]}",
            content=ft.Column([
                ft.Divider(),
                create_info_row("Nom:", teacher[3]),
                create_info_row("Prénom:", teacher[4]),
                create_info_row("Identifiant:", teacher[1]),
                create_info_row("Mot de passe:", teacher[2]),
                create_info_row("Email:", teacher[5]),
                create_info_row("Téléphone:", teacher[6]),
                create_info_row("Établissement:", teacher[7]),
                ft.Divider(),
            ],
            width=450,
            height=350,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            spacing=10,
            ),
            actions=[
                ft.TextButton(
                    "Fermer",
                    icon=ft.Icons.CLOSE,
                    icon_color=ft.Colors.RED,
                    on_click=lambda e: Dialog.close_dialog(detail_dialog)
                )
            ]
        )
    
    def create_info_row(label, value):
        """Crée une ligne d'information"""
        return ft.Row([
            ft.Text(label, size=15, weight=ft.FontWeight.BOLD, width=150),
            ft.Text(str(value or "N/A"), size=15, selectable=True, expand=True),
        ], spacing=10)
    
    def edit_teacher(teacher):
        """Modifie un enseignant"""
        name_field = ft.TextField(label="Nom", value=teacher[3])
        prenom_field = ft.TextField(label="Prénom", value=teacher[4])
        ident_field = ft.TextField(label="Identifiant", value=teacher[1], read_only=True, disabled=True)
        pass_field = ft.TextField(label="Mot de passe", value=teacher[2])
        email_field = ft.TextField(label="Email", value=teacher[5])
        tele_field = ft.TextField(label="Téléphone", value=teacher[6])
        etabl_field = ft.TextField(label="Établissement", value=teacher[7], read_only=True, disabled=True)
        
        def save_changes(e, dialog):
            con = None
            try:
                con = sqlite3.connect("base.db")
                cur = con.cursor()
                
                cur.execute("""
                    UPDATE User 
                    SET nom = ?, passwords = ?, prenom = ?, email = ?, telephone = ?
                    WHERE identifiant = ? AND titre = 'prof'
                """, (
                    name_field.value.strip(),
                    pass_field.value,
                    prenom_field.value.strip(),
                    email_field.value.strip(),
                    tele_field.value.strip(),
                    ident_field.value
                ))
                con.commit()
                
                Dialog.info_toast("Modifications enregistrées !")
                Dialog.close_dialog(dialog)
                refresh_display()
                
            except sqlite3.Error as e:
                Dialog.error_toast(f"Erreur: {str(e)}")
            finally:
                if con:
                    con.close()
        
        edit_dialog = Dialog.custom_dialog(
            title=f"✏️ Modifier - {teacher[3]} {teacher[4]}",
            content=ft.Column([
                name_field,
                prenom_field,
                ident_field,
                pass_field,
                email_field,
                tele_field,
                etabl_field,
            ],
            width=400,
            height=380,
            scroll=ft.ScrollMode.AUTO,
            spacing=10
            ),
            actions=[
                ft.TextButton(
                    "Annuler",
                    on_click=lambda e: Dialog.close_dialog(edit_dialog)
                ),
                ft.ElevatedButton(
                    "Enregistrer",
                    bgcolor=ft.Colors.BLUE,
                    color=ft.Colors.WHITE,
                    on_click=lambda e: save_changes(e, edit_dialog)
                )
            ]
        )
    
    def confirm_delete(teacher):
        """Demande confirmation avant suppression"""
        confirm_dialog = Dialog.custom_dialog(
            title="⚠️ Confirmation de suppression",
            content=ft.Column([
                ft.Icon(ft.Icons.WARNING_ROUNDED, color=ft.Colors.RED, size=50),
                ft.Text(
                    "Êtes-vous sûr de vouloir supprimer cet enseignant ?",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    f"Enseignant: {teacher[3]} {teacher[4]}",
                    size=14,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "⚠️ Cette action est irréversible !",
                    color=ft.Colors.RED,
                    size=12,
                    italic=True,
                    text_align=ft.TextAlign.CENTER
                )
            ],
            width=400,
            height=220,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15
            ),
            actions=[
                ft.TextButton(
                    "Annuler",
                    on_click=lambda e: Dialog.close_dialog(confirm_dialog)
                ),
                ft.ElevatedButton(
                    "Supprimer",
                    bgcolor=ft.Colors.RED,
                    color=ft.Colors.WHITE,
                    icon=ft.Icons.DELETE_FOREVER,
                    on_click=lambda e: execute_delete(teacher, confirm_dialog)
                )
            ]
        )
    
    def execute_delete(teacher, dialog):
        """Exécute la suppression"""
        con = None
        try:
            con = sqlite3.connect("base.db")
            cur = con.cursor()
            
            # Suppression de User
            cur.execute("DELETE FROM User WHERE identifiant = ? AND titre = 'prof'", (teacher[1],))
            
            # Suppression de Teacher
            cur.execute("DELETE FROM Teacher WHERE ident = ?", (teacher[1],))
            
            con.commit()
            
            Dialog.info_toast("Enseignant supprimé !")
            Dialog.close_dialog(dialog)
            refresh_display()
            
        except sqlite3.Error as e:
            Dialog.error_toast(f"Erreur de suppression: {str(e)}")
        finally:
            if con:
                con.close()
    
    def refresh_display():
        """Rafraîchit l'affichage de la liste"""
        Dialog.close_dialog(main_dialog)
        # Réouvre le dialog avec les données à jour
        Gestion_Prof(page, Donner)
    
    def create_teacher_card(teacher):
        """Crée une carte pour un enseignant"""
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    f"{teacher[3]} {teacher[4]}",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(f"📧 {teacher[5] or 'N/A'}", size = 15),
                ft.Text(f"📞 {teacher[6] or 'N/A'}", size=15),
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.INFO,
                        tooltip="Détails",
                        icon_color=ft.Colors.BLUE,
                        on_click=lambda e, t=teacher: show_details(t)
                    ),
                    ft.IconButton(
                        icon=ft.Icons.EDIT,
                        tooltip="Modifier",
                        icon_color=ft.Colors.GREEN,
                        on_click=lambda e, t=teacher: edit_teacher(t)
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        tooltip="Supprimer",
                        icon_color=ft.Colors.RED,
                        on_click=lambda e, t=teacher: confirm_delete(t)
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8
            ),
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=ft.border_radius.only(top_right=20, bottom_left=20),
            padding=20,
            margin=10,
            
            width=280,
            height=200,
            #bgcolor=ft.Colors.ON_SURFACE_VARIANT,
        )
    
    # Chargement des enseignants
    teachers = load_teachers()
    teacher_cards = [create_teacher_card(teacher) for teacher in teachers]
    
    # Si aucun enseignant
    if not teacher_cards:
        teacher_cards = [
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.SCHOOL, size=60, color=ft.Colors.GREY_400),
                    ft.Text(
                        "Aucun enseignant trouvé",
                        size=16,
                        color=ft.Colors.GREY_600
                    ),
                    ft.Text(
                        "Cliquez sur 'Ajouter' pour commencer",
                        size=12,
                        color=ft.Colors.GREY_500
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
        title=f"👨‍🏫 Liste des Enseignants ({len(teachers)})",
        content=ft.Column([
            ft.Row(
                [
                    ft.Column(
                        controls=teacher_cards,
                        scroll=ft.ScrollMode.AUTO,
                        height=330,
                        width = 350,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            ft.Container(expand=True),
            ft.Divider(),
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.ADD, color=ft.Colors.WHITE),
                    ft.Text("Ajouter un enseignant", color=ft.Colors.WHITE),
                ], spacing=8),
                bgcolor=ft.Colors.GREEN_700,
                on_click=lambda e: add_teacher(),
            )
        ],
        width=450,
        height=450,
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