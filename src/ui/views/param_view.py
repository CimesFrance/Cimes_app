"""
Vue Paramètres — coordinateur.
Construit la nav latérale et délègue chaque section à son sous-module.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil

from src.utils.file_manager import get_project_root
from src.ui.widgets.ui_utils import COLOR_FRAME_BG, COLOR_CARD_BG, load_icon
from src.ui.views.param_subviews.sensor_settings import create_sensor_settings
from src.ui.views.param_subviews.calibration_settings import create_calibration_settings
from src.ui.views.param_subviews.analysis_settings import create_analysis_settings
from src.ui.views.param_subviews.transmission_settings import (
    create_transmission_settings,
)


class ParamView:
    """ Classe principale de la vue Paramètres."""

    # pylint: disable=too-many-instance-attributes,too-few-public-methods
    def __init__(self, parent, app):
        """
        Initialise la vue Paramètres

        Args:
            parent: Widget parent
            app: Instance de l'application principale
        """
        self.parent = parent
        self.app = app
        self.app.use_undistortion_var.set(True)
        self.frame = tk.Frame(parent, bg=COLOR_FRAME_BG)
        self.param_nav_buttons = {}

        # Initialisation pour Pylint
        self.auto_params_frame = None
        self.manual_params_frame = None
        self.capture_interval_frame = None
        self.time_frame = None
        self.days_frame = None

        self._build_ui()

    def _build_ui(self):
        """
        Construit l'interface utilisateur de la vue Paramètres.
        """
        param_area = tk.Frame(self.frame, bg=COLOR_FRAME_BG)
        param_area.pack(fill="both", expand=True, padx=20, pady=10)
        param_area.columnconfigure(1, weight=1)
        param_area.rowconfigure(0, weight=1)
        # Navigation latérale
        nav_frame = ttk.Frame(param_area, style="Card.TFrame", width=240)
        nav_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 20), pady=0)
        nav_frame.pack_propagate(False)
        tk.Label(
            nav_frame,
            text="CATÉGORIES",
            bg=COLOR_CARD_BG,
            fg="#9ca3af",
            font=("Segoe UI", 9, "bold"),
            padx=15,
            pady=5,
        ).pack(fill="x", anchor="n", pady=(15, 5))
        nav_items = [
            ("sensor", "Capteur", "temperature-control.png"),
            ("calibration", "Calibration", "target.png"),
            ("analysis", "Analyse", "analysis.png"),
            ("transmission", "Transmission", "send.png"),
        ]
        self.nav_icons = {}
        for key, label, icon_name in nav_items:
            icon = load_icon(icon_name, size=(20, 20))
            self.nav_icons[key] = icon
            btn = ttk.Button(
                nav_frame,
                text="  " + label,
                image=icon,
                compound="left",
                style="ParamNav.TButton",
                command=lambda k=key: self._switch_param_view(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.param_nav_buttons[key] = btn

        # Spacer pour pousser le bouton guide vers le bas
        tk.Frame(nav_frame, bg=COLOR_CARD_BG).pack(fill="y", expand=True)

        # Bouton Guide d'utilisation
        guide_icon = load_icon("download.png", size=(20, 20))
        self.nav_icons["guide"] = guide_icon
        guide_btn = ttk.Button(
            nav_frame,
            text="  Guide d'utilisation",
            image=guide_icon,
            compound="left",
            style="ParamNav.TButton",
            command=self._download_guide,
        )
        guide_btn.pack(fill="x", side="bottom", padx=10, pady=20)

        # Conteneur du contenu
        self.param_content_frame = tk.Frame(param_area, bg=COLOR_FRAME_BG)
        self.param_content_frame.grid(
            row=0, column=1, sticky="nsew", padx=(0, 0), pady=0
        )
        self.param_content_frame.grid_columnconfigure(0, weight=1)
        self.param_content_frame.grid_rowconfigure(0, weight=1)
        # Créer toutes les vues (délégation aux sous-modules)
        self.sensor_settings_frame = create_sensor_settings(self)
        self.calibration_settings_frame = create_calibration_settings(self)
        self.analysis_settings_frame = create_analysis_settings(self)
        self.transmission_settings_frame = create_transmission_settings(self)
        # Vue par défaut
        self._switch_param_view("sensor")

    def _switch_param_view(self, key):
        """
        Active la vue sélectionnée et grise les autres.

        Args:
            key: Clé de la vue à activer.
        """
        for k, btn in self.param_nav_buttons.items():
            btn.configure(
                style="ParamNavActive.TButton" if k == key else "ParamNav.TButton"
            )
        frames = {
            "sensor": self.sensor_settings_frame,
            "calibration": self.calibration_settings_frame,
            "analysis": self.analysis_settings_frame,
            "transmission": self.transmission_settings_frame,
        }
        for frame in frames.values():
            if frame:
                frame.grid_forget()
        frame_to_show = frames.get(key)
        if frame_to_show:
            frame_to_show.grid(row=0, column=0, sticky="nsew")

    def _toggle_capture_controls(self):
        """Active/désactive les contrôles selon le mode de capture."""
        mode = self.app.capture_mode_var.get()
        if mode == "automatique":
            self.auto_params_frame.pack(before=self.sensor_bottom_separator, fill="x", pady=(0, 20))
            self.manual_params_frame.pack_forget()
            for widget in self.capture_interval_frame.winfo_children():
                widget.configure(state="normal")
            for widget in self.time_frame.winfo_children():
                widget.configure(state="normal")
            for widget in self.days_frame.winfo_children():
                widget.configure(state="normal")
        else:
            self.auto_params_frame.pack_forget()
            self.manual_params_frame.pack(before=self.sensor_bottom_separator, fill="x", pady=(0, 20))
            for widget in self.capture_interval_frame.winfo_children():
                widget.configure(state="disabled")
            for widget in self.time_frame.winfo_children():
                widget.configure(state="disabled")
            for widget in self.days_frame.winfo_children():
                widget.configure(state="disabled")

    def _download_guide(self):
        """Permet de télécharger (sauvegarder) le guide d'utilisation PDF."""
        guide_path = os.path.join(get_project_root(), "assets", "Guide_Utilisation.pdf")
        
        if not os.path.exists(guide_path):
            messagebox.showwarning(
                "Fichier introuvable", 
                "Le guide d'utilisation (Guide_Utilisation.pdf) est introuvable dans le dossier assets."
            )
            return
            
        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile="Guide_Utilisation.pdf",
            title="Enregistrer le guide d'utilisation",
            filetypes=[("Fichiers PDF", "*.pdf")]
        )
        
        if save_path:
            try:
                shutil.copy2(guide_path, save_path)
                messagebox.showinfo("Succès", "Le guide a été téléchargé avec succès.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors du téléchargement :\n{str(e)}")
