# -*- coding: utf-8 -*-
"""
Initialisation de toutes les variables tkinter de l'application principale.
"""
import tkinter as tk
import os
import time

from src.ui.widgets.ui_utils import (
    COLOR_STATUS_STOPPED, LOGO_PATH
)
from src.utils.file_manager import load_correction_parameters, load_conversion_param


def initialize_variables(app):
    """Initialise toutes les variables de l'application sur l'objet app."""

    # État de la caméra
    app.camera_running = False
    app.video_stream = None
    app._after_id = None
    app._countdown_id = None
    app.frame_index = 0
    app.captured_count = 0
    app.last_capture_time = time.time()

    # Variables d'état
    app.status_color_var = tk.StringVar(value=COLOR_STATUS_STOPPED)
    app.status_var = tk.StringVar(value="ARRÊTÉE")
    app.last_capture_time_var = tk.StringVar(value="N/A")
    app.datetime_var = tk.StringVar()
    app.images_count_var = tk.StringVar(value="0")
    app.status_detail_var = tk.StringVar(value="(Hors-ligne)")

    # Paramètres du capteur
    app.url_var = tk.StringVar(value="rtsp://192.168.1.30:554/stream1")
    app.save_path_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "CIMES_Data"))
    app.start_time_var = tk.StringVar(value="08:00")
    app.end_time_var = tk.StringVar(value="18:00")
    app.capture_time_val_var = tk.StringVar(value="5")
    app.capture_time_unit_var = tk.StringVar(value="s")
    app.save_delay_display_var = tk.StringVar(value="5 s")

    # Statistiques
    app.time_left_capture_var = tk.StringVar(value="--")
    app.particles_count_var = tk.StringVar(value="0")
    app.last_captured_frame = None

    # Jours de fonctionnement
    app.days_vars = {
        "Lundi":    tk.BooleanVar(value=True),
        "Mardi":    tk.BooleanVar(value=True),
        "Mercredi": tk.BooleanVar(value=True),
        "Jeudi":    tk.BooleanVar(value=True),
        "Vendredi": tk.BooleanVar(value=True),
        "Samedi":   tk.BooleanVar(value=False),
        "Dimanche": tk.BooleanVar(value=False),
    }

    # Mode de capture
    app.capture_mode_var = tk.StringVar(value="automatique")

    # Transmission
    app.transmission_enabled_var = tk.BooleanVar(value=False)
    app.transmission_mode_var = tk.StringVar(value="capture")
    app.transmission_time_var = tk.StringVar(value="17:00")
    app.transmission_email_var = tk.StringVar(value="")

    # Chemins
    app.results_path_var = tk.StringVar(
        value=os.path.join(os.path.expanduser("~"), "CIMES_Results")
    )

    # Comparaison et rapports
    app.comparison_captures = []
    app.comparison_mode = False
    app.selected_captures_for_report = []
    app.report_logo_path = LOGO_PATH
    app.report_commentary = tk.StringVar(value="")
    app.show_corrected_curve_var = tk.BooleanVar(value=True)

    # Données
    app.daily_data = []
    app.capture_history = []
    app.current_capture_index = -1

    # Navigation
    app.nav_buttons = {}

    # Options du rapport
    app.report_options = {
        "include_captured_image":    tk.BooleanVar(value=True),
        "include_segmented_image":   tk.BooleanVar(value=True),
        "include_granulometric_curve": tk.BooleanVar(value=True),
        "include_distribution_curve": tk.BooleanVar(value=True),
        "include_statistics":        tk.BooleanVar(value=True),
        "custom_comment":            tk.StringVar(value=""),
    }

    # Correction empirique
    vars_corr = load_correction_parameters()
    app.correction_granulo = {
        "scale":  tk.DoubleVar(value=vars_corr["scale"]),
        "offset": tk.DoubleVar(value=vars_corr["offset"]),
    }

    # Calibration
    app.use_undistortion_var = tk.BooleanVar(value=False)
    app.use_homography_var = tk.BooleanVar(value=False)
    app.mtx = None
    app.dist = None
    app.calib_path = None
    app.homo_matrix = None

    # Conversion mm-pixel : chargé depuis le JSON de calibration
    # facteur_conversion = "coefficient de conversion pixel-mm" et "Échelle (mm/px)"
    param = load_conversion_param()
    app.facteur_conversion = tk.StringVar(value=str(param))
