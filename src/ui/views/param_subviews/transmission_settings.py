# -*- coding: utf-8 -*-
"""Paramètres de transmission et configuration du rapport PDF."""
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

from src.ui.widgets.ui_utils import (
    COLOR_CARD_BG, create_setting_header
)


def create_transmission_settings(view):
    """Construit le frame 'Transmission' et le retourne."""
    frame = ttk.Frame(view.param_content_frame, style="Card.TFrame")
    create_setting_header(frame, "Transmission programmée des résultats")

    inner = tk.Frame(frame, bg=COLOR_CARD_BG, padx=40, pady=20)
    inner.pack(fill="both", expand=True)

    # Activation
    ttk.Checkbutton(
        inner,
        text="Activer la transmission des résultats",
        variable=view.app.transmission_enabled_var,
        command=lambda: _toggle_transmission_settings(view)
    ).pack(anchor="w", pady=(0, 20))

    view.transmission_params_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
    view.transmission_params_frame.pack(fill="x", pady=(0, 10))

    # Mode
    tk.Label(view.transmission_params_frame, text="Mode de transmission",
             bg=COLOR_CARD_BG, fg="#111827", anchor="w",
             font=("Segoe UI", 10, "bold")).pack(fill="x", pady=(0, 10))

    mode_frame = tk.Frame(view.transmission_params_frame, bg=COLOR_CARD_BG)
    mode_frame.pack(fill="x", pady=(0, 15))

    ttk.Radiobutton(mode_frame, text="À chaque capture", value="capture",
                    variable=view.app.transmission_mode_var).pack(anchor="w", pady=(0, 5))
    ttk.Radiobutton(mode_frame, text="À la fin de journée", value="daily",
                    variable=view.app.transmission_mode_var).pack(anchor="w", pady=(0, 5))

    # Heure d'envoi
    view.time_transmission_frame = tk.Frame(view.transmission_params_frame, bg=COLOR_CARD_BG)
    view.time_transmission_frame.pack(fill="x", pady=(0, 15))

    tk.Label(view.time_transmission_frame, text="Heure d'envoi (fin de journée) :",
             bg=COLOR_CARD_BG, anchor="w",
             font=("Segoe UI", 10, "bold")).pack(fill="x", pady=(0, 5))

    time_frame = tk.Frame(view.time_transmission_frame, bg=COLOR_CARD_BG)
    time_frame.pack(fill="x", pady=(0, 10))
    ttk.Entry(time_frame, textvariable=view.app.transmission_time_var, width=8,
              font=("Segoe UI", 10)).pack(side="left")
    tk.Label(time_frame, text="(format HH:MM, ex: 18:00)",
             bg=COLOR_CARD_BG, font=("Segoe UI", 9, "italic")).pack(side="left", padx=(10, 0))

    # Email
    tk.Label(view.transmission_params_frame, text="Adresse Email pour transmission",
             bg=COLOR_CARD_BG, fg="#111827", anchor="w",
             font=("Segoe UI", 10, "bold")).pack(fill="x", pady=(10, 5))
    ttk.Entry(view.transmission_params_frame, textvariable=view.app.transmission_email_var,
              width=40, font=("Segoe UI", 10)).pack(fill="x", pady=(0, 20))

    # Courbe corrigée DNA
    ttk.Checkbutton(view.transmission_params_frame,
                    text="Inclure la courbe corrigée DNA dans les rapports",
                    variable=view.app.show_corrected_curve_var).pack(anchor="w", pady=(0, 10))

    ttk.Separator(view.transmission_params_frame, orient="horizontal").pack(fill="x", pady=(10, 20))

    # Configuration du rapport PDF
    tk.Label(view.transmission_params_frame, text="Configuration du rapport PDF",
             bg=COLOR_CARD_BG, fg="#111827", anchor="w",
             font=("Segoe UI", 11, "bold")).pack(fill="x", pady=(0, 10))

    report_options_frame = tk.Frame(view.transmission_params_frame, bg=COLOR_CARD_BG)
    report_options_frame.pack(fill="x", pady=(0, 15))

    options_grid = tk.Frame(report_options_frame, bg=COLOR_CARD_BG)
    options_grid.pack(fill="x")

    col1 = tk.Frame(options_grid, bg=COLOR_CARD_BG)
    col1.pack(side="left", fill="both", expand=True)
    ttk.Checkbutton(col1, text="✓ Image capturée",
                    variable=view.app.report_options["include_captured_image"]).pack(anchor="w", pady=2)
    ttk.Checkbutton(col1, text="✓ Image segmentée",
                    variable=view.app.report_options["include_segmented_image"]).pack(anchor="w", pady=2)
    ttk.Checkbutton(col1, text="✓ Courbe granulométrique",
                    variable=view.app.report_options["include_granulometric_curve"]).pack(anchor="w", pady=2)

    col2 = tk.Frame(options_grid, bg=COLOR_CARD_BG)
    col2.pack(side="left", fill="both", expand=True, padx=(20, 0))
    ttk.Checkbutton(col2, text="✓ Courbe de distribution",
                    variable=view.app.report_options["include_distribution_curve"]).pack(anchor="w", pady=2)
    ttk.Checkbutton(col2, text="✓ Tableau statistique",
                    variable=view.app.report_options["include_statistics"]).pack(anchor="w", pady=2)

    # Zone commentaire
    comment_frame = tk.Frame(view.transmission_params_frame, bg=COLOR_CARD_BG)
    comment_frame.pack(fill="x", pady=(15, 10))
    tk.Label(comment_frame, text="Commentaire (optionnel)", bg=COLOR_CARD_BG, fg="#4b5563",
             font=("Segoe UI", 10, "bold")).pack(anchor="w")
    view.comment_text = tk.Text(comment_frame, height=4, font=("Segoe UI", 10))
    view.comment_text.pack(fill="x", pady=(5, 0))
    if view.app.report_options["custom_comment"].get():
        view.comment_text.insert("1.0", view.app.report_options["custom_comment"].get())

    # Note informative
    note_frame = tk.Frame(view.transmission_params_frame, bg=COLOR_CARD_BG)
    note_frame.pack(fill="x", pady=(10, 0))
    tk.Label(note_frame,
             text="⚠️ Les options d'inclusion sont configurées dans Paramètres → Transmission",
             bg=COLOR_CARD_BG, fg="#dc2626",
             font=("Segoe UI", 9, "italic"), wraplength=500).pack(anchor="w")

    ttk.Separator(view.transmission_params_frame, orient="horizontal").pack(fill="x", pady=(15, 20))

    # Bouton de sauvegarde
    ttk.Button(view.transmission_params_frame,
               text="Sauvegarder",
               style="ParamSave.TButton",
               command=lambda: _save_report_configuration(view)).pack(pady=(0, 10))

    _toggle_transmission_settings(view)
    view.app.transmission_mode_var.trace_add(
        "write", lambda *a: _update_transmission_mode_display(view)
    )

    return frame


def _toggle_transmission_settings(view):
    state = "normal" if view.app.transmission_enabled_var.get() else "disabled"
    for widget in view.transmission_params_frame.winfo_children():
        if isinstance(widget, (tk.Label, ttk.Entry, ttk.Combobox,
                               ttk.Spinbox, ttk.Radiobutton, ttk.Checkbutton)):
            widget.configure(state=state)


def _update_transmission_mode_display(view):
    mode = view.app.transmission_mode_var.get()
    if mode == "daily":
        view.time_transmission_frame.pack(fill="x", pady=(0, 15))
    else:
        view.time_transmission_frame.pack_forget()


def _save_report_configuration(view):
    comment = view.comment_text.get("1.0", tk.END).strip()
    view.app.report_options["custom_comment"].set(comment)

    report_config = {
        "include_captured_image":      view.app.report_options["include_captured_image"].get(),
        "include_segmented_image":     view.app.report_options["include_segmented_image"].get(),
        "include_granulometric_curve": view.app.report_options["include_granulometric_curve"].get(),
        "include_distribution_curve":  view.app.report_options["include_distribution_curve"].get(),
        "include_statistics":          view.app.report_options["include_statistics"].get(),
        "custom_comment":              comment,
        "dna_correction_enabled":      view.app.show_corrected_curve_var.get(),
    }
    try:
        save_dir = os.path.join(os.path.expanduser("~"), "CIMES_Settings")
        os.makedirs(save_dir, exist_ok=True)
        with open(os.path.join(save_dir, "report_configuration.json"), "w", encoding="utf-8") as f:
            json.dump(report_config, f, indent=4, ensure_ascii=False)
        messagebox.showinfo("Succès", "Configuration du rapport sauvegardée avec succès !")
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde : {str(e)}")
