# -*- coding: utf-8 -*-
import warnings
warnings.filterwarnings('ignore')

import sys
import os

# Ajouter la racine au path pour que les imports src.* fonctionnent
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.main_app import CimesApp

if __name__ == "__main__":
    try:
        app = CimesApp()
        app.mainloop()
    except Exception as e:
        print(f"Erreur : {e}")
        import traceback
        traceback.print_exc()
        input("Appuyez sur Entrée pour quitter...")