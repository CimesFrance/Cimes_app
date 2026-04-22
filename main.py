# -*- coding: utf-8 -*-
import warnings
warnings.filterwarnings('ignore')

from gui.main_app import CimesApp


if __name__ == "__main__":
    try:
        app = CimesApp()
        app.mainloop()
    except Exception as e:
        print(f"Erreur : {e}")
        import traceback
        traceback.print_exc()
        input("Appuyez sur Entrée pour quitter...")