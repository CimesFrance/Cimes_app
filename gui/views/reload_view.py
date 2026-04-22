# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np
import pandas as pd
import os
import threading
from scipy import interpolate
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

from gui.widgets.utils import (
    COLOR_FRAME_BG, COLOR_CARD_BG, COLOR_ACCENT,
    COLOR_STAT_GOOD, COLOR_STAT_WARN, COLOR_STAT_BAD
)
from core.segmentation import segment_and_analyze
from core.granulometry import calculate_granulometric_curve_with_dna
from core.calibration import undistort_img, homo_and_pixel_conversion

class ReloadView:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent, bg=COLOR_FRAME_BG)
        
        # Variables pour le rechargement
        self.loaded_image_path = None
        self.loaded_image_data = None
        self.reload_image_preview = None
        self.current_reload_capture = None
        
        # Variables pour les courbes CSV
        self.csv_curves = []  # Liste des courbes CSV chargées
        self.csv_curve_names = []  # Noms des courbes CSV
        
        # Variables pour l'image segmentée
        self.segmented_tk_img = None
        
        self._build_ui()
    
    def _build_ui(self):
        """Construit l'interface de la vue Recharger"""
        self.frame.columnconfigure(0, weight=0, minsize=300)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=1)
    
        # Panneau latéral gauche
        sidebar = ttk.Frame(self.frame, style="Card.TFrame", width=300)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        sidebar.pack_propagate(False)
    
        # Titre
        tk.Label(sidebar, text="Analyse d'Images Existantes", bg="#e5e7eb",
                 anchor="w", font=("Segoe UI", 12, "bold"), padx=10, pady=10).pack(fill="x")
    
        # Zone de contenu
        content = tk.Frame(sidebar, bg=COLOR_CARD_BG, padx=15, pady=15)
        content.pack(fill="both", expand=True)
    
        # Bouton pour parcourir les images
        tk.Label(content, text="Analyse d'image :", bg=COLOR_CARD_BG,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
    
        browse_img_btn = ttk.Button(content, text="📁 Parcourir image...",
                                    style="Secondary.TButton",
                                    command=self._browse_and_analyze_image)
        browse_img_btn.pack(fill="x", pady=(0, 10))
    
        # Chemin sélectionné pour l'image
        self.selected_path_label = tk.Label(content, text="Aucune image sélectionnée",
                                           bg=COLOR_CARD_BG, fg="#6b7280",
                                           font=("Segoe UI", 9), wraplength=250)
        self.selected_path_label.pack(fill="x", pady=(0, 20))
    
        # Bouton Analyser
        self.analyze_btn = ttk.Button(content, text="🔬 Analyser l'image",
                                     style="Secondary.TButton",
                                     state="disabled",
                                     command=self._analyze_loaded_image)
        self.analyze_btn.pack(fill="x", pady=(10, 0))
        
        # Séparateur
        ttk.Separator(content, orient='horizontal').pack(fill='x', pady=20)
        
        # Section pour charger les courbes CSV
        tk.Label(content, text="Courbes de tamisage CSV :", bg=COLOR_CARD_BG,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        # Bouton pour charger un CSV
        browse_csv_btn = ttk.Button(content, text="📊 Charger courbe CSV...",
                                   style="Secondary.TButton",
                                   command=self._load_csv_curve)
        browse_csv_btn.pack(fill="x", pady=(0, 10))
        
        # Bouton pour supprimer toutes les courbes CSV
        clear_csv_btn = ttk.Button(content, text="🗑️ Supprimer toutes les courbes",
                                  style="Secondary.TButton",
                                  command=self._clear_all_csv_curves)
        clear_csv_btn.pack(fill="x", pady=(0, 10))
        
        # Frame pour afficher les courbes CSV chargées
        self.csv_curves_frame = tk.Frame(content, bg=COLOR_CARD_BG)
        self.csv_curves_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # Label pour l'état des courbes CSV
        self.csv_status_label = tk.Label(self.csv_curves_frame, 
                                        text="Aucune courbe CSV chargée",
                                        bg=COLOR_CARD_BG, fg="#6b7280",
                                        font=("Segoe UI", 9))
        self.csv_status_label.pack(anchor="w")
        
        # Liste des courbes CSV (scrollable)
        csv_list_frame = tk.Frame(self.csv_curves_frame, bg=COLOR_CARD_BG)
        csv_list_frame.pack(fill="both", expand=True, pady=(5, 0))
        
        # Canvas avec scrollbar pour la liste des courbes
        csv_canvas = tk.Canvas(csv_list_frame, bg=COLOR_CARD_BG, 
                              highlightthickness=0, height=150)
        scrollbar = ttk.Scrollbar(csv_list_frame, orient="vertical", 
                                 command=csv_canvas.yview)
        self.csv_list_container = tk.Frame(csv_canvas, bg=COLOR_CARD_BG)
        
        csv_canvas.create_window((0, 0), window=self.csv_list_container, anchor="nw")
        csv_canvas.configure(yscrollcommand=scrollbar.set)
        
        csv_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Configurer le scroll
        self.csv_list_container.bind("<Configure>", 
            lambda e: csv_canvas.configure(scrollregion=csv_canvas.bbox("all")))
        
        # Ajouter une info sur le format CSV
        info_text = """Format CSV attendu :
- Colonne 1 : Diamètres (mm)
- Colonne 2 : % Passant cumulé
- En-têtes facultatives"""
        
        info_label = tk.Label(content, text=info_text,
                             bg=COLOR_CARD_BG, fg="#6b7280",
                             font=("Segoe UI", 8), justify="left",
                             wraplength=250)
        info_label.pack(anchor="w", pady=(10, 0))
    
        # Zone d'affichage des résultats (droite)
        results_area = tk.Frame(self.frame, bg=COLOR_FRAME_BG)
        results_area.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        results_area.columnconfigure(0, weight=1)
        results_area.rowconfigure(0, weight=1)
    
        # Notebook pour les résultats
        self.reload_notebook = ttk.Notebook(results_area)
        self.reload_notebook.grid(row=0, column=0, sticky="nsew")
    
        # Onglet : Image Segmentée
        self.segmented_image_tab = ttk.Frame(self.reload_notebook)
        self.reload_notebook.add(self.segmented_image_tab, text="Image Segmentée")
        
        # Container pour l'image segmentée
        self.segmented_image_container = tk.Frame(self.segmented_image_tab, bg=COLOR_CARD_BG)
        self.segmented_image_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Label pour l'image segmentée
        self.segmented_label = tk.Label(self.segmented_image_container, 
                                       text="Aucune image segmentée disponible",
                                       bg=COLOR_CARD_BG, fg="#666",
                                       font=("Segoe UI", 12))
        self.segmented_label.pack(expand=True)
        
        # Onglet : Courbe Granulométrique
        self.reload_curve_tab = ttk.Frame(self.reload_notebook)
        self.reload_notebook.add(self.reload_curve_tab, text="Courbe Granulométrique")
        
        # Container pour la courbe
        self.reload_curve_frame = tk.Frame(self.reload_curve_tab, bg=COLOR_CARD_BG)
        self.reload_curve_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Label pour la courbe
        self.curve_label = tk.Label(self.reload_curve_frame, 
                                   text="Aucune courbe disponible",
                                   bg=COLOR_CARD_BG, fg="#666",
                                   font=("Segoe UI", 12))
        self.curve_label.pack(expand=True)
        
        # Panneau gauche pour l'aperçu de l'image (à créer)
        self.reload_left_panel = tk.Frame(sidebar, bg=COLOR_CARD_BG, width=300)
        self.reload_left_panel.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _browse_and_analyze_image(self):
        """Ouvre une boîte de dialogue pour sélectionner une image"""
        file_path = filedialog.askopenfilename(
            parent=self.frame,
            title="Sélectionner une image à analyser",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.bmp *.tiff"),
                ("Tous les fichiers", "*.*")
            ]
        )
        
        if file_path:
            self.loaded_image_path = file_path
            # Afficher le chemin raccourci
            display_path = file_path
            if len(display_path) > 40:
                display_path = "..." + display_path[-40:]
            self.selected_path_label.config(text=display_path)
            self.analyze_btn.config(state="normal")
            
            # Afficher un aperçu de l'image
            self._display_image_preview(file_path)
    
    def _display_image_preview(self, image_path):
        """Affiche un aperçu de l'image sélectionnée"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("Impossible de lire l'image")
        
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
        
            # Nettoyer les onglets
            self._clear_segmented_tab()
            self._clear_curve_tab()
            
            # Afficher le message dans l'onglet segmenté
            self.segmented_label.config(text="Image chargée - Cliquez sur 'Analyser' pour la segmentation")
        
            # Afficher un aperçu dans le panneau gauche
            self._display_thumbnail_in_sidebar(pil_image, image_path, image.shape)
        
            # Stocker l'image originale
            self.loaded_image_data = image
        
        except Exception as e:
            self._display_error_in_sidebar(f"Erreur de chargement:\n{str(e)}")
    
    def _display_thumbnail_in_sidebar(self, pil_image, image_path, image_shape):
        """Affiche la vignette dans la barre latérale"""
        for widget in self.reload_left_panel.winfo_children():
            widget.destroy()
    
        # Créer un cadre pour l'image
        img_frame = tk.Frame(self.reload_left_panel, bg=COLOR_CARD_BG)
        img_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
        # Ajouter un titre
        tk.Label(img_frame, text="Aperçu de l'image", 
                 bg=COLOR_CARD_BG, font=("Segoe UI", 11, "bold")).pack(pady=(0, 10))
    
        # Redimensionner pour l'aperçu
        max_width = 280
        max_height = 200
        ratio = min(max_width / pil_image.width, max_height / pil_image.height)
        new_width = int(pil_image.width * ratio)
        new_height = int(pil_image.height * ratio)
    
        resized_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        tk_image = ImageTk.PhotoImage(resized_image)
    
        # Stocker la référence
        self.reload_image_preview = tk_image
        img_label = tk.Label(img_frame, image=tk_image, bg=COLOR_CARD_BG)
        img_label.pack()
        img_label.image = tk_image
    
        # Informations sous l'image
        info_frame = tk.Frame(img_frame, bg=COLOR_CARD_BG)
        info_frame.pack(fill="x", pady=(10, 0))
    
        file_name = os.path.basename(image_path)
        if len(file_name) > 25:
            file_name = file_name[:22] + "..."
    
        tk.Label(info_frame, text=f"Fichier: {file_name}", 
                 bg=COLOR_CARD_BG, font=("Segoe UI", 9)).pack()
    
        dimensions = f"{image_shape[1]}×{image_shape[0]} px"
        tk.Label(info_frame, text=f"Taille: {dimensions}", 
                 bg=COLOR_CARD_BG, font=("Segoe UI", 9)).pack()
    
    def _display_error_in_sidebar(self, error_message):
        """Affiche un message d'erreur dans la barre latérale"""
        for widget in self.reload_left_panel.winfo_children():
            widget.destroy()
    
        error_label = tk.Label(self.reload_left_panel, 
                              text=error_message,
                              bg=COLOR_CARD_BG, fg=COLOR_STAT_BAD,
                              font=("Segoe UI", 10))
        error_label.pack(expand=True)
    
    def _clear_segmented_tab(self):
        """Efface le contenu de l'onglet image segmentée"""
        for widget in self.segmented_image_container.winfo_children():
            widget.destroy()
        
        self.segmented_label = tk.Label(self.segmented_image_container, 
                                       text="Aucune image segmentée disponible",
                                       bg=COLOR_CARD_BG, fg="#666",
                                       font=("Segoe UI", 12))
        self.segmented_label.pack(expand=True)
    
    def _clear_curve_tab(self):
        """Efface le contenu de l'onglet courbe"""
        for widget in self.reload_curve_frame.winfo_children():
            widget.destroy()
        
        self.curve_label = tk.Label(self.reload_curve_frame, 
                                   text="Aucune courbe disponible",
                                   bg=COLOR_CARD_BG, fg="#666",
                                   font=("Segoe UI", 12))
        self.curve_label.pack(expand=True)
    
    def _analyze_loaded_image(self):
        """Analyse l'image chargée"""
        if not self.loaded_image_path or self.loaded_image_data is None:
            messagebox.showwarning("Attention", "Veuillez d'abord sélectionner une image.")
            return
        
        try:
            scale = float(self.app.scale_var.get().replace(",", "."))
            
            self.analyze_btn.config(state="disabled", text="Analyse en cours...")
            
            threading.Thread(target=self._process_loaded_image,
                           args=(self.loaded_image_data.copy(), scale)).start()
            
        except ValueError:
            messagebox.showerror("Erreur", "Échelle invalide. Vérifiez les paramètres.")
            self.analyze_btn.config(state="normal", text="🔬 Analyser l'image")
    
    def _process_loaded_image(self, image, scale):
        """Traite l'image chargée en arrière-plan"""
        try:
            processed_frame = image.copy()
            
            # if self.app.use_undistortion_var.get() and self.app.mtx is not None and self.app.dist is not None:
            #     processed_frame = undistort_img(self.app.dist, self.app.mtx, processed_frame)
            
            # if self.app.use_homography_var.get() and self.app.homo_matrix is not None:
            #     processed_frame = homo_and_pixel_conversion(processed_frame, self.app.homo_matrix)
            
            # Appeler la fonction d'analyse (MÊME FONCTION QUE DANS MeasureView)
            masks, segmented_img, particles_data, _, L_min_axis, L_max_axis = segment_and_analyze(
                processed_frame, 1
            )
            L_min_axis = [(elt * float(self.app.facteur_conversion.get())) for elt in L_min_axis]
            # Calculer la courbe granulométrique
            tamis_exp, cumulative_raw, cumulative_corrected, minor_axes_mm = calculate_granulometric_curve_with_dna(
                particles_data, L_min_axis, self.app.correction_granulo['scale'].get() , self.app.correction_granulo['offset'].get() , scale
            )
            
            # Préparer les données
            capture_data = {
                'timestamp': datetime.now(),
                'image_raw': image,
                'image_processed': processed_frame,
                'segmented_image': segmented_img,
                'masks': masks,
                'particles_data': particles_data,
                'L_min_axis': L_min_axis,
                'L_max_axis': L_max_axis,
                'L_min_axis_mm': (np.array(L_min_axis) * scale).tolist() if L_min_axis else [],
                'L_max_axis_mm': (np.array(L_max_axis) * scale).tolist() if L_max_axis else [],
                'tamis_exp': tamis_exp,
                'cumulative_raw': cumulative_raw,
                'cumulative_corrected': cumulative_corrected,
                'minor_axes_mm': minor_axes_mm,
                'particles_count': len(particles_data),
                'scale': scale,
                'source': 'loaded'
            }
            
            # Mettre à jour l'interface
            self.app.after(0, lambda: self._display_loaded_results(capture_data))
            
        except Exception as e:
            error_msg = f"Erreur d'analyse: {str(e)}"
            self.app.after(0, lambda: self._display_loaded_error(error_msg))
            import traceback
            traceback.print_exc()
    
    def _display_loaded_results(self, capture_data):
        """Affiche les résultats de l'analyse"""
        self.analyze_btn.config(state="normal", text="🔬 Analyser l'image")
    
        self.current_reload_capture = capture_data
    
        # Afficher l'image segmentée
        self._display_segmented_image(capture_data['segmented_image'])
        
        # Afficher la courbe granulométrique
        self._show_loaded_curve(capture_data)
    
        messagebox.showinfo("Analyse terminée", 
                           f"L'analyse est terminée.\n"
                           f"{capture_data['particles_count']} particules détectées.")
    
    def _display_segmented_image(self, segmented_img):
        """Affiche l'image segmentée dans l'onglet correspondant"""
        if segmented_img is None:
            self.segmented_label.config(text="Segmentation non disponible")
            return
        
        try:
            # Effacer le contenu précédent
            for widget in self.segmented_image_container.winfo_children():
                widget.destroy()
            
            # Convertir l'image pour l'affichage
            if segmented_img.ndim == 3 and segmented_img.shape[2] == 3:
                cv2image = cv2.cvtColor(segmented_img, cv2.COLOR_BGR2RGB)
            elif segmented_img.ndim == 3:
                cv2image = segmented_img
            else:
                cv2image = cv2.cvtColor(segmented_img, cv2.COLOR_GRAY2RGB)
            
            pil_img = Image.fromarray(cv2image)
            
            # Créer un canvas avec scrollbars pour l'image
            canvas_frame = tk.Frame(self.segmented_image_container, bg=COLOR_CARD_BG)
            canvas_frame.pack(fill="both", expand=True)
            
            # Canvas pour l'image
            canvas = tk.Canvas(canvas_frame, bg=COLOR_CARD_BG, highlightthickness=0)
            
            # Scrollbars
            h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
            v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
            
            canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
            
            # Placement des widgets
            canvas.grid(row=0, column=0, sticky="nsew")
            v_scrollbar.grid(row=0, column=1, sticky="ns")
            h_scrollbar.grid(row=1, column=0, sticky="ew")
            
            canvas_frame.grid_rowconfigure(0, weight=1)
            canvas_frame.grid_columnconfigure(0, weight=1)
            
            # Convertir en PhotoImage
            self.segmented_tk_img = ImageTk.PhotoImage(pil_img)
            
            # Ajouter l'image au canvas
            canvas.create_image(0, 0, anchor="nw", image=self.segmented_tk_img)
            canvas.image = self.segmented_tk_img
            
            # Configurer la région de défilement
            canvas.config(scrollregion=canvas.bbox("all"))
            
            # Activer le zoom avec la molette de la souris
            def on_mouse_wheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
            canvas.bind_all("<MouseWheel>", on_mouse_wheel)
            
        except Exception as e:
            error_label = tk.Label(self.segmented_image_container, 
                                  text=f"Erreur d'affichage:\n{str(e)}",
                                  bg=COLOR_CARD_BG, fg=COLOR_STAT_BAD,
                                  font=("Segoe UI", 10))
            error_label.pack(expand=True)
    
    def _show_loaded_curve(self, capture_data):
        """Affiche la courbe granulométrique avec les courbes CSV si disponibles"""
        for widget in self.reload_curve_frame.winfo_children():
            widget.destroy()

        if not capture_data.get('tamis_exp') or not capture_data.get('cumulative_raw'):
            tk.Label(self.reload_curve_frame, 
                     text="Aucune donnée granulométrique disponible",
                     bg=COLOR_CARD_BG, fg="#666", font=("Segoe UI", 12)).pack(expand=True)
            return

        try:
            fig = Figure(figsize=(18, 9), dpi=100, facecolor='#f5f5f5')
            ax = fig.add_subplot(111, facecolor='white')
        
            # Courbes de référence
            diameters_vss = [0, 22.4, 31.5, 40, 50, 63, 100]
            cumFraction_vss = [0, 4, 26, 70, 99, 99, 100]
            diameters_vsi = [0, 22.4, 31.5, 40, 50, 50, 50]
            cumFraction_vsi = [0, 0, 0, 25, 70, 70, 70]
        
            ax.plot(diameters_vss, cumFraction_vss, 'g--', linewidth=2, alpha=0.7, label='VSS')
            ax.plot(diameters_vsi, cumFraction_vsi, color='orange', linestyle='--', linewidth=2, alpha=0.7, label='VSI')
        
            # Récupérer les données
            tamis_num = capture_data['tamis_exp']
            cumul_num = capture_data['cumulative_raw']
            cumulative_corrected = capture_data['cumulative_corrected']
        
            # Afficher la courbe numérique
            ax.plot(tamis_num, cumul_num, 'b-o', linewidth=2, markersize=6, 
                    label='Courbe numérique', zorder=5)
            
            # Afficher la courbe numérique corrigée
            ax.plot(tamis_num, cumulative_corrected, 'o-', color='brown', linewidth=2, markersize=6, 
                    label='Courbe numérique corrigée', zorder=5)

            # Ajouter les courbes CSV si disponibles
            colors = ['red', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
            for idx, (csv_data, curve_name) in enumerate(zip(self.csv_curves, self.csv_curve_names)):
                if len(csv_data) >= 2:
                    color_idx = idx % len(colors)
                    ax.plot(csv_data[:, 0], csv_data[:, 1], 
                           color=colors[color_idx], 
                           linestyle='-', 
                           linewidth=2, 
                           marker='s', 
                           markersize=4,
                           alpha=0.8,
                           label=f'CSV: {curve_name}')
        
            # Configuration des axes
            ax.set_xlabel("Taille du tamis (mm)", fontsize=12, fontweight='bold')
            ax.set_ylabel("% passant cumulé", fontsize=12, fontweight='bold')
            ax.set_title("Courbe Granulométrique", fontsize=14, fontweight='bold')
        
            # Ajuster les limites
            max_tamis = 80
            if tamis_num:
                max_tamis = max(max(tamis_num), 80)
            
            # Vérifier aussi les courbes CSV pour les limites
            for csv_data in self.csv_curves:
                if len(csv_data) >= 2 and len(csv_data[:, 0]) > 0:
                    csv_max = max(csv_data[:, 0])
                    if csv_max > max_tamis:
                        max_tamis = csv_max
            
            ax.set_xlim([0, max_tamis + 10])
            ax.set_ylim([0, 105])
            ax.set_yticks(np.arange(0, 101, 10))
        
            # Ajouter une grille
            ax.grid(True, alpha=0.3, linestyle='--')
        
            # Légende
            ax.legend(loc='upper left', fontsize=10)
        
            fig.tight_layout()

            # Intégrer dans tkinter
            canvas = FigureCanvasTkAgg(fig, master=self.reload_curve_frame)
            canvas.draw()
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(fill="both", expand=True)

            # Bouton d'export
            export_frame = tk.Frame(self.reload_curve_frame, bg=COLOR_CARD_BG)
            export_frame.pack(fill="x", pady=(10, 0))

            ttk.Button(export_frame, text="💾 Sauvegarder cette courbe",
                      style="Secondary.TButton",
                      command=lambda: self._save_reload_curve(fig)).pack(side="left")
            
            # Bouton pour exporter les données
            ttk.Button(export_frame, text="📊 Exporter toutes les données",
                      style="Secondary.TButton",
                      command=lambda: self._export_all_curves_data(capture_data)).pack(side="left", padx=(10, 0))

        except Exception as e:
            tk.Label(self.reload_curve_frame, 
                     text=f"Erreur lors de l'affichage de la courbe:\n{str(e)}",
                     bg=COLOR_CARD_BG, fg=COLOR_STAT_BAD, font=("Segoe UI", 10)).pack(expand=True)
            print(f"Erreur affichage courbe: {e}")
    
    def _display_loaded_error(self, error_msg):
        """Affiche une erreur dans les onglets"""
        self.analyze_btn.config(state="normal", text="🔬 Analyser l'image")
    
        # Afficher l'erreur dans l'onglet image segmentée
        self._clear_segmented_tab()
        self.segmented_label.config(text=f"❌ Erreur d'analyse\n{error_msg}")
        
        # Afficher l'erreur dans l'onglet courbe
        self._clear_curve_tab()
        self.curve_label.config(text=f"❌ Erreur d'analyse\n{error_msg}")
    
    def _save_reload_curve(self, fig):
        """Sauvegarde la courbe"""
        file_path = filedialog.asksaveasfilename(
            parent=self.frame,
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("PDF files", "*.pdf"),
                ("All files", "*.*")
            ],
            title="Sauvegarder la courbe granulométrique"
        )
    
        if file_path:
            try:
                fig.savefig(file_path, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Succès", f"Courbe sauvegardée : {file_path}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur de sauvegarde : {str(e)}")
    
    def _load_csv_curve(self):
        """Charge une courbe de tamisage depuis un fichier CSV (format flexible)"""
        file_path = filedialog.askopenfilename(
            parent=self.frame,
            title="Sélectionner un fichier de courbe granulométrique",
            filetypes=[
                ("Fichiers Excel", "*.xlsx *.xls"),
                ("Fichiers CSV", "*.csv"),
                ("Fichiers texte", "*.txt"),
                ("Tous les fichiers", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            # Détecter le type de fichier
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext in ['.xlsx', '.xls']:
                # Lire fichier Excel
                df = pd.read_excel(file_path, decimal=',')
            else:
                # Lire fichier CSV/texte - essayer différents formats
                try:
                    # Format européen : point-virgule comme séparateur, virgule comme décimal
                    df = pd.read_csv(file_path, sep=';', decimal=',', encoding='utf-8')
                except:
                    try:
                        # Format standard : virgule comme séparateur, point comme décimal
                        df = pd.read_csv(file_path, sep=',', decimal='.', encoding='utf-8')
                    except:
                        # Dernier essai : détection automatique
                        df = pd.read_csv(file_path, encoding='utf-8')
            
            if df.empty:
                messagebox.showerror("Erreur", "Le fichier est vide ou ne contient pas de données.")
                return
            
            # Chercher les colonnes pertinentes
            diameter_col = None
            cumulative_col = None
            
            # Noms possibles pour les colonnes (en minuscules pour comparaison insensible à la casse)
            column_names = [str(col).lower().strip() for col in df.columns]
            
            # Chercher la colonne des diamètres
            diameter_keywords = ['diamètre', 'diametre', 'diameter', 'tamis', 'size', 'mm', 'granulo']
            for idx, col_name in enumerate(column_names):
                if any(keyword in col_name for keyword in diameter_keywords):
                    diameter_col = df.columns[idx]
                    break
            
            # Chercher la colonne des pourcentages cumulés
            cumulative_keywords = ['cumulatif', 'cumulative', 'passant', 'pourcentage', '%', 'cumul']
            for idx, col_name in enumerate(column_names):
                if any(keyword in col_name for keyword in cumulative_keywords):
                    cumulative_col = df.columns[idx]
                    break
            
            # Si non trouvé, utiliser la première et deuxième colonne
            if diameter_col is None:
                if len(df.columns) >= 1:
                    diameter_col = df.columns[0]
            
            if cumulative_col is None:
                if len(df.columns) >= 2:
                    cumulative_col = df.columns[1]
            
            if diameter_col is None or cumulative_col is None:
                messagebox.showerror("Format non reconnu",
                                    f"Impossible d'identifier les colonnes de diamètre et pourcentage.\n\n"
                                    f"Colonnes disponibles: {df.columns.tolist()}\n\n"
                                    f"Assurez-vous que votre fichier contient:\n"
                                    f"1. Une colonne avec les diamètres/tamis (mm)\n"
                                    f"2. Une colonne avec les pourcentages cumulés (%)")
                return
            
            # Extraire les données
            def convert_to_float_series(series):
                """Convertit une série en float, gérant les virgules décimales"""
                return series.astype(str).str.replace(',', '.').astype(float, errors='ignore')
            
            diameters = pd.to_numeric(convert_to_float_series(df[diameter_col]), errors='coerce').dropna().values
            cumulatives = pd.to_numeric(convert_to_float_series(df[cumulative_col]), errors='coerce').dropna().values
            
            # Vérifier que nous avons des données
            if len(diameters) == 0 or len(cumulatives) == 0:
                messagebox.showerror("Données manquantes",
                                    f"Aucune donnée numérique valide trouvée.\n\n"
                                    f"Colonne '{diameter_col}': {df[diameter_col].tolist()}\n"
                                    f"Colonne '{cumulative_col}': {df[cumulative_col].tolist()}")
                return
            
            # S'assurer que les deux tableaux ont la même longueur
            min_length = min(len(diameters), len(cumulatives))
            diameters = diameters[:min_length]
            cumulatives = cumulatives[:min_length]
            
            # Trier par diamètre croissant (important pour les courbes granulométriques)
            sorted_indices = np.argsort(diameters)
            diameters = diameters[sorted_indices]
            cumulatives = cumulatives[sorted_indices]
            
            # Ajouter le point (0,0) si nécessaire (début de courbe)
            if diameters[0] > 0:
                diameters = np.insert(diameters, 0, 0)
                cumulatives = np.insert(cumulatives, 0, 0)
            
            # Ajouter le point (max_diameter, 100) si nécessaire (fin de courbe)
            if cumulatives[-1] < 100 and diameters[-1] > 0:
                diameters = np.append(diameters, diameters[-1] * 1.5)  # Augmenter légèrement
                cumulatives = np.append(cumulatives, 100)
            
            # Stocker les données
            curve_data = np.column_stack((diameters, cumulatives))
            curve_name = os.path.basename(file_path)
            
            if len(curve_name) > 20:
                curve_name = curve_name[:17] + "..."
            
            self.csv_curves.append(curve_data)
            self.csv_curve_names.append(curve_name)
            
            # Mettre à jour l'affichage
            self._update_csv_curves_list()
            
            # Rafraîchir la courbe si une analyse est déjà affichée
            if self.current_reload_capture:
                self._show_loaded_curve(self.current_reload_capture)
            
            messagebox.showinfo("Succès", 
                               f"✅ Courbe chargée avec succès !\n\n"
                               f"📁 Fichier: {curve_name}\n"
                               f"📊 Points de données: {len(diameters)}\n"
                               f"📏 Diamètres (mm): {', '.join([f'{d:.1f}' for d in diameters])}\n"
                               f"📈 Pourcentages: {', '.join([f'{c:.1f}%' for c in cumulatives])}")
            
            return True
            
        except Exception as e:
            messagebox.showerror("Erreur de chargement",
                                f"❌ Impossible de charger le fichier.\n\n"
                                f"📄 Fichier: {os.path.basename(file_path)}\n\n"
                                f"💡 Assurez-vous que le fichier contient:\n"
                                f"   - Une colonne avec les diamètres (ex: 22,4; 31,5; 40; 50)\n"
                                f"   - Une colonne avec les pourcentages (ex: 1,4; 20,46; 62,71; 93,09)\n\n"
                                f"⚠️ Erreur: {str(e)}")
            return False
    
    def _update_csv_curves_list(self):
        """Met à jour la liste affichée des courbes CSV"""
        for widget in self.csv_list_container.winfo_children():
            widget.destroy()
        
        if not self.csv_curves:
            self.csv_status_label.config(text="Aucune courbe CSV chargée")
            return
        
        self.csv_status_label.config(text=f"{len(self.csv_curves)} courbe(s) CSV chargée(s) :")
        
        # Afficher chaque courbe avec un bouton de suppression
        for idx, (curve_data, curve_name) in enumerate(zip(self.csv_curves, self.csv_curve_names)):
            curve_frame = tk.Frame(self.csv_list_container, bg=COLOR_CARD_BG)
            curve_frame.pack(fill="x", pady=2)
            
            # Info de la courbe
            info_text = f"{curve_name} ({len(curve_data)} points)"
            info_label = tk.Label(curve_frame, text=info_text,
                                 bg=COLOR_CARD_BG, font=("Segoe UI", 9),
                                 anchor="w")
            info_label.pack(side="left", padx=(5, 0))
            
            # Bouton de suppression
            remove_btn = tk.Button(curve_frame, text="✕",
                                  font=("Segoe UI", 8, "bold"),
                                  bg=COLOR_STAT_BAD, fg="white",
                                  width=2, height=1,
                                  command=lambda i=idx: self._remove_csv_curve(i))
            remove_btn.pack(side="right", padx=(5, 0))
    
    def _remove_csv_curve(self, index):
        """Supprime une courbe CSV spécifique"""
        if 0 <= index < len(self.csv_curves):
            curve_name = self.csv_curve_names[index]
            self.csv_curves.pop(index)
            self.csv_curve_names.pop(index)
            
            self._update_csv_curves_list()
            
            # Rafraîchir la courbe si une analyse est déjà affichée
            if self.current_reload_capture:
                self._show_loaded_curve(self.current_reload_capture)
            
            messagebox.showinfo("Succès", f"Courbe '{curve_name}' supprimée.")
    
    def _clear_all_csv_curves(self):
        """Supprime toutes les courbes CSV"""
        if not self.csv_curves:
            messagebox.showinfo("Information", "Aucune courbe CSV à supprimer.")
            return
        
        if messagebox.askyesno("Confirmation", 
                              f"Voulez-vous vraiment supprimer toutes les {len(self.csv_curves)} courbes CSV ?"):
            self.csv_curves.clear()
            self.csv_curve_names.clear()
            
            self._update_csv_curves_list()
            
            # Rafraîchir la courbe si une analyse est déjà affichée
            if self.current_reload_capture:
                self._show_loaded_curve(self.current_reload_capture)
            
            messagebox.showinfo("Succès", "Toutes les courbes CSV ont été supprimées.")
    
    def _export_all_curves_data(self, capture_data):
        """Exporte toutes les données de courbes dans un fichier Excel"""
        if not self.csv_curves and not capture_data.get('tamis_exp'):
            messagebox.showwarning("Avertissement", "Aucune donnée à exporter.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[
                ("Fichiers Excel", "*.xlsx"),
                ("Fichiers CSV", "*.csv"),
                ("Tous les fichiers", "*.*")
            ],
            title="Exporter toutes les données de courbes"
        )
        
        if not file_path:
            return
        
        try:
            # Créer un DataFrame pour chaque courbe
            data_frames = {}
            
            # Courbe numérique
            if capture_data.get('tamis_exp'):
                df_num = pd.DataFrame({
                    'Diametre_mm': capture_data['tamis_exp'],
                    'Pourcentage_Cumulatif': capture_data['cumulative_raw']
                })
                data_frames['Courbe_Numerique'] = df_num
            
            # Courbes CSV
            for idx, (curve_data, curve_name) in enumerate(zip(self.csv_curves, self.csv_curve_names)):
                # Nettoyer le nom pour qu'il soit valide comme nom de feuille Excel
                sheet_name = f"CSV_{idx+1}_{curve_name[:25]}"
                sheet_name = ''.join(c for c in sheet_name if c.isalnum() or c in ' _')
                
                df_csv = pd.DataFrame({
                    'Diametre_mm': curve_data[:, 0],
                    'Pourcentage_Cumulatif': curve_data[:, 1]
                })
                data_frames[sheet_name] = df_csv
            
            # Exporter vers Excel
            if file_path.endswith('.xlsx'):
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    for sheet_name, df in data_frames.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
            else:  # CSV
                # Pour CSV, exporter uniquement la première courbe
                first_sheet = list(data_frames.keys())[0]
                data_frames[first_sheet].to_csv(file_path, index=False)
            
            messagebox.showinfo("Succès", f"Données exportées avec succès : {file_path}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'export : {str(e)}")