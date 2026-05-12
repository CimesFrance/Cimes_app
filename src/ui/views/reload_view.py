"""
Vue Recharger — coordinateur.
Construit le layout et délègue via ImageAnalyzer + CsvManager.
"""

import tkinter as tk
from tkinter import ttk

from src.ui.widgets.ui_utils import (
    COLOR_FRAME_BG,
    COLOR_CARD_BG,
    COLOR_ACCENT,
    load_icon,
)
from src.ui.views.reload_subviews.image_analyzer import ImageAnalyzer
from src.ui.views.reload_subviews.csv_manager import CsvManager


class ReloadView(ImageAnalyzer, CsvManager):
    """
    Classe principale de la vue Recharger.
    Cette vue permet de recharger des images existantes et de les analyser.
    """
    # pylint: disable=too-few-public-methods,too-many-instance-attributes

    def __init__(self, parent, app):
        """
        Initialise la vue Recharger.
        Args:
            parent: Fenêtre parente
            app: Application principale
        """
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent, bg=COLOR_FRAME_BG)
        self.loaded_image_path = None
        self.loaded_image_data = None
        self.reload_image_preview = None
        self.current_reload_capture = None
        self.csv_curves = []
        self.csv_curve_names = []
        self.segmented_tk_img = None
        self.icons = {
            "analyze": load_icon("analysis.png", size=(20, 20)),
            "load": load_icon("download.png", size=(20, 20)),
            "delete": load_icon("bin.png", size=(20, 20)),
        }

        # Initialisation des widgets à None (résout W0201)
        self.selected_path_label = None
        self.analyze_btn = None
        self.reload_left_panel = None
        self.csv_curves_frame = None
        self.csv_status_label = None
        self.csv_list_container = None
        self.reload_notebook = None
        self.segmented_image_tab = None
        self.segmented_image_container = None
        self.segmented_label = None
        self.reload_curve_tab = None
        self.reload_curve_frame = None
        self.curve_label = None
        self._build_ui()

    def _build_ui(self):
        """Construit le layout de la vue Recharger."""
        self.frame.columnconfigure(0, weight=0, minsize=300)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=1)
        self._setup_sidebar()
        self._setup_results_area()

    def _setup_sidebar(self):
        """Construit le panneau latéral gauche."""
        sidebar = ttk.Frame(self.frame, style="Card.TFrame", width=300)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        sidebar.pack_propagate(False)
        tk.Label(
            sidebar,
            text=" Analyse d'images existantes",
            image=self.icons["analyze"],
            compound="left",
            bg="#e5e7eb",
            fg=COLOR_ACCENT,
            anchor="w",
            font=("Segoe UI", 12, "bold"),
            padx=10,
            pady=5,
        ).pack(fill="x")
        content = tk.Frame(sidebar, bg=COLOR_CARD_BG, padx=15, pady=15)
        content.pack(fill="both", expand=True)
        # Section Image
        tk.Label(content, text="Analyse d'image :", bg=COLOR_CARD_BG,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        ttk.Button(content, text="Parcourir image", style="Secondary.TButton",
                   command=self._browse_and_analyze_image).pack(fill="x", pady=(0, 10))
        self.selected_path_label = tk.Label(
            content, text="Aucune image sélectionnée",
            bg=COLOR_CARD_BG, fg="#6b7280",
            font=("Segoe UI", 9), wraplength=250
        )
        self.selected_path_label.pack(fill="x", pady=(0, 20))
        self.analyze_btn = ttk.Button(
            content, text=" Analyser l'image",
            image=self.icons["analyze"], compound="left",
            style="Secondary.TButton", state="disabled",
            command=self._analyze_loaded_image
        )
        self.analyze_btn.pack(fill="x", pady=(10, 0))
        ttk.Separator(content, orient="horizontal").pack(fill="x", pady=20)
        # Section CSV
        self._setup_csv_section(content)
        # Aperçu image
        self.reload_left_panel = tk.Frame(sidebar, bg=COLOR_CARD_BG, width=300)
        self.reload_left_panel.pack(fill="both", expand=True, padx=10, pady=10)
    def _setup_csv_section(self, parent):
        """Construit la section de chargement CSV."""
        tk.Label(parent, text="Courbes de tamisage CSV :", bg=COLOR_CARD_BG,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        ttk.Button(parent, text=" Charger courbe CSV", image=self.icons["load"],
                   compound="left", style="Secondary.TButton",
                   command=self._load_csv_curve).pack(fill="x", pady=(0, 10))
        ttk.Button(parent, text=" Supprimer les courbes", image=self.icons["delete"],
                   compound="left", style="Secondary.TButton",
                   command=self._clear_all_csv_curves).pack(fill="x", pady=(0, 10))
        self.csv_curves_frame = tk.Frame(parent, bg=COLOR_CARD_BG)
        self.csv_curves_frame.pack(fill="both", expand=True, pady=(10, 0))
        self.csv_status_label = tk.Label(
            self.csv_curves_frame, text="Aucune courbe CSV chargée",
            bg=COLOR_CARD_BG, fg="#6b7280", font=("Segoe UI", 9)
        )
        self.csv_status_label.pack(anchor="w")
        csv_list_frame = tk.Frame(self.csv_curves_frame, bg=COLOR_CARD_BG)
        csv_list_frame.pack(fill="both", expand=True, pady=(5, 0))
        csv_canvas = tk.Canvas(csv_list_frame, bg=COLOR_CARD_BG, highlightthickness=0, height=150)
        scrollbar = ttk.Scrollbar(csv_list_frame, orient="vertical", command=csv_canvas.yview)
        self.csv_list_container = tk.Frame(csv_canvas, bg=COLOR_CARD_BG)
        csv_canvas.create_window((0, 0), window=self.csv_list_container, anchor="nw")
        csv_canvas.configure(yscrollcommand=scrollbar.set)
        csv_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.csv_list_container.bind(
            "<Configure>",
            lambda e: csv_canvas.configure(scrollregion=csv_canvas.bbox("all"))
        )
        tk.Label(parent,
                 text="Format CSV attendu :\n- Colonne 1 : Diamètres (mm)\n"
                      "- Colonne 2 : % Passant cumulé\n- En-têtes facultatives",
                 bg=COLOR_CARD_BG, fg="#6b7280", font=("Segoe UI", 8),
                 justify="left", wraplength=250).pack(anchor="w", pady=(10, 0))

    def _setup_results_area(self):
        """Construit la zone d'affichage des résultats (notebook)."""
        results_area = tk.Frame(self.frame, bg=COLOR_FRAME_BG)
        results_area.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        results_area.columnconfigure(0, weight=1)
        results_area.rowconfigure(0, weight=1)
        self.reload_notebook = ttk.Notebook(results_area)
        self.reload_notebook.grid(row=0, column=0, sticky="nsew")
        # Onglet Image Segmentée
        self.segmented_image_tab = ttk.Frame(self.reload_notebook)
        self.reload_notebook.add(self.segmented_image_tab, text="Image Segmentée")
        self.segmented_image_container = tk.Frame(self.segmented_image_tab, bg=COLOR_CARD_BG)
        self.segmented_image_container.pack(fill="both", expand=True, padx=10, pady=10)
        self.segmented_label = tk.Label(
            self.segmented_image_container,
            text="Aucune image segmentée disponible",
            bg=COLOR_CARD_BG, fg="#666", font=("Segoe UI", 12)
        )
        self.segmented_label.pack(expand=True)
        # Onglet Courbe Granulométrique
        self.reload_curve_tab = ttk.Frame(self.reload_notebook)
        self.reload_notebook.add(self.reload_curve_tab, text="Courbe Granulométrique")
        self.reload_curve_frame = tk.Frame(self.reload_curve_tab, bg=COLOR_CARD_BG)
        self.reload_curve_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.curve_label = tk.Label(
            self.reload_curve_frame,
            text="Aucune courbe disponible",
            bg=COLOR_CARD_BG, fg="#666", font=("Segoe UI", 12)
        )
        self.curve_label.pack(expand=True)
