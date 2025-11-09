#!/usr/bin/env python3
"""
Script de build Nuitka pour BulletinPro
Utilisation : python nuitka-build.py [windows|linux]
"""

import sys
import os
import subprocess
import platform

def build_windows():
    """Build Windows .exe"""
    print("🔨 Building Windows executable with Nuitka...")
    
    cmd = [
        "python", "-m", "nuitka",
        "--standalone",
        "--onefile",
        "--enable-plugin=tk-inter",
        "--windows-disable-console",
        "--include-data-files=config.py=config.py",
        "--output-dir=dist",
        "--output-filename=BulletinPro.exe",
        "--assume-yes-for-downloads",
        # Optimisations
        "--lto=yes",  # Link Time Optimization
        "--prefer-source-code",  # Meilleure compatibilité
        # Modules Flet (IMPORTANT !)
        "--include-package=flet",
        "--include-package=flet_core",
        "--include-package=flet_runtime",
        "--include-module=flet_desktop",
        # Autres modules à inclure
        "--include-module=sqlite3",
        "--include-module=weasyprint",
        "--include-module=jinja2",
        "--include-module=supabase",
        "--include-module=dotenv",
        # Fichier principal
        "Page2.py"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ Build Windows terminé : dist/BulletinPro.exe")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur build : {e}")
        sys.exit(1)

def build_linux():
    """Build Linux executable"""
    print("🔨 Building Linux executable with Nuitka...")
    
    cmd = [
        "python", "-m", "nuitka",
        "--standalone",
        "--onefile",
        "--enable-plugin=tk-inter",
        "--include-data-files=config.py=config.py",
        "--output-dir=dist",
        "--output-filename=BulletinPro",
        "--assume-yes-for-downloads",
        # Optimisations
        "--lto=yes",
        "--prefer-source-code",
        # Modules
        "--include-module=flet",
        "--include-module=sqlite3",
        "--include-module=weasyprint",
        "--include-module=jinja2",
        "--include-module=supabase",
        "--include-module=dotenv",
        # Fichier principal
        "Page2.py"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        
        # Rendre exécutable
        os.chmod("dist/BulletinPro", 0o755)
        
        print("✅ Build Linux terminé : dist/BulletinPro")
        
        # Créer le .deb
        print("\n📦 Création du package .deb...")
        create_deb_package()
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur build : {e}")
        sys.exit(1)

def create_deb_package():
    """Crée le package .deb"""
    import shutil
    
    version = "1.0.0"
    arch = "amd64"
    package_name = f"bulletinpro_{version}_{arch}"
    
    # Créer structure
    dirs = [
        f"{package_name}/DEBIAN",
        f"{package_name}/usr/bin",
        f"{package_name}/usr/share/applications",
        f"{package_name}/usr/share/doc/bulletinpro",
    ]
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    
    # Copier l'exécutable
    shutil.copy("dist/BulletinPro", f"{package_name}/usr/bin/bulletinpro")
    os.chmod(f"{package_name}/usr/bin/bulletinpro", 0o755)
    
    # Control file
    with open(f"{package_name}/DEBIAN/control", "w") as f:
        f.write(f"""Package: bulletinpro
Version: {version}
Section: education
Priority: optional
Architecture: {arch}
Depends: libcairo2, libpango-1.0-0, libgdk-pixbuf2.0-0
Maintainer: BulletinPro Team <contact@bulletinpro.com>
Description: Système de gestion de bulletins scolaires
 Application complète de gestion scolaire.
""")
    
    # Desktop entry
    with open(f"{package_name}/usr/share/applications/bulletinpro.desktop", "w") as f:
        f.write("""[Desktop Entry]
Version=1.0
Type=Application
Name=BulletinPro
Comment=Gestion de bulletins scolaires
Exec=/usr/bin/bulletinpro
Terminal=false
Categories=Education;Office;
""")
    
    # Build .deb
    subprocess.run(["dpkg-deb", "--build", package_name], check=True)
    
    print(f"✅ Package .deb créé : {package_name}.deb")

def main():
    """Point d'entrée principal"""
    
    # Détecter l'OS si pas spécifié
    if len(sys.argv) > 1:
        target = sys.argv[1].lower()
    else:
        system = platform.system().lower()
        target = "windows" if system == "windows" else "linux"
    
    print(f"🎯 Target : {target}")
    print(f"🐍 Python : {sys.version}")
    
    # Vérifier Nuitka
    try:
        import nuitka
        print(f"✅ Nuitka : {nuitka.__version__}")
    except ImportError:
        print("❌ Nuitka n'est pas installé")
        print("Installez-le : pip install nuitka ordered-set zstandard")
        sys.exit(1)
    
    # Build
    if target == "windows":
        build_windows()
    elif target == "linux":
        build_linux()
    else:
        print(f"❌ Target inconnu : {target}")
        print("Usage : python nuitka-build.py [windows|linux]")
        sys.exit(1)

if __name__ == "__main__":
    main()
