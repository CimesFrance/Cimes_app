# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
# from app_toplevel import Application_calibrage

import json
import os
import numpy as np
from datetime import datetime
import time

from utils.file_manager import save_conversion_parameter,load_calibration_files

from gui.widgets.utils import (
    COLOR_FRAME_BG, COLOR_CARD_BG, COLOR_ACCENT,
    display_read_only_param, create_setting_header
)

from modules.app_calibrage_cam.ui.main_window import ApplicationCalibrage

class ParamView:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        # self.path = r"D:\apprendre Tkinter\CIMES_Project-vers3\calibration_maj_1.npz"
        # data = np.load(self.path)
        # self.app.mtx = data['camMatrix']
        # self.app.dist = data['distCoeff'] # Matrice de calibration de la caméra
        self.app.use_undistortion_var.set(True)
        self.frame = tk.Frame(parent, bg=COLOR_FRAME_BG)
        # Variables pour les paramètres
        self.param_nav_buttons = {}
        
        self._build_ui()
    
    def _build_ui(self):
        """Construit l'interface de la vue Paramètres"""

        param_area = tk.Frame(self.frame, bg=COLOR_FRAME_BG)
        param_area.pack(fill="both", expand=True, padx=20, pady=10)

        param_area.columnconfigure(1, weight=1)
        param_area.rowconfigure(0, weight=1)

        # Navigation latérale
        nav_frame = ttk.Frame(param_area, style="Card.TFrame", width=200)
        nav_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        nav_frame.pack_propagate(False)

        tk.Label(nav_frame, text="Catégories :", bg=COLOR_CARD_BG,
                 font=("Segoe UI", 10, "bold"),
                 padx=10, pady=5).pack(fill="x", anchor="n")

        # Boutons de navigation
        self.param_nav_buttons["sensor"] = ttk.Button(
            nav_frame, text="📷 Capteur",
            style="ParamNav.TButton",
            command=lambda: self._switch_param_view("sensor")
        )
        self.param_nav_buttons["sensor"].pack(fill="x", padx=5, pady=(5, 2))

        self.param_nav_buttons["calibration"] = ttk.Button(
            nav_frame, text="⚙️ Calibration Caméra",
            style="ParamNav.TButton",
            command=lambda: self._switch_param_view("calibration")
        )
        self.param_nav_buttons["calibration"].pack(fill="x", padx=5, pady=2)

        self.param_nav_buttons["analysis"] = ttk.Button(
            nav_frame, text="🔬 Analyse",
            style="ParamNav.TButton",
            command=lambda: self._switch_param_view("analysis")
        )
        self.param_nav_buttons["analysis"].pack(fill="x", padx=5, pady=2)

        self.param_nav_buttons["transmission"] = ttk.Button(
            nav_frame, text="📤 Transmission",
            style="ParamNav.TButton",
            command=lambda: self._switch_param_view("transmission")
        )
        self.param_nav_buttons["transmission"].pack(fill="x", padx=5, pady=2)

        # Conteneur pour le contenu
        self.param_content_frame = tk.Frame(param_area, bg=COLOR_FRAME_BG)
        self.param_content_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)
        self.param_content_frame.grid_columnconfigure(0, weight=1)
        self.param_content_frame.grid_rowconfigure(0, weight=1)

        # Créer toutes les vues
        self._create_sensor_settings()
        self._create_calibration_settings()
        self._create_analysis_settings()
        self._create_transmission_settings()

        # Afficher la vue par défaut
        self._switch_param_view("sensor")
    
    def _switch_param_view(self, key):
        """Change la vue des paramètres"""
        for k, btn in self.param_nav_buttons.items():
            if k == key:
                btn.configure(style="ParamNavActive.TButton")
            else:
                btn.configure(style="ParamNav.TButton")

        frames = {
            "sensor": getattr(self, "sensor_settings_frame", None),
            "calibration": getattr(self, "calibration_settings_frame", None),
            "analysis": getattr(self, "analysis_settings_frame", None),
            "transmission": getattr(self, "transmission_settings_frame", None),
        }

        frame_to_show = frames.get(key)
        if frame_to_show:
            for name, frame in frames.items():
                if frame:
                    frame.grid_forget()

            frame_to_show.grid(row=0, column=0, sticky="nsew")
    
    def _create_sensor_settings(self):
        """Crée l'interface des paramètres du capteur"""
        self.sensor_settings_frame = ttk.Frame(self.param_content_frame, style="Card.TFrame")
        create_setting_header(self.sensor_settings_frame, "Configuration du Capteur")

        inner = tk.Frame(self.sensor_settings_frame, bg=COLOR_CARD_BG, padx=20, pady=10)
        inner.pack(fill="both", expand=True)

        # Adresse IP RTSP
        tk.Label(inner, text="Adresse IP du Capteur RTSP :", bg=COLOR_CARD_BG,
                 anchor="w", font=("Segoe UI", 10, "bold")).pack(fill="x", pady=(5, 0))
        ttk.Entry(inner, textvariable=self.app.url_var, width=50,
                  font=("Segoe UI", 10)).pack(fill="x")

        tk.Label(inner,
                 text="Exemple : rtsp://utilisateur:motdepasse@192.168.1.10:554/stream",
                 bg=COLOR_CARD_BG, fg="#6b7280",
                 font=("Segoe UI", 8, "italic")).pack(fill="x", pady=(0, 15))

        # Chemin de sauvegarde
        tk.Label(inner, text="Chemin de sauvegarde des résultats :", bg=COLOR_CARD_BG,
                 anchor="w", font=("Segoe UI", 10, "bold")).pack(fill="x", pady=(5, 0))

        path_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
        path_frame.pack(fill="x", pady=(0, 15))

        ttk.Entry(path_frame, textvariable=self.app.results_path_var, width=50,
                  font=("Segoe UI", 10)).pack(side="left", fill="x", expand=True)
        ttk.Button(path_frame, text="Parcourir",
                   style="Secondary.TButton",
                   command=self._browse_results_path).pack(side="left", padx=5)

        # Mode de capture
        tk.Label(inner, text="Mode de capture :",
                 bg=COLOR_CARD_BG, anchor="w",
                 font=("Segoe UI", 10, "bold")).pack(fill="x", pady=(15, 0))

        mode_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
        mode_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Radiobutton(mode_frame, text="Automatique", value="automatique",
                       variable=self.app.capture_mode_var,
                       command=self._toggle_capture_controls).pack(side="left", padx=(0, 20))
        
        ttk.Radiobutton(mode_frame, text="Manuel", value="manuel",
                       variable=self.app.capture_mode_var,
                       command=self._toggle_capture_controls).pack(side="left")

        # Paramètres automatiques
        self.auto_params_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
        self.auto_params_frame.pack(fill="x", pady=(0, 20))

        tk.Label(self.auto_params_frame, text="Intervalle entre captures :",
                 bg=COLOR_CARD_BG, anchor="w",
                 font=("Segoe UI", 10, "bold")).pack(fill="x", pady=(5, 0))

        self.capture_interval_frame = tk.Frame(self.auto_params_frame, bg=COLOR_CARD_BG)
        self.capture_interval_frame.pack(fill="x", pady=(0, 15))

        ttk.Entry(self.capture_interval_frame, textvariable=self.app.capture_time_val_var, width=10,
                  font=("Segoe UI", 10)).pack(side="left")
        ttk.Combobox(self.capture_interval_frame, textvariable=self.app.capture_time_unit_var,
                     values=["s", "min", "h"], width=5, state="readonly",
                     font=("Segoe UI", 10)).pack(side="left", padx=(10, 0))

        # Programmation des heures
        tk.Label(self.auto_params_frame, text="Programmation des heures de fonctionnement :",
                 bg=COLOR_CARD_BG, anchor="w",
                 font=("Segoe UI", 10, "bold")).pack(fill="x", pady=(5, 0))

        self.time_frame = tk.Frame(self.auto_params_frame, bg=COLOR_CARD_BG)
        self.time_frame.pack(fill="x", pady=(0, 10))

        tk.Label(self.time_frame, text="Début :",
                 bg=COLOR_CARD_BG, font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        ttk.Entry(self.time_frame, textvariable=self.app.start_time_var, width=8,
                  font=("Segoe UI", 10)).pack(side="left", padx=(0, 20))

        tk.Label(self.time_frame, text="Fin :",
                 bg=COLOR_CARD_BG, font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        ttk.Entry(self.time_frame, textvariable=self.app.end_time_var, width=8,
                  font=("Segoe UI", 10)).pack(side="left")

        # Jours de fonctionnement
        tk.Label(self.auto_params_frame, text="Jours de fonctionnement :",
                 bg=COLOR_CARD_BG, anchor="w",
                 font=("Segoe UI", 10, "bold")).pack(fill="x", pady=(15, 0))

        self.days_frame = tk.Frame(self.auto_params_frame, bg=COLOR_CARD_BG)
        self.days_frame.pack(fill="x", pady=(0, 20))

        jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        for i, jour in enumerate(jours):
            ttk.Checkbutton(self.days_frame, text=jour[:3],
                           variable=self.app.days_vars[jour]).pack(side="left", padx=(0, 10))

        # Paramètres manuels
        self.manual_params_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
        self.manual_params_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(self.manual_params_frame, text="Mode Manuel :",
                 bg=COLOR_CARD_BG, anchor="w",
                 font=("Segoe UI", 10, "bold")).pack(fill="x", pady=(5, 0))
        
        tk.Label(self.manual_params_frame, 
                 text="En mode manuel, vous déclenchez les captures manuellement\n"
                      "en cliquant sur le bouton 'Capture Manuelle' dans la vue Mesure.",
                 bg=COLOR_CARD_BG, fg="#6b7280",
                 font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(5, 0))

        # Bouton de sauvegarde
        button_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
        button_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(
            button_frame, text="Sauvegarder les Paramètres",
            style="Start.TButton",
            command=self._save_sensor_settings
        ).pack(side="left")
        
        self._toggle_capture_controls()
    
    def _toggle_capture_controls(self):
        """Active/désactive les contrôles selon le mode"""
        mode = self.app.capture_mode_var.get()
        
        if mode == "automatique":
            self.auto_params_frame.pack(fill="x", pady=(0, 20))
            self.manual_params_frame.pack_forget()
            
            for widget in self.capture_interval_frame.winfo_children():
                widget.configure(state="normal")
            for widget in self.time_frame.winfo_children():
                widget.configure(state="normal")
            for widget in self.days_frame.winfo_children():
                widget.configure(state="normal")
        else:
            self.auto_params_frame.pack_forget()
            self.manual_params_frame.pack(fill="x", pady=(0, 20))
            
            for widget in self.capture_interval_frame.winfo_children():
                widget.configure(state="disabled")
            for widget in self.time_frame.winfo_children():
                widget.configure(state="disabled")
            for widget in self.days_frame.winfo_children():
                widget.configure(state="disabled")
    
    def _browse_results_path(self):
        """Ouvre une boîte de dialogue pour choisir le dossier de sauvegarde"""
        folder = filedialog.askdirectory(parent=self.app, title="Sélectionner le dossier de sauvegarde des résultats")
        if folder:
            self.app.results_path_var.set(folder)
    
    def _save_sensor_settings(self):
        """Sauvegarde les paramètres du capteur"""
        settings = {
            "url": self.app.url_var.get(),
            "results_path": self.app.results_path_var.get(),
            "start_time": self.app.start_time_var.get(),
            "end_time": self.app.end_time_var.get(),
            "days_active": {day: var.get() for day, var in self.app.days_vars.items()},
            "capture_interval": {
                "value": self.app.capture_time_val_var.get(),
                "unit": self.app.capture_time_unit_var.get()
            },
            "capture_mode": self.app.capture_mode_var.get(),
            "scale": self.app.scale_var.get(),
            "dna_correction_enabled": self.app.show_corrected_curve_var.get()
        }
        
        try:
            save_dir = os.path.join(os.path.expanduser("~"), "CIMES_Settings")
            os.makedirs(save_dir, exist_ok=True)
            
            settings_file = os.path.join(save_dir, "sensor_settings.json")
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            
            # Mettre à jour l'affichage
            if hasattr(self.app, 'measure_view'):
                self.app.measure_view.update_active_params_display()
            
            if hasattr(self.app, 'curve_view') and self.app.curve_view.frame.winfo_ismapped():
                self.app.curve_view._update_curve_view()
            
            messagebox.showinfo("Succès", "Paramètres du capteur sauvegardés avec succès !")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde : {str(e)}")
    
    def _create_calibration_settings(self):
        """Crée l'interface de calibration"""
        self.calibration_settings_frame = ttk.Frame(self.param_content_frame, style="Card.TFrame")
        create_setting_header(self.calibration_settings_frame, "Calibration Caméra")

        inner = tk.Frame(self.calibration_settings_frame, bg=COLOR_CARD_BG, padx=20, pady=10)
        inner.pack(fill="both", expand=True)

        # Statut de calibration
        tk.Label(inner, text="📊 Statut de Calibration", bg=COLOR_CARD_BG,
                 anchor="w", font=("Segoe UI", 11, "bold")).pack(fill="x", pady=(0, 10))
    
        status_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
        status_frame.pack(fill="x", pady=(0, 20))
     
        # Statut camera_params.npz
        row1 = tk.Frame(status_frame, bg=COLOR_CARD_BG)
        row1.pack(fill="x", pady=5)
        _,_,cam_calib_path = load_calibration_files()
        tk.Label(row1,text=f"Le fichier de calibration utilisé est : {cam_calib_path}",bg=COLOR_CARD_BG,font=("Segoe UI", 10)).pack(anchor='w')

        # tk.Label(row1, text="Fichier camera_params.npz :", bg=COLOR_CARD_BG,
        #          font=("Segoe UI", 10), width=25, anchor="w").pack(side="left")
     
        # self.camera_params_status = tk.Label(row1, text="", bg=COLOR_CARD_BG,
        #                                     font=("Segoe UI", 10, "bold"))
        # self.camera_params_status.pack(side="left", padx=(10, 0))
     
        # ttk.Button(row1, text="Recharger", style="Secondary.TButton",
        #           command=self._reload_camera_params).pack(side="left", padx=(10, 0))
     
        # Statut homography.npz
        row2 = tk.Frame(status_frame, bg=COLOR_CARD_BG)
        row2.pack(fill="x", pady=5)
     
        # tk.Label(row2, text="Fichier homography.npz :", bg=COLOR_CARD_BG,
        #          font=("Segoe UI", 10), width=25, anchor="w").pack(side="left")
     
        # self.homography_status = tk.Label(row2, text="", bg=COLOR_CARD_BG,
        #                                  font=("Segoe UI", 10, "bold"))
        # self.homography_status.pack(side="left", padx=(10, 0))
     
        # ttk.Button(row2, text="Recharger", style="Secondary.TButton",
        #           command=self._reload_homography).pack(side="left", padx=(10, 0))
        # tk.Label(status_frame,text=f"Le fichier de calibration utilisé est : {self.path}",bg=COLOR_CARD_BG,font=("Segoe UI", 10)).pack(anchor='w')
        tk.Label(row2,text=f"le coefficient de conversion pixel-mm actuel : ",bg=COLOR_CARD_BG,font=("Segoe UI", 10),anchor='w').pack(side='left')
        tk.Label(row2,textvariable=self.app.facteur_conversion,bg=COLOR_CARD_BG,font=("Segoe UI", 10),anchor='w').pack(side='left')
        ttk.Button(row2,text="Modifier",style="Secondary.TButton",command=self._call_measure_app).pack(side="left",padx=(10, 0))
     
        # Instructions
        tk.Label(inner, 
                 text="Les fichiers de calibration sont automatiquement chargés au démarrage\n"
                      "s'ils sont présents dans le dossier de l'application.",
                 bg=COLOR_CARD_BG, fg="#6b7280",
                 font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(0, 20))
     
        # Correction d'image
        tk.Label(inner, text="⚙️ Correction d'Image", bg=COLOR_CARD_BG,
                 anchor="w", font=("Segoe UI", 11, "bold")).pack(fill="x", pady=(10, 0))
     
        corr_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
        corr_frame.pack(fill="x", pady=10)
     
        # Case à cocher pour l'undistortion
        self.undistort_check = ttk.Checkbutton(corr_frame, 
                                              text="Utiliser la correction de distorsion",
                                              variable=self.app.use_undistortion_var,
                                              command=self._update_undistort_status)
        self.undistort_check.pack(anchor="w", pady=(5, 0))
     
        # Case à cocher pour l'homographie
        self.homography_check = ttk.Checkbutton(corr_frame, 
                                               text="Utiliser la correction d'homographie",
                                               variable=self.app.use_homography_var,
                                               command=self._update_homography_status)
        self.homography_check.pack(anchor="w", pady=(5, 0))
     
        tk.Label(corr_frame, 
                 text="Ces corrections sont appliquées automatiquement lors de l'analyse.",
                 bg=COLOR_CARD_BG, fg="#6b7280",
                 font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(5, 0))
     
        # Échelle de calibration
        tk.Label(inner, text="📏 Échelle de Calibration", bg=COLOR_CARD_BG,
                 anchor="w", font=("Segoe UI", 11, "bold")).pack(fill="x", pady=(20, 10))
     
        scale_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
        scale_frame.pack(fill="x", pady=(0, 10))
     
        tk.Label(scale_frame, text="Échelle (mm/px):", bg=COLOR_CARD_BG,
                 font=("Segoe UI", 10), width=15, anchor="w").pack(side="left")
     
        self.calibration_scale_entry = ttk.Entry(scale_frame, 
                                                textvariable=self.app.calibration_scale_var,
                                                width=15, font=("Segoe UI", 10))
        self.calibration_scale_entry.pack(side="left", padx=(5, 10))
     
        self.apply_scale_btn = ttk.Button(scale_frame, text="Appliquer",
                                         style="Secondary.TButton",
                                         command=self._apply_calibration_scale)
        self.apply_scale_btn.pack(side="left")
     
        # Valeur actuelle affichée
        current_scale_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
        current_scale_frame.pack(fill="x", pady=(5, 0))
     
        tk.Label(current_scale_frame, text="Échelle actuelle:", bg=COLOR_CARD_BG,
                 font=("Segoe UI", 10), width=15, anchor="w").pack(side="left")
     
        self.current_scale_label = tk.Label(current_scale_frame, 
                                           text=f"{self.app.scale_var.get()} mm/px",
                                           bg=COLOR_CARD_BG, fg=COLOR_ACCENT,
                                           font=("Segoe UI", 10, "bold"))
        self.current_scale_label.pack(side="left", padx=(5, 0))
      
        # Instructions
        tk.Label(inner, 
                 text="Entrez la valeur d'échelle pour convertir les pixels en millimètres.\n"
                      "Exemple : 0.10 signifie que 1 pixel = 0.10 mm\n"
                      "Cette valeur sera utilisée pour toutes les conversions pixel → mm.",
                 bg=COLOR_CARD_BG, fg="#6b7280",
                 font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(5, 20))
     
        # Bouton de sauvegarde
        button_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
        button_frame.pack(fill="x", pady=(10, 0))
     
        ttk.Button(button_frame, text="💾 Sauvegarder toute la configuration",
                  style="Start.TButton",
                  command=self._save_all_calibration_settings).pack()
     
        # Mettre à jour le statut initial
        # self._update_calibration_status()
     
        # Mettre à jour l'affichage de l'échelle
        # self._update_current_scale_display()
    def _call_measure_app(self):
        if hasattr(self, 'calibration_process') and self.calibration_process.poll() is None:
            # Process is already running
            return
            
        import subprocess
        import threading
        import sys
        import os
        
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "modules", "app_calibrage_cam", "main.py")
        self.calibration_process = subprocess.Popen([sys.executable, script_path])
        
        def wait_and_update():
            self.calibration_process.wait()
            self.parent.after(0, update_params)
            
        def update_params():
            try:
                param = load_conversion_param()
                self.app.facteur_conversion.set(str(param))
            except Exception as e:
                pass

        threading.Thread(target=wait_and_update, daemon=True).start()
    
    def _update_calibration_status(self):
        """Met à jour l'affichage du statut des fichiers de calibration"""
        # camera_params.npz
        if self.app.mtx is not None and self.app.dist is not None:
            self.camera_params_status.config(text="✓ Chargé", fg="#10b981")
            self.undistort_check.config(state="normal")
        else:
            self.camera_params_status.config(text="✗ Non chargé", fg="#dc2626")
            self.undistort_check.config(state="disabled")
            self.app.use_undistortion_var.set(False)
        
        # homography.npz
        if self.app.homo_matrix is not None:
            self.homography_status.config(text="✓ Chargé", fg="#10b981")
            self.homography_check.config(state="normal")
        else:
            self.homography_status.config(text="✗ Non chargé", fg="#dc2626")
            self.homography_check.config(state="disabled")
            self.app.use_homography_var.set(False)
    
    def _reload_camera_params(self):
        """Recharge camera_params.npz"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            camera_params_path = os.path.join(current_dir, "camera_params.npz")
            
            if os.path.exists(camera_params_path):
                data = np.load(camera_params_path)
                self.app.mtx = data['mtx']
                self.app.dist = data['dist']
                self.app.use_undistortion_var.set(True)
                self._update_calibration_status()
                
                messagebox.showinfo("Succès", "Fichier camera_params.npz rechargé")
            else:
                messagebox.showerror("Erreur", f"Fichier introuvable: {camera_params_path}")
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur de rechargement : {str(e)}")
    
    def _reload_homography(self):
        """Recharge homography.npz"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            homography_path = os.path.join(current_dir, "homography.npz")
            
            if os.path.exists(homography_path):
                data = np.load(homography_path)
                self.app.homo_matrix = data["H"]
                self.app.use_homography_var.set(True)
                self._update_calibration_status()
                
                messagebox.showinfo("Succès", "Fichier homography.npz rechargé")
            else:
                messagebox.showerror("Erreur", f"Fichier introuvable: {homography_path}")
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur de rechargement : {str(e)}")
    
    def _update_undistort_status(self):
        """Met à jour le statut de l'undistortion"""
        if self.app.mtx is None or self.app.dist is None:
            self.app.use_undistortion_var.set(False)
            messagebox.showwarning("Attention", 
                                  "Impossible d'activer la correction de distorsion:\n"
                                  "Fichier camera_params.npz non chargé.")
    
    def _update_homography_status(self):
        """Met à jour le statut de l'homographie"""
        if self.app.homo_matrix is None:
            self.app.use_homography_var.set(False)
            messagebox.showwarning("Attention",
                                  "Impossible d'activer la correction d'homographie:\n"
                                  "Fichier homography.npz non chargé.")
    
    def _apply_calibration_scale(self):
        """Applique l'échelle de calibration"""
        try:
            scale = float(self.app.calibration_scale_var.get().replace(",", "."))
            if scale <= 0:
                raise ValueError("L'échelle doit être positive")
            
            self.app.scale_var.set(f"{scale:.4f}")
            self._update_current_scale_display()
            messagebox.showinfo("Succès", f"Échelle appliquée: {scale:.4f} mm/px")
            
        except ValueError as e:
            messagebox.showerror("Erreur", f"Erreur d'application: {str(e)}")
    
    def _update_current_scale_display(self):
        """Met à jour l'affichage de l'échelle actuelle"""
        self.current_scale_label.config(text=f"{self.app.scale_var.get()} mm/px")
    
    def _save_all_calibration_settings(self):
        """Sauvegarde tous les paramètres de calibration"""
        try:
            settings = {
                "scale": self.app.scale_var.get(),
                "use_undistortion": self.app.use_undistortion_var.get(),
                "use_homography": self.app.use_homography_var.get(),
                "calibration_files_loaded": {
                    "camera_params": self.app.mtx is not None,
                    "homography": self.app.homo_matrix is not None
                }
            }
            
            save_dir = os.path.join(os.path.expanduser("~"), "CIMES_Settings")
            os.makedirs(save_dir, exist_ok=True)
            
            settings_file = os.path.join(save_dir, "calibration_settings.json")
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("Succès", "Paramètres de calibration sauvegardés !")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur de sauvegarde : {str(e)}")
    
    def _create_analysis_settings(self):
        """Crée l'interface des paramètres d'analyse"""
        self.analysis_settings_frame = ttk.Frame(self.param_content_frame, style="Card.TFrame")
        create_setting_header(self.analysis_settings_frame, "Paramètres d'Analyse Granulométrique")

        inner = tk.Frame(self.analysis_settings_frame, bg=COLOR_CARD_BG, padx=20, pady=10)
        inner.pack(fill="both", expand=True)

        # Correction DNA
        tk.Label(inner, text="Correction DNA de la courbe granulométrique :", bg=COLOR_CARD_BG,
                 anchor="w", font=("Segoe UI", 11, "bold")).pack(fill="x", pady=(0, 10))
        
        corr_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
        corr_frame.pack(fill="x", pady=(5, 20))
        
        ttk.Checkbutton(corr_frame, text="Afficher la courbe corrigée (DNA)",
                       variable=self.app.show_corrected_curve_var,
                       command=self._update_curve_display).pack(anchor="w", pady=(0, 10))
        
        param_frame = tk.Frame(corr_frame, bg=COLOR_CARD_BG)
        param_frame.pack(fill="x", pady=(5, 0))
        
        tk.Label(param_frame, text="Paramètres de correction DNA :", bg=COLOR_CARD_BG,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        params_grid = tk.Frame(param_frame, bg=COLOR_CARD_BG)
        params_grid.pack(fill="x", pady=(0, 10))
        
        scale_frame = tk.Frame(params_grid, bg=COLOR_CARD_BG)
        scale_frame.pack(side="left", padx=(0, 20))
        
        tk.Label(scale_frame, text="Scale:", bg=COLOR_CARD_BG,
                 font=("Segoe UI", 10)).pack(side="left")
        tk.Label(scale_frame, text="0.823", bg=COLOR_CARD_BG,
                 font=("Segoe UI", 10, "bold"), fg=COLOR_ACCENT).pack(side="left", padx=(5, 0))
        
        offset_frame = tk.Frame(params_grid, bg=COLOR_CARD_BG)
        offset_frame.pack(side="left")
        
        tk.Label(offset_frame, text="Offset:", bg=COLOR_CARD_BG,
                 font=("Segoe UI", 10)).pack(side="left")
        tk.Label(offset_frame, text="8.5", bg=COLOR_CARD_BG,
                 font=("Segoe UI", 10, "bold"), fg=COLOR_ACCENT).pack(side="left", padx=(5, 0))
        
        tk.Label(corr_frame, 
                 text="La correction DNA applique une transformation linéaire\n"
                      "aux tailles de tamis pour améliorer la précision des mesures.",
                 bg=COLOR_CARD_BG, fg="#6b7280",
                 font=("Segoe UI", 9, "italic"), justify="left").pack(anchor="w", pady=(5, 0))

        # Segmentation Cellpose
        tk.Label(inner, text="Segmentation Cellpose :", bg=COLOR_CARD_BG,
                 anchor="w", font=("Segoe UI", 11, "bold")).pack(fill="x", pady=(10, 0))
        
        try:
            from cellpose import models
            cellpose_available = True
        except:
            cellpose_available = False
        
        cellpose_status = "INSTALLÉ" if cellpose_available else "NON INSTALLÉ"
        cellpose_color = "#10b981" if cellpose_available else "#dc2626"
        
        status_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
        status_frame.pack(fill="x", pady=(5, 0))
        
        tk.Label(status_frame, text="Statut: ", bg=COLOR_CARD_BG,
                 font=("Segoe UI", 10)).pack(side="left")
        tk.Label(status_frame, text=cellpose_status, bg=COLOR_CARD_BG,
                 fg=cellpose_color, font=("Segoe UI", 10, "bold")).pack(side="left", padx=(5, 0))
        
        if not cellpose_available:
            tk.Label(inner, text="Installez avec: pip install cellpose", 
                    bg=COLOR_CARD_BG, fg="#dc2626", font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(5, 10))
        
        # Paramètres de segmentation
        tk.Label(inner, text="Paramètres de segmentation :", bg=COLOR_CARD_BG,
                 anchor="w", font=("Segoe UI", 10, "bold")).pack(fill="x", pady=(10, 0))
        
        param_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
        param_frame.pack(fill="x", pady=(5, 20))
        
        tk.Label(param_frame, text="Diamètre estimé (px):", bg=COLOR_CARD_BG,
                 font=("Segoe UI", 10), width=20, anchor="w").pack(side="left")
        
        self.diameter_var = tk.StringVar(value="80")
        ttk.Entry(param_frame, textvariable=self.diameter_var, width=10,
                  font=("Segoe UI", 10)).pack(side="left")
        
        # Bouton d'application
        button_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(button_frame, text="Appliquer les paramètres",
                  style="Secondary.TButton",
                  command=self._apply_analysis_settings).pack()
    
    def _update_curve_display(self):
        """Met à jour l'affichage de la courbe"""
        if hasattr(self.app, 'curve_view') and self.app.curve_view.frame.winfo_ismapped():
            self.app.curve_view._update_curve_view()
            
        if self.app.capture_history and self.app.current_capture_index >= 0:
            capture = self.app.capture_history[self.app.current_capture_index]
            if len(capture.get('tamis_exp', [])) > 0:
                if hasattr(self.app, 'measure_view'):
                    self.app.measure_view._display_granulometric_curve(
                        capture['tamis_exp'], 
                        capture.get('cumulative_raw', []),
                        capture.get('cumulative_corrected', []) if self.app.show_corrected_curve_var.get() else None
                    )
    
    def _apply_analysis_settings(self):
        """Applique les paramètres d'analyse"""
        try:
            diameter = float(self.diameter_var.get())
            if diameter <= 0:
                raise ValueError("Le diamètre doit être positif")
            
            messagebox.showinfo("Succès", 
                              f"Paramètres d'analyse appliqués:\n"
                              f"- Diamètre Cellpose: {diameter} px\n"
                              f"- Correction DNA: {'Activée' if self.app.show_corrected_curve_var.get() else 'Désactivée'}")
            
        except ValueError as e:
            messagebox.showerror("Erreur", f"Paramètre invalide: {str(e)}")
    
    def _create_transmission_settings(self):
        """Crée l'interface des paramètres de transmission"""
        self.transmission_settings_frame = ttk.Frame(self.param_content_frame, style="Card.TFrame")
        create_setting_header(self.transmission_settings_frame,
                              "Transmission Programmé des Résultats")

        inner = tk.Frame(self.transmission_settings_frame, bg=COLOR_CARD_BG, padx=20, pady=10)
        inner.pack(fill="both", expand=True)

        # Activation de la transmission
        ttk.Checkbutton(
            inner,
            text="Activer la transmission des résultats",
            variable=self.app.transmission_enabled_var,
            command=self._toggle_transmission_settings
        ).pack(anchor="w", pady=(0, 20))

        self.transmission_params_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
        self.transmission_params_frame.pack(fill="x", pady=(0, 10))
        
        # Mode de transmission
        tk.Label(self.transmission_params_frame, text="Mode de transmission :",
                 bg=COLOR_CARD_BG, anchor="w",
                 font=("Segoe UI", 10, "bold")).pack(fill="x", pady=(0, 10))
        
        mode_frame = tk.Frame(self.transmission_params_frame, bg=COLOR_CARD_BG)
        mode_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Radiobutton(mode_frame, text="À chaque capture", value="capture",
                       variable=self.app.transmission_mode_var).pack(anchor="w", pady=(0, 5))
        
        ttk.Radiobutton(mode_frame, text="À la fin de journée", value="daily",
                       variable=self.app.transmission_mode_var).pack(anchor="w", pady=(0, 5))
        
        # Heure d'envoi
        self.time_transmission_frame = tk.Frame(self.transmission_params_frame, bg=COLOR_CARD_BG)
        self.time_transmission_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(self.time_transmission_frame, text="Heure d'envoi (fin de journée) :",
                 bg=COLOR_CARD_BG, anchor="w",
                 font=("Segoe UI", 10, "bold")).pack(fill="x", pady=(0, 5))
        
        time_frame = tk.Frame(self.time_transmission_frame, bg=COLOR_CARD_BG)
        time_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Entry(time_frame, textvariable=self.app.transmission_time_var, width=8,
                  font=("Segoe UI", 10)).pack(side="left")
        tk.Label(time_frame, text="(format HH:MM, ex: 18:00)",
                 bg=COLOR_CARD_BG, font=("Segoe UI", 9, "italic")).pack(side="left", padx=(10, 0))
        
        # Adresse Email
        tk.Label(self.transmission_params_frame, text="Adresse Email pour transmission :",
                 bg=COLOR_CARD_BG, anchor="w",
                 font=("Segoe UI", 10, "bold")).pack(fill="x", pady=(10, 0))
        
        ttk.Entry(self.transmission_params_frame, textvariable=self.app.transmission_email_var, width=40,
                  font=("Segoe UI", 10)).pack(fill="x", pady=(0, 20))
        
        # Correction DNA pour rapports
        ttk.Checkbutton(self.transmission_params_frame, 
                       text="Inclure la courbe corrigée DNA dans les rapports",
                       variable=self.app.show_corrected_curve_var).pack(anchor="w", pady=(0, 20))
        
        # Configuration du rapport PDF
        tk.Label(self.transmission_params_frame, text="Configuration du Rapport PDF :",
                 bg=COLOR_CARD_BG, anchor="w",
                 font=("Segoe UI", 11, "bold")).pack(fill="x", pady=(20, 10))
        
        # Options d'inclusion
        report_options_frame = tk.Frame(self.transmission_params_frame, bg=COLOR_CARD_BG)
        report_options_frame.pack(fill="x", pady=(0, 15))
        
        options_grid = tk.Frame(report_options_frame, bg=COLOR_CARD_BG)
        options_grid.pack(fill="x")
        
        # Colonne 1
        col1 = tk.Frame(options_grid, bg=COLOR_CARD_BG)
        col1.pack(side="left", fill="both", expand=True)
        
        ttk.Checkbutton(col1, text="✓ Image capturée",
                       variable=self.app.report_options["include_captured_image"]).pack(anchor="w", pady=2)
        ttk.Checkbutton(col1, text="✓ Image segmentée",
                       variable=self.app.report_options["include_segmented_image"]).pack(anchor="w", pady=2)
        ttk.Checkbutton(col1, text="✓ Courbe granulométrique",
                       variable=self.app.report_options["include_granulometric_curve"]).pack(anchor="w", pady=2)
        
        # Colonne 2
        col2 = tk.Frame(options_grid, bg=COLOR_CARD_BG)
        col2.pack(side="left", fill="both", expand=True, padx=(20, 0))
        
        ttk.Checkbutton(col2, text="✓ Courbe de distribution",
                       variable=self.app.report_options["include_distribution_curve"]).pack(anchor="w", pady=2)
        ttk.Checkbutton(col2, text="✓ Tableau statistique",
                       variable=self.app.report_options["include_statistics"]).pack(anchor="w", pady=2)
        
        # Pré-remplir avec la valeur existante
        if self.app.report_options["custom_comment"].get():
            self.comment_text.insert("1.0", self.app.report_options["custom_comment"].get())
        
        # Bouton de sauvegarde
        save_report_btn = ttk.Button(self.transmission_params_frame, 
                                   text="💾 Sauvegarder configuration rapport",
                                   style="Secondary.TButton",
                                   command=self._save_report_configuration)
        save_report_btn.pack(pady=(0, 10))
    
        self._toggle_transmission_settings()
        self.app.transmission_mode_var.trace_add("write", lambda *args: self._update_transmission_mode_display())
    
    def _toggle_transmission_settings(self):
        """Active/désactive les contrôles de transmission"""
        state = "normal" if self.app.transmission_enabled_var.get() else "disabled"
        
        for widget in self.transmission_params_frame.winfo_children():
            if isinstance(widget, (tk.Label, ttk.Entry, ttk.Combobox, ttk.Spinbox, ttk.Radiobutton, ttk.Checkbutton)):
                widget.configure(state=state)
    
    def _update_transmission_mode_display(self):
        """Met à jour l'affichage selon le mode de transmission"""
        mode = self.app.transmission_mode_var.get()
        
        if mode == "daily":
            self.time_transmission_frame.pack(fill="x", pady=(0, 15))
        else:
            self.time_transmission_frame.pack_forget()
    
    def _save_report_configuration(self):
        """Sauvegarde la configuration du rapport PDF"""
        # Récupérer le commentaire
        comment = self.comment_text.get("1.0", tk.END).strip()
        self.app.report_options["custom_comment"].set(comment)
        
        # Préparer les données
        report_config = {
            "include_captured_image": self.app.report_options["include_captured_image"].get(),
            "include_segmented_image": self.app.report_options["include_segmented_image"].get(),
            "include_granulometric_curve": self.app.report_options["include_granulometric_curve"].get(),
            "include_distribution_curve": self.app.report_options["include_distribution_curve"].get(),
            "include_statistics": self.app.report_options["include_statistics"].get(),
            "custom_comment": comment,
            "dna_correction_enabled": self.app.show_corrected_curve_var.get()
        }
        
        try:
            save_dir = os.path.join(os.path.expanduser("~"), "CIMES_Settings")
            os.makedirs(save_dir, exist_ok=True)
            
            config_file = os.path.join(save_dir, "report_configuration.json")
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(report_config, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("Succès", "Configuration du rapport sauvegardée avec succès !")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde : {str(e)}")