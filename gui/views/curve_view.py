# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib

from gui.widgets.utils import (
    COLOR_FRAME_BG, COLOR_CARD_BG, COLOR_ACCENT,
    COLOR_STAT_GOOD, COLOR_STAT_WARN, COLOR_STAT_BAD,
    create_display_card
)
from analysis.statistics import calculer_statistiques_granulometriques

class CurveView:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent, bg=COLOR_FRAME_BG)
        
        # Variables pour les statistiques
        self.stat_value_labels = {}
        self.particles_tree = None
        
        self._build_ui()
    
    def _build_ui(self):
        """Construit l'interface de la vue Courbe"""
        main_content = tk.Frame(self.frame, bg=COLOR_FRAME_BG)
        main_content.pack(fill="both", expand=True, padx=20, pady=10)

        main_content.columnconfigure(0, weight=2)
        main_content.columnconfigure(1, weight=2)
        main_content.columnconfigure(2, weight=3)
        main_content.rowconfigure(0, weight=1)

        # Colonne gauche : Statistiques
        stats_column = tk.Frame(main_content, bg=COLOR_FRAME_BG)
        stats_column.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)

        stats_frame = ttk.Frame(stats_column, style="Card.TFrame")
        stats_frame.pack(fill="both", expand=True)

        tk.Label(stats_frame, text="📊 Statistiques Granulométriques", bg="#e5e7eb",
                 anchor="w", font=("Segoe UI", 12, "bold"), padx=10, pady=5).pack(fill="x")

        self.stats_inner_frame = tk.Frame(stats_frame, bg=COLOR_CARD_BG)
        self.stats_inner_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Conteneur avec scrollbar pour les stats
        self.stats_canvas_container = tk.Frame(self.stats_inner_frame, bg=COLOR_CARD_BG)
        self.stats_canvas_container.pack(fill="both", expand=True)

        self.stats_canvas = tk.Canvas(self.stats_canvas_container, bg=COLOR_CARD_BG, highlightthickness=0)
        self.stats_scrollbar = ttk.Scrollbar(self.stats_canvas_container, orient="vertical", 
                                             command=self.stats_canvas.yview)

        self.stats_content_frame = tk.Frame(self.stats_canvas, bg=COLOR_CARD_BG)
        self.stats_canvas.create_window((0, 0), window=self.stats_content_frame, anchor="nw")

        self.stats_canvas.configure(yscrollcommand=self.stats_scrollbar.set)

        self.stats_canvas.pack(side="left", fill="both", expand=True)
        self.stats_scrollbar.pack(side="right", fill="y")

        # Créer les labels de statistiques
        self._create_fixed_stat_labels()
        
        # Colonne centrale : Tableau des particules + Historique
        middle_column = tk.Frame(main_content, bg=COLOR_FRAME_BG)
        middle_column.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=0)

        # Tableau des particules
        table_frame = ttk.Frame(middle_column, style="Card.TFrame")
        table_frame.pack(fill="both", expand=True)

        tk.Label(table_frame, text="📋 Tableau des Cailloux Détectés", bg="#e5e7eb",
                 anchor="w", font=("Segoe UI", 11, "bold"), padx=10, pady=5).pack(fill="x")

        particles_frame = tk.Frame(table_frame, bg=COLOR_CARD_BG)
        particles_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self._create_particles_table(particles_frame)

        # Historique des captures
        history_frame = ttk.Frame(middle_column, style="Card.TFrame")
        history_frame.pack(fill="both", expand=True, pady=(10, 0))

        tk.Label(history_frame, text="🕐 Historique des Captures", bg="#e5e7eb",
                 anchor="w", font=("Segoe UI", 11, "bold"), padx=10, pady=5).pack(fill="x")

        date_sel_frame = tk.Frame(history_frame, bg=COLOR_CARD_BG, padx=10, pady=10)
        date_sel_frame.pack(fill="both", expand=True)

        # Boutons de comparaison et rapport
        comparison_frame = tk.Frame(date_sel_frame, bg=COLOR_CARD_BG)
        comparison_frame.pack(fill="x", pady=(0, 10))
        
        self.comparison_btn = ttk.Button(comparison_frame, text="🔄 Comparaison Multi-Captures",
                                        style="Secondary.TButton",
                                        command=self._open_comparison_dialog)
        self.comparison_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.report_btn = ttk.Button(comparison_frame, text="📄 Rapport PDF",
                                    style="Secondary.TButton",
                                    command=self._generate_professional_report)
        self.report_btn.pack(side="left", fill="x", expand=True)
        
        # Navigation entre captures
        nav_frame = tk.Frame(date_sel_frame, bg=COLOR_CARD_BG)
        nav_frame.pack(fill="x", pady=(0, 10))
        
        self.prev_btn = ttk.Button(nav_frame, text="◀ Précédente", 
                                  style="Secondary.TButton",
                                  command=self._prev_capture)
        self.prev_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.next_btn = ttk.Button(nav_frame, text="Suivante ▶", 
                                  style="Secondary.TButton",
                                  command=self._next_capture)
        self.next_btn.pack(side="left", fill="x", expand=True)
        
        # Informations sur la capture sélectionnée
        self.capture_info_frame = tk.Frame(date_sel_frame, bg=COLOR_CARD_BG)
        self.capture_info_frame.pack(fill="x", pady=(0, 10))
        
        self.capture_info_label = tk.Label(self.capture_info_frame, 
                                          text="Aucune capture disponible",
                                          bg=COLOR_CARD_BG, font=("Segoe UI", 9),
                                          wraplength=250, justify="left")
        self.capture_info_label.pack()

        # Liste d'historique
        hist_frame = tk.Frame(date_sel_frame, bg=COLOR_CARD_BG)
        hist_frame.pack(fill="both", expand=True)
        
        canvas_frame = tk.Frame(hist_frame, bg=COLOR_CARD_BG)
        canvas_frame.pack(fill="both", expand=True)
        
        self.history_canvas = tk.Canvas(canvas_frame, bg=COLOR_CARD_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.history_canvas.yview)
        
        self.history_frame = tk.Frame(self.history_canvas, bg=COLOR_CARD_BG)
        self.history_canvas.create_window((0, 0), window=self.history_frame, anchor="nw")
        
        self.history_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.history_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.history_frame.bind("<Configure>", 
                              lambda e: self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all")))
        self.history_canvas.bind("<Configure>", 
                                lambda e: self.history_canvas.itemconfig(1, width=e.width))
        self._setup_mousewheel_scrolling()

        
        self.history_frame.bind("<Configure>", 
                               lambda e: self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all")))
        self.history_canvas.bind("<Configure>", 
                                lambda e: self.history_canvas.itemconfig(1, width=e.width))

        # Colonne droite : Graphiques
        right_column = tk.Frame(main_content, bg=COLOR_FRAME_BG)
        right_column.grid(row=0, column=2, sticky="nsew")

        right_column.columnconfigure(0, weight=1)
        right_column.rowconfigure(0, weight=1)

        notebook = ttk.Notebook(right_column)
        notebook.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        # Onglet 1 : Courbe Granulométrique
        curve_tab = ttk.Frame(notebook)
        notebook.add(curve_tab, text="📈 Courbe Granulométrique")
        
        curve_card = ttk.Frame(curve_tab, style="Card.TFrame")
        curve_card.pack(fill="both", expand=True)
        
        tk.Label(curve_card, text="Courbe Granulométrique Cumulative", bg="#e5e7eb",
                 anchor="w", font=("Segoe UI", 11, "bold"), padx=10).pack(fill="x")
        
        self.graph_frame = tk.Frame(curve_card, bg=COLOR_CARD_BG)
        self.graph_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.fig = Figure(figsize=(10, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title('Courbe Granulométrique Cumulative', fontsize=14, fontweight='bold')
        self.ax.set_xlabel('Taille du tamis (mm)', fontsize=12)
        self.ax.set_ylabel('% passant', fontsize=12)
        self.ax.grid(True, alpha=0.3)
        
        self.ax.set_xticks([0, 22.4, 31.5, 40, 50, 63, 80])
        self.ax.set_xticklabels(['0', '22.4', '31.5', '40', '50', '63', '80'], fontsize=11)
        self.ax.set_yticks(np.arange(0, 101, 10))
        self.ax.set_yticklabels([f'{int(y)}%' for y in np.arange(0, 101, 10)], fontsize=11)
        self.ax.set_xlim([0, 80])
        self.ax.set_ylim([0, 105])
        
        self.ax.text(0.5, 0.5, 'Capturez des images pour voir les courbes granulométriques',
                    horizontalalignment='center', verticalalignment='center',
                    transform=self.ax.transAxes, fontsize=12, color='gray')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Onglet 2 : Distribution Granulométrique
        hist_tab = ttk.Frame(notebook)
        notebook.add(hist_tab, text="📊 Distribution Granulométrique")
        
        hist_card = ttk.Frame(hist_tab, style="Card.TFrame")
        hist_card.pack(fill="both", expand=True)
        
        tk.Label(hist_card, text="Histogramme de Distribution des Particules", bg="#e5e7eb",
                 anchor="w", font=("Segoe UI", 11, "bold"), padx=10).pack(fill="x")
        
        self.hist_frame = tk.Frame(hist_card, bg=COLOR_CARD_BG)
        self.hist_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.hist_fig = Figure(figsize=(10, 6), dpi=100)
        self.hist_ax = self.hist_fig.add_subplot(111)
        self.hist_ax.set_title('Distribution Granulométrique des Particules', fontsize=14, fontweight='bold')
        self.hist_ax.set_xlabel('Taille (mm)', fontsize=12)
        self.hist_ax.set_ylabel('Nombre de particules', fontsize=12)
        self.hist_ax.grid(True, alpha=0.3)
        
        self.hist_ax.text(0.5, 0.5, 'Capturez des images pour voir la distribution granulométrique',
                         horizontalalignment='center', verticalalignment='center',
                         transform=self.hist_ax.transAxes, fontsize=12, color='gray')
        
        self.hist_canvas = FigureCanvasTkAgg(self.hist_fig, master=self.hist_frame)
        self.hist_canvas.draw()
        self.hist_canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def _create_fixed_stat_labels(self):
        """Crée les labels des statistiques une seule fois"""
        for widget in self.stats_content_frame.winfo_children():
            widget.destroy()
    
        # Titre
        title_label = tk.Label(self.stats_content_frame, text="📊 STATISTIQUES GRANULOMÉTRIQUES",
                              bg=COLOR_CARD_BG, font=("Segoe UI", 12, "bold"),
                              fg=COLOR_ACCENT)
        title_label.pack(anchor="w", pady=(0, 15), padx=5)
    
        # Configuration des statistiques
        stats_config = [
            ('n_particules', "Nombre de particules:", "", "normal"),
            ('', "", "", "separator"),
            ('min_mm_minor', "Min (Axe mineur):", " mm", "normal"),
            ('max_mm_minor', "Max (Axe mineur):", " mm", "normal"),
            ('min_mm_major', "Min (Axe majeur):", " mm", "normal"),
            ('max_mm_major', "Max (Axe majeur):", " mm", "normal"),
            ('moyenne_mm_minor', "Moyenne (Axe mineur):", " mm", "normal"),
            ('moyenne_mm_major', "Moyenne (Axe majeur):", " mm", "normal"),
            ('', "", "", "separator"),
            ('D10_mm', "D10 (10% plus fins):", " mm", "percentile"),
            ('D25_mm', "D25 (25% plus fins):", " mm", "percentile"),
            ('D50_mm', "D50 (Taille médiane):", " mm", "percentile"),
            ('D75_mm', "D75 (75% plus fins):", " mm", "percentile"),
            ('D90_mm', "D90 (90% plus fins):", " mm", "percentile"),
        ]
     
        # Créer chaque ligne
        for stat_key, label_text, unit, stat_type in stats_config:
            if stat_type == "separator":
                ttk.Separator(self.stats_content_frame, orient="horizontal").pack(fill="x", pady=10)
                continue
         
            stat_frame = tk.Frame(self.stats_content_frame, bg=COLOR_CARD_BG)
            stat_frame.pack(fill="x", pady=2, padx=5)
         
            name_label = tk.Label(stat_frame, text=label_text, bg=COLOR_CARD_BG,
                                 font=("Segoe UI", 10), width=25, anchor="w")
            name_label.pack(side="left")
        
            value_label = tk.Label(stat_frame, text="N/A", bg=COLOR_CARD_BG,
                                  fg="#000000", font=("Segoe UI", 10, "bold"),
                                  anchor="w", width=12)
            value_label.pack(side="left", padx=(5, 0))
         
            if unit:
                unit_label = tk.Label(stat_frame, text=unit, bg=COLOR_CARD_BG,
                                     font=("Segoe UI", 10), fg="#6b7280")
                unit_label.pack(side="left", padx=(2, 0))
         
            if stat_key:
                self.stat_value_labels[stat_key] = value_label
     
        self.stats_content_frame.update_idletasks()
        self.stats_canvas.configure(scrollregion=self.stats_canvas.bbox("all"))
    
    def _create_particles_table(self, parent):
        """Crée le tableau des particules"""
        table_frame = tk.Frame(parent, bg=COLOR_CARD_BG)
        table_frame.pack(fill="both", expand=True)

        columns = ('id', 'minor_mm', 'major_mm')
        self.particles_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        self.particles_tree.heading('id', text='ID')
        self.particles_tree.heading('minor_mm', text='Axe Mineur (mm)')
        self.particles_tree.heading('major_mm', text='Axe Majeur (mm)')
        
        self.particles_tree.column('id', width=50, anchor='center')
        self.particles_tree.column('minor_mm', width=150, anchor='center')
        self.particles_tree.column('major_mm', width=150, anchor='center')
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.particles_tree.yview)
        self.particles_tree.configure(yscrollcommand=scrollbar.set)
        
        self.particles_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _update_particles_table(self):
        """Met à jour le tableau des particules"""
        if not self.particles_tree:
            return
            
        for item in self.particles_tree.get_children():
            self.particles_tree.delete(item)
        
        if hasattr(self.app, 'measure_view') and hasattr(self.app.measure_view, 'particles_table_data'):
            for particle in self.app.measure_view.particles_table_data:
                self.particles_tree.insert('', 'end', values=(
                    particle['id'],
                    f"{particle['minor_mm']:.2f}",
                    f"{particle['major_mm']:.2f}"
                ))
    
    def _update_particles_table_for_capture(self, index):
        """Met à jour le tableau pour une capture spécifique"""
        if 0 <= index < len(self.app.capture_history):
            capture = self.app.capture_history[index]
            particles_data = []
            
            for i, particle in enumerate(capture.get('particles_data', [])):
                particles_data.append({
                    'id': i + 1,
                    'minor_mm': particle['minor_axis_mm'],
                    'major_mm': particle['major_axis_mm']
                })
            
            # Mettre à jour le tableau dans measure_view
            if hasattr(self.app, 'measure_view'):
                self.app.measure_view.particles_table_data = particles_data
            
            self._update_particles_table()
    
    def update_statistics_display(self, capture_data):
        """Met à jour l'affichage des statistiques"""
        if not capture_data or not capture_data.get('particles_data'):
            for key, label in self.stat_value_labels.items():
                label.config(text="N/A", fg="#000000")
            return
    
        particles_data = capture_data.get('particles_data', [])
        minor_axes_mm = []
        major_axes_mm = []
    
        for particle in particles_data:
            minor_mm = particle.get('minor_axis_mm', 0)
            major_mm = particle.get('major_axis_mm', 0)
        
            if minor_mm > 0.1:
                minor_axes_mm.append(minor_mm)
            if major_mm > 0.1:
                major_axes_mm.append(major_mm)
    
        if not minor_axes_mm:
            for key, label in self.stat_value_labels.items():
                label.config(text="N/A", fg="#000000")
            return
    
        stats = calculer_statistiques_granulometriques(
            particles_data, 
            minor_axes_mm,
            major_axes_mm
        )
    
        if not stats:
            return
    
        for stat_key, label in self.stat_value_labels.items():
            if stat_key in stats:
                value = stats[stat_key]
             
                if isinstance(value, (int, float)):
                    if value == 0:
                        display_text = "0"
                    else:
                        display_text = f"{value:.2f}"
                else:
                    display_text = str(value)
             
                color = "#000000"
                label.config(text=display_text, fg=color)
     
        self.stats_content_frame.update_idletasks()
        self.stats_canvas.configure(scrollregion=self.stats_canvas.bbox("all"))
    
    def _update_capture_history_display(self):
        """Met à jour l'affichage de l'historique des captures"""
        for widget in self.history_frame.winfo_children():
            widget.destroy()
     
        if not self.app.capture_history:
            tk.Label(self.history_frame, text="Aucune capture disponible",
                    bg=COLOR_CARD_BG, fg="#666", font=("Segoe UI", 10)).pack(pady=20)
            return
     
        # Afficher TOUTES les captures (plus récentes en premier)
        for i in range(len(self.app.capture_history) - 1, -1, -1):
            idx = i
            capture = self.app.capture_history[idx]
         
            frame = tk.Frame(self.history_frame, bg=COLOR_CARD_BG, relief="solid", borderwidth=1)
            frame.pack(fill="x", pady=2, padx=2)
         
            if idx == self.app.current_capture_index:
                frame.configure(bg="#e3f2fd")
                bg_color = "#e3f2fd"
            else:
                bg_color = COLOR_CARD_BG
         
            content_frame = tk.Frame(frame, bg=bg_color)
            content_frame.pack(fill="x", padx=8, pady=4)
         
            title_frame = tk.Frame(content_frame, bg=bg_color)
            title_frame.pack(fill="x")
         
            tk.Label(title_frame, text=f"#{capture['id']}", 
                    bg=bg_color, font=("Segoe UI", 9, "bold")).pack(side="left")
         
            tk.Label(title_frame, text=f" {capture['timestamp'].strftime('%H:%M')}", 
                    bg=bg_color, font=("Segoe UI", 8)).pack(side="left", padx=(0, 5))
         
            info_frame = tk.Frame(content_frame, bg=bg_color)
            info_frame.pack(fill="x", pady=(2, 0))
         
            tk.Label(info_frame, text=f"Objets: {capture['particles_count']}",
                    bg=bg_color, font=("Segoe UI", 8)).pack(side="left")
         
            btn_frame = tk.Frame(content_frame, bg=bg_color)
            btn_frame.pack(fill="x", pady=(3, 0))
          
            btn = ttk.Button(btn_frame, text="Afficher", style="Secondary.TButton",
                            command=lambda idx=idx: self._select_capture(idx))
            btn.pack(side="right")
     
        # Mettre à jour la région de défilement
        self.history_frame.update_idletasks()
        self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))
     
        # Rebinder la roulette sur les nouveaux éléments
        self._setup_mousewheel_scrolling()
        
    def _setup_mousewheel_scrolling(self):
        """Configure le défilement avec la roulette pour l'historique des captures"""
    
        def on_mousewheel(event):
            """Gère l'événement de la roulette de la souris"""
            # Windows/MacOS : event.delta
            # Linux : event.num (4=up, 5=down)
        
            # Vers le bas
            if (hasattr(event, 'delta') and event.delta < 0) or event.num == 5:
                self.history_canvas.yview_scroll(1, "units")
            # Vers le haut
            elif (hasattr(event, 'delta') and event.delta > 0) or event.num == 4:
                self.history_canvas.yview_scroll(-1, "units")
        
            return "break"
    
        # Bind sur le canvas de l'historique
        self.history_canvas.bind("<MouseWheel>", on_mousewheel)
        self.history_canvas.bind("<Button-4>", on_mousewheel)  # Linux scroll up
        self.history_canvas.bind("<Button-5>", on_mousewheel)  # Linux scroll down
    
        # Bind aussi sur le frame qui contient les captures
        self.history_frame.bind("<MouseWheel>", on_mousewheel)
        self.history_frame.bind("<Button-4>", on_mousewheel)
        self.history_frame.bind("<Button-5>", on_mousewheel)
     
        # Fonction pour bind sur tous les enfants
        def bind_to_children(widget):
            for child in widget.winfo_children():
                child.bind("<MouseWheel>", on_mousewheel)
                child.bind("<Button-4>", on_mousewheel)
                child.bind("<Button-5>", on_mousewheel)
                # Récursif pour les enfants des enfants
                bind_to_children(child)
     
        # Bind sur tous les widgets enfants de l'historique
        bind_to_children(self.history_frame)
    
    def _select_capture(self, index):
        """Sélectionne une capture dans l'historique"""
        if 0 <= index < len(self.app.capture_history):
            self.app.current_capture_index = index
            self._update_capture_history_display()
            self._update_curve_view_for_capture(self.app.capture_history[index]['id'])
            self._update_histogram_for_capture(self.app.capture_history[index]['id'])
            self._update_capture_info()
            self._update_particles_table_for_capture(index)
            self.update_statistics_display(self.app.capture_history[index])
    
    def _prev_capture(self):
        """Affiche la capture précédente"""
        if self.app.current_capture_index > 0:
            self._select_capture(self.app.current_capture_index - 1)
    
    def _next_capture(self):
        """Affiche la capture suivante"""
        if self.app.current_capture_index < len(self.app.capture_history) - 1:
            self._select_capture(self.app.current_capture_index + 1)
    
    def _update_capture_info(self):
        """Met à jour les informations de la capture sélectionnée"""
        if not self.app.capture_history or self.app.current_capture_index < 0:
            self.capture_info_label.config(text="Aucune capture disponible")
            return
        
        capture = self.app.capture_history[self.app.current_capture_index]
        info_text = f"Capture #{capture['id']}\n"
        info_text += f"{capture['timestamp'].strftime('%H:%M:%S')}\n"
        info_text += f"Objets: {capture['particles_count']}"
        
        self.capture_info_label.config(text=info_text)
    
    def _update_histogram_for_capture(self, capture_id):
        """Met à jour l'histogramme pour une capture spécifique"""
        if not self.app.capture_history:
            return
        
        capture = None
        for cap in self.app.capture_history:
            if cap['id'] == capture_id:
                capture = cap
                break
        
        if not capture:
            self.hist_ax.clear()
            self.hist_ax.text(0.5, 0.5, 'Aucune capture sélectionnée\nVeuillez sélectionner une capture dans l\'historique',
                             horizontalalignment='center', verticalalignment='center',
                             transform=self.hist_ax.transAxes, fontsize=12, color='gray')
            self.hist_ax.set_xlabel('Taille (mm)', fontsize=12)
            self.hist_ax.set_ylabel('Nombre de particules', fontsize=12)
            self.hist_ax.set_title('Distribution Granulométrique des Particules', fontsize=14, fontweight='bold')
            self.hist_ax.grid(True, alpha=0.3)
            self.hist_canvas.draw()
            return
        
        self.hist_ax.clear()
        
        if capture.get('minor_axes_mm') and len(capture['minor_axes_mm']) > 0:
            try:
                minor_axes_mm = np.array([x for x in capture['minor_axes_mm'] if x > 0.1])
                
                if len(minor_axes_mm) == 0:
                    raise ValueError("Pas de données après filtrage")
                
                bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 100]
                bin_labels = ['<10', '10-20', '20-30', '30-40', '40-50', '50-60', '60-70', '70-80', '>80']
                
                hist, bin_edges = np.histogram(minor_axes_mm, bins=bins)
                
                colors = plt.cm.viridis(np.linspace(0, 1, len(hist)))
                bars = self.hist_ax.bar(range(len(hist)), hist, color=colors, edgecolor='black', alpha=0.8)
                
                for i, (bar, val) in enumerate(zip(bars, hist)):
                    height = bar.get_height()
                    self.hist_ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                                     f'{val}', ha='center', va='bottom', fontsize=9)
                
                self.hist_ax.set_xlabel('Taille des particules (mm)', fontsize=12)
                self.hist_ax.set_ylabel('Nombre de particules', fontsize=12)
                self.hist_ax.set_title(f'Distribution Granulométrique - Capture #{capture["id"]}', 
                                      fontsize=14, fontweight='bold')
                
                self.hist_ax.set_xticks(range(len(bin_labels)))
                self.hist_ax.set_xticklabels(bin_labels, rotation=45, fontsize=10)
                
                self.hist_ax.grid(True, alpha=0.3, linestyle='--', axis='y')
                
                mean_size = np.mean(minor_axes_mm)
                median_size = np.median(minor_axes_mm)
                
                stats_text = (f"Total particules: {len(minor_axes_mm)}\n"
                            f"Moyenne: {mean_size:.1f} mm\n"
                            f"Médiane: {median_size:.1f} mm\n")
                           
                
                self.hist_ax.text(0.02, 0.98, stats_text, transform=self.hist_ax.transAxes,
                                 verticalalignment='top', fontsize=9,
                                 bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))
                
                self.hist_ax.set_ylim([0, max(hist) * 1.2])
                
                self.hist_fig.tight_layout(pad=3.0)
                
            except Exception as e:
                self.hist_ax.text(0.5, 0.5, f'Erreur lors du tracé de l\'histogramme\n{str(e)[:50]}',
                                 horizontalalignment='center', verticalalignment='center',
                                 transform=self.hist_ax.transAxes, fontsize=12, color='red')
                self.hist_ax.grid(True, alpha=0.3)
                self.hist_ax.set_xlabel('Taille (mm)', fontsize=12)
                self.hist_ax.set_ylabel('Nombre de particules', fontsize=12)
                self.hist_ax.set_title('Distribution Granulométrique des Particules', fontsize=14, fontweight='bold')
        else:
            self.hist_ax.text(0.5, 0.5, 'Aucune donnée de distribution disponible\npour cette capture',
                             horizontalalignment='center', verticalalignment='center',
                             transform=self.hist_ax.transAxes, fontsize=12, color='gray')
            self.hist_ax.set_xlabel('Taille (mm)', fontsize=12)
            self.hist_ax.set_ylabel('Nombre de particules', fontsize=12)
            self.hist_ax.set_title('Distribution Granulométrique des Particules', fontsize=14, fontweight='bold')
            self.hist_ax.grid(True, alpha=0.3)
        
        self.hist_canvas.draw()
    
    def _update_curve_view_for_capture(self, capture_id):
        """Met à jour la courbe granulométrique pour une capture spécifique"""
        if capture_id is None:
            self.ax.clear()
            self.ax.text(0.5, 0.5, 'Capturez des images pour voir les courbes granulométriques',
                        horizontalalignment='center', verticalalignment='center',
                        transform=self.ax.transAxes, fontsize=12, color='gray')
            self.ax.set_title('Courbe Granulométrique Cumulative', fontsize=14, fontweight='bold')
            self.ax.set_xlabel('Taille du tamis (mm)', fontsize=12)
            self.ax.set_ylabel('% passant', fontsize=12)
            self.ax.grid(True, alpha=0.3)
            self.ax.set_xticks([0, 22.4, 31.5, 40, 50, 63, 80])
            self.ax.set_xticklabels(['0', '22.4', '31.5', '40', '50', '63', '80'], fontsize=11)
            self.ax.set_yticks(np.arange(0, 101, 10))
            self.ax.set_yticklabels([f'{int(y)}%' for y in np.arange(0, 101, 10)], fontsize=11)
            self.ax.set_xlim([0, 80])
            self.ax.set_ylim([0, 105])
            self.canvas.draw()
            return
        
        capture = None
        for cap in self.app.capture_history:
            if cap['id'] == capture_id:
                capture = cap
                break
        
        if not capture or not capture.get('tamis_exp'):
            self.ax.clear()
            self.ax.text(0.5, 0.5, 'Aucune donnée granulométrique disponible\npour cette capture',
                        horizontalalignment='center', verticalalignment='center',
                        transform=self.ax.transAxes, fontsize=12, color='gray')
            self.ax.set_title('Courbe Granulométrique Cumulative', fontsize=14, fontweight='bold')
            self.ax.set_xlabel('Taille du tamis (mm)', fontsize=12)
            self.ax.set_ylabel('% passant', fontsize=12)
            self.ax.grid(True, alpha=0.3)
            self.ax.set_xticks([0, 22.4, 31.5, 40, 50, 63, 80])
            self.ax.set_xticklabels(['0', '22.4', '31.5', '40', '50', '63', '80'], fontsize=11)
            self.ax.set_yticks(np.arange(0, 101, 10))
            self.ax.set_yticklabels([f'{int(y)}%' for y in np.arange(0, 101, 10)], fontsize=11)
            self.ax.set_xlim([0, 85])
            self.ax.set_ylim([0, 105])
            self.canvas.draw()
            return
        
        self.ax.clear()
        
        diameters_vss = [0, 22.4, 31.5, 40, 50, 63, 100]
        cumFraction_vss = [0, 4, 26, 70, 99, 99, 100]
        diameters_vsi = [0, 22.4, 31.5, 40, 50, 50, 50]
        cumFraction_vsi = [0, 0, 0, 25, 70, 70, 70]
        
        self.ax.plot(diameters_vss, cumFraction_vss, 'g--', linewidth=1.5, label='VSS')
        self.ax.plot(diameters_vsi, cumFraction_vsi, color='orange', linestyle='--', linewidth=2, alpha=0.7, label='VSI')
        
        tamis = capture['tamis_exp']
        cumul = capture['cumulative_raw']
        
        if self.app.show_corrected_curve_var.get() and capture.get('cumulative_corrected'):
            cumul = capture['cumulative_corrected']
            label = 'Courbe corrigée (DNA)'
        else:
            label = 'Courbe brute'
        
        self.ax.plot(tamis, cumul, 'b-o', linewidth=2, markersize=4, label=label)
        
        self.ax.set_xlabel("Taille du tamis (mm)", fontsize=12)
        self.ax.set_ylabel("% passant cumulé", fontsize=12)
        self.ax.set_title(f"Courbe Granulométrique - Capture #{capture['id']}", 
                         fontsize=14, fontweight='bold')
        self.ax.set_xticks([0, 22.4, 31.5, 40, 50, 63, 80])
        self.ax.set_xticklabels(['0', '22.4', '31.5', '40', '50', '63', '80'], fontsize=11)
        self.ax.set_yticks(np.arange(0, 101, 10))
        self.ax.set_yticklabels([f'{int(y)}%' for y in np.arange(0, 101, 10)], fontsize=11)
        self.ax.set_xlim([0, 85])
        self.ax.set_ylim([0, 105])
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(loc='upper left', fontsize=10)
        
        for i, (x, y) in enumerate(zip(tamis, cumul)):
            self.ax.annotate(f'{y:.1f}%', 
                            xy=(x, y), 
                            xytext=(0, 5 if i % 2 == 0 else -15),
                            textcoords='offset points',
                            ha='center', va='bottom' if i % 2 == 0 else 'top',
                            fontsize=9, fontweight='bold',
                            bbox=dict(boxstyle="round,pad=0.2", 
                                     facecolor="white", 
                                     edgecolor="lightblue", 
                                     alpha=0.8))
        
        self.canvas.draw()
    
    def _open_comparison_dialog(self):
        """Ouvre la boîte de dialogue pour la comparaison multi-captures"""
        from tkinter import messagebox
        
        if not self.app.capture_history:
            messagebox.showinfo("Information", "Aucune capture disponible pour comparaison.")
            return
        
        dialog = tk.Toplevel(self.app)
        dialog.title("Comparaison Multi-Captures")
        dialog.geometry("500x400")
        dialog.configure(bg=COLOR_FRAME_BG)
        
        tk.Label(dialog, text="Sélectionnez les captures à comparer:",
                font=("Segoe UI", 12, "bold"), 
                bg=COLOR_FRAME_BG,  # Fond
                fg="white",         # ← Texte en BLANC
                pady=10).pack()
        list_frame = tk.Frame(dialog, bg=COLOR_FRAME_BG)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        listbox = tk.Listbox(list_frame, selectmode="multiple", 
                            yscrollcommand=scrollbar.set,
                            font=("Segoe UI", 10))
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)
        
        for capture in self.app.capture_history:
            listbox.insert(tk.END, 
                          f"Capture #{capture['id']} - {capture['timestamp'].strftime('%H:%M:%S')} - {capture['particles_count']} particules")
        
        button_frame = tk.Frame(dialog, bg=COLOR_FRAME_BG)
        button_frame.pack(pady=10)
        
        def apply_comparison():
            selections = listbox.curselection()
            if len(selections) < 2:
                messagebox.showwarning("Attention", "Veuillez sélectionner au moins 2 captures.")
                return
            
            self.app.comparison_captures = [self.app.capture_history[i]['id'] for i in selections]
            self.app.comparison_mode = True
            self._display_comparison_chart()
            dialog.destroy()
            messagebox.showinfo("Succès", f"Comparaison de {len(selections)} captures activée.")
        
        ttk.Button(button_frame, text="Comparer", 
                  style="Start.TButton",
                  command=apply_comparison).pack(side="left", padx=5)
        
        ttk.Button(button_frame, text="Annuler",
                  style="Secondary.TButton",
                  command=dialog.destroy).pack(side="left", padx=5)
    
    def _display_comparison_chart(self):
        """Affiche le graphique de comparaison avec zoom interactif"""
        if not self.app.comparison_captures:
            return

        comp_fig = Figure(figsize=(12, 8))
        comp_ax = comp_fig.add_subplot(111)

        # Activer les outils de navigation
        from matplotlib.backend_bases import MouseButton
        comp_fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.1)

        colors = plt.cm.tab10(np.linspace(0, 1, len(self.app.comparison_captures)))

        # Dictionnaire pour stocker les annotations
        all_annotations = []

        for i, capture_id in enumerate(self.app.comparison_captures):
            capture = next((c for c in self.app.capture_history if c['id'] == capture_id), None)
            if capture and capture.get('tamis_exp') and capture.get('cumulative_raw'):
                tamis = capture['tamis_exp']
                cumul = capture['cumulative_raw']
            
                if self.app.show_corrected_curve_var.get() and capture.get('cumulative_corrected'):
                    cumul = capture['cumulative_corrected']
             
                # Tracer la courbe
                comp_ax.plot(tamis, cumul, marker='o', color=colors[i], linewidth=2,
                           label=f"Capture #{capture_id} ({capture['particles_count']} part.)")
             
                # Ajouter les annotations de pourcentage
                capture_annotations = []
                for j, (x, y) in enumerate(zip(tamis, cumul)):
                    # Déterminer la position de l'annotation (haut ou bas selon l'index)
                    offset_direction = 5 if j % 2 == 0 else -15
                    vertical_alignment = 'bottom' if j % 2 == 0 else 'top'
                 
                    # Créer l'annotation
                    ann = comp_ax.annotate(f'{y:.1f}%', 
                                xy=(x, y), 
                                xytext=(0, offset_direction),
                                textcoords='offset points',
                                ha='center', 
                                va=vertical_alignment,
                                fontsize=8, 
                                fontweight='bold',
                                color=colors[i],  # Même couleur que la courbe
                                bbox=dict(boxstyle="round,pad=0.2", 
                                         facecolor="white", 
                                         edgecolor=colors[i], 
                                         alpha=0.8))
                    capture_annotations.append(ann)
             
                # Stocker les annotations pour cette courbe
                all_annotations.append(capture_annotations)
     
        diameters_vss = [0, 22.4, 31.5, 40, 50, 63, 100]
        cumFraction_vss = [0, 4, 26, 70, 99, 99, 100]
        diameters_vsi = [0, 22.4, 31.5, 40, 50, 50, 50]
        cumFraction_vsi = [0, 0, 0, 25, 70, 70, 70]
    
        # Tracer les courbes de référence (sans annotations pour éviter la surcharge)
        comp_ax.plot(diameters_vss, cumFraction_vss, 'g--', linewidth=2,
                    label='Courbe VSS', alpha=0.7)
        comp_ax.plot(diameters_vsi, cumFraction_vsi, 'orange', linewidth=2, linestyle='--',
                    label='Courbe VSI', alpha=0.7)
    
        comp_ax.set_xlabel("Taille du tamis (mm)", fontsize=12)
        comp_ax.set_ylabel("% passant cumulé", fontsize=12)
        comp_ax.set_title("Comparaison Multi-Captures (Appuyez sur Z pour activer le zoom)", fontsize=14, fontweight='bold')
        comp_ax.set_xticks([0, 22.4, 31.5, 40, 50, 63, 80])
        comp_ax.set_yticks(np.arange(0, 101, 10))
        comp_ax.set_xlim([0, 85])
        comp_ax.set_ylim([0, 105])
        comp_ax.grid(True, alpha=0.3)
     
        # Fonction pour gérer la visibilité des annotations lors du zoom
        def update_annotations_visibility():
            """Met à jour la visibilité des annotations en fonction du zoom"""
            x_lim = comp_ax.get_xlim()
            y_lim = comp_ax.get_ylim()
         
            for capture_anns in all_annotations:
                for ann in capture_anns:
                    x, y = ann.xy
                    # Afficher l'annotation seulement si elle est dans les limites du zoom
                    if x_lim[0] <= x <= x_lim[1] and y_lim[0] <= y <= y_lim[1]:
                        ann.set_visible(True)
                    else:
                        ann.set_visible(False)
            comp_fig.canvas.draw_idle()
     
        # Variables pour le zoom - DÉSACTIVÉ par défaut
        zoom_state = {'enabled': False, 'start_x': None, 'start_y': None, 'rect': None}
     
        def on_press(event):
            if not zoom_state['enabled']:
                return
            if event.inaxes != comp_ax:
                return
            if event.button == MouseButton.LEFT:
                # Début du zoom
                zoom_state['start_x'] = event.xdata
                zoom_state['start_y'] = event.ydata
                zoom_state['rect'] = plt.Rectangle((event.xdata, event.ydata), 0, 0,
                                                   fill=False, edgecolor='red', linewidth=1)
                comp_ax.add_patch(zoom_state['rect'])
                comp_fig.canvas.draw()
            elif event.button == MouseButton.RIGHT:
                # Reset zoom
                comp_ax.set_xlim([0, 85])
                comp_ax.set_ylim([0, 105])
                comp_ax.set_xticks([0, 22.4, 31.5, 40, 50, 63, 80])
                comp_ax.set_yticks(np.arange(0, 101, 10))
                # Réafficher toutes les annotations après reset
                for capture_anns in all_annotations:
                    for ann in capture_anns:
                        ann.set_visible(True)
                comp_fig.canvas.draw()
 
        def on_motion(event):
            if not zoom_state['enabled']:
                return
            if event.inaxes != comp_ax:
                return
            if zoom_state['start_x'] is not None and zoom_state['rect'] is not None:
                # Mise à jour du rectangle de sélection
                width = event.xdata - zoom_state['start_x']
                height = event.ydata - zoom_state['start_y']
                zoom_state['rect'].set_width(width)
                zoom_state['rect'].set_height(height)
                comp_fig.canvas.draw()
     
        def on_release(event):
            if not zoom_state['enabled']:
                return
            if event.inaxes != comp_ax:
                return
            if event.button == MouseButton.LEFT and zoom_state['start_x'] is not None:
                # Appliquer le zoom
                end_x = event.xdata
                end_y = event.ydata
             
                if zoom_state['rect']:
                    zoom_state['rect'].remove()
                    zoom_state['rect'] = None
             
                # S'assurer que les coordonnées sont dans le bon ordre
                x1, x2 = sorted([zoom_state['start_x'], end_x])
                y1, y2 = sorted([zoom_state['start_y'], end_y])
             
                # Appliquer le zoom seulement si la zone est suffisamment grande
                if abs(x2 - x1) > 1 and abs(y2 - y1) > 5:
                    comp_ax.set_xlim(x1, x2)
                    comp_ax.set_ylim(y1, y2)
                 
                    # Mettre à jour les ticks
                    x_ticks = np.linspace(x1, x2, 6)
                    y_ticks = np.linspace(y1, y2, 6)
                 
                    comp_ax.set_xticks(x_ticks)
                    comp_ax.set_xticklabels([f'{x:.1f}' for x in x_ticks])
                    comp_ax.set_yticks(y_ticks)
                    comp_ax.set_yticklabels([f'{y:.1f}' for y in y_ticks])
                 
                    # Mettre à jour la visibilité des annotations
                    update_annotations_visibility()
             
                zoom_state['start_x'] = None
                zoom_state['start_y'] = None
                comp_fig.canvas.draw()
     
        def on_scroll(event):
            if not zoom_state['enabled']:
                return
            if event.inaxes != comp_ax:
                return
         
            # Zoom avec la molette
            zoom_factor = 1.2 if event.step > 0 else 0.8
         
            # Récupérer les limites actuelles
            x_lim = comp_ax.get_xlim()
            y_lim = comp_ax.get_ylim()
         
            # Calculer le centre
            x_center = event.xdata
            y_center = event.ydata
         
            # Appliquer le zoom
            new_x_width = (x_lim[1] - x_lim[0]) * zoom_factor
            new_y_width = (y_lim[1] - y_lim[0]) * zoom_factor
         
            comp_ax.set_xlim([x_center - new_x_width/2, x_center + new_x_width/2])
            comp_ax.set_ylim([y_center - new_y_width/2, y_center + new_y_width/2])
         
            # Mettre à jour les ticks
            x_ticks = np.linspace(comp_ax.get_xlim()[0], comp_ax.get_xlim()[1], 6)
            y_ticks = np.linspace(comp_ax.get_ylim()[0], comp_ax.get_ylim()[1], 6)
         
            comp_ax.set_xticks(x_ticks)
            comp_ax.set_xticklabels([f'{x:.1f}' for x in x_ticks])
            comp_ax.set_yticks(y_ticks)
            comp_ax.set_yticklabels([f'{y:.1f}' for y in y_ticks])
         
            # Mettre à jour la visibilité des annotations
            update_annotations_visibility()
         
            comp_fig.canvas.draw()
     
        def on_key(event):
            if event.key == 'r' or event.key == 'R':
                # Reset zoom avec la touche R
                comp_ax.set_xlim([0, 85])
                comp_ax.set_ylim([0, 105])
                comp_ax.set_xticks([0, 22.4, 31.5, 40, 50, 63, 80])
                comp_ax.set_xticklabels(['0', '22.4', '31.5', '40', '50', '63', '80'])
                comp_ax.set_yticks(np.arange(0, 101, 10))
                comp_ax.set_yticklabels([f'{int(y)}%' for y in np.arange(0, 101, 10)])
             
                # Réafficher toutes les annotations après reset
                for capture_anns in all_annotations:
                    for ann in capture_anns:
                        ann.set_visible(True)
             
                comp_fig.canvas.draw()
            elif event.key == 'z' or event.key == 'Z':
                # Activer/désactiver le zoom
                zoom_state['enabled'] = not zoom_state['enabled']
                status = "activé" if zoom_state['enabled'] else "désactivé"
                comp_ax.set_title(f"Comparaison Multi-Captures - Zoom {status}", fontsize=14, fontweight='bold')
             
                # Changer la couleur du titre pour indiquer l'état
                if zoom_state['enabled']:
                    comp_ax.title.set_color('red')
                    # Afficher un message temporaire
                    comp_ax.text(0.5, 0.02, 'Zoom activé - Cliquez-glissez pour sélectionner une zone', 
                                transform=comp_ax.transAxes, fontsize=10, color='red',
                                ha='center', va='bottom', 
                                bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
                else:
                    comp_ax.title.set_color('black')
                    # Effacer le message temporaire
                    for text in comp_ax.texts:
                        if 'Zoom activé' in text.get_text():
                            text.remove()
             
                # Mettre à jour la visibilité des annotations quand on active/désactive le zoom
                if not zoom_state['enabled']:
                    # Si on désactive le zoom, réafficher toutes les annotations
                    for capture_anns in all_annotations:
                        for ann in capture_anns:
                            ann.set_visible(True)
             
                comp_fig.canvas.draw()
            elif event.key == 'a' or event.key == 'A':
                # Option pour afficher/masquer toutes les annotations
                visible = all_annotations[0][0].get_visible() if all_annotations and all_annotations[0] else False
                new_visibility = not visible
             
                for capture_anns in all_annotations:
                    for ann in capture_anns:
                        ann.set_visible(new_visibility)
             
                comp_ax.set_title(f"Comparaison Multi-Captures - Annotations {'masquées' if not new_visibility else 'affichées'}", 
                                fontsize=14, fontweight='bold')
                comp_fig.canvas.draw()
     
        # Connecter les événements de la souris et du clavier
        comp_fig.canvas.mpl_connect('button_press_event', on_press)
        comp_fig.canvas.mpl_connect('motion_notify_event', on_motion)
        comp_fig.canvas.mpl_connect('button_release_event', on_release)
        comp_fig.canvas.mpl_connect('scroll_event', on_scroll)
        comp_fig.canvas.mpl_connect('key_press_event', on_key)
     
        # Ajuster la légende pour éviter qu'elle ne recouvre les annotations
        comp_ax.legend(loc='upper left', fontsize=9, bbox_to_anchor=(0.02, 0.98))
     
        comp_fig.tight_layout(pad=3.0)
     
        comp_window = tk.Toplevel(self.app)
        comp_window.title("Comparaison Multi-Captures - Appuyez sur Z pour activer le zoom")
        comp_window.geometry("1100x750")
     
        # Instructions
        instructions_frame = tk.Frame(comp_window)
        instructions_frame.pack(fill="x", padx=10, pady=5)
     
        instructions = tk.Label(instructions_frame, 
                              text="🖱️ Zoom: DÉSACTIVÉ - Appuyez sur Z pour activer | R = Reset zoom | A = Toggle annotations",
                              font=("Segoe UI", 9), fg="#666666")
        instructions.pack()
     
        canvas = FigureCanvasTkAgg(comp_fig, master=comp_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=5)
     
        # Toolbar de navigation matplotlib
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        toolbar = NavigationToolbar2Tk(canvas, comp_window)
        toolbar.update()
        canvas.get_tk_widget().pack(fill="both", expand=True)
     
        save_frame = tk.Frame(comp_window)
        save_frame.pack(pady=10)
     
        # Bouton pour sauvegarder l'image
        ttk.Button(save_frame, text="💾 Sauvegarder l'image",
                  style="Secondary.TButton",
                  command=lambda: self._save_comparison_chart(comp_fig)).pack()
   
    def _save_comparison_chart(self, fig):
        """Sauvegarde le graphique de comparaison"""
        from tkinter import filedialog, messagebox
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Sauvegarder le graphique de comparaison"
        )
        
        if file_path:
            try:
                fig.savefig(file_path, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Succès", f"Graphique sauvegardé : {file_path}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur de sauvegarde : {str(e)}")
    
    def _generate_professional_report(self):
        """Génère un rapport PDF professionnel"""
        from tkinter import filedialog, messagebox
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        import tempfile
        import shutil
        import sys
        import subprocess
        import os
     
        if not self.app.capture_history:
            messagebox.showwarning("Attention", "Aucune capture disponible pour générer un rapport.")
            return
 
        dialog = tk.Toplevel(self.app)
        dialog.title("Génération de Rapport PDF")
        dialog.geometry("600x800")  # Augmenté pour accommoder les nouvelles options
        dialog.configure(bg=COLOR_FRAME_BG)
 
     # MODIFICATION : Titre changé pour sélection multiple
        tk.Label(dialog, text="Sélectionnez les captures pour le rapport:",
                font=("Segoe UI", 12, "bold"), 
                bg=COLOR_FRAME_BG,
                fg="white",  # ← AJOUTEZ CETTE LIGNE POUR LE TEXTE BLANC
                pady=10).pack()
 
        list_frame = tk.Frame(dialog, bg=COLOR_FRAME_BG)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
 
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
 
        # MODIFICATION : Listbox en mode sélection multiple
        listbox = tk.Listbox(list_frame, selectmode="multiple",
                            yscrollcommand=scrollbar.set,
                            font=("Segoe UI", 10))
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)
 
        for capture in self.app.capture_history:
            listbox.insert(tk.END, 
                         f"Capture #{capture['id']} - {capture['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} - {capture['particles_count']} particules")
 
        # MODIFICATION : Ajout des options de mode de génération
        mode_frame = tk.Frame(dialog, bg=COLOR_FRAME_BG)
        mode_frame.pack(fill="x", padx=20, pady=(15, 0))

        # Label en blanc
        tk.Label(mode_frame, text="Mode de génération:",
                bg=COLOR_FRAME_BG, 
                fg="white",  # ← Texte blanc
                font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))

        report_mode = tk.StringVar(value="separate")  # Valeur par défaut
 
        # Note sur les options (existante)
        note_frame = tk.Frame(dialog, bg=COLOR_FRAME_BG)
        note_frame.pack(fill="x", padx=20, pady=(10, 0))
 
        tk.Label(note_frame, 
                text="⚠️ Les options d'inclusion sont configurées dans Paramètres → Transmission",
                bg=COLOR_FRAME_BG, fg="#dc2626", font=("Segoe UI", 9, "italic"),
                wraplength=500).pack(anchor="w")
 
        # Logo
        logo_frame = tk.Frame(dialog, bg=COLOR_FRAME_BG)
        logo_frame.pack(fill="x", padx=20, pady=(15, 4))
 
        tk.Label(logo_frame, text="Logo du rapport:", 
                 bg=COLOR_FRAME_BG, 
                 fg="white",  # ← Blanc
         font=("Segoe UI", 10)).pack(anchor="w")
 
        logo_subframe = tk.Frame(logo_frame, bg=COLOR_FRAME_BG) 
        logo_subframe.pack(fill="x", pady=(5, 0))
  
        logo_path_var = tk.StringVar(value=self.app.report_logo_path) 
        logo_entry = ttk.Entry(logo_subframe, textvariable=logo_path_var, width=40) 
        logo_entry.pack(side="left", fill="x", expand=True)
 
        def browse_logo():
            file_path = filedialog.askopenfilename(
                title="Sélectionner le logo",
                filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")]
            )
            if file_path:
                logo_path_var.set(file_path)
 
        ttk.Button(logo_subframe, text="Parcourir",
                  style="Secondary.TButton",
                  command=browse_logo).pack(side="left", padx=5)
 
        # Commentaire
        comment_frame = tk.Frame(dialog, bg=COLOR_FRAME_BG)
        comment_frame.pack(fill="x", padx=20, pady=(15, 10))
 
        tk.Label(comment_frame, text="Commentaire (optionnel):",
                bg=COLOR_FRAME_BG, 
                fg="white",  # ← Blanc
                font=("Segoe UI", 10, "bold")).pack(anchor="w")
 
        comment_text = tk.Text(comment_frame, height=4, font=("Segoe UI", 10))
        comment_text.pack(fill="x", pady=(5, 0))
 
     # Pré-remplir avec la valeur existante
        if self.app.report_options["custom_comment"].get():
            comment_text.insert("1.0", self.app.report_options["custom_comment"].get())
 
        button_frame = tk.Frame(dialog, bg=COLOR_FRAME_BG)
        button_frame.pack(pady=10)
 
        def generate_report():
            selections = listbox.curselection()
            if not selections:
                messagebox.showwarning("Attention", "Veuillez sélectionner au moins une capture.")
                return
 
            selected_indices = list(selections)
            selected_captures = [self.app.capture_history[i] for i in selected_indices]
 
            self.app.report_logo_path = logo_path_var.get()
 
            comment = comment_text.get("1.0", tk.END).strip()
 
            # Utiliser les options définies dans Paramètres → Transmission
            include_options = {
                "include_captured_image": self.app.report_options["include_captured_image"].get(),
                "include_segmented_image": self.app.report_options["include_segmented_image"].get(),
                "include_granulometric_curve": self.app.report_options["include_granulometric_curve"].get(),
                "include_distribution_curve": self.app.report_options["include_distribution_curve"].get(),
                "include_statistics": self.app.report_options["include_statistics"].get()
            }
 
            # MODIFICATION : Logique selon le mode choisi
            mode = report_mode.get()
         
            if mode == "separate":
                # Générer des PDF séparés
                output_dir = filedialog.askdirectory(
                title="Sélectionnez le dossier pour enregistrer les rapports PDF"
            )

                if not output_dir:  # L'utilisateur a annulé
                    return
 
                success_count = 0
                total_count = len(selected_captures)
 
                for i, capture in enumerate(selected_captures):
                    try:
                        # Nom du fichier pour cette capture
                        filename = f"Rapport_Capture_{capture['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        file_path = os.path.join(output_dir, filename)
             
                        # Générer le PDF pour cette capture unique
                        self._create_single_capture_pdf_report(capture, include_options, comment, file_path)
                        success_count += 1
             
                        # Afficher une progression
                        dialog.title(f"Génération en cours... ({i+1}/{total_count})")
                        dialog.update()
              
                    except Exception as e:
                        print(f"Erreur lors de la génération du PDF pour la capture #{capture['id']}: {e}")
 
                dialog.destroy()
 
                # Message de confirmation
                if success_count == total_count:
                    messagebox.showinfo("Succès", 
                                      f"{success_count} rapport(s) PDF généré(s) avec succès dans :\n{output_dir}")
                elif success_count > 0:
                    messagebox.showwarning("Partiel", 
                                         f"{success_count} sur {total_count} rapport(s) PDF généré(s).\n"
                                         f"Dossier : {output_dir}")
                else:
                    messagebox.showerror("Échec", 
                                       "Aucun rapport PDF n'a pu être généré.")
         
            else:  # mode == "combined"
             # Générer un seul PDF combiné
            # Vérifier si la fonction existe
                if hasattr(self, '_create_multi_capture_pdf_report'):
                    self._create_multi_capture_pdf_report(selected_captures, include_options, comment)
                else:
                    # Fallback : utiliser la fonction pour une seule capture
                    if len(selected_captures) == 1:
                        file_path = filedialog.asksaveasfilename(
                            defaultextension=".pdf",
                            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                            title="Enregistrer le rapport PDF",
                            initialfile=f"Rapport_Capture_{selected_captures[0]['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        )
                        if file_path:
                            self._create_single_capture_pdf_report(selected_captures[0], include_options, comment, file_path)
                    else:
                        # Si plusieurs captures mais pas de fonction combinée, avertir
                        messagebox.showwarning("Option non disponible",
                                             "La génération de PDF combiné n'est pas disponible.\n"
                                             "Veuillez utiliser le mode 'PDF par capture'.")
                        return
             
                dialog.destroy()
 
        # MODIFICATION : Changement du texte du bouton
        ttk.Button(button_frame, text="Générer le(s) Rapport(s) PDF",
                  style="Start.TButton",
                  command=generate_report).pack(side="left", padx=5)
 
        ttk.Button(button_frame, text="Annuler",
                  style="Secondary.TButton",
                  command=dialog.destroy).pack(side="left", padx=5)
    def _create_single_capture_pdf_report(self, capture, include_options, custom_comment, file_path):
        """Crée un rapport PDF pour une seule capture"""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        import tempfile
        import shutil
        import os
        import cv2
        from reportlab.lib.units import inch
        import numpy as np
        import matplotlib.pyplot as plt
        from matplotlib.figure import Figure
    
        try:
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            styles = getSampleStyleSheet()
        
            # Styles personnalisés
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=24,
                textColor=colors.HexColor('#0D1321'),
                spaceBefore=30,
                spaceAfter=20
            )
        
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor('#F76F00'),
                spaceAfter=10
            )
         
            normal_style = styles['Normal']
            normal_style.fontSize = 10
            normal_style.leading = 12
         
            content = []
           
            # Logo
            if os.path.exists(self.app.report_logo_path):
                try:
                    logo_width = 3.25 * inch   
                    logo_height = 0.75 * inch 
                    logo_img = RLImage(self.app.report_logo_path, width=logo_width, height=logo_height)
                  
                    logo_table_data = [[logo_img]]
                    logo_table = Table(logo_table_data, colWidths=[8.27*inch])
                  
                    logo_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                        ('VALIGN', (0, 0), (0, 0), 'TOP'),
                        ('LEFTPADDING', (0, 0), (0, 0), 0),
                        ('TOPPADDING', (0, 0), (0, 0), -72),
                        ('BOTTOMPADDING', (0, 0), (0, 0), -72),
                    ]))
                
                    content.append(logo_table)
                    content.append(Spacer(1, 5))
                except Exception as e:
                    print(f"Erreur chargement logo: {e}")
        
            # Titre
            content.append(Paragraph("RAPPORT GRANULOMÉTRIQUE", title_style))
            content.append(Spacer(1, 10))
         
            # Informations de la capture
            content.append(Paragraph("INFORMATIONS DE LA CAPTURE", heading_style))
         
            info_data = [
                ["ID de capture:", f"#{capture['id']}"],
                ["Date et heure:", capture['timestamp'].strftime('%Y-%m-%d %H:%M:%S')],
                ["Nombre de particules:", str(capture['particles_count'])],
            ]
         
            info_table = Table(info_data, colWidths=[3*inch, 3*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
         
            content.append(info_table)
            content.append(Spacer(1, 20))
         
            # Statistiques
            if include_options.get("include_statistics", True):
                particles_data = capture.get('particles_data', [])
                minor_axes_mm = []
                major_axes_mm = []
 
                for particle in particles_data:
                    minor_mm = particle.get('minor_axis_mm', 0)
                    major_mm = particle.get('major_axis_mm', 0)
 
                    if isinstance(minor_mm, (int, float)) and minor_mm > 0.1:
                        minor_axes_mm.append(float(minor_mm))
 
                    if isinstance(major_mm, (int, float)) and major_mm > 0.1:
                        major_axes_mm.append(float(major_mm))
 
                mean_minor_mm = np.mean(minor_axes_mm) if minor_axes_mm else 0
                mean_major_mm = np.mean(major_axes_mm) if major_axes_mm else 0
 
                if minor_axes_mm:
                    stats = calculer_statistiques_granulometriques(particles_data, minor_axes_mm)
 
                    if stats:
                        content.append(Paragraph("STATISTIQUES GRANULOMÉTRIQUES", heading_style))
 
                        stats_data = [
                            ["Paramètre", "Valeur", "Unité"],
                            ["Nombre de particules", f"{stats.get('n_particules', 0)}", ""],
                            ["Minimum (Axe mineur)", f"{stats.get('min_mm_minor', 0):.2f}", "mm"],  
                            ["Maximum (Axe mineur)", f"{stats.get('max_mm_minor', 0):.2f}", "mm"],  
                            ["Minimum (Axe majeur)", f"{stats.get('min_mm_major', 0):.2f}", "mm"],  
                            ["Maximum (Axe majeur)", f"{stats.get('max_mm_major', 0):.2f}", "mm"],  
                            ["Moyenne (Axe mineur)", f"{mean_minor_mm:.2f}", "mm"],
                            ["Moyenne (Axe majeur)", f"{mean_major_mm:.2f}", "mm"],
                            ["D10 (10% plus fins)", f"{stats.get('D10_mm', 0):.2f}", "mm"],
                            ["D25 (25% plus fins)", f"{stats.get('D25_mm', 0):.2f}", "mm"],
                            ["D50 (Médiane)", f"{stats.get('D50_mm', 0):.2f}", "mm"],
                            ["D75 (75% plus fins)", f"{stats.get('D75_mm', 0):.2f}", "mm"],
                            ["D90 (90% plus fins)", f"{stats.get('D90_mm', 0):.2f}", "mm"]
                        ]
 
                        stats_table = Table(stats_data, colWidths=[2*inch, 1.5*inch, 1*inch])
                        stats_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0D1321')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 0), (-1, -1), 9),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.white)
                        ]))
 
                        content.append(stats_table)
                        content.append(Spacer(1, 20))

            temp_dir = tempfile.mkdtemp()
        
            try:
                # Image capturée
                if include_options.get("include_captured_image", True) and capture.get('image_processed') is not None:
                    try:
                        img_path = os.path.join(temp_dir, "captured_image.png")
                        cv2.imwrite(img_path, capture['image_processed'])
 
                        content.append(Paragraph("IMAGE CAPTURÉE", heading_style))
                        img = RLImage(img_path, width=6*inch, height=3*inch)
                        content.append(img)
                        content.append(Spacer(1, 20))
                    except Exception as e:
                        print(f"Erreur image capturée: {e}")
             
                # Image segmentée
                if include_options.get("include_segmented_image", True) and capture.get('segmented_image') is not None:
                    try:
                        img_path = os.path.join(temp_dir, "segmented_image.png")
                        cv2.imwrite(img_path, capture['segmented_image'])
 
                        content.append(Paragraph("IMAGE SEGMENTÉE", heading_style))
                        img = RLImage(img_path, width=6*inch, height=3*inch)
                        content.append(img)
                        content.append(Spacer(1, 20))
                    except Exception as e:
                        print(f"Erreur image segmentée: {e}")
             
                # Courbe granulométrique
                if include_options.get("include_granulometric_curve", True) and capture.get('tamis_exp'):
                    try:
                        fig = Figure(figsize=(10, 6))
                        ax = fig.add_subplot(111)
 
                        # Créer la courbe
                        diameters_vss = [0, 22.4, 31.5, 40, 50, 63, 100]
                        cumFraction_vss = [0, 4, 26, 70, 99, 99, 100]
                        diameters_vsi = [0, 22.4, 31.5, 40, 50, 50, 50]
                        cumFraction_vsi = [0, 0, 0, 25, 70, 70, 70]
 
                        ax.plot(diameters_vss, cumFraction_vss, 'g--', linewidth=1.5, label='VSS')
                        ax.plot(diameters_vsi, cumFraction_vsi, color='orange', linestyle='--', linewidth=2, alpha=0.7, label='VSI')
 
                        tamis = capture['tamis_exp']
                        cumul = capture['cumulative_raw']
 
                        if hasattr(self.app, 'show_corrected_curve_var') and self.app.show_corrected_curve_var.get() and capture.get('cumulative_corrected'):
                            cumul = capture['cumulative_corrected']
                            curve_label = 'Courbe corrigée'
                        else:
                            curve_label = 'Courbe brute'
 
                        ax.plot(tamis, cumul, 'b-o', linewidth=2, markersize=4, label=curve_label)
 
                        # Ajouter les annotations de pourcentage
                        for i, (x, y) in enumerate(zip(tamis, cumul)):
                            offset_direction = 5 if i % 2 == 0 else -15
                            vertical_alignment = 'bottom' if i % 2 == 0 else 'top'
 
                            ax.annotate(f'{y:.1f}%', 
                                      xy=(x, y), 
                                      xytext=(0, offset_direction),
                                      textcoords='offset points',
                                      ha='center', 
                                      va=vertical_alignment,
                                      fontsize=9, 
                                      fontweight='bold',
                                      color='blue',
                                      bbox=dict(boxstyle="round,pad=0.2", 
                                               facecolor="white", 
                                               edgecolor="lightblue", 
                                               alpha=0.8))
 
                        ax.set_xlabel("Taille du tamis (mm)", fontsize=10)
                        ax.set_ylabel("% passant cumulé", fontsize=10)
                        ax.set_title(f"Courbe Granulométrique - Capture #{capture['id']}", 
                                   fontsize=12, fontweight='bold')
                        ax.set_xticks([0, 22.4, 31.5, 40, 50, 63, 80])
                        ax.set_xticklabels(['0', '22.4', '31.5', '40', '50', '63', '80'], fontsize=9)
                        ax.set_yticks(np.arange(0, 101, 10))
                        ax.set_yticklabels([f'{int(y)}%' for y in np.arange(0, 101, 10)], fontsize=9)
                        ax.set_xlim([0, 85])
                        ax.set_ylim([0, 105])
                        ax.grid(True, alpha=0.3)
                        ax.legend(loc='upper left', fontsize=9)
 
                        fig.tight_layout(pad=3.0)
 
                        curve_path = os.path.join(temp_dir, "curve.png")
                        fig.savefig(curve_path, dpi=150, bbox_inches='tight')
                        plt.close(fig)
 
                        content.append(Paragraph("COURBE GRANULOMÉTRIQUE", heading_style))
                        curve_img = RLImage(curve_path, width=6*inch, height=4*inch)
                        content.append(curve_img)
                        content.append(Spacer(1, 20))
                    except Exception as e:
                        print(f"Erreur courbe granulométrique: {e}")
             
                # Distribution granulométrique
                if include_options.get("include_distribution_curve", True) and capture.get('minor_axes_mm'):
                    try:
                        fig = Figure(figsize=(10, 6))
                        ax = fig.add_subplot(111)
 
                        minor_axes_mm = [x for x in capture['minor_axes_mm'] if x > 0.1]
 
                        if minor_axes_mm:
                            bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 100]
                            bin_labels = ['<10', '10-20', '20-30', '30-40', '40-50', '50-60', '60-70', '70-80', '>80']
 
                            hist, bin_edges = np.histogram(minor_axes_mm, bins=bins)
   
                            colors_hist = plt.cm.viridis(np.linspace(0, 1, len(hist)))
                            bars = ax.bar(range(len(hist)), hist, color=colors_hist, edgecolor='black', alpha=0.8)
 
                            # Ajouter les valeurs sur les barres
                            for i, (bar, val) in enumerate(zip(bars, hist)):
                                height = bar.get_height()
                                if height > 0:
                                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                                           f'{val}', ha='center', va='bottom', fontsize=9,
                                           fontweight='bold',
                                           bbox=dict(boxstyle="round,pad=0.2", 
                                                    facecolor="white", 
                                                    edgecolor="black", 
                                                    alpha=0.7))
 
                            ax.set_xlabel("Taille (mm)", fontsize=10)
                            ax.set_ylabel("Nombre de particules", fontsize=10)
                            ax.set_title(f"Distribution Granulométrique - Capture #{capture['id']}", 
                                       fontsize=12, fontweight='bold')
                            ax.set_xticks(range(len(bin_labels)))
                            ax.set_xticklabels(bin_labels, rotation=45, fontsize=9)
                            ax.grid(True, alpha=0.3, linestyle='--', axis='y')
 
                            max_height = max(hist) if hist.size > 0 else 1
                            ax.set_ylim([0, max_height * 1.15])
 
                            fig.tight_layout(pad=3.0)
 
                            hist_path = os.path.join(temp_dir, "distribution.png")
                            fig.savefig(hist_path, dpi=150, bbox_inches='tight')
                            plt.close(fig)
 
                            content.append(Paragraph("DISTRIBUTION GRANULOMÉTRIQUE", heading_style))
                            hist_img = RLImage(hist_path, width=6*inch, height=4*inch)
                            content.append(hist_img)
                            content.append(Spacer(1, 20))
                    except Exception as e:
                        print(f"Erreur distribution granulométrique: {e}")
             
                # Commentaire personnalisé
                if custom_comment:
                    content.append(Paragraph("COMMENTAIRE", heading_style))
                    content.append(Paragraph(custom_comment, normal_style))
                    content.append(Spacer(1, 20))
             
                # Pied de page
                content.append(Spacer(1, 30))
                footer_style = ParagraphStyle(
                   'Footer',
                    parent=styles['Normal'],
                    fontSize=8,
                    textColor=colors.grey,
                    alignment=1  # Centré
                )
                content.append(Paragraph(f"Généré le {datetime.now().strftime('%Y-%m-%d à %H:%M:%S')}", footer_style))
             
                # Générer le PDF
                doc.build(content)
               
            except Exception as e:
                raise e
            finally:
                # Nettoyer le répertoire temporaire
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                 
        except Exception as e:
            raise e
    
    def _create_pdf_report_with_options(self, capture, include_options, custom_comment=""):
        """Crée un rapport PDF avec les options spécifiées"""
        from tkinter import filedialog, messagebox
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        import tempfile
        import shutil
        import sys
        import subprocess
        import os
        import cv2
        from reportlab.lib.units import inch
    
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Enregistrer le rapport PDF",
                initialfile=f"Rapport_Capture_{capture['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
         
            if not file_path:
                return
         
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            styles = getSampleStyleSheet()
        
            # Styles personnalisés
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=24,
                textColor=colors.HexColor('#0D1321'),
                spaceBefore=50,
                spaceAfter=40
            )
         
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor('#F76F00'),
                spaceAfter=10
            )
         
            normal_style = styles['Normal']
            normal_style.fontSize = 10
            normal_style.leading = 12
         
            content = []
         
            # Logo
            if os.path.exists(self.app.report_logo_path):  # CORRECTION: utiliser self.app
                try:
                    logo_width = 3.25 * inch   
                    logo_height = 0.75 * inch 
     
                    logo_img = RLImage(self.app.report_logo_path,  # CORRECTION: utiliser self.app
                              width=logo_width, 
                              height=logo_height)
     
                    logo_table_data = [[logo_img]]
                    logo_table = Table(logo_table_data, colWidths=[8.27*inch])
                 
                    logo_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                        ('VALIGN', (0, 0), (0, 0), 'TOP'),
                        ('LEFTPADDING', (0, 0), (0, 0), 0),
                        ('TOPPADDING', (0, 0), (0, 0), -72),
                        ('BOTTOMPADDING', (0, 0), (0, 0), -72),
                    ]))
     
                    content.append(logo_table)
                    content.append(Spacer(1, 5))
                except Exception as e:
                    print(f"Erreur chargement logo: {e}")
         
            # Titre
            content.append(Paragraph("RAPPORT GRANULOMÉTRIQUE", title_style))
            content.append(Spacer(1, 10))
         
            # Informations de la capture
            content.append(Paragraph("INFORMATIONS DE LA CAPTURE", heading_style))
         
            info_data = [
                ["ID de capture:", f"#{capture['id']}"],
                ["Date et heure:", capture['timestamp'].strftime('%Y-%m-%d %H:%M:%S')],
                ["Nombre de particules:", str(capture['particles_count'])],
            ]
         
            info_table = Table(info_data, colWidths=[3*inch, 3*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
         
            content.append(info_table)
            content.append(Spacer(1, 20))
         
            # Statistiques
            if include_options.get("include_statistics", True):
                # Calculer les statistiques pour cette capture
                particles_data = capture.get('particles_data', [])
 
                # Initialiser les listes correctement
                minor_axes_mm = []
                major_axes_mm = []
 
                for particle in particles_data:
                    minor_mm = particle.get('minor_axis_mm', 0)
                    major_mm = particle.get('major_axis_mm', 0)
         
                    # Filtrer les valeurs valides
                    if isinstance(minor_mm, (int, float)) and minor_mm > 0.1:
                        minor_axes_mm.append(float(minor_mm))
         
                    if isinstance(major_mm, (int, float)) and major_mm > 0.1:
                        major_axes_mm.append(float(major_mm))
 
                # Calculer les moyennes
                mean_minor_mm = 0
                mean_major_mm = 0
 
                if minor_axes_mm:  # Vérifier que la liste n'est pas vide
                    mean_minor_mm = np.mean(minor_axes_mm) if minor_axes_mm else 0
 
                if major_axes_mm:  # Vérifier que la liste n'est pas vide
                    mean_major_mm = np.mean(major_axes_mm) if major_axes_mm else 0
 
                if minor_axes_mm:  # S'il y a des données pour calculer les stats
                    stats = calculer_statistiques_granulometriques(particles_data, minor_axes_mm)
          
                    if stats:
                        content.append(Paragraph("STATISTIQUES GRANULOMÉTRIQUES", heading_style))
              
                        stats_data = [
                            ["Paramètre", "Valeur", "Unité"],
                            ["Nombre de particules", f"{stats.get('n_particules', 0)}", ""],
                            ["Minimum (Axe mineur)", f"{stats.get('min_mm_minor', 0):.2f}", "mm"],  
                            ["Maximum (Axe mineur)", f"{stats.get('max_mm_minor', 0):.2f}", "mm"],  
                            ["Minimum (Axe majeur)", f"{stats.get('min_mm_major', 0):.2f}", "mm"],  
                            ["Maximum (Axe majeur)", f"{stats.get('max_mm_major', 0):.2f}", "mm"],  
                            ["Moyenne (Axe mineur)", f"{mean_minor_mm:.2f}", "mm"],
                            ["Moyenne (Axe majeur)", f"{mean_major_mm:.2f}", "mm"],
                            ["D10 (10% plus fins)", f"{stats.get('D10_mm', 0):.2f}", "mm"],
                            ["D25 (25% plus fins)", f"{stats.get('D25_mm', 0):.2f}", "mm"],
                            ["D50 (Médiane)", f"{stats.get('D50_mm', 0):.2f}", "mm"],
                            ["D75 (75% plus fins)", f"{stats.get('D75_mm', 0):.2f}", "mm"],
                            ["D90 (90% plus fins)", f"{stats.get('D90_mm', 0):.2f}", "mm"]
                        ]
              
                        stats_table = Table(stats_data, colWidths=[2*inch, 1.5*inch, 1*inch])
                        stats_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0D1321')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 0), (-1, -1), 9),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.white)
                        ]))
            
                        content.append(stats_table)
                        content.append(Spacer(1, 20))
            
            temp_dir = tempfile.mkdtemp()
         
            try:
                # Image capturée
                if include_options.get("include_captured_image", True) and capture.get('image_processed') is not None:
                    try:
                        img_path = os.path.join(temp_dir, "captured_image.png")
                        cv2.imwrite(img_path, capture['image_processed'])
                    
                        content.append(Paragraph("IMAGE CAPTURÉE", heading_style))
                        img = RLImage(img_path, width=6*inch, height=3*inch)
                        content.append(img)
                        content.append(Spacer(1, 20))
                    except Exception as e:
                        print(f"Erreur image capturée: {e}")
             
                # Image segmentée
                if include_options.get("include_segmented_image", True) and capture.get('segmented_image') is not None:
                    try:
                        img_path = os.path.join(temp_dir, "segmented_image.png")
                        cv2.imwrite(img_path, capture['segmented_image'])
                     
                        content.append(Paragraph("IMAGE SEGMENTÉE", heading_style))
                        img = RLImage(img_path, width=6*inch, height=3*inch)
                        content.append(img)
                        content.append(Spacer(1, 20))
                    except Exception as e:
                        print(f"Erreur image segmentée: {e}")
             
                 # Courbe granulométrique
                if include_options.get("include_granulometric_curve", True) and capture.get('tamis_exp'):
                    try:
                        fig = Figure(figsize=(10, 6))
                        ax = fig.add_subplot(111)
                    
                        # Créer la courbe
                        diameters_vss = [0, 22.4, 31.5, 40, 50, 63, 100]
                        cumFraction_vss = [0, 4, 26, 70, 99, 99, 100]
                        diameters_vsi = [0, 22.4, 31.5, 40, 50, 50, 50]
                        cumFraction_vsi = [0, 0, 0, 25, 70, 70, 70]
                    
                        ax.plot(diameters_vss, cumFraction_vss, 'g--', linewidth=1.5, label='VSS')
                        ax.plot(diameters_vsi, cumFraction_vsi, color='orange', linestyle='--', linewidth=2, alpha=0.7, label='VSI')
                    
                        tamis = capture['tamis_exp']
                        cumul = capture['cumulative_raw']
                    
                        # CORRECTION: utiliser self.app.show_corrected_curve_var.get()
                        if hasattr(self.app, 'show_corrected_curve_var') and self.app.show_corrected_curve_var.get() and capture.get('cumulative_corrected'):
                            cumul = capture['cumulative_corrected']
                            curve_label = 'Courbe corrigée'
                        else:
                            curve_label = 'Courbe brute'
                     
                        ax.plot(tamis, cumul, 'b-o', linewidth=2, markersize=4, label=curve_label)
                     
                        # AJOUT : Ajouter les annotations de pourcentage
                        for i, (x, y) in enumerate(zip(tamis, cumul)):
                            # Déterminer la position de l'annotation (haut ou bas selon l'index)
                            offset_direction = 5 if i % 2 == 0 else -15
                            vertical_alignment = 'bottom' if i % 2 == 0 else 'top'
                         
                            # Créer l'annotation
                            ax.annotate(f'{y:.1f}%', 
                                      xy=(x, y), 
                                      xytext=(0, offset_direction),
                                      textcoords='offset points',
                                      ha='center', 
                                      va=vertical_alignment,
                                      fontsize=9, 
                                      fontweight='bold',
                                      color='blue',
                                      bbox=dict(boxstyle="round,pad=0.2", 
                                               facecolor="white", 
                                               edgecolor="lightblue", 
                                               alpha=0.8))
                     
                        ax.set_xlabel("Taille du tamis (mm)", fontsize=10)
                        ax.set_ylabel("% passant cumulé", fontsize=10)
                        ax.set_title(f"Courbe Granulométrique - Capture #{capture['id']}", 
                                   fontsize=12, fontweight='bold')
                        ax.set_xticks([0, 22.4, 31.5, 40, 50, 63, 80])
                        ax.set_xticklabels(['0', '22.4', '31.5', '40', '50', '63', '80'], fontsize=9)
                        ax.set_yticks(np.arange(0, 101, 10))
                        ax.set_yticklabels([f'{int(y)}%' for y in np.arange(0, 101, 10)], fontsize=9)
                        ax.set_xlim([0, 85])
                        ax.set_ylim([0, 105])
                        ax.grid(True, alpha=0.3)
                        ax.legend(loc='upper left', fontsize=9)
                     
                        fig.tight_layout(pad=3.0)
                     
                        curve_path = os.path.join(temp_dir, "curve.png")
                        fig.savefig(curve_path, dpi=150, bbox_inches='tight')
                        plt.close(fig)
                     
                        content.append(Paragraph("COURBE GRANULOMÉTRIQUE", heading_style))
                        curve_img = RLImage(curve_path, width=6*inch, height=4*inch)
                        content.append(curve_img)
                        content.append(Spacer(1, 20))
                    except Exception as e:
                        print(f"Erreur courbe granulométrique: {e}")
             
                # Distribution granulométrique
                if include_options.get("include_distribution_curve", True) and capture.get('minor_axes_mm'):
                    try:
                        fig = Figure(figsize=(10, 6))
                        ax = fig.add_subplot(111)
        
                        minor_axes_mm = [x for x in capture['minor_axes_mm'] if x > 0.1]
        
                        if minor_axes_mm:
                            bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 100]
                            bin_labels = ['<10', '10-20', '20-30', '30-40', '40-50', '50-60', '60-70', '70-80', '>80']
            
                            hist, bin_edges = np.histogram(minor_axes_mm, bins=bins)
            
                            colors_hist = plt.cm.viridis(np.linspace(0, 1, len(hist)))
                            bars = ax.bar(range(len(hist)), hist, color=colors_hist, edgecolor='black', alpha=0.8)
             
                             # AJOUT : Ajouter les valeurs sur les barres
                            for i, (bar, val) in enumerate(zip(bars, hist)):
                                height = bar.get_height()
                                if height > 0:  # N'afficher que si la valeur est > 0
                                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                                           f'{val}', ha='center', va='bottom', fontsize=9,
                                           fontweight='bold',
                                           bbox=dict(boxstyle="round,pad=0.2", 
                                                    facecolor="white", 
                                                    edgecolor="black", 
                                                    alpha=0.7))
             
                            ax.set_xlabel("Taille (mm)", fontsize=10)
                            ax.set_ylabel("Nombre de particules", fontsize=10)
                            ax.set_title(f"Distribution Granulométrique - Capture #{capture['id']}", 
                                        fontsize=12, fontweight='bold')
                            ax.set_xticks(range(len(bin_labels)))
                            ax.set_xticklabels(bin_labels, rotation=45, fontsize=9)
                            ax.grid(True, alpha=0.3, linestyle='--', axis='y')
              
                            # Ajuster l'échelle Y pour laisser de l'espace pour les annotations
                            max_height = max(hist) if hist.size > 0 else 1
                            ax.set_ylim([0, max_height * 1.15])
               
                            fig.tight_layout(pad=3.0)
             
                            hist_path = os.path.join(temp_dir, "distribution.png")
                            fig.savefig(hist_path, dpi=150, bbox_inches='tight')
                            plt.close(fig)
               
                            content.append(Paragraph("DISTRIBUTION GRANULOMÉTRIQUE", heading_style))
                            hist_img = RLImage(hist_path, width=6*inch, height=4*inch)
                            content.append(hist_img)
                            content.append(Spacer(1, 20))
                    except Exception as e:
                        print(f"Erreur distribution granulométrique: {e}")
             
                # Commentaire personnalisé
                if custom_comment:
                    content.append(Paragraph("COMMENTAIRE", heading_style))
                    content.append(Paragraph(custom_comment, normal_style))
                    content.append(Spacer(1, 20))
             
                # Pied de page
                content.append(Spacer(1, 30))
                footer_style = ParagraphStyle(
                    'Footer',
                    parent=styles['Normal'],
                    fontSize=8,
                    textColor=colors.grey,
                    alignment=1  # Centré
                )
                content.append(Paragraph(f"Généré le {datetime.now().strftime('%Y-%m-%d à %H:%M:%S')}", footer_style))
               
                # Générer le PDF
                doc.build(content)
             
                messagebox.showinfo("Succès", f"Rapport PDF généré avec succès:\n{file_path}")
             
                # Ouvrir le PDF
                if sys.platform == "win32":
                    os.startfile(file_path)
                elif sys.platform == "darwin":
                    subprocess.run(["open", file_path])
                else:
                    subprocess.run(["xdg-open", file_path])
                 
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la génération du PDF:\n{str(e)}")
                raise e
            finally:
                # Nettoyer le répertoire temporaire
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la création du PDF:\n{str(e)}")
  
    def _update_curve_view(self):
        """Met à jour l'affichage de la courbe en fonction de la capture actuelle"""
        if not self.app.capture_history or self.app.current_capture_index < 0:
            self._update_curve_view_for_capture(None)
            return
        
        current_capture = self.app.capture_history[self.app.current_capture_index]
        if current_capture:
            self._update_curve_view_for_capture(current_capture['id'])
            self._update_histogram_for_capture(current_capture['id'])
            self._update_capture_history_display()
            self._update_capture_info()
            self._update_particles_table()
            self.update_statistics_display(current_capture)
        