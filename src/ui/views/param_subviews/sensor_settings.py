# -*- coding: utf-8 -*-
"""Paramètres du capteur : URL, chemin, horaires, mode de capture."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os

from src.ui.widgets.ui_utils import (
    COLOR_CARD_BG, COLOR_STATUS_RUNNING, COLOR_ACCENT,
    create_setting_header
)


def create_sensor_settings(view):
    """
    Construit le frame 'Capteur' et le retourne.
    view = l'instance ParamView.
    """
    frame = ttk.Frame(view.param_content_frame, style="Card.TFrame")
    create_setting_header(frame, "Configuration du Capteur")

    inner = tk.Frame(frame, bg=COLOR_CARD_BG, padx=40, pady=20)
    inner.pack(fill="both", expand=True)

    # Adresse IP RTSP
    tk.Label(inner, text="Adresse IP du Capteur RTSP", bg=COLOR_CARD_BG, fg="#111827",
             anchor="w", font=("Segoe UI", 10, "bold")).pack(fill="x", pady=(0, 5))
    ttk.Entry(inner, textvariable=view.app.url_var, width=50,
              font=("Segoe UI", 10)).pack(fill="x")
    tk.Label(inner,
             text="Exemple : rtsp://utilisateur:motdepasse@192.168.1.10:554/stream",
             bg=COLOR_CARD_BG, fg="#6b7280",
             font=("Segoe UI", 8, "italic")).pack(fill="x", pady=(2, 20))

    # Chemin de sauvegarde
    tk.Label(inner, text="Chemin de sauvegarde des résultats", bg=COLOR_CARD_BG, fg="#111827",
             anchor="w", font=("Segoe UI", 10, "bold")).pack(fill="x", pady=(0, 5))

    path_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
    path_frame.pack(fill="x", pady=(0, 20))

    ttk.Entry(path_frame, textvariable=view.app.results_path_var, width=50,
              font=("Segoe UI", 10)).pack(side="left", fill="x", expand=True)
    ttk.Button(path_frame, text="Parcourir", style="ParamAction.TButton",
               command=lambda: _browse_results_path(view)).pack(side="left", padx=(10, 0))

    ttk.Separator(inner, orient="horizontal").pack(fill="x", pady=(10, 20))

    # Mode de capture
    tk.Label(inner, text="Mode de capture", bg=COLOR_CARD_BG, fg="#111827", anchor="w",
             font=("Segoe UI", 10, "bold")).pack(fill="x", pady=(0, 10))

    mode_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
    mode_frame.pack(fill="x", pady=(0, 15))

    ttk.Radiobutton(mode_frame, text="Automatique", value="automatique",
                    variable=view.app.capture_mode_var,
                    command=view._toggle_capture_controls).pack(side="left", padx=(0, 30))
    ttk.Radiobutton(mode_frame, text="Manuel", value="manuel",
                    variable=view.app.capture_mode_var,
                    command=view._toggle_capture_controls).pack(side="left")

    # Paramètres automatiques
    view.auto_params_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
    view.auto_params_frame.pack(fill="x", pady=(0, 20))

    tk.Label(view.auto_params_frame, text="Intervalle entre captures :",
             bg=COLOR_CARD_BG, fg="#4b5563", anchor="w",
             font=("Segoe UI", 9)).pack(fill="x", pady=(0, 5))

    view.capture_interval_frame = tk.Frame(view.auto_params_frame, bg=COLOR_CARD_BG)
    view.capture_interval_frame.pack(fill="x", pady=(0, 15))

    ttk.Entry(view.capture_interval_frame, textvariable=view.app.capture_time_val_var,
              width=10, font=("Segoe UI", 10)).pack(side="left")
    ttk.Combobox(view.capture_interval_frame, textvariable=view.app.capture_time_unit_var,
                 values=["s", "min", "h"], width=5, state="readonly",
                 font=("Segoe UI", 10)).pack(side="left", padx=(10, 0))

    # Programmation des heures
    tk.Label(view.auto_params_frame,
             text="Programmation des heures de fonctionnement :",
             bg=COLOR_CARD_BG, fg="#4b5563", anchor="w",
             font=("Segoe UI", 9)).pack(fill="x", pady=(5, 5))

    view.time_frame = tk.Frame(view.auto_params_frame, bg=COLOR_CARD_BG)
    view.time_frame.pack(fill="x", pady=(0, 15))

    tk.Label(view.time_frame, text="Début :", bg=COLOR_CARD_BG, fg="#4b5563",
             font=("Segoe UI", 9)).pack(side="left", padx=(0, 5))
    ttk.Entry(view.time_frame, textvariable=view.app.start_time_var, width=8,
              font=("Segoe UI", 10)).pack(side="left", padx=(0, 20))
    tk.Label(view.time_frame, text="Fin :", bg=COLOR_CARD_BG, fg="#4b5563",
             font=("Segoe UI", 9)).pack(side="left", padx=(0, 5))
    ttk.Entry(view.time_frame, textvariable=view.app.end_time_var, width=8,
              font=("Segoe UI", 10)).pack(side="left")

    # Jours de fonctionnement
    tk.Label(view.auto_params_frame, text="Jours de fonctionnement :",
             bg=COLOR_CARD_BG, fg="#4b5563", anchor="w",
             font=("Segoe UI", 9)).pack(fill="x", pady=(5, 5))

    view.days_frame = tk.Frame(view.auto_params_frame, bg=COLOR_CARD_BG)
    view.days_frame.pack(fill="x", pady=(0, 20))

    for jour in ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]:
        ttk.Checkbutton(view.days_frame, text=jour[:3],
                        variable=view.app.days_vars[jour]).pack(side="left", padx=(0, 15))

    # Paramètres manuels
    view.manual_params_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
    view.manual_params_frame.pack(fill="x", pady=(0, 20))

    tk.Label(view.manual_params_frame,
             text="En mode manuel, vous déclenchez les captures manuellement\n"
                  "en cliquant sur le bouton 'Capture Manuelle' dans la vue Mesure.",
             bg=COLOR_CARD_BG, fg="#6b7280",
             font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(0, 0))

    # Bouton de sauvegarde
    ttk.Separator(inner, orient="horizontal").pack(fill="x", pady=(0, 20))
    
    button_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
    button_frame.pack(fill="x", pady=(0, 10))
    ttk.Button(button_frame, text="Sauvegarder les Paramètres",
               style="ParamSave.TButton",
               command=lambda: _save_sensor_settings(view)).pack(side="left")

    view._toggle_capture_controls()
    return frame


def _browse_results_path(view):
    folder = filedialog.askdirectory(
        parent=view.app, title="Sélectionner le dossier de sauvegarde des résultats"
    )
    if folder:
        view.app.results_path_var.set(folder)


def _save_sensor_settings(view):
    settings = {
        "url":          view.app.url_var.get(),
        "results_path": view.app.results_path_var.get(),
        "start_time":   view.app.start_time_var.get(),
        "end_time":     view.app.end_time_var.get(),
        "days_active":  {day: var.get() for day, var in view.app.days_vars.items()},
        "capture_interval": {
            "value": view.app.capture_time_val_var.get(),
            "unit":  view.app.capture_time_unit_var.get(),
        },
        "capture_mode": view.app.capture_mode_var.get(),
        "scale":        view.app.scale_var.get(),
        "dna_correction_enabled": view.app.show_corrected_curve_var.get(),
    }
    try:
        save_dir = os.path.join(os.path.expanduser("~"), "CIMES_Settings")
        os.makedirs(save_dir, exist_ok=True)
        with open(os.path.join(save_dir, "sensor_settings.json"), "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)

        if hasattr(view.app, "measure_view"):
            view.app.measure_view.update_active_params_display()
        if hasattr(view.app, "curve_view") and view.app.curve_view.frame.winfo_ismapped():
            view.app.curve_view._update_curve_view()

        messagebox.showinfo("Succès", "Paramètres du capteur sauvegardés avec succès !")
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde : {str(e)}")
