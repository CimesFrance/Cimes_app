# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw
import cv2
import numpy as np
import time
from datetime import datetime
import threading
import os

from gui.widgets.utils import (
    COLOR_FRAME_BG, COLOR_CARD_BG, COLOR_STATUS_RUNNING, 
    COLOR_STATUS_STOPPED, COLOR_ACCENT, COLOR_BG_DARK,
    COLOR_TEXT_LIGHT, configure_styles, create_display_card,
    display_read_only_param
)
from core.segmentation import segment_and_analyze
from core.granulometry import calculate_granulometric_curve_with_dna
from core.calibration import undistort_img, homo_and_pixel_conversion
from analysis.statistics import calculer_statistiques_granulometriques, generer_rapport_statistique
from utils.file_manager import save_capture_data

class MeasureView:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent, bg=COLOR_FRAME_BG)
        # Variables locales
        self.captured_tk_img = None
        self.segmented_tk_img = None
        self.curve_tk_img = None
        self.live_tk_img = None
        self.particles_table_data = []
        self.is_segmenting = False
        self.last_capture_time = time.time()
        
        self._build_ui()
    
    def _build_ui(self):
        """Construit l'interface de la vue Mesure"""
        self.frame.columnconfigure(0, weight=0, minsize=400)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=1)

        # Panneau latéral gauche
        info_card = ttk.Frame(self.frame, style="Card.TFrame")
        info_card.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        widget = tk.Label(info_card, text="Capteur - Contrôles", bg="#e5e7eb",
                          anchor="w", font=("Segoe UI", 11, "bold"), padx=10)
        widget.pack(fill="x")

        tk.Label(info_card,text="Facteur de conversion actuel :").pack(fill='x')
        tk.Label(info_card,textvariable=self.app.facteur_conversion).pack(fill='x')

        inner = tk.Frame(info_card, bg=COLOR_CARD_BG, padx=20, pady=10)
        inner.pack(fill="both", expand=True)

        # Boutons de contrôle
        button_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
        button_frame.pack(fill="x", pady=(0, 20))

        self.start_btn = ttk.Button(button_frame, text="▶ Démarrer",
                                    style="Start.TButton", 
                                    command=self.app.start_camera)
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.stop_btn = ttk.Button(button_frame, text="◼ Arrêter",
                                   style="Stop.TButton", 
                                   command=self.app.stop_camera)
        self.stop_btn.pack(side="left", fill="x", expand=True)

        self.manual_capture_btn = ttk.Button(button_frame, text="📸 Capture Manuelle",
                                           style="Secondary.TButton",
                                           command=self._manual_capture)
        self.manual_capture_btn.pack(side="left", fill="x", expand=True, padx=(10, 0))
        self.manual_capture_btn.pack_forget()

        ttk.Separator(inner, orient="horizontal").pack(fill="x", pady=10)

        # État du capteur
        widget = tk.Label(inner, text="État du Capteur", bg=COLOR_CARD_BG,
                          font=("Segoe UI", 11, "bold"))
        widget.pack(anchor="w", pady=(5, 0))

        status_row = tk.Frame(inner, bg=COLOR_CARD_BG)
        status_row.pack(anchor="w")

        self.status_indicator = tk.Canvas(status_row, width=16, height=16,
                                          bg=COLOR_CARD_BG, highlightthickness=0)
        self.status_indicator.pack(side="left", padx=(0, 8))
        self.status_circle = self.status_indicator.create_oval(1, 1, 15, 15,
                                                               fill=COLOR_STATUS_STOPPED,
                                                               outline="")

        self.status_label = tk.Label(status_row, textvariable=self.app.status_var,
                                     bg=COLOR_CARD_BG, fg=COLOR_STATUS_STOPPED,
                                     font=("Segoe UI", 11, "bold"))
        self.status_label.pack(side="left")

        tk.Label(status_row, textvariable=self.app.status_detail_var, bg=COLOR_CARD_BG,
                 fg="#6b7280", font=("Segoe UI", 9, "italic")).pack(side="left", padx=5)

        # Paramètres actifs
        widget = tk.Label(inner, text="Paramètres Actifs", bg=COLOR_CARD_BG,
                          font=("Segoe UI", 11, "bold"))
        widget.pack(anchor="w", pady=(15, 0))

        self.params_active_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
        self.params_active_frame.pack(fill="x", pady=5)

        ttk.Separator(inner, orient="horizontal").pack(fill="x", pady=10)

        # Statistiques de session
        widget = tk.Label(inner, text="Statistiques de Session", bg=COLOR_CARD_BG,
                          font=("Segoe UI", 11, "bold"))
        widget.pack(anchor="w", pady=(5, 0))

        widget = tk.Label(inner, text="Heure système :", bg=COLOR_CARD_BG,
                          font=("Segoe UI", 10))
        widget.pack(anchor="w", pady=(5, 0))
        tk.Label(inner, textvariable=self.app.datetime_var, bg=COLOR_CARD_BG,
                 fg="#4b5563").pack(anchor="w")

        widget = tk.Label(inner, text="Temps avant prochaine capture :",
                          bg=COLOR_CARD_BG, font=("Segoe UI", 10))
        widget.pack(anchor="w", pady=(10, 0))
        tk.Label(inner, textvariable=self.app.time_left_capture_var, bg=COLOR_CARD_BG,
                 fg=COLOR_STATUS_RUNNING, font=("Segoe UI", 16, "bold")).pack(anchor="w")

        widget = tk.Label(inner, text="Particules détectées (dernière capture) :",
                          bg=COLOR_CARD_BG, font=("Segoe UI", 10))
        widget.pack(anchor="w", pady=(10, 0))
        tk.Label(inner, textvariable=self.app.particles_count_var, bg=COLOR_CARD_BG,
                 fg="#0ea5e9", font=("Segoe UI", 16, "bold")).pack(anchor="w")

        widget = tk.Label(inner, text="Total images capturées :",
                          bg=COLOR_CARD_BG, font=("Segoe UI", 10))
        widget.pack(anchor="w", pady=(10, 0))
        tk.Label(inner, textvariable=self.app.images_count_var, bg=COLOR_CARD_BG,
                 fg=COLOR_ACCENT, font=("Segoe UI", 16, "bold")).pack(anchor="w")

        widget = tk.Label(inner, text="Horodatage dernière capture :",
                          bg=COLOR_CARD_BG, font=("Segoe UI", 10))
        widget.pack(anchor="w", pady=(10, 0))
        tk.Label(inner, textvariable=self.app.last_capture_time_var,
                 bg=COLOR_CARD_BG, font=("Segoe UI", 10, "italic")).pack(anchor="w")

        # Grille d'images (droite)
        grid_frame = tk.Frame(self.frame, bg=COLOR_FRAME_BG)
        grid_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)

        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)
        grid_frame.rowconfigure(0, weight=1)
        grid_frame.rowconfigure(1, weight=1)

        # Création des 4 cartes d'affichage
        camera_card = create_display_card(
            grid_frame, "Flux Caméra Temps Réel", 0, 0, (0, 5),
            "Flux caméra (Hors-ligne)\nConfigurer dans Paramètres."
        )
        self.live_label = camera_card.winfo_children()[1].winfo_children()[0]

        cap_card = create_display_card(
            grid_frame, "Image Capturée", 0, 1, (5, 0),
            "Aucune image capturée."
        )
        self.captured_label = cap_card.winfo_children()[1].winfo_children()[0]

        seg_card = create_display_card(
            grid_frame, "Masque Segmenté", 1, 0, (0, 5),
            "En attente de segmentation..."
        )
        self.segmented_label = seg_card.winfo_children()[1].winfo_children()[0]

        curve_card = create_display_card(
            grid_frame, "Courbe Granulométrique", 1, 1, (5, 0),
            "En attente de données pour la courbe..."
        )
        self.curve_label = curve_card.winfo_children()[1].winfo_children()[0]


    def update_active_params_display(self):
        """Met à jour l'affichage des paramètres actifs"""
        for widget in self.params_active_frame.winfo_children():
            widget.destroy()

        url_display = self.app.url_var.get()
        if len(url_display) > 30:
            url_display = url_display[:27] + "..."
        
        try:
            scale_value = float(self.app.scale_var.get().replace(",", "."))
            scale_display = f"{scale_value:.4f}"
        except:
            scale_display = self.app.scale_var.get()
        
        path_display = self.app.results_path_var.get()
        if len(path_display) > 30:
            path_display = path_display[:15] + "..." + path_display[-15:]
        
        mode = self.app.capture_mode_var.get()
        mode_display = "Automatique" if mode == "automatique" else "Manuel"
        mode_color = COLOR_STATUS_RUNNING if mode == "automatique" else COLOR_ACCENT
        
        display_read_only_param(self.params_active_frame, "Mode capture :", 
                              mode_display, value_color=mode_color)
        display_read_only_param(self.params_active_frame, "URL/IP active :", url_display)
        
        if mode == "automatique":
            display_read_only_param(self.params_active_frame, "Délai capture :", 
                                  self.app.save_delay_display_var.get())
            display_read_only_param(self.params_active_frame, "Heures actives :", 
                                  f"{self.app.start_time_var.get()} - {self.app.end_time_var.get()}")
        else:
            display_read_only_param(self.params_active_frame, "Délai capture :", "Manuel")
            display_read_only_param(self.params_active_frame, "Heures actives :", "Non applicable")
        
        display_read_only_param(self.params_active_frame, "Chemin résultats :", path_display)
        display_read_only_param(self.params_active_frame, "Échelle :", f"{scale_display} mm/px")
    
    def update_camera_status_ui(self, is_running):
        """Met à jour l'interface selon l'état de la caméra"""
        if is_running:
            self.status_indicator.itemconfig(self.status_circle, fill=COLOR_STATUS_RUNNING)
            self.status_label.config(fg=COLOR_STATUS_RUNNING)
            self.app.status_var.set("EN COURS")  # ← AJOUTER
            self.app.status_detail_var.set("(En ligne)")  # ← AJOUTER
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            
            if self.app.capture_mode_var.get() == "manuel":
                self.manual_capture_btn.pack(side="left", fill="x", expand=True, padx=(10, 0))
            else:
                self.manual_capture_btn.pack_forget()
        else:
            self.status_indicator.itemconfig(self.status_circle, fill=COLOR_STATUS_STOPPED)
            self.status_label.config(fg=COLOR_STATUS_STOPPED)
            self.app.status_var.set("ARRÊTÉE")  # ← AJOUTER
            self.app.status_detail_var.set("(Hors-ligne)")  # ← AJOUTER
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.manual_capture_btn.pack_forget()
    
    def update_live_feed(self, frame):
        """Met à jour le flux vidéo en direct"""
        if frame is not None and hasattr(self, 'live_label') and self.live_label:
            self.app.last_captured_frame = frame
            
            display_frame = frame.copy()
            
            try:
                cv2image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(cv2image)
                container = self.live_label.image_container
                container_width = container.winfo_width()
                container_height = container.winfo_height()
                
                if container_width > 10 and container_height > 10:
                    ratio_width = container_width / pil_img.width
                    ratio_height = container_height / pil_img.height
                    ratio = min(ratio_width, ratio_height)
                    
                    if ratio < 0.1:
                        ratio = max(ratio_width, ratio_height)
                    
                    new_width = int(pil_img.width * ratio)
                    new_height = int(pil_img.height * ratio)
                    
                    resized_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    self.live_tk_img = ImageTk.PhotoImage(resized_img)
                    self.live_label.config(image=self.live_tk_img, text="")
                    self.live_label.image = self.live_tk_img
                    
                    if (self.app.use_undistortion_var.get() and self.app.mtx is not None) or \
                        (self.app.use_homography_var.get() and self.app.homo_matrix is not None):
                        info_text = "✓ Corrections actives (appliquées lors de l'analyse)"
                        self.live_label.config(text=info_text, compound='bottom')
                        
            except Exception as e:
                print(f"Erreur d'affichage: {e}")
        else:
            if hasattr(self, 'live_label') and self.live_label:
                self.live_label.config(image='', 
                                      text="Flux caméra (Hors-ligne)\nConfigurer dans Paramètres.")
    
    def _manual_capture(self):
        """Capture manuelle déclenchée par l'utilisateur"""
        if not self.app.camera_running:
            from tkinter import messagebox
            messagebox.showwarning("Caméra non démarrée", 
                                 "Veuillez démarrer la caméra d'abord.")
            return
        
        if self.is_segmenting:
            from tkinter import messagebox
            messagebox.showinfo("Capture en cours", 
                              "Une capture est déjà en cours. Veuillez patienter.")
            return
        
        self._perform_capture()
    
    def _perform_capture(self):
        """Effectue une capture et lance l'analyse"""
        frame_to_analyze = self.app.last_captured_frame
        if frame_to_analyze is None:
            print("Aucune frame disponible.")
            self.last_capture_time = time.time()
            return

        if self.is_segmenting:
            print("Capture déjà en cours.")
            return

        self.is_segmenting = True
        self.last_capture_time = time.time()
        
        # Afficher l'image capturée (avec corrections si activées)
        frame_for_display = frame_to_analyze.copy()
        if self.app.use_undistortion_var.get() and self.app.mtx is not None and self.app.dist is not None:
            frame_for_display = undistort_img(self.app.dist, self.app.mtx, frame_for_display)
        # if self.app.use_homography_var.get() and self.app.homo_matrix is not None:
        #     frame_for_display = homo_and_pixel_conversion(frame_for_display, self.app.homo_matrix)
        
        self._update_display_label(self.captured_label, frame_for_display, "captured_tk_img")
        
        # Lancer le traitement en arrière-plan
        threading.Thread(target=self._process_capture_in_background,
                         args=(frame_to_analyze.copy(),)).start()
    
    def _process_capture_in_background(self, frame_to_analyze):
        """Traite la capture en arrière-plan"""
        try:
            print("je suis rentrée iciiiiii")
            processed_frame = frame_to_analyze.copy()
            print(self.app.mtx)
            print(self.app.dist)
            # Appliquer les corrections si activées
            if self.app.use_undistortion_var.get() and self.app.mtx is not None and self.app.dist is not None:
                processed_frame = undistort_img(self.app.dist, self.app.mtx, processed_frame)
            
            # if self.app.use_homography_var.get() and self.app.homo_matrix is not None:
            #     processed_frame = homo_and_pixel_conversion(processed_frame, self.app.homo_matrix)
            print("maintenant je suis la")
            print(self.app.scale_var.get())
            scale = float(self.app.scale_var.get()) if self.app.scale_var.get() else 0.1
            print(scale)
            
            # Segmentation et analyse
            masks, segmented_img, particles_data, _, L_min_axis, L_max_axis = segment_and_analyze(
                processed_frame, scale
            )
            L_min_axis = [(elt * float(self.app.facteur_conversion.get())) for elt in L_min_axis]
            # L_min_axis = L_min_axis * float(self.app.facteur_conversion.get())
            
            # Calcul de la courbe granulométrique
            tamis_exp, cumulative_raw, cumulative_corrected, minor_axes_mm = calculate_granulometric_curve_with_dna(
                particles_data, L_min_axis,  self.app.correction_granulo['scale'].get() , self.app.correction_granulo['offset'].get() , scale
            )
            
            # Préparer les données pour l'affichage
            self.particles_table_data = []
            for i, particle in enumerate(particles_data):
                minor_mm = particle.get('minor_axis_mm', 0)
                major_mm = particle.get('major_axis_mm', 0)
            
                if minor_mm > 0.1 and major_mm > 0.1:
                    self.particles_table_data.append({
                        'id': i + 1,
                        'minor_mm': minor_mm,
                        'major_mm': major_mm
                    })
            
            capture_data = {
                'id': len(self.app.capture_history) + 1,
                'timestamp': datetime.now(),
                'image_raw': frame_to_analyze,
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
                'scale': scale
            }
            
            # Mettre à jour l'interface
            self.app.after(0, lambda: self._update_capture_results(capture_data))

        except Exception as e:
            print(f"Erreur traitement: {e}")
            self.app.after(0, lambda: self._capture_error(e))
    
    def _update_capture_results(self, capture_data):
        """Met à jour l'interface avec les résultats de la capture"""
        self.is_segmenting = False
        self.app.capture_history.append(capture_data)
        self.app.current_capture_index = len(self.app.capture_history) - 1
        
        # Mettre à jour les compteurs
        self.app.captured_count += 1
        self.app.images_count_var.set(str(self.app.captured_count))
        self.app.last_capture_time_var.set(capture_data['timestamp'].strftime("%Y/%m/%d %H:%M:%S"))
        self.app.particles_count_var.set(str(capture_data['particles_count']))
        
        # Afficher l'image segmentée
        if capture_data['segmented_image'] is not None:
            self._update_display_label(self.segmented_label, 
                                      capture_data['segmented_image'], 
                                      "segmented_tk_img")
        else:
            self.segmented_label.config(image='', text="Segmentation non disponible\nCellpose non installé")
        
        # Afficher la courbe granulométrique
        if len(capture_data['tamis_exp']) > 0:
            print("afficher courbe")
            self._display_granulometric_curve(
                capture_data['tamis_exp'], 
                capture_data['cumulative_raw'],
                capture_data['cumulative_corrected'] if self.app.show_corrected_curve_var.get() else None
            )
        else:
            print("ne pas afficher courbe")
            self._display_granulometric_curve([], [])
        
        # Sauvegarder la capture
        from utils.file_manager import save_capture_data
        save_capture_data(capture_data, self.app.results_path_var.get(), self.app)
        
        # Mettre à jour les autres vues
        if hasattr(self.app, 'curve_view'):
            self.app.curve_view._update_capture_history_display()
            self.app.curve_view._update_curve_view_for_capture(capture_data['id'])
            self.app.curve_view._update_particles_table()
            self.app.curve_view.update_statistics_display(capture_data)
        
        # Ajouter aux données quotidiennes
        self.app.daily_data.append(capture_data)
    
    def _capture_error(self, error):
        """Affiche une erreur de capture"""
        self.is_segmenting = False
        self.segmented_label.config(image='', text=f"Erreur de traitement\n{str(error)[:50]}")
        self.curve_label.config(image='', text="Erreur de traitement")
    
    def _update_display_label(self, label, frame, attribute_name):
        """Met à jour un label avec une image"""
        try:
            if frame is None:
                label.config(image='', text="Image non disponible")
                return
                
            if frame.ndim == 3 and frame.shape[2] == 3:
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            elif frame.ndim == 3:
                cv2image = frame
            else:
                cv2image = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)

            pil_img = Image.fromarray(cv2image)
            container = label.image_container
            container_width = container.winfo_width()
            container_height = container.winfo_height()

            if container_width > 10 and container_height > 10:
                ratio = min(container_width / pil_img.width, container_height / pil_img.height)
                new_width = int(pil_img.width * ratio)
                new_height = int(pil_img.height * ratio)
                resized_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(resized_img)
                setattr(self, attribute_name, tk_img)
                label.config(image=tk_img, text="")
                label.image = tk_img

        except Exception as e:
            print(f"Erreur affichage: {e}")
            label.config(image='', text=f"Erreur d'affichage:\n{e}")
    
    def _display_granulometric_curve(self, tamis_exp, cumulative_raw, cumulative_corrected=None):
        """Affiche la courbe granulométrique"""
        try:
            diameters_vss = [0, 22.4, 31.5, 40, 50, 63, 100]
            cumFraction_vss = [0, 4, 26, 70, 99, 99, 100]
        
            diameters_vsi = [0, 22.4, 31.5, 40, 50, 50, 50]
            cumFraction_vsi = [0, 0, 0, 25, 70, 70, 70]
        
            if not tamis_exp or not cumulative_raw:
                self.curve_label.config(image='', text="Aucune donnée disponible\npour la granulométrie")
                return
        
            import matplotlib.pyplot as plt
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from io import BytesIO
            
            fig = Figure(figsize=(16,8), dpi=100, facecolor='#f5f5f5')
            ax = fig.add_subplot(111, facecolor='white')
        
            tamis_sizes = list(tamis_exp)
            cumul_raw = list(cumulative_raw)
            cumul_corrected = list(cumulative_corrected) if cumulative_corrected else None
        
            line_vss, = ax.plot(diameters_vss, cumFraction_vss, 
                             color='#10b981', linewidth=5, 
                             linestyle='--', alpha=0.8, 
                             label='Courbe VSS (Référence)',
                             marker='^', markersize=4,
                             markerfacecolor='white',
                             markeredgewidth=4,
                             markeredgecolor='#10b981')
        
            line_vsi, = ax.plot(diameters_vsi, cumFraction_vsi, 
                             color='#f59e0b', linewidth=5, 
                             linestyle='--', alpha=0.8,
                             label='Courbe VSI (Référence)',
                             marker='s', markersize=4,
                             markerfacecolor='white',
                             markeredgewidth=4,
                             markeredgecolor='#f59e0b')
        
            # line1, = ax.plot(tamis_sizes, cumul_raw, 
            #              marker='o', color='#2563eb', linewidth=5, 
            #              markersize=12, label='Courbe brute',
            #              markerfacecolor='white', markeredgewidth=4,
            #              markeredgecolor='#2563eb')
        
            if cumul_corrected and len(cumul_corrected) == len(tamis_sizes) and self.app.show_corrected_curve_var.get():
                line2, = ax.plot(tamis_sizes, cumul_corrected, 
                                 marker='s', color='#dc2626', linewidth=5, 
                                 label='Courbe corrigée (DNA)',
                                 markerfacecolor='white', markeredgewidth=4,
                                 markeredgecolor='#dc2626')
        
            ax.set_xlabel("Taille du tamis (mm)", fontsize=22, fontweight='bold', color='#1f2937')
            ax.set_xlim([0, 80])
            ax.set_xticks([0, 22.4, 31.5, 40, 50, 63, 80])
            ax.set_xticklabels(['0', '22.4', '31.5', '40', '50', '63', '80'], 
                              fontsize=22, fontweight='bold', color='#374151')
        
            ax.set_ylabel("% passant cumulé", fontsize=22, fontweight='bold', color='#1f2937')
            ax.set_ylim([0, 105])
            ax.set_yticks(np.arange(0, 101, 10))
            ax.set_yticklabels([f'{int(y)}%' for y in np.arange(0, 101, 10)], 
                              fontsize=22, color='#374151')
        
            ax.grid(True, which='major', linestyle='--', linewidth=0.7, alpha=0.3, color='#9ca3af')
            ax.grid(True, which='minor', linestyle=':', linewidth=0.5, alpha=0.2, color='#d1d5db')
            ax.minorticks_on()
        
            for spine in ax.spines.values():
                spine.set_linewidth(1.5)
                spine.set_color('#4b5563')
        
            ax.legend(loc='upper left', fontsize=20, framealpha=0.9, 
                     facecolor='white', edgecolor='#d1d5db',
                     frameon=True, shadow=True)
        
            for x, y in zip(tamis_sizes, cumul_raw):
                ax.annotate(f'{y:.1f}%', 
                           xy=(x, y), xytext=(0, 8),
                           textcoords='offset points', 
                           ha='center', va='bottom',
                           fontsize=16, fontweight='bold', color='#1e40af',
                           bbox=dict(boxstyle="round,pad=0.4", 
                                    facecolor="white", 
                                    edgecolor="#93c5fd", 
                                    alpha=0.9))
        
            if cumul_corrected and self.app.show_corrected_curve_var.get():
                for x, y in zip(tamis_sizes, cumul_corrected):
                    ax.annotate(f'{y:.1f}%', 
                               xy=(x, y), xytext=(0, -12),
                               textcoords='offset points', 
                               ha='center', va='top',
                               fontsize=16, fontweight='bold', color='#991b1b',
                               bbox=dict(boxstyle="round,pad=0.4", 
                                        facecolor="white", 
                                        edgecolor="#fca5a5", 
                                        alpha=0.9))
        
            info_text = f"Captures analysées: {self.app.captured_count}"
            ax.text(0.02, 0.98, info_text, transform=ax.transAxes,
                   fontsize=9, verticalalignment='top',
                   bbox=dict(boxstyle="round", facecolor="#fef3c7", 
                            edgecolor="#f59e0b", alpha=0.8))
        
            fig.tight_layout(pad=3.0)
        
            canvas = FigureCanvasTkAgg(fig, master=self.curve_label.image_container)
            canvas.draw()
        
            buf = BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', 
                       pad_inches=0.3, dpi=100, facecolor=fig.get_facecolor())
            buf.seek(0)
        
            pil_img = Image.open(buf)
        
            container = self.curve_label.image_container
            container_width = max(100, container.winfo_width())
            container_height = max(100, container.winfo_height())
        
            ratio = min(container_width / pil_img.width, 
                       container_height / pil_img.height)
            new_width = int(pil_img.width * ratio)
            new_height = int(pil_img.height * ratio)
        
            resized_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
            tk_img = ImageTk.PhotoImage(resized_img)
            self.curve_tk_img = tk_img
        
            self.curve_label.config(image=tk_img, text="")
            self.curve_label.image = tk_img
        
            plt.close(fig)
        
        except Exception as e:
            print(f"Erreur création courbe: {e}")
            self.curve_label.config(image='', 
                                   text=f"Erreur création courbe\n{str(e)[:50]}")