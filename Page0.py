import flet as ft
import sqlite3
from Zeli_Dialog import ZeliDialog2
from Page1 import Page1

def Get_on_db_local(mention):
    def User():
        donne = []
        con = None
        try:
            con = sqlite3.connect("base.db")
            cur = con.cursor()
            cur.execute("SELECT * FROM User")
            donne = cur.fetchall()
            cur.close()
            
        except sqlite3.Error as e:
            pass
        finally:
            if con:
                con.close()
        return donne
    
    dic = {
        "User":User
    }
    
    func = dic.get(mention)
    if not func:
        return []   # return empty list when unknown mention
    return func()

def Submit(page , Ident , Pass): 
    Dialog = ZeliDialog2(page)
    #================================================================
    def login_success(donner_info,Dial):
        Dialog.close_dialog(Dial)  # Fermer le dialogue
        page.clean()  # Nettoyer tout le contenu de la page

        # Récupérer sidebar et main_content
        sidebar, main_content = Page1(page, donner_info)
        
        # Ajouter à la page
        page.add(
            ft.Row([
                sidebar,
                main_content,
            ], spacing=0, expand=True)
        )
        page.update()
    #=================
    Donne = Get_on_db_local("User")
    if all([Ident.value == "Deg" , Pass.value == "Deg"]):
        Donner = {
                "ident": "Deg",
                "pass" : "Deg",
                "name": "Zeli",
                "role": "creator"
        }
        Dial = Dialog.custom_dialog(
            title = "Notification",
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE_OUTLINE,
                        size = 60,
                        color=ft.Colors.GREEN_200,
                    ),
                    ft.Text(
                        value="Bienvenue Mon createur"
                    )
                ],
                height=100,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            actions=[
                ft.ElevatedButton(
                    content=ft.Text(
                        value ="Ok",
                        color=ft.Colors.WHITE,
                        ),
                    bgcolor=ft.Colors.GREEN_300,
                    on_click=lambda e : login_success(Donner ,Dial )
                )
            ]
        )
        #pass #Nxte page
    elif Donne:
        found = False
        for elmt in Donne:
            ident , passs = elmt[1],elmt[2]
            if ident == Ident.value and passs == Pass.value:
                found = True
                
                Donner = {
                    "ident": ident,
                    "pass" : passs,
                    "name": elmt[3],
                    "role": elmt[8]
                    }
                
                Dial = Dialog.custom_dialog(
                    title = "Notification",
                    content=ft.Column(
                        [
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE_OUTLINE,
                                size = 60,
                                color=ft.Colors.GREEN_200,
                            ),
                            ft.Text(
                                value=f"Bienvenue {Ident.value}"
                            )
                        ],
                        height=100,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    actions=[
                        ft.ElevatedButton(
                            content=ft.Text(
                                value ="Ok",
                                color=ft.Colors.WHITE,
                                ),
                            bgcolor=ft.Colors.GREEN_200,
                            on_click=lambda e : login_success(Donner ,Dial )
                        )
                    ]
                )
                #break  # stop after first match
        if not found:
            # show error dialog when no matching credentials found
            Dial = Dialog.custom_dialog(
                title = "Notification",
                content=ft.Column(
                    [
                        ft.Icon(
                            ft.Icons.ERROR_ROUNDED,
                            size = 60,
                            color=ft.Colors.RED_200,
                        ),
                        ft.Text(
                            value="Erreur de connexion"
                        )
                    ],
                    height=100,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                actions=[
                    ft.ElevatedButton(
                        content=ft.Text(
                            value ="Ok",
                            color=ft.Colors.WHITE,
                            ),
                        bgcolor=ft.Colors.RED_200,
                        on_click=lambda e : Dialog.close_dialog(Dial)
                    )
                ]
            )
    else:
        Dial = Dialog.custom_dialog(
            title = "Notification",
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.ERROR_ROUNDED,
                        size = 60,
                        color=ft.Colors.RED_200,
                    ),
                    ft.Text(
                        value="Erreur de connexion"
                    )
                ],
                height=100,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            actions=[
                ft.ElevatedButton(
                    content=ft.Text(
                        value ="Ok",
                        color=ft.Colors.WHITE,
                        ),
                    bgcolor=ft.Colors.RED_200,
                    on_click=lambda e : Dialog.close_dialog(Dial)
                )
            ]
        )
def Page0(page):#page: ft.Page):
    page.title = "Login page"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK
    #page.bgcolor = "#1a0d2e"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    
    # Fonction de connexion
    def learn_more_click(e):
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Learn More clicked!", color=ft.Colors.WHITE),
            bgcolor=ft.Colors.BLUE_700,
        )
        page.snack_bar.open = True
        page.update()
    
    # Champs de formulaire
    
    # Panneau gauche - Welcome
    left_panel = ft.Container(
        content=ft.Column([
            # Logo
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text("", size=0),
                        width=8,
                        height=30,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=2,
                    ),
                    ft.Container(width=5),
                    ft.Container(
                        content=ft.Text("", size=0),
                        width=8,
                        height=30,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=2,
                    ),
                ], spacing=0),
                margin=ft.margin.only(bottom=40),
            ),
            
            # Welcome text
            ft.Text(
                "Welcome",
                size=60,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
            ),
            
            ft.Text(
                "On BulletinPro !",
                size=25,
                #weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
            ),
            
            # Ligne d�corative
            ft.Container(
                width=80,
                height=4,
                bgcolor="#ff6b6b",
                border_radius=2,
                margin=ft.margin.only(top=10, bottom=30),
            ),
            
            # Description
            ft.Container(
                content=ft.Text(
                    value = "Simplifiez la gestion académique de votre établissement.Générez des bulletins scolaires professionnels en quelques clics, suivez les performances de vos élèves et concentrez-vous sur l'essentiel : leur réussite éducative.Commencez dès maintenant et transformez votre gestion scolaire !",

                    size=14,
                    color="#b8a7d1",
                    text_align=ft.TextAlign.LEFT,
                ),
                width=350,
                margin=ft.margin.only(bottom=40),
            ),
            
            # Bouton Learn More
        ], 
        horizontal_alignment=ft.CrossAxisAlignment.START,
        spacing=0),
        padding=60,
        alignment=ft.alignment.center_left,
    )
    
    # Ajout d'une fonction pour gérer la visibilité du mot de passe
    def toggle_password_visibility(e):
        Pass.password = not Pass.password
        e.control.icon = ft.Icons.VISIBILITY_OFF if Pass.password else ft.Icons.VISIBILITY
        page.update()
    
    Pass = ft.TextField(
        label="Password",
        hint_text="Password",
        password=True,
        color=ft.Colors.WHITE,
        suffix_icon=ft.IconButton(
            icon=ft.Icons.VISIBILITY_OFF,
            icon_color=ft.Colors.WHITE60,
            on_click=toggle_password_visibility,
            tooltip="Afficher/Masquer le mot de passe"
        ),
    )
    Ident = ft.TextField(
        label =  "User Name",
        hint_text =  "User Name",
        color=ft.Colors.WHITE,
    )
    
    def forgot_password(e):
        Dialog = ZeliDialog2(page)
        
        def validate_and_search(e):
            if not all([name_field.value, surname_field.value, email_field.value]):
                error_text.value = "Tous les champs sont obligatoires"
                page.update()
                return
                
            Donne = Get_on_db_local("User")
            found = False
            
            for user in Donne:
                # Structure: id(0), ident(1), pass(2), nom(3), prenom(4), annee(5), email(6)
                if all([user[3].lower() == name_field.value.lower(),
                       user[4].lower() == surname_field.value.lower(),
                       user[6].lower() == email_field.value.lower()]):
                    found = True
                    if user[8]: # Si c'est un mot de passe par défaut
                        Dialog.custom_dialog(
                            title="Récupération réussie",
                            content=ft.Column(
                                [
                                    ft.Icon(
                                        ft.Icons.CHECK_CIRCLE_OUTLINE,
                                        size=50,
                                        color=ft.Colors.GREEN
                                    ),
                                    ft.Text("Vos identifiants:"),
                                    ft.Container(height=10),
                                    ft.Text(f"Identifiant: {user[1]}", size=16),
                                    ft.Text(f"Mot de passe: {user[2]}", size=16, weight=ft.FontWeight.BOLD),
                                ],
                                height=200,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            actions=[
                                ft.ElevatedButton(
                                    text="Ok",
                                    bgcolor=ft.Colors.GREEN,
                                    color=ft.Colors.WHITE,
                                    on_click=lambda e: Dialog.close_dialog(search_dialog)
                                )
                            ]
                        )
                    else:
                        Dialog.alert_dialog(
                            title="Mot de passe personnalisé",
                            message="Vous avez personnalisé votre mot de passe. Veuillez répondre à votre question de sécurité."
                        )
                        security_dialog = Dialog.custom_dialog(
                            title="Question de sécurité",
                            content=ft.Column(
                                [
                                    ft.Text("Question:"),
                                    ft.Text(user[9], size=16, weight=ft.FontWeight.BOLD),  # question
                                    ft.Container(height=20),
                                    ft.TextField(
                                        label="Votre réponse",
                                        password=True
                                    ),
                                    ft.Text("", color="red")  # error text
                                ],
                                height=200,
                                width=400,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            actions=[
                                ft.TextButton("Annuler", 
                                            on_click=lambda e: Dialog.close_dialog(security_dialog)),
                                ft.ElevatedButton(
                                    "Vérifier",
                                    on_click=lambda e: verify_security_answer(
                                        security_dialog.content.controls[3].value,  # réponse
                                        user[10],  # réponse correcte
                                        security_dialog,
                                        user,
                                        security_dialog.content.controls[4]  # error text
                                    )
                                )
                            ]
                        )
                    break
                    
            if not found:
                error_text.value = "Aucun compte trouvé avec ces informations"
                page.update()

        def verify_security_answer(answer, correct_answer, dialog, user, error_text):
            if answer == correct_answer:
                Dialog.custom_dialog(
                    title="Identifiants récupérés",
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.LOCK_OPEN, color=ft.Colors.GREEN, size=50),
                            ft.Text("Vos identifiants:"),
                            ft.Text(f"Identifiant: {user[1]}", size=16),
                            ft.Text(f"Mot de passe: {user[2]}", size=16, weight=ft.FontWeight.BOLD)
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    actions=[
                        ft.ElevatedButton("Ok", 
                                        on_click=lambda e: [Dialog.close_dialog(dialog), 
                                                          Dialog.close_dialog(search_dialog)])
                    ]
                )
            else:
                error_text.value = "Réponse incorrecte"
                page.update()

        name_field = ft.TextField(
            label="Nom",
            hint_text="Votre nom",
            width=300,
            text_align=ft.TextAlign.CENTER,
        )
        
        surname_field = ft.TextField(
            label="Prénom",
            hint_text="Votre prénom",
            width=300,
            text_align=ft.TextAlign.CENTER,
        )
        
        email_field = ft.TextField(
            label="Email",
            hint_text="Votre email",
            width=300,
            text_align=ft.TextAlign.CENTER,
        )
        
        error_text = ft.Text(
            value="",
            color=ft.Colors.RED,
            size=12,
        )

        search_dialog = Dialog.custom_dialog(
            title="Récupération de mot de passe",
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.PASSWORD_ROUNDED,
                        size=50,
                        color=ft.Colors.BLUE,
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        "Veuillez entrer vos informations",
                        text_align=ft.TextAlign.CENTER,
                        size=14,
                    ),
                    ft.Container(height=20),
                    name_field,
                    surname_field,
                    email_field,
                    error_text,
                ],
                height=400,
                width=400,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10
            ),
            actions=[
                ft.TextButton(
                    text="Annuler",
                    on_click=lambda e: Dialog.close_dialog(search_dialog)
                ),
                ft.ElevatedButton(
                    text="Rechercher",
                    bgcolor=ft.Colors.BLUE,
                    color=ft.Colors.WHITE,
                    on_click=validate_and_search
                ),
            ]
        )

    # Panneau droit - Sign in
    right_panel = ft.Container(
        content=ft.Column([
            # Titre Sign in
            ft.Text(
                "Sign in",
                size=36,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
                text_align=ft.TextAlign.CENTER,
            ),
            
            ft.Container(height=30),
            
            # User Name
            ft.Column([
                Ident,
                ft.Container(height=8),
            ], spacing=0),
            
            ft.Container(height=20),
            
            # Password
            ft.Column([
                Pass,
                ft.Container(height=8),
            ], spacing=0),
            
            ft.Container(height=5),
            
            # Lien "Mot de passe oublié"
            ft.TextButton(
                text = "Mot de passe oublié",
                on_click=forgot_password,
                ),
            ft.Container(height=30),
            ft.Container(
                content=ft.Text(
                    "Submit",
                    size=16,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.WHITE,
                    text_align=ft.TextAlign.CENTER,
                ),
                width=280,
                height=50,
                bgcolor=None,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.center_left,
                    end=ft.alignment.center_right,
                    colors=["#ff7b54", "#ff5252"],
                ),
                border_radius=25,
                alignment=ft.alignment.center,
                ink=True,
                on_click = lambda e : Submit(page , Ident , Pass),
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=20,
                    color="#ff5252",
                    offset=ft.Offset(0, 5),
                ),
            ),
            
            ft.Container(height=25),
            
            # Social media Icons
            ft.Row([
                ft.IconButton(
                    icon=ft.Icons.FACEBOOK,
                    icon_color=ft.Colors.WHITE,
                    icon_size=22,
                    tooltip="Facebook",
                ),
                ft.IconButton(
                    icon=ft.Icons.CAMERA_ALT,
                    icon_color=ft.Colors.WHITE,
                    icon_size=22,
                    tooltip="Instagram",
                ),
                ft.IconButton(
                    icon=ft.Icons.PUSH_PIN,
                    icon_color=ft.Colors.WHITE,
                    icon_size=22,
                    tooltip="Pinterest",
                ),
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=15),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=0),
        bgcolor="#3d2f52",
        padding=50,
        border_radius=ft.border_radius.only(top_right=15, bottom_right=15),
        width=400,
        #alignment=ft.alignment.center,
    )
    
    # Conteneur principal avec fond d�coratif
    main_container = ft.Container(
        content=ft.Stack([
            # Formes d�coratives en arri�re-plan
            ft.Container(
                width=400,
                height=400,
                border_radius=200,
                bgcolor="#2d1b47",
                opacity=0.3,
                left=-100,
                top=-100,
            ),
            ft.Container(
                width=300,
                height=300,
                border_radius=150,
                bgcolor="#4a2d6b",
                opacity=0.2,
                right=-50,
                top=100,
            ),
            ft.Container(
                width=200,
                height=200,
                border_radius=100,
                bgcolor="#5c3d7a",
                opacity=0.25,
                left=100,
                bottom=-50,
            ),
            
            # Panneau de login avec effet glassmorphism
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=left_panel,
                        bgcolor="#2d1947",
                        expand=True,
                        border_radius=ft.border_radius.only(top_left=15, bottom_left=15),
                    ),
                    right_panel,
                ], spacing=0),
                width=900,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=50,
                    color="#000000",
                    offset=ft.Offset(0, 10),
                ),
                border_radius=15,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
            ),
        ]),
        alignment=ft.alignment.center,
        expand=True,
    )
    
    # Boutons en haut
    
    # Layout complet
    return ft.Stack([
            main_container,
        ], expand=True)

