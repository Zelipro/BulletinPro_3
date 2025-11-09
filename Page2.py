from Page0 import Page0
from Page1 import Page1
import flet as ft

def main(page : ft.Page):
    page.add(
        Page0(page)
    )
    
ft.app(target=main)