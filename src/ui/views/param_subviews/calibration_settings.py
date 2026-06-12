"""Paramètres de calibration caméra : fichiers npz, corrections, échelle."""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import subprocess
import threading
import sys

from src.ui.widgets.ui_utils import COLOR_CARD_BG, COLOR_ACCENT, create_setting_header, add_tooltip
from src.utils.file_manager import (
    load_calibration_files,
    load_conversion_param,
    get_project_root,
    save_conversion_parameter,
)


def create_calibration_settings(view):
    """Construit le frame 'Calibration' et le retourne."""
    frame = ttk.Frame(view.param_content_frame, style="Card.TFrame")
    create_setting_header(frame, "Calibration Caméra")
    inner = tk.Frame(frame, bg=COLOR_CARD_BG, padx=40, pady=20)
    inner.pack(fill="both", expand=True)
    # Statut calibration
    tk.Label(
        inner,
        text="Statut de calibration",
        bg=COLOR_CARD_BG,
        fg="#111827",
        anchor="w",
        font=("Segoe UI", 11, "bold"),
    ).pack(fill="x", pady=(0, 10))
    status_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
    status_frame.pack(fill="x", pady=(0, 20))
    row1 = tk.Frame(status_frame, bg=COLOR_CARD_BG)
    row1.pack(fill="x", pady=5)
    _, _, cam_calib_path = load_calibration_files()
    tk.Label(
        row1,
        text=f"Le fichier de calibration utilisé est : {cam_calib_path}",
        bg=COLOR_CARD_BG,
        font=("Segoe UI", 10),
    ).pack(anchor="w")
    row2 = tk.Frame(status_frame, bg=COLOR_CARD_BG)
    row2.pack(fill="x", pady=5)
    tk.Label(
        row2,
        text="le coefficient de conversion pixel-mm actuel : ",
        bg=COLOR_CARD_BG,
        font=("Segoe UI", 10),
        anchor="w",
    ).pack(side="left")
    tk.Label(
        row2,
        textvariable=view.app.facteur_conversion,
        bg=COLOR_CARD_BG,
        font=("Segoe UI", 10),
        anchor="w",
    ).pack(side="left")
    ttk.Button(
        row2,
        text="Modifier",
        style="ParamAction.TButton",
        command=lambda: _call_measure_app(view),
    ).pack(side="left", padx=(10, 0))
    tk.Label(
        inner,
        text="Les fichiers de calibration sont automatiquement chargés au démarrage\n"
        "s'ils sont présents dans le dossier de l'application.",
        bg=COLOR_CARD_BG,
        fg="#6b7280",
        font=("Segoe UI", 9, "italic"),
    ).pack(anchor="w", pady=(0, 15))
    ttk.Separator(inner, orient="horizontal").pack(fill="x", pady=(5, 15))
    # Correction d'image
    tk.Label(
        inner,
        text="Correction d'image",
        bg=COLOR_CARD_BG,
        fg="#111827",
        anchor="w",
        font=("Segoe UI", 11, "bold"),
    ).pack(fill="x", pady=(0, 10))
    corr_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
    corr_frame.pack(fill="x", pady=(0, 10))
    undistort_row = tk.Frame(corr_frame, bg=COLOR_CARD_BG)
    undistort_row.pack(fill="x", pady=(5, 0))
    view.undistort_check = ttk.Checkbutton(
        undistort_row,
        text="Utiliser la correction de distorsion",
        variable=view.app.use_undistortion_var,
        command=lambda: _update_undistort_status(view),
    )
    view.undistort_check.pack(side="left")
    add_tooltip(
        undistort_row,
        "Corrige la déformation optique de la lentille (effet 'fish-eye').\n\n"
        "Résultat : les lignes droites dans la réalité apparaissent droites \u00e0 l'écran,\n"
        "ce qui améliore la précision des mesures de taille des grains.",
    ).pack(side="left")
    homography_row = tk.Frame(corr_frame, bg=COLOR_CARD_BG)
    homography_row.pack(fill="x", pady=(5, 0))
    view.homography_check = ttk.Checkbutton(
        homography_row,
        text="Utiliser la correction d'homographie",
        variable=view.app.use_homography_var,
        command=lambda: _update_homography_status(view),
    )
    view.homography_check.pack(side="left")
    add_tooltip(
        homography_row,
        "Corrige la perspective (vue de biais) en redressant l'image\n"
        "comme si la caméra était à la verticale exacte du tapis.\n\n"
        "Recommandé si la caméra est inclinée ou décalée par rapport\n"
        "au plan de mesure.",
    ).pack(side="left")
    tk.Label(
        corr_frame,
        text="Ces corrections sont appliquées automatiquement lors de l'analyse.",
        bg=COLOR_CARD_BG,
        fg="#6b7280",
        font=("Segoe UI", 9, "italic"),
    ).pack(anchor="w", pady=(5, 10))
    ttk.Separator(inner, orient="horizontal").pack(fill="x", pady=(5, 15))
    # Échelle de calibration
    tk.Label(
        inner,
        text="Échelle de calibration",
        bg=COLOR_CARD_BG,
        fg="#111827",
        anchor="w",
        font=("Segoe UI", 11, "bold"),
    ).pack(fill="x", pady=(0, 10))
    scale_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
    scale_frame.pack(fill="x", pady=(0, 10))
    scale_label_row = tk.Frame(scale_frame, bg=COLOR_CARD_BG)
    scale_label_row.pack(side="left")
    tk.Label(
        scale_label_row,
        text="Échelle (mm/px):",
        bg=COLOR_CARD_BG,
        font=("Segoe UI", 10),
        anchor="w",
    ).pack(side="left")
    add_tooltip(
        scale_label_row,
        "Facteur de conversion entre pixels et millimètres réels.\n\n"
        "Définit combien de millimètres correspond à 1 pixel sur l'image.\n\n",
    ).pack(side="left")
    view.calibration_scale_entry = ttk.Entry(
        scale_frame,
        textvariable=view.app.facteur_conversion,
        width=15,
        font=("Segoe UI", 10),
    )
    view.calibration_scale_entry.pack(side="left", padx=(5, 10))
    view.apply_scale_btn = ttk.Button(
        scale_frame,
        text="Appliquer",
        style="ParamAction.TButton",
        command=lambda: _apply_calibration_scale(view),
    )
    view.apply_scale_btn.pack(side="left")
    # Valeur actuelle
    current_scale_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
    current_scale_frame.pack(fill="x", pady=(5, 0))
    tk.Label(
        current_scale_frame,
        text="Échelle actuelle:",
        bg=COLOR_CARD_BG,
        font=("Segoe UI", 10),
        width=15,
        anchor="w",
    ).pack(side="left")
    view.current_scale_label = tk.Label(
        current_scale_frame,
        textvariable=view.app.facteur_conversion,
        bg=COLOR_CARD_BG,
        fg=COLOR_ACCENT,
        font=("Segoe UI", 10, "bold"),
    )
    view.current_scale_label.pack(side="left", padx=(5, 0))
    tk.Label(
        current_scale_frame,
        text=" mm/px",
        bg=COLOR_CARD_BG,
        font=("Segoe UI", 10, "bold"),
        fg=COLOR_ACCENT,
    ).pack(side="left")
    tk.Label(
        inner,
        text="Entrez la valeur d'échelle pour convertir les pixels en millimètres.\n"
        "Exemple : 0.10 signifie que 1 pixel = 0.10 mm\n"
        "Cette valeur sera utilisée pour toutes les conversions pixel → mm.",
        bg=COLOR_CARD_BG,
        fg="#6b7280",
        font=("Segoe UI", 9, "italic"),
    ).pack(anchor="w", pady=(5, 20))
    ttk.Separator(inner, orient="horizontal").pack(fill="x", pady=(0, 20))
    button_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
    button_frame.pack(fill="x", pady=(0, 10))
    ttk.Button(
        button_frame,
        text="Sauvegarder",
        style="ParamSave.TButton",
        command=lambda: _save_all_calibration_settings(view),
    ).pack()
    return frame


# ── Fonctions privées ─────────────────────────────────────────────────────
def _call_measure_app(view):
    """Ouvre l'application de calibration"""
    if hasattr(view, "calibration_process") and view.calibration_process.poll() is None:
        return
    if getattr(sys, "frozen", False):
        # En mode frozen, on relance l'exécutable avec un argument spécial
        view.calibration_process = subprocess.Popen(
            [sys.executable, "--module-calibration"]
        )
    else:
        root_dir = get_project_root()
        script_path = os.path.normpath(
            os.path.join(root_dir, "modules", "app_calibrage_cam", "main.py")
        )
        view.calibration_process = subprocess.Popen(
            [sys.executable, script_path]
        )  # pylint: disable=consider-using-with

    def wait_and_update():
        """Attend que l'application de calibration 
        se ferme et met à jour le facteur de conversion"""
        view.calibration_process.wait()
        view.parent.after(0, _update_conversion)

    def _update_conversion():
        """Met à jour le facteur de conversion"""
        try:
            param = load_conversion_param()
            view.app.facteur_conversion.set(str(param))
        except Exception as e:  # pylint: disable=broad-exception-caught
            messagebox.showwarning(
                "Mise à jour impossible",
                f"L'application de calibration s'est fermée, mais le nouveau "
                f"facteur de conversion n'a pas pu être récupéré.\n\nDétails : {e}",
            )

    threading.Thread(target=wait_and_update, daemon=True).start()


def _update_undistort_status(view):
    """Met à jour le statut de la correction de distorsion"""
    if view.app.mtx is None or view.app.dist is None:
        view.app.use_undistortion_var.set(False)
        messagebox.showwarning(
            "Attention",
            "Impossible d'activer la correction de distorsion :\n"
            "Fichier camera_params.npz non chargé.",
        )


def _update_homography_status(view):
    """Met à jour le statut de la correction d'homographie"""
    if view.app.homo_matrix is None:
        view.app.use_homography_var.set(False)
        messagebox.showwarning(
            "Attention",
            "Impossible d'activer la correction d'homographie :\n"
            "Fichier homography.npz non chargé.",
        )


def _apply_calibration_scale(view):
    """Applique le facteur de conversion et le sauvegarde"""
    try:
        scale_str = view.app.facteur_conversion.get().replace(",", ".")
        scale = float(scale_str)
        if scale <= 0:
            raise ValueError("L'échelle doit être positive")
        # Mettre à jour la variable unique (déjà fait par textvariable mais on formate si besoin)
        view.app.facteur_conversion.set(str(scale))
        # Sauvegarder immédiatement dans le fichier JSON
        save_conversion_parameter(scale)
        messagebox.showinfo(
            "Succès", f"Échelle appliquée et sauvegardée : {scale:.4f} mm/px"
        )
    except ValueError as e:
        messagebox.showerror("Erreur", f"Erreur d'application: {str(e)}")


def _save_all_calibration_settings(view):
    """Sauvegarde tous les paramètres de calibration"""
    try:
        settings = {
            "scale": view.app.facteur_conversion.get(),
            "use_undistortion": view.app.use_undistortion_var.get(),
            "use_homography": view.app.use_homography_var.get(),
            "calibration_files_loaded": {
                "camera_params": view.app.mtx is not None,
                "homography": view.app.homo_matrix is not None,
            },
        }
        save_dir = os.path.join(os.path.expanduser("~"), "CIMES_Settings")
        os.makedirs(save_dir, exist_ok=True)
        with open(
            os.path.join(save_dir, "calibration_settings.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        messagebox.showinfo("Succès", "Paramètres de calibration sauvegardés !")
    except Exception as e:  # pylint: disable=broad-exception-caught
        messagebox.showerror("Erreur", f"Erreur de sauvegarde : {str(e)}")
