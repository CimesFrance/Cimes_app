"""
Vue Courbe — coordinateur.
Layout à 3 colonnes : stats | tableau+historique | graphiques.
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.ui.widgets.ui_utils import (
    COLOR_FRAME_BG,
    COLOR_CARD_BG,
    COLOR_ACCENT,
    load_icon,
)
from src.ui.views.curve_subviews.stats_panel import StatsPanel
from src.ui.views.curve_subviews.history_panel import HistoryPanel
from src.ui.views.curve_subviews.chart_panel import ChartPanel
from src.ui.views.curve_subviews.comparison_dialog import ComparisonDialog


class CurveView(StatsPanel, HistoryPanel, ChartPanel, ComparisonDialog):
    """ Classe principale de la vue Courbe """
    # pylint: disable=too-many-instance-attributes,too-few-public-methods

    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent, bg=COLOR_FRAME_BG)
        self.stat_value_labels = {}
        self.particles_tree = None
        # Initialisation UI pour Pylint (W0201)
        self.stats_inner_frame = None
        self.stats_canvas_container = None
        self.stats_canvas = None
        self.stats_scrollbar = None
        self.stats_content_frame = None
        self.comparison_btn = None
        self.report_btn = None
        self.prev_btn = None
        self.next_btn = None
        self.capture_info_frame = None
        self.capture_info_label = None
        self.history_canvas = None
        self.history_frame = None
        self.graph_frame = None
        self.fig = None
        self.ax = None
        self.canvas = None
        self.hist_frame = None
        self.hist_fig = None
        self.hist_ax = None
        self.hist_canvas = None
        # Icônes
        self.icon_stats = load_icon("bar-chart.png", size=(20, 20))
        self.icon_table = load_icon("dashboard.png", size=(20, 20))
        self.icon_history = load_icon("history.png", size=(20, 20))
        self.icon_wave = load_icon("wave-graph.png", size=(20, 20))
        self._build_ui()

    def _build_ui(self):
        """Construit le layout à 3 colonnes."""
        main_content = tk.Frame(self.frame, bg=COLOR_FRAME_BG)
        main_content.pack(fill="both", expand=True, padx=20, pady=10)
        main_content.columnconfigure(0, weight=2)
        main_content.columnconfigure(1, weight=2)
        main_content.columnconfigure(2, weight=3)
        main_content.rowconfigure(0, weight=1)
        self._setup_stats_column(main_content)
        self._setup_middle_column(main_content)
        self._setup_graphs_column(main_content)

    def _setup_stats_column(self, main_content):
        """Configure la colonne des statistiques (gauche)."""
        # ── Colonne gauche : Statistiques ───────────────────────────────
        stats_column = tk.Frame(main_content, bg=COLOR_FRAME_BG)
        stats_column.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        stats_frame = ttk.Frame(stats_column, style="Card.TFrame")
        stats_frame.pack(fill="both", expand=True)
        tk.Label(
            stats_frame,
            text=" Statistiques granulométriques",
            image=self.icon_stats,
            compound="left",
            bg="#e5e7eb",
            fg=COLOR_ACCENT,
            anchor="w",
            font=("Segoe UI", 12, "bold"),
            padx=10,
            pady=5,
        ).pack(fill="x")
        self.stats_inner_frame = tk.Frame(stats_frame, bg=COLOR_CARD_BG)
        self.stats_inner_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.stats_canvas_container = tk.Frame(self.stats_inner_frame, bg=COLOR_CARD_BG)
        self.stats_canvas_container.pack(fill="both", expand=True)
        self.stats_canvas = tk.Canvas(
            self.stats_canvas_container, bg=COLOR_CARD_BG, highlightthickness=0
        )
        self.stats_scrollbar = ttk.Scrollbar(
            self.stats_canvas_container,
            orient="vertical",
            command=self.stats_canvas.yview,
        )
        self.stats_content_frame = tk.Frame(self.stats_canvas, bg=COLOR_CARD_BG)
        self.stats_canvas.create_window(
            (0, 0), window=self.stats_content_frame, anchor="nw"
        )
        self.stats_canvas.configure(yscrollcommand=self.stats_scrollbar.set)
        self.stats_canvas.pack(side="left", fill="both", expand=True)
        self.stats_scrollbar.pack(side="right", fill="y")
        self._create_fixed_stat_labels()  # StatsPanel

    def _setup_middle_column(self, main_content):
        """Configure la colonne centrale (tableau et historique)."""
        # ── Colonne centrale : Tableau + Historique ─────────────────────
        middle_column = tk.Frame(main_content, bg=COLOR_FRAME_BG)
        middle_column.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=0)
        # Tableau des particules
        table_frame = ttk.Frame(middle_column, style="Card.TFrame")
        table_frame.pack(fill="both", expand=True)
        tk.Label(
            table_frame,
            text=" Tableau des cailloux détectés",
            image=self.icon_table,
            compound="left",
            bg="#e5e7eb",
            fg=COLOR_ACCENT,
            anchor="w",
            font=("Segoe UI", 11, "bold"),
            padx=10,
            pady=5,
        ).pack(fill="x")
        particles_container = tk.Frame(table_frame, bg=COLOR_CARD_BG)
        particles_container.pack(fill="both", expand=True, padx=10, pady=10)
        self._create_particles_table(particles_container)  # HistoryPanel
        # Historique des captures
        history_frame = ttk.Frame(middle_column, style="Card.TFrame")
        history_frame.pack(fill="both", expand=True, pady=(10, 0))
        tk.Label(
            history_frame,
            text=" Historique des captures",
            image=self.icon_history,
            compound="left",
            bg="#e5e7eb",
            fg=COLOR_ACCENT,
            anchor="w",
            font=("Segoe UI", 11, "bold"),
            padx=10,
            pady=5,
        ).pack(fill="x")
        date_sel_frame = tk.Frame(history_frame, bg=COLOR_CARD_BG, padx=10, pady=10)
        date_sel_frame.pack(fill="both", expand=True)
        # Boutons comparaison / rapport
        comparison_frame = tk.Frame(date_sel_frame, bg=COLOR_CARD_BG)
        comparison_frame.pack(fill="x", pady=(0, 10))
        self.comparison_btn = ttk.Button(
            comparison_frame,
            text="🔄 Comparaison capture",
            style="Secondary.TButton",
            command=self._open_comparison_dialog,
        )
        self.comparison_btn.pack(side="left", fill="x", expand=True, padx=(0, 2.5))
        self.report_btn = ttk.Button(
            comparison_frame,
            text="📄 Rapport pdf",
            style="Secondary.TButton",
            command=self._generate_professional_report,
        )
        self.report_btn.pack(side="left", fill="x", expand=True)
        # Navigation prev / next
        nav_frame = tk.Frame(date_sel_frame, bg=COLOR_CARD_BG)
        nav_frame.pack(fill="x", pady=(0, 10))
        self.prev_btn = ttk.Button(
            nav_frame,
            text="◀ Précédente",
            style="Secondary.TButton",
            command=self._prev_capture,
        )
        self.prev_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.next_btn = ttk.Button(
            nav_frame,
            text="Suivante ▶",
            style="Secondary.TButton",
            command=self._next_capture,
        )
        self.next_btn.pack(side="left", fill="x", expand=True)
        # Info capture
        self.capture_info_frame = tk.Frame(date_sel_frame, bg=COLOR_CARD_BG)
        self.capture_info_frame.pack(fill="x", pady=(0, 10))
        self.capture_info_label = tk.Label(
            self.capture_info_frame,
            text="Aucune capture disponible",
            bg=COLOR_CARD_BG,
            font=("Segoe UI", 9),
            wraplength=250,
            justify="left",
        )
        self.capture_info_label.pack()
        # Liste d'historique avec canvas scrollable
        hist_frame = tk.Frame(date_sel_frame, bg=COLOR_CARD_BG)
        hist_frame.pack(fill="both", expand=True)
        canvas_frame = tk.Frame(hist_frame, bg=COLOR_CARD_BG)
        canvas_frame.pack(fill="both", expand=True)
        self.history_canvas = tk.Canvas(
            canvas_frame, bg=COLOR_CARD_BG, highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            canvas_frame, orient="vertical", command=self.history_canvas.yview
        )
        self.history_frame = tk.Frame(self.history_canvas, bg=COLOR_CARD_BG)
        self.history_canvas.create_window(
            (0, 0), window=self.history_frame, anchor="nw"
        )
        self.history_canvas.configure(yscrollcommand=scrollbar.set)
        self.history_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.history_frame.bind(
            "<Configure>",
            lambda e: self.history_canvas.configure(
                scrollregion=self.history_canvas.bbox("all")
            ),
        )
        self.history_canvas.bind(
            "<Configure>", lambda e: self.history_canvas.itemconfig(1, width=e.width)
        )
        self._setup_mousewheel_scrolling()  # HistoryPanel

    def _setup_graphs_column(self, main_content):
        """Configure la colonne de droite (graphiques)."""
        # ── Colonne droite : Graphiques (notebook 2 onglets) ────────────
        right_column = tk.Frame(main_content, bg=COLOR_FRAME_BG)
        right_column.grid(row=0, column=2, sticky="nsew")
        right_column.columnconfigure(0, weight=1)
        right_column.rowconfigure(0, weight=1)
        notebook = ttk.Notebook(right_column)
        notebook.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        # Onglet 1 : Courbe Granulométrique
        curve_tab = ttk.Frame(notebook)
        notebook.add(curve_tab, text=" Courbe granulométrique")
        curve_card = ttk.Frame(curve_tab, style="Card.TFrame")
        curve_card.pack(fill="both", expand=True)
        tk.Label(
            curve_card,
            text=" Courbe granulométrique cumulative",
            image=self.icon_wave,
            compound="left",
            bg="#e5e7eb",
            fg=COLOR_ACCENT,
            anchor="w",
            font=("Segoe UI", 11, "bold"),
            padx=10,
            pady=5,
        ).pack(fill="x")
        self.graph_frame = tk.Frame(curve_card, bg=COLOR_CARD_BG)
        self.graph_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.fig = Figure(figsize=(10, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title(
            "Courbe granulométrique cumulative", fontsize=14, fontweight="bold"
        )
        self.ax.set_xlabel("Taille du tamis (mm)", fontsize=12)
        self.ax.set_ylabel("% passant", fontsize=12)
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xticks([0, 22.4, 31.5, 40, 50, 63, 80])
        self.ax.set_xticklabels(
            ["0", "22.4", "31.5", "40", "50", "63", "80"], fontsize=11
        )
        self.ax.set_yticks(np.arange(0, 101, 10))
        self.ax.set_yticklabels(
            [f"{int(y)}%" for y in np.arange(0, 101, 10)], fontsize=11
        )
        self.ax.set_xlim([0, 80])
        self.ax.set_ylim([0, 105])
        self.ax.text(
            0.5,
            0.5,
            "Capturez des images pour voir les courbes granulométriques",
            ha="center",
            va="center",
            transform=self.ax.transAxes,
            fontsize=12,
            color="gray",
        )
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        # Onglet 2 : Distribution Granulométrique
        hist_tab = ttk.Frame(notebook)
        notebook.add(hist_tab, text=" Distribution granulométrique")
        hist_card = ttk.Frame(hist_tab, style="Card.TFrame")
        hist_card.pack(fill="both", expand=True)
        tk.Label(
            hist_card,
            text=" Histogramme de distribution des particules",
            image=self.icon_stats,
            compound="left",
            bg="#e5e7eb",
            fg=COLOR_ACCENT,
            anchor="w",
            font=("Segoe UI", 11, "bold"),
            padx=10,
            pady=5,
        ).pack(fill="x")
        self.hist_frame = tk.Frame(hist_card, bg=COLOR_CARD_BG)
        self.hist_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.hist_fig = Figure(figsize=(10, 6), dpi=100)
        self.hist_ax = self.hist_fig.add_subplot(111)
        self.hist_ax.set_title(
            "Distribution granulométrique des particules",
            fontsize=14,
            fontweight="bold",
        )
        self.hist_ax.set_xlabel("Taille (mm)", fontsize=12)
        self.hist_ax.set_ylabel("Nombre de particules", fontsize=12)
        self.hist_ax.grid(True, alpha=0.3)
        self.hist_ax.text(
            0.5,
            0.5,
            "Capturez des images pour voir la distribution granulométrique",
            ha="center",
            va="center",
            transform=self.hist_ax.transAxes,
            fontsize=12,
            color="gray",
        )
        self.hist_canvas = FigureCanvasTkAgg(self.hist_fig, master=self.hist_frame)
        self.hist_canvas.draw()
        self.hist_canvas.get_tk_widget().pack(fill="both", expand=True)
