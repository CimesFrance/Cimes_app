import os
import json
from tkinter import messagebox
import cv2
import numpy as np
from datetime import datetime
import zipfile
import pandas as pd
from io import StringIO

def creer_dossier(path):
    """Crée un dossier s'il n'existe pas"""
    os.makedirs(path, exist_ok=True)
    return path

def save_capture_data(capture_data, results_path, app):
    """Sauvegarde les données d'une capture"""
    try:
        # Créer le dossier principal avec la date
        main_date_dir = os.path.join(results_path, 
                                    capture_data['timestamp'].strftime("%Y-%m-%d"))
        os.makedirs(main_date_dir, exist_ok=True)
        # Créer un dossier unique pour cette exécution
        if not hasattr(app, 'current_session_dir'):
            start_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            app.current_session_dir = os.path.join(main_date_dir, f"execution_{start_time}")
            os.makedirs(app.current_session_dir, exist_ok=True)
        # Compter les captures dans cette session
        existing_captures = []
        for item in os.listdir(app.current_session_dir):
            if os.path.isdir(os.path.join(app.current_session_dir, item)) and item.startswith("capture_"):
                existing_captures.append(item)
        if existing_captures:
            capture_numbers = [int(c.split("_")[1]) for c in existing_captures]
            capture_number = max(capture_numbers) + 1
        else:
            capture_number = 1
        # Créer le dossier de capture
        capture_dir = os.path.join(app.current_session_dir, f"capture_{capture_number}")
        os.makedirs(capture_dir, exist_ok=True)
        # Sauvegarde de courbe 
        if len(app.capture_history) > 0:
            zip_measure_path = os.path.join(capture_dir, f"mesure.zip")
            data = [[tamis,cumul] for tamis, cumul in zip(app.capture_history[-1]['tamis_exp'],app.capture_history[-1]['cumulative_corrected'])]
            colonnes = ["Tamis(mm)", "Cumul(%)"]
            df = pd.DataFrame(data, columns=colonnes)
            # On écrit le CSV dans un buffer en mémoire (pour éviter de créer un .csv qu'on ne va pas utiliser)
            buffer_csv = StringIO()
            df.to_csv(buffer_csv, index=False)
            texte = "Scale = "+str(app.correction_granulo["scale"].get())+"\nOffset = "+str(app.correction_granulo["offset"].get())
            with zipfile.ZipFile(zip_measure_path, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("data.csv", buffer_csv.getvalue())
                z.writestr("params_correction.txt", texte)
        # Sauvegarde des fichiers
        if capture_data['image_processed'] is not None:
            raw_path = os.path.join(capture_dir, f"raw.png")
            cv2.imwrite(raw_path, capture_data['image_processed'])
        if capture_data['segmented_image'] is not None:
            seg_path = os.path.join(capture_dir, f"segmented.png")
            cv2.imwrite(seg_path, cv2.cvtColor(capture_data['segmented_image'], cv2.COLOR_RGB2BGR))
        # Extraire les données pour les statistiques
        particles_data = capture_data.get('particles_data', [])
        minor_axes_mm = capture_data.get('minor_axes_mm', [])
        major_axes_mm = []
        for particle in particles_data:
            if 'major_axis_mm' in particle:
                major_axes_mm.append(particle['major_axis_mm'])
        # Calculer les statistiques
        from src.core.statistics import calculer_statistiques_granulometriques, generer_rapport_statistique
        if particles_data and minor_axes_mm:
            stats = calculer_statistiques_granulometriques(
                particles_data, 
                minor_axes_mm,
                major_axes_mm
            )
            if stats:
                # Sauvegarder les statistiques JSON
                stats_path = os.path.join(capture_dir, f"statistiques.json")
                with open(stats_path, 'w', encoding='utf-8') as f:
                    json.dump(stats, f, indent=4, ensure_ascii=False, default=str)
                # Sauvegarder le rapport texte
                report_path = os.path.join(capture_dir, f"rapport.txt")
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(generer_rapport_statistique(stats))
        # Sauvegarder les données JSON complètes
        data_path = os.path.join(capture_dir, f"data.json")
        with open(data_path, 'w', encoding='utf-8') as f:
            json_data = {
                'id': capture_data['id'],
                'timestamp': capture_data['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                'particles_count': capture_data['particles_count'],
                'scale': capture_data['scale'],
                'particle_sizes_mm': capture_data['minor_axes_mm'],
                'tamis_exp': capture_data['tamis_exp'],
                'cumulative_raw': capture_data['cumulative_raw'],
                'cumulative_corrected': capture_data['cumulative_corrected']
            }
            # Ajouter les dimensions si disponibles
            if 'stats' in locals() and stats:
                json_data['dimensions'] = {
                    'minor_axis_min_mm': stats.get('min_mm_minor', 0),  
                    'minor_axis_max_mm': stats.get('max_mm_minor', 0),  
                    'minor_axis_mean_mm': stats.get('moyenne_mm_minor', 0),  
                    'major_axis_min_mm': stats.get('min_mm_major', 0),  
                    'major_axis_max_mm': stats.get('max_mm_major', 0),  
                    'major_axis_mean_mm': stats.get('moyenne_mm_major', 0),  
                }
            json.dump(json_data, f, indent=4, ensure_ascii=False)
        print(f"[SAUVEGARDE] Capture #{capture_data['id']} sauvegardée dans {capture_dir}")
    except Exception as e:
        messagebox.showerror("Erreur Sauvegarde", f"Échec de la sauvegarde des données de capture.\n\nDétails : {e}")

def load_calibration_files():
    """Charge les fichiers de calibration automatiquement"""
    print("[CALIBRATION] Recherche des fichiers de calibration...")
    mtx = None
    dist = None
    homo_matrix = None
    # Chemin du répertoire racine
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    # 1. Charger camera_params.npz
    camera_params_path = os.path.join(root_dir, "assets", "calibration_maj_1.npz")
    if os.path.exists(camera_params_path):
        try:
            data = np.load(camera_params_path)
            mtx = data['camMatrix']
            dist = data['distCoeff']
            print(f"[CALIBRATION]  camera_params.npz chargé depuis {camera_params_path}")
        except Exception as e:
            messagebox.showwarning("Calibration", f"Erreur lors du chargement des paramètres de caméra (Calibration).\n\nDétails : {e}")
    else:
        print(f"[CALIBRATION]  Fichier introuvable: {camera_params_path}")
    
    # # 2. Charger homography.npz
    # homography_path = os.path.join(current_dir, "homography.npz")
    # if os.path.exists(homography_path):
    #     try:
    #         data = np.load(homography_path)
    #         homo_matrix = data["H"]
    #         print(f"[CALIBRATION]  homography.npz chargé depuis {homography_path}")
    #     except Exception as e:
    #         print(f"[CALIBRATION]  Erreur chargement homography: {e}")
    # else:
    #     print(f"[CALIBRATION]  Fichier introuvable: {homography_path}")
    return mtx, dist, camera_params_path

def ensure_results_directory(results_path):
    """S'assure que le dossier de résultats existe"""
    try:
        os.makedirs(results_path, exist_ok=True)
        print(f"[DIRECTORY] Dossier de résultats prêt: {results_path}")
        return True
    except Exception as e:
        messagebox.showerror("Erreur Dossier", f"Impossible de créer le dossier des réglages.\n\nDétails : {e}")
        return False

def get_settings_dir():
    """Renvoie le dossier de paramètres standard (~/CIMES_Settings)"""
    save_dir = os.path.join(os.path.expanduser("~"), "CIMES_Settings")
    os.makedirs(save_dir, exist_ok=True)
    return save_dir

def load_correction_parameters():
    """Charge les paramètres de correction depuis le fichier JSON central"""
    settings_file = os.path.join(get_settings_dir(), "correction_settings.json")
    
    # Valeurs par défaut
    params = {"scale": 1.0, "offset": 0.0}
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                params.update(json.load(f))
        except Exception as e:
            messagebox.showwarning("Chargement Paramètres", f"Erreur lors du chargement des paramètres de correction.\n\nDétails : {e}")     
    # Tentative de migration depuis l'ancien format .txt si le JSON n'existe pas ou est incomplet
    old_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "param_correct.txt")
    if not os.path.exists(settings_file) and os.path.exists(old_file):
        try:
            with open(old_file, "r", encoding="utf-8") as f:
                for line in f:
                    if "=" in line:
                        k, v = line.split("=")
                        params[k.strip().lower()] = float(v.strip())
            # Sauvegarde immédiate au nouveau format
            save_correction_parameters(params['scale'], params['offset'])
        except:
            pass
    return params

def save_correction_parameters(scale, offset):
    """Sauvegarde les paramètres de correction en format JSON"""
    settings_file = os.path.join(get_settings_dir(), "correction_settings.json")
    data = {"scale": scale, "offset": offset}
    try:
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        messagebox.showerror("Sauvegarde Paramètres", f"Impossible de sauvegarder les paramètres de correction.\n\nDétails : {e}")

def load_conversion_param():
    """Charge le facteur de conversion mm/pixel depuis le fichier JSON central"""
    settings_file = os.path.join(get_settings_dir(), "calibration_settings.json")
    valeur = 1.0
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                valeur = data.get("facteur_conversion", 1.0)
        except Exception as e:
            messagebox.showwarning("Chargement Calibration", f"Erreur lors du chargement du facteur de conversion.\n\nDétails : {e}")   
    # Migration depuis l'ancien format .txt
    old_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "param_convers_mm_pixel.txt")
    if not os.path.exists(settings_file) and os.path.exists(old_file):
        try:
            with open(old_file, "r", encoding="utf-8") as f:
                line = f.read().strip()
                if "=" in line:
                    _, v = line.split("=")
                    valeur = float(v.strip())
            save_conversion_parameter(valeur)
        except:
            pass   
    return valeur

def save_conversion_parameter(param):
    """Sauvegarde le facteur de conversion mm/pixel en format JSON"""
    settings_file = os.path.join(get_settings_dir(), "calibration_settings.json")
    data = {"facteur_conversion": param}
    try:
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        messagebox.showerror("Sauvegarde Calibration", f"Impossible de sauvegarder le facteur de conversion.\n\nDétails : {e}")
        
        
