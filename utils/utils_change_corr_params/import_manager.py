import os
from PIL import Image, ImageTk
import zipfile
import pandas as pd

def importer_image_tk(nom_image):
    dossier_script = os.path.dirname(os.path.abspath(__file__))
    chemin_fichier = os.path.join(dossier_script, nom_image)
    img = Image.open(chemin_fichier)
    img = img.resize((24, 24), Image.LANCZOS)
    return ImageTk.PhotoImage(img)


def info_extract_courbe_numerique(zip_file):
    with zipfile.ZipFile(zip_file, "r") as z:
        # --- Lire le CSV directement dans un DataFrame ---
        with z.open("data.csv") as f:
            df = pd.read_csv(f)
        # --- Lire le TXT directement dans une variable ---
        with z.open("params_correction.txt") as f:
            texte = f.read().decode("utf-8")  # convertir les bytes en strin
    variables = {}
    for ligne in texte.splitlines():
        # ignorer les lignes vides
        if ligne.strip():
            # séparer par le '='
            nom, val = ligne.split("=")
            nom = nom.strip()        # enlever espaces autour du nom
            val = val.strip()        # enlever espaces autour de la valeur
            # convertir en float si possible
            try:
                val = float(val)
            except ValueError:
                pass  # garder en string si ce n'est pas un nombre
            variables[nom] = val
    granulometrie = {"tamis" : df["Tamis(mm)"].tolist() , "cumul" : df["Cumul(%)"].tolist()}
    return granulometrie , variables