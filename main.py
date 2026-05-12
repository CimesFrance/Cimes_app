"""
Main entry point for the Cimes application
"""

import sys
import os
import warnings

#Gestion du dossier des DLL de torch dans l'exécutable
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Ajout du dossier des DLLs de torch au chemin de recherche
    torch_dll_path = os.path.join(sys._MEIPASS, "_internal", "torch", "lib")
    if os.path.exists(torch_dll_path):
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(torch_dll_path)
        else:
            os.environ["PATH"] = torch_dll_path + os.pathsep + os.environ["PATH"]
    
    # Import anticipé de torch pour stabiliser le chargement des DLLs
    try:
        import torch
    except ImportError:
        pass

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
