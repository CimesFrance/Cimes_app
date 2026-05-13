"""
Main entry point for the Cimes application
"""

import sys
import os
import warnings

# Redirection des logs vers un fichier pour le débogage de l'exécutable
if getattr(sys, 'frozen', False):
    log_path = os.path.join(os.path.dirname(sys.executable), "debug_log.txt")
    try:
        sys.stdout = open(log_path, 'w', encoding='utf-8')
        sys.stderr = sys.stdout
    except Exception:
        pass
    print(f"=== Démarrage de l'application (Frozen mode) ===")
    print(f"Executable: {sys.executable}")
    print(f"MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}")

# Gestion du dossier des DLL de torch dans l'exécutable
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Chemins possibles pour les DLLs de torch (dépend de onedir vs onefile)
    torch_dll_paths = [
        os.path.join(sys._MEIPASS, "_internal", "torch", "lib"),
        os.path.join(sys._MEIPASS, "torch", "lib")
    ]
    for torch_dll_path in torch_dll_paths:
        if os.path.exists(torch_dll_path):
            print(f"Ajout du dossier DLL torch: {torch_dll_path}")
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(torch_dll_path)
            else:
                os.environ["PATH"] = torch_dll_path + os.pathsep + os.environ["PATH"]
    
    # Import anticipé de torch pour stabiliser le chargement des DLLs
    try:
        import torch
        print(f"Torch chargé avec succès (version {torch.__version__})")
        print(f"CUDA disponible: {torch.cuda.is_available()}")
    except Exception as e:
        print(f"Erreur lors du pré-chargement de torch: {e}")

from src.ui.main_app import CimesApp


warnings.filterwarnings("ignore")

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    # pylint: disable=protected-access
    sys.path.insert(0, sys._MEIPASS)
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


if __name__ == "__main__":
    # Gestion des modules secondaires via arguments pour l'exécutable PyInstaller
    if len(sys.argv) > 1:
        if sys.argv[1] == "--module-calibration":
            from modules.app_calibrage_cam.ui.main_window import ApplicationCalibrage
            app = ApplicationCalibrage()
            app.mainloop()
            sys.exit()
        elif sys.argv[1] == "--module-correction":
            from modules.app_change_corr_params.src.ui.main_window import CIMESApp
            app = CIMESApp()
            app.mainloop()
            sys.exit()
    try:
        app = CimesApp()
        app.mainloop()
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Erreur : {e}")
        import traceback
        traceback.print_exc()
        input("Appuyez sur Entrée pour quitter...")
