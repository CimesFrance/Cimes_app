# -*- coding: utf-8 -*-
"""Paramètres de calibration caméra : fichiers npz, corrections, échelle."""
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import numpy as np
import subprocess
import threading
import sys

from src.ui.widgets.ui_utils import (
    COLOR_CARD_BG, COLOR_ACCENT, create_setting_header
)
from src.utils.file_manager import load_calibration_files, load_conversion_param, get_project_root


def create_calibration_settings(view):
    """Construit le frame 'Calibration' et le retourne."""
    frame = ttk.Frame(view.param_content_frame, style="Card.TFrame")
    create_setting_header(frame, "Calibration Caméra")

    inner = tk.Frame(frame, bg=COLOR_CARD_BG, padx=40, pady=20)
    inner.pack(fill="both", expand=True)

    # Statut calibration
    tk.Label(inner, text="Statut de calibration", bg=COLOR_CARD_BG, fg="#111827",
             anchor="w", font=("Segoe UI", 11, "bold")).pack(fill="x", pady=(0, 10))

    status_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
    status_frame.pack(fill="x", pady=(0, 20))

    row1 = tk.Frame(status_frame, bg=COLOR_CARD_BG)
    row1.pack(fill="x", pady=5)
    _, _, cam_calib_path = load_calibration_files()
    tk.Label(row1, text=f"Le fichier de calibration utilisé est : {cam_calib_path}",
             bg=COLOR_CARD_BG, font=("Segoe UI", 10)).pack(anchor="w")

    row2 = tk.Frame(status_frame, bg=COLOR_CARD_BG)
    row2.pack(fill="x", pady=5)
    tk.Label(row2, text="le coefficient de conversion pixel-mm actuel : ",
             bg=COLOR_CARD_BG, font=("Segoe UI", 10), anchor="w").pack(side="left")
    tk.Label(row2, textvariable=view.app.facteur_conversion, bg=COLOR_CARD_BG,
             font=("Segoe UI", 10), anchor="w").pack(side="left")
    ttk.Button(row2, text="Modifier", style="ParamAction.TButton",
               command=lambda: _call_measure_app(view)).pack(side="left", padx=(10, 0))

    tk.Label(inner,
             text="Les fichiers de calibration sont automatiquement chargés au démarrage\n"
                  "s'ils sont présents dans le dossier de l'application.",
             bg=COLOR_CARD_BG, fg="#6b7280",
             font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(0, 15))

    ttk.Separator(inner, orient="horizontal").pack(fill="x", pady=(5, 15))

    # Correction d'image
    tk.Label(inner, text="Correction d'image", bg=COLOR_CARD_BG, fg="#111827",
             anchor="w", font=("Segoe UI", 11, "bold")).pack(fill="x", pady=(0, 10))

    corr_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
    corr_frame.pack(fill="x", pady=(0, 10))

    view.undistort_check = ttk.Checkbutton(corr_frame,
                                           text="Utiliser la correction de distorsion",
                                           variable=view.app.use_undistortion_var,
                                           command=lambda: _update_undistort_status(view))
    view.undistort_check.pack(anchor="w", pady=(5, 0))

    view.homography_check = ttk.Checkbutton(corr_frame,
                                            text="Utiliser la correction d'homographie",
                                            variable=view.app.use_homography_var,
                                            command=lambda: _update_homography_status(view))
    view.homography_check.pack(anchor="w", pady=(5, 0))

    tk.Label(corr_frame,
             text="Ces corrections sont appliquées automatiquement lors de l'analyse.",
             bg=COLOR_CARD_BG, fg="#6b7280",
             font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(5, 10))

    ttk.Separator(inner, orient="horizontal").pack(fill="x", pady=(5, 15))

    # Échelle de calibration
    tk.Label(inner, text="Échelle de calibration", bg=COLOR_CARD_BG, fg="#111827",
             anchor="w", font=("Segoe UI", 11, "bold")).pack(fill="x", pady=(0, 10))

    scale_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
    scale_frame.pack(fill="x", pady=(0, 10))

    tk.Label(scale_frame, text="Échelle (mm/px):", bg=COLOR_CARD_BG,
             font=("Segoe UI", 10), width=15, anchor="w").pack(side="left")

    view.calibration_scale_entry = ttk.Entry(
        scale_frame, textvariable=view.app.calibration_scale_var,
        width=15, font=("Segoe UI", 10)
    )
    view.calibration_scale_entry.pack(side="left", padx=(5, 10))

    view.apply_scale_btn = ttk.Button(scale_frame, text="Appliquer",
                                      style="ParamAction.TButton",
                                      command=lambda: _apply_calibration_scale(view))
    view.apply_scale_btn.pack(side="left")

    # Valeur actuelle
    current_scale_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
    current_scale_frame.pack(fill="x", pady=(5, 0))

    tk.Label(current_scale_frame, text="Échelle actuelle:", bg=COLOR_CARD_BG,
             font=("Segoe UI", 10), width=15, anchor="w").pack(side="left")

    view.current_scale_label = tk.Label(
        current_scale_frame,
        text=f"{view.app.scale_var.get()} mm/px",
        bg=COLOR_CARD_BG, fg=COLOR_ACCENT,
        font=("Segoe UI", 10, "bold")
    )
    view.current_scale_label.pack(side="left", padx=(5, 0))

    tk.Label(inner,
             text="Entrez la valeur d'échelle pour convertir les pixels en millimètres.\n"
                  "Exemple : 0.10 signifie que 1 pixel = 0.10 mm\n"
                  "Cette valeur sera utilisée pour toutes les conversions pixel → mm.",
             bg=COLOR_CARD_BG, fg="#6b7280",
             font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(5, 20))

    ttk.Separator(inner, orient="horizontal").pack(fill="x", pady=(0, 20))

    button_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
    button_frame.pack(fill="x", pady=(0, 10))
    ttk.Button(button_frame, text="Sauvegarder",
               style="ParamSave.TButton",
               command=lambda: _save_all_calibration_settings(view)).pack()

    return frame


# ── Fonctions privées ──────────────────────────────────────────────────────────

def _call_measure_app(view):
    if hasattr(view, "calibration_process") and view.calibration_process.poll() is None:
        return
    root_dir = get_project_root()
    script_path = os.path.normpath(
        os.path.join(root_dir, "modules", "app_calibrage_cam", "main.py")
    )
    view.calibration_process = subprocess.Popen([sys.executable, script_path])

    def wait_and_update():
        view.calibration_process.wait()
        view.parent.after(0, _update_conversion)

    def _update_conversion():
        try:
            param = load_conversion_param()
            view.app.facteur_conversion.set(str(param))
        except Exception:
            pass

    threading.Thread(target=wait_and_update, daemon=True).start()


def _update_undistort_status(view):
    if view.app.mtx is None or view.app.dist is None:
        view.app.use_undistortion_var.set(False)
        messagebox.showwarning(
            "Attention",
            "Impossible d'activer la correction de distorsion :\n"
            "Fichier camera_params.npz non chargé."
        )


def _update_homography_status(view):
    if view.app.homo_matrix is None:
        view.app.use_homography_var.set(False)
        messagebox.showwarning(
            "Attention",
            "Impossible d'activer la correction d'homographie :\n"
            "Fichier homography.npz non chargé."
        )


def _apply_calibration_scale(view):
    try:
        scale = float(view.app.calibration_scale_var.get().replace(",", "."))
        if scale <= 0:
            raise ValueError("L'échelle doit être positive")
        # Mettre à jour scale_var ET facteur_conversion (coefficient pixel-mm de l'onglet Paramètres)
        view.app.scale_var.set(f"{scale:.4f}")
        view.app.facteur_conversion.set(str(scale))
        view.current_scale_label.config(text=f"{view.app.scale_var.get()} mm/px")
        # Sauvegarder immédiatement dans le fichier JSON
        from src.utils.file_manager import save_conversion_parameter
        save_conversion_parameter(scale)
        messagebox.showinfo("Succès", f"Échelle appliquée et sauvegardée : {scale:.4f} mm/px")
    except ValueError as e:
        messagebox.showerror("Erreur", f"Erreur d'application: {str(e)}")


def _save_all_calibration_settings(view):
    try:
        settings = {
            "scale":              view.app.scale_var.get(),
            "use_undistortion":   view.app.use_undistortion_var.get(),
            "use_homography":     view.app.use_homography_var.get(),
            "calibration_files_loaded": {
                "camera_params": view.app.mtx is not None,
                "homography":    view.app.homo_matrix is not None,
            },
        }
        save_dir = os.path.join(os.path.expanduser("~"), "CIMES_Settings")
        os.makedirs(save_dir, exist_ok=True)
        with open(os.path.join(save_dir, "calibration_settings.json"), "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        messagebox.showinfo("Succès", "Paramètres de calibration sauvegardés !")
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur de sauvegarde : {str(e)}")
