# -*- coding: utf-8 -*-
"""
Panneau de statistiques granulométriques de la vue Courbe.
"""
import tkinter as tk
from tkinter import ttk

from src.ui.widgets.ui_utils import (
    COLOR_CARD_BG, COLOR_ACCENT
)
from src.core.statistics import calculer_statistiques_granulometriques


class StatsPanel:
    """
    Mixin pour CurveView — gère le panneau de statistiques.
    """

    def _create_fixed_stat_labels(self):
        """Crée les labels des statistiques une seule fois."""
        for widget in self.stats_content_frame.winfo_children():
            widget.destroy()

        tk.Label(self.stats_content_frame, text="📊 STATISTIQUES GRANULOMÉTRIQUES",
                 bg=COLOR_CARD_BG, font=("Segoe UI", 12, "bold"),
                 fg=COLOR_ACCENT).pack(anchor="w", pady=(0, 15), padx=5)

        stats_config = [
            ("n_particules",    "Nombre de particules:",  "",     "normal"),
            ("",                "",                        "",     "separator"),
            ("min_mm_minor",    "Min (Axe mineur):",      " mm",  "normal"),
            ("max_mm_minor",    "Max (Axe mineur):",      " mm",  "normal"),
            ("min_mm_major",    "Min (Axe majeur):",      " mm",  "normal"),
            ("max_mm_major",    "Max (Axe majeur):",      " mm",  "normal"),
            ("moyenne_mm_minor","Moyenne (Axe mineur):",  " mm",  "normal"),
            ("moyenne_mm_major","Moyenne (Axe majeur):",  " mm",  "normal"),
            ("",                "",                        "",     "separator"),
            ("D10_mm",          "D10 (10% plus fins):",   " mm",  "percentile"),
            ("D25_mm",          "D25 (25% plus fins):",   " mm",  "percentile"),
            ("D50_mm",          "D50 (Taille médiane):",  " mm",  "percentile"),
            ("D75_mm",          "D75 (75% plus fins):",   " mm",  "percentile"),
            ("D90_mm",          "D90 (90% plus fins):",   " mm",  "percentile"),
        ]

        for stat_key, label_text, unit, stat_type in stats_config:
            if stat_type == "separator":
                ttk.Separator(self.stats_content_frame, orient="horizontal").pack(fill="x", pady=10)
                continue

            stat_frame = tk.Frame(self.stats_content_frame, bg=COLOR_CARD_BG)
            stat_frame.pack(fill="x", pady=2, padx=5)

            tk.Label(stat_frame, text=label_text, bg=COLOR_CARD_BG,
                     font=("Segoe UI", 10), width=25, anchor="w").pack(side="left")

            value_label = tk.Label(stat_frame, text="N/A", bg=COLOR_CARD_BG,
                                   fg="#000000", font=("Segoe UI", 10, "bold"),
                                   anchor="w", width=12)
            value_label.pack(side="left", padx=(5, 0))

            if unit:
                tk.Label(stat_frame, text=unit, bg=COLOR_CARD_BG,
                         font=("Segoe UI", 10), fg="#6b7280").pack(side="left", padx=(2, 0))

            if stat_key:
                self.stat_value_labels[stat_key] = value_label

        self.stats_content_frame.update_idletasks()
        self.stats_canvas.configure(scrollregion=self.stats_canvas.bbox("all"))

    def update_statistics_display(self, capture_data):
        """Met à jour l'affichage des statistiques."""
        if not capture_data or not capture_data.get("particles_data"):
            for label in self.stat_value_labels.values():
                label.config(text="N/A", fg="#000000")
            return

        particles_data = capture_data.get("particles_data", [])
        minor_axes_mm = [p.get("minor_axis_mm", 0) for p in particles_data if p.get("minor_axis_mm", 0) > 0.1]
        major_axes_mm = [p.get("major_axis_mm", 0) for p in particles_data if p.get("major_axis_mm", 0) > 0.1]

        if not minor_axes_mm:
            for label in self.stat_value_labels.values():
                label.config(text="N/A", fg="#000000")
            return

        stats = calculer_statistiques_granulometriques(particles_data, minor_axes_mm, major_axes_mm)
        if not stats:
            return

        for stat_key, label in self.stat_value_labels.items():
            if stat_key in stats:
                value = stats[stat_key]
                if isinstance(value, (int, float)):
                    display_text = "0" if value == 0 else f"{value:.2f}"
                else:
                    display_text = str(value)
                label.config(text=display_text, fg="#000000")

        self.stats_content_frame.update_idletasks()
        self.stats_canvas.configure(scrollregion=self.stats_canvas.bbox("all"))
