import flet as ft
from Zeli_Dialog import ZeliDialog2
import sqlite3
import os
import shutil
from pathlib import Path
from time import sleep

def Gestion_Matiere(page,Donner):
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
                
    def Get_all():
        #Creer la base de donner des matireere si elle n'existe pas et revoi tous les elements de matire et on peux aussi ajouter
        con = None
        etablissement = Return("etablissement")

        try:
            print("\n-------------Ici Fait 1--------------------------\n")
            con = sqlite3.connect("base.db")
            cur = con.cursor()
            #Ici j'ai pas mise le coef car ca peux varier d'une classe a l'autre
            cur.execute("CREATE TABLE IF NOT EXISTS Matieres(nom TEXT NOT NULL, genre TEXT NOT NULL , etablissement TEXT NOT NULL)")
            con.commit()
            cur.close()
            
            print("\n-------------Ici Fait 2--------------------------\n")
            cur = con.cursor()
            cur.execute("SELECT * FROM Matieres WHERE etablissement = ?" ,(etablissement[0][0] ,))
            donne = cur.fetchall()
            cur.close()
            
            print("\n-------------Ici Fait 33--------------------------\n")
            
            return donne
        except:
            return
        finally:
            if con:
                con.close()
    
    def edit_matiere(matiere):
        def save():
            con = None
            try:
                con = sqlite3.connect("base.db")
                cur =  con.cursor()
                
                #====== Verifier que les nouveau info ne sont pas deja dans la base de donné ======
                cur.execute("SELECT * FROM Matieres WHERE nom = ? AND genre = ?",(non_field.value,genre_field.value))
                donne = cur.fetchall()
                cur.close()
                #==========================================================
                if donne:
                    Dialog.error_toast("Cette matiere existe déjà")
                    return
                
                cur = con.cursor()
                cur.execute("UPDATE Matieres SET nom = ? , genre = ? WHERE nom = ? AND etablissement = ? ",(non_field.value ,genre_field.value ,matiere[0] ,matiere[2]))
                con.commit()
                
                Dialog.alert_dialog(
                    title = "Sucess",
                    message='Modification effectué'
                )
                
                # NOUVEAU : Sync vers Supabase
                try:
                    from sync_manager import sync_manager
                    sync_manager.sync_table_to_supabase(
                        "Matieres",
                        filter_col="etablissement",
                        filter_val=matiere[2]
                    )
                except Exception as e:
                    Dialog.error_toast(f"⚠️ Erreur sync: {e}")
                
                Dialog.alert_dialog(
                    title = "Sucess",
                    message='Modification effectué'
                )
                
                sleep(0.2)
                Gestion_Matiere(page , Donner)
            except:
                Dialog.error_toast("Erreur de modification")
            
            finally:
                if con:
                    con.close()
                    
        non_field = ft.TextField(label= "Intitulé de la matiere",value = matiere[0],text_align="center")
        genre_field = ft.Dropdown(
            label="Genre",
            hint_text = "Selection du genre",
            options=[
                ft.dropdown.Option("Scientifique",leading_icon=ft.Icons.SCIENCE),
                ft.dropdown.Option("Littérature",leading_icon=ft.Icons.PAGES_ROUNDED),
                ft.dropdown.Option("Art",leading_icon=ft.Icons.ART_TRACK_ROUNDED),
            ]
        )
        
        diag = Dialog.custom_dialog(
            title = "Modification de matiere",
            content=ft.Column(
                [
                    non_field,
                    genre_field
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                height=100,
            ),
            actions=[
                ft.ElevatedButton(
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.CLOSE,
                                color="white"
                            ),
                            ft.Text(
                                value="Annuler",
                                color="white"
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    bgcolor="red",
                    on_click=lambda e : Dialog.close_dialog(diag),
                    width = 100,
                ),
                 ft.ElevatedButton(
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.SAVE,
                                color="white"
                            ),
                            ft.Text(
                                value="Enregistrer",
                                color="white"
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    bgcolor="green",
                    width = 120,
                    on_click= lambda e : save()
                ),
            ]
        )
    
    def add_matiere():
        etabl = Return("etablissement")
        def save():
            con = None
            try:
                con = sqlite3.connect("base.db")
                cur =  con.cursor()
                
                #====== Verifier que les nouveau info ne sont pas deja dans la base de donné ======
                cur.execute("SELECT * FROM Matieres WHERE nom = ? AND genre = ?",(non_field.value,genre_field.value))
                donne = cur.fetchall()
                cur.close()
                #==========================================================
                if donne:
                    Dialog.error_toast("Cette matiere existe déjà")
                    return
                
                cur = con.cursor()
                cur.execute("INSERT INTO Matieres(nom , genre ,etablissement ) VALUES (?,?,?) ",(non_field.value ,genre_field.value ,etabl[0][0]))
                con.commit()
                
                # NOUVEAU : Sync vers Supabase
                try:
                    from sync_manager import sync_manager
                    sync_manager.sync_table_to_supabase(
                        "Matieres",
                        filter_col="etablissement",
                        filter_val=etabl[0][0]
                    )
                except Exception as e:
                    Dialog.error_toast(f"⚠️ Erreur sync: {e}")
                
                Dialog.alert_dialog(
                    title = "Sucess",
                    message='Ajout effectué'
                )
                
                Gestion_Matiere(page , Donner)
            except:
                Dialog.error_toast("Erreur d'ajout'")
            
            finally:
                if con:
                    con.close()
                    
        non_field = ft.TextField(label= "Intitulé de la matiere",text_align="center")
        genre_field = ft.Dropdown(
            label="Genre",
            hint_text = "Selection du genre",
            options=[
                ft.dropdown.Option("Scientifique",leading_icon=ft.Icons.SCIENCE),
                ft.dropdown.Option("Littérature",leading_icon=ft.Icons.PAGES_ROUNDED),
                ft.dropdown.Option("Art",leading_icon=ft.Icons.ART_TRACK_ROUNDED),
            ]
        )
        
        diag = Dialog.custom_dialog(
            title = "Ajout de matiere",
            content=ft.Column(
                [
                    non_field,
                    genre_field
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                height=100,
            ),
            actions=[
                ft.ElevatedButton(
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.CLOSE,
                                color="white"
                            ),
                            ft.Text(
                                value="Annuler",
                                color="white"
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    bgcolor="red",
                    on_click=lambda e : Dialog.close_dialog(diag),
                    width = 100,
                ),
                 ft.ElevatedButton(
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.SAVE,
                                color="white"
                            ),
                            ft.Text(
                                value="Enregistrer",
                                color="white"
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    bgcolor="green",
                    width = 120,
                    on_click= lambda e : save()
                ),
            ]
        )
        
    def create_matiere_card(matiere):
        """Crée une carte pour un enseignant"""
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    f"{matiere[0]}",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(f"Domaine :{matiere[1]}", size = 15),
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.EDIT,
                        tooltip="Modifier",
                        icon_color=ft.Colors.GREEN,
                        on_click=lambda e, t=matiere: edit_matiere(t)
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
    matieres = Get_all()
    matiere_cards = [create_matiere_card(matiere) for matiere in matieres]
    
    # Si aucun enseignant
    if not matiere_cards:
        matiere_cards = [
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.SCHOOL, size=60, color=ft.Colors.GREY_400),
                    ft.Text(
                        "Aucune matiere trouvé",
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
        title=f"👨‍🏫 Liste des matieres ({len(matieres)})",
        content=ft.Column([
            ft.Row(
                [
                    ft.Column(
                        controls=matiere_cards,
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
                    ft.Text("Ajouter une matiere", color=ft.Colors.WHITE),
                ], spacing=8),
                bgcolor=ft.Colors.GREEN_700,
                on_click=lambda e: add_matiere(),
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

