# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw
from datetime import datetime
import time
import cv2
import numpy as np
import threading
import json
import os
import warnings
warnings.filterwarnings('ignore')

from gui.widgets.camera_widget import VideoStream
from gui.widgets.utils import (
    COLOR_BG_DARK, COLOR_ACCENT, COLOR_TEXT_LIGHT,
    COLOR_FRAME_BG, COLOR_CARD_BG, COLOR_STATUS_RUNNING,
    COLOR_STATUS_STOPPED, COLOR_READONLY_BG,
    COLOR_STAT_GOOD, COLOR_STAT_WARN, COLOR_STAT_BAD,
    LOGO_PATH, configure_styles, creer_dossier
)
from gui.views.measure_view import MeasureView
from gui.views.curve_view import CurveView
from gui.views.reload_view import ReloadView
from gui.views.param_view import ParamView
from utils.file_manager import load_calibration_files, ensure_results_directory,load_correction_parameters,save_correction_parameters,load_conversion_param,save_conversion_parameter
from utils.config_manager import load_sensor_settings, load_report_configuration, load_calibration_settings

from modules.app_change_corr_params.main import CIMESApp

class CimesApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Configuration de base
        self.geometry("1600x1000")
        self.minsize(1400, 800)
        self.configure(bg=COLOR_FRAME_BG)
        self.title("CIMES - Analyse granulométrique")
       
        
        # Configurer les styles
        configure_styles(self)
        
        # Variables principales
        self._initialize_variables()
        
        # Initialiser les vues
        self._initialize_views()

        # Configuration initiale
        self._setup_initial_configuration()

        # Démarrer les mises à jour automatiques
        self._start_auto_updates()
        
        # Gérer la fermeture de l'application
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
    def _on_closing(self):
        """Méthode appelée lors de la fermeture de la fenêtre principale"""
        # Fermer le process de correction s'il est en cours
        if hasattr(self, 'correction_process') and self.correction_process.poll() is None:
            try:
                self.correction_process.terminate()
            except Exception:
                pass
        
        # Fermer le process de calibration s'il est en cours
        if hasattr(self, 'param_view') and hasattr(self.param_view, 'calibration_process'):
            if self.param_view.calibration_process.poll() is None:
                try:
                    self.param_view.calibration_process.terminate()
                except Exception:
                    pass
                    
        # Détruire la fenêtre principale
        self.destroy()
    
    def _initialize_variables(self):
        """Initialise toutes les variables de l'application"""
        # État de la caméra
        self.camera_running = False
        self.video_stream = None
        self._after_id = None
        self._countdown_id = None
        self.frame_index = 0
        self.captured_count = 0
        self.last_capture_time = time.time()
        
        # Variables d'état
        self.status_color_var = tk.StringVar(value=COLOR_STATUS_STOPPED)
        self.status_var = tk.StringVar(value="ARRÊTÉE")
        self.last_capture_time_var = tk.StringVar(value="N/A")
        self.datetime_var = tk.StringVar()
        self.images_count_var = tk.StringVar(value="0")
        self.status_detail_var = tk.StringVar(value="(Hors-ligne)")
        
        # Paramètres du capteur
        self.url_var = tk.StringVar(value="rtsp://192.168.1.30:554/stream1")
        self.save_path_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "CIMES_Data"))
        self.start_time_var = tk.StringVar(value="08:00")
        self.end_time_var = tk.StringVar(value="18:00")
        self.capture_time_val_var = tk.StringVar(value="5")
        self.capture_time_unit_var = tk.StringVar(value="s")
        self.save_delay_display_var = tk.StringVar(value="5 s")
        self.scale_var = tk.StringVar(value="1,0")
        
        # Statistiques
        self.time_left_capture_var = tk.StringVar(value="--")
        self.particles_count_var = tk.StringVar(value="0")
        self.last_captured_frame = None
        
        # Jours de fonctionnement
        self.days_vars = {
            "Lundi": tk.BooleanVar(value=True),
            "Mardi": tk.BooleanVar(value=True),
            "Mercredi": tk.BooleanVar(value=True),
            "Jeudi": tk.BooleanVar(value=True),
            "Vendredi": tk.BooleanVar(value=True),
            "Samedi": tk.BooleanVar(value=False),
            "Dimanche": tk.BooleanVar(value=False)
        }
        
        # Mode de capture
        self.capture_mode_var = tk.StringVar(value="automatique")
        
        # Transmission
        self.transmission_enabled_var = tk.BooleanVar(value=False)
        self.transmission_mode_var = tk.StringVar(value="capture")
        self.transmission_time_var = tk.StringVar(value="17:00")
        self.transmission_email_var = tk.StringVar(value="")
        
        # Chemins
        self.results_path_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "CIMES_Results"))
        
        # Comparaison et rapports
        self.comparison_captures = []
        self.comparison_mode = False
        self.selected_captures_for_report = []
        
        self.report_logo_path = LOGO_PATH
        self.report_commentary = tk.StringVar(value="")
        self.show_corrected_curve_var = tk.BooleanVar(value=True)
        
        # Données
        self.daily_data = []
        self.capture_history = []
        self.current_capture_index = -1
        
        # Calibration
        self.use_undistortion_var = tk.BooleanVar(value=False)
        self.use_homography_var = tk.BooleanVar(value=False)
        self.mtx = None
        self.dist = None
        self.calib_path = None
        self.homo_matrix = None
        
        self.calibration_scale_var = tk.StringVar(value="0.10")
        
        # Navigation
        self.nav_buttons = {}
        
        # Options du rapport
        self.report_options = {
            "include_captured_image": tk.BooleanVar(value=True),
            "include_segmented_image": tk.BooleanVar(value=True),
            "include_granulometric_curve": tk.BooleanVar(value=True),
            "include_distribution_curve": tk.BooleanVar(value=True),
            "include_statistics": tk.BooleanVar(value=True),
            "custom_comment": tk.StringVar(value="")
        }

        #Correction empirique:
        vars = load_correction_parameters()
        self.correction_granulo = {'scale' : tk.DoubleVar(value=vars["scale"]) , 'offset' : tk.DoubleVar(value=vars["offset"])}

        #Conversion mm-pixel
        param = load_conversion_param()
        self.facteur_conversion = tk.StringVar(value=str(param)) 




            
    def _initialize_views(self):
        """Initialise toutes les vues de l'application"""
        # Créer l'en-tête
        self._create_header()
        
        # Créer le conteneur principal
        self.content_frame = tk.Frame(self, bg=COLOR_FRAME_BG)
        self.content_frame.pack(side="top", fill="both", expand=True)
        
        # Créer les vues (mais ne pas les afficher encore)
        self.measure_view = MeasureView(self.content_frame, self)
        self.curve_view = CurveView(self.content_frame, self)
        self.reload_view = ReloadView(self.content_frame, self)
        self.param_view = ParamView(self.content_frame, self)
        
        # Afficher la vue par défaut
        self.show_measure_view()
        self._set_active_nav("measure")
    
    def _create_header(self):
        """Crée l'en-tête de l'application avec logo et navigation"""
        header = tk.Frame(self, bg=COLOR_BG_DARK, height=150)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)
        
        # Logo
        try:
            img = Image.open(LOGO_PATH)
            logo_height = 150
            ratio = img.width / img.height if img.height > 0 else 1
            logo_width = int(logo_height * ratio)
            logo_img = img.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            self.logo_header = ImageTk.PhotoImage(logo_img)
            tk.Label(header, image=self.logo_header, bg=COLOR_BG_DARK).pack(side="left", padx=(20, 5), pady=5)
        except Exception:
            tk.Label(header, text="CIMES", bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT,
                     font=("Segoe UI", 30, "bold")).pack(side="left", padx=(20, 5), pady=5)
        
        # Navigation
        nav_frame = tk.Frame(header, bg=COLOR_BG_DARK)
        nav_frame.pack(side="right", padx=20)
        
        self.nav_buttons["measure"] = ttk.Button(nav_frame, text="Mesure",
                                                 style="Nav.TButton",
                                                 command=lambda: self._on_nav_clicked("measure"))
        self.nav_buttons["measure"].pack(side="left", padx=5)
        
        self.nav_buttons["curve"] = ttk.Button(nav_frame, text="Courbe",
                                               style="Nav.TButton",
                                               command=lambda: self._on_nav_clicked("curve"))
        self.nav_buttons["curve"].pack(side="left", padx=5)
        
        self.nav_buttons["reload"] = ttk.Button(nav_frame, text="Recharger",
                                               style="Nav.TButton",
                                               command=lambda: self._on_nav_clicked("reload"))
        self.nav_buttons["reload"].pack(side="left", padx=5)
        
        self.nav_buttons["param"] = ttk.Button(nav_frame, text="Paramètres",
                                               style="Nav.TButton",
                                               command=lambda: self._on_nav_clicked("param"))
        self.nav_buttons["param"].pack(side="left", padx=5)
        self.change_corr_btn = ttk.Button(nav_frame, text="Modifier correction",
                                               style="Nav.TButton",
                                               command=lambda: self._change_correction())
        self.change_corr_btn.pack(side="left", padx=5)
    
    def _change_correction(self):
        if hasattr(self, 'correction_process') and self.correction_process.poll() is None:
            # Process is already running
            return
            
        import subprocess
        import threading
        import sys
        import os
        
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "modules", "app_change_corr_params", "main.py")
        self.correction_process = subprocess.Popen([sys.executable, script_path])
        
        def wait_and_update():
            self.correction_process.wait()
            self.after(0, update_params)
            
        def update_params():
            try:
                vars = load_correction_parameters()
                self.correction_granulo["scale"].set(vars["scale"])
                self.correction_granulo["offset"].set(vars["offset"])
            except Exception as e:
                pass
                
        threading.Thread(target=wait_and_update, daemon=True).start()
    
    def _setup_initial_configuration(self):
        """Configure l'application au démarrage"""

        # Mettre à jour l'horloge
        self._update_clock()
        
        # Charger les paramètres
        self._load_initial_settings()

        # Charger les fichiers de calibration
        self._load_calibration_files_automatically()
        
        # Créer le dossier de résultats
        ensure_results_directory(self.results_path_var.get())
        
        # Mettre à jour l'affichage
        self._update_active_params_display()
        self._update_save_delay_display()
    
    def _load_initial_settings(self):
        """Charge les paramètres initiaux"""
        load_sensor_settings(self)
        self.scale_var.set(1.0)
        load_report_configuration(self)
        load_calibration_settings(self)
    
    def _load_calibration_files_automatically(self):
        """Charge automatiquement les fichiers de calibration"""
        self.mtx, self.dist, self.calib_path = load_calibration_files()
        
        # Activer automatiquement si les fichiers sont chargés
        if self.mtx is not None:
            self.use_undistortion_var.set(True)
        if self.homo_matrix is not None:
            self.use_homography_var.set(True)
    
    def _start_auto_updates(self):
        """Démarre les mises à jour automatiques"""
        # Mettre à jour l'horloge chaque seconde
        self.after(1000, self._update_clock)
        
        # Suivre les changements de variables
        self.url_var.trace_add("write", lambda *args: self._update_active_params_display())
        self.capture_time_val_var.trace_add("write", lambda *args: self._update_active_params_display())
        self.capture_time_unit_var.trace_add("write", lambda *args: self._update_save_delay_display())
        self.results_path_var.trace_add("write", lambda *args: self._update_active_params_display())
        self.start_time_var.trace_add("write", lambda *args: self._update_active_params_display())
        self.end_time_var.trace_add("write", lambda *args: self._update_active_params_display())
        self.capture_mode_var.trace_add("write", lambda *args: self._on_capture_mode_changed())
        self.scale_var.trace_add("write", lambda *args: self._on_scale_changed())
    
    def _update_clock(self):
        """Met à jour l'horloge"""
        current_datetime = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        self.datetime_var.set(current_datetime)
        self.after(1000, self._update_clock)
    
    def _update_active_params_display(self):
        """Met à jour l'affichage des paramètres actifs"""
        if hasattr(self, 'measure_view'):
            self.measure_view.update_active_params_display()
    
    def _update_save_delay_display(self):
        """Met à jour l'affichage du délai de sauvegarde"""
        mode = self.capture_mode_var.get()
        if mode == "automatique":
            self.save_delay_display_var.set(f"{self.capture_time_val_var.get()} {self.capture_time_unit_var.get()}")
        else:
            self.save_delay_display_var.set("Manuel")
        self._update_active_params_display()
    
    def _on_capture_mode_changed(self):
        """Gère le changement de mode de capture"""
        self._update_active_params_display()
        if hasattr(self, 'param_view'):
            self.param_view._toggle_capture_controls()
    
    def _on_scale_changed(self):
        """Gère le changement d'échelle"""
        try:
            print("apperçu rapide :")
            print(self.scale_var.get())
            scale_value = float(self.scale_var.get().replace(",", "."))
            if scale_value <= 0:
                return
            self._update_active_params_display()
            if hasattr(self, 'curve_view') and self.curve_view.frame.winfo_ismapped():
                self.curve_view._update_curve_view()
        except ValueError:
            pass
    
    # Méthodes de navigation
    def _set_active_nav(self, key):
        """Met en surbrillance le bouton de navigation actif"""
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(style="NavActive.TButton")
            else:
                btn.configure(style="Nav.TButton")
    
    def _on_nav_clicked(self, key):
        """Gère le clic sur un bouton de navigation"""
        if key == "measure":
            self.show_measure_view()
        elif key == "curve":
            self.show_curve_view()
            if hasattr(self, 'curve_view'):
                self.curve_view._update_curve_view()
        elif key == "reload":
            self.show_reload_view()
        elif key == "param":
            self.show_param_view()
        self._set_active_nav(key)
    
    def _raise_view(self, view):
        """Affiche une vue et cache les autres"""
        # Liste de toutes les vues
        views = [
            getattr(self, "measure_view", None),
            getattr(self, "curve_view", None),
            getattr(self, "reload_view", None),
            getattr(self, "param_view", None)
        ]
        
        # Cacher toutes les vues
        for v in views:
            if v and hasattr(v, 'frame'):
                v.frame.pack_forget()
        
        # Afficher la vue demandée
        if view and hasattr(view, 'frame'):
            view.frame.pack(fill="both", expand=True)
    
    def show_measure_view(self):
        """Affiche la vue Mesure"""
        self._raise_view(self.measure_view)
    
    def show_curve_view(self):
        """Affiche la vue Courbe"""
        self._raise_view(self.curve_view)
    
    def show_reload_view(self):
        """Affiche la vue Recharger"""
        self._raise_view(self.reload_view)
    
    def show_param_view(self):
        """Affiche la vue Paramètres"""
        self._raise_view(self.param_view)
    
    # Méthodes de contrôle de la caméra
    def start_camera(self):
        """Démarre la caméra"""
        if self.camera_running:
            return

        rtsp_url = self.url_var.get()
        if not rtsp_url or "N/A" in rtsp_url or "configurer" in rtsp_url:
            from tkinter import messagebox
            messagebox.showerror("Erreur", "URL de caméra non configurée.")
            return

        mode = self.capture_mode_var.get()
        if mode == "automatique" and not self._is_within_operating_hours():
            from tkinter import messagebox
            messagebox.showwarning("Hors plage horaire", 
                                 "Le système est actuellement hors des heures de fonctionnement configurées.\n"
                                 f"Heures actives : {self.start_time_var.get()} - {self.end_time_var.get()}")
            return

        if self.video_stream:
            self.video_stream.stop()
            self.video_stream = None

        self.video_stream = VideoStream(rtsp_url)
        if self.video_stream.start():
            self.camera_running = True
            self._update_camera_status_ui(True)
            self._start_live_feed()
            self.last_capture_time = time.time()
            self.last_capture_time_var.set("En cours...")
            
            if mode == "manuel":
                if hasattr(self, 'measure_view'):
                    self.measure_view.manual_capture_btn.pack(side="left", fill="x", expand=True, padx=(10, 0))
            else:
                if hasattr(self, 'measure_view'):
                    self.measure_view.manual_capture_btn.pack_forget()
            
            if mode == "automatique":
                self._start_countdown()
        else:
            self.camera_running = False
            self._update_camera_status_ui(False)
            from tkinter import messagebox
            messagebox.showerror("Erreur", f"Impossible de se connecter à : {rtsp_url}")
    
    def stop_camera(self):
        """Arrête la caméra"""
        from tkinter import messagebox
        
        confirmation = messagebox.askyesno(
            "Confirmation",
            "Voulez-vous vraiment arrêter la caméra ?"
        )
    
        if not confirmation:
            return
    
        if not self.camera_running:
            return

        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None

        if self._countdown_id:
            self.after_cancel(self._countdown_id)
            self._countdown_id = None

        if self.video_stream:
            self.video_stream.stop()
            self.video_stream = None

        self.camera_running = False
        self.last_captured_frame = None
        self._update_camera_status_ui(False)
        self.time_left_capture_var.set("--")
        
        if hasattr(self, 'measure_view'):
            self.measure_view.manual_capture_btn.pack_forget()
    
    def _update_camera_status_ui(self, is_running):
        """Met à jour l'interface selon l'état de la caméra"""
        if hasattr(self, 'measure_view'):
            self.measure_view.update_camera_status_ui(is_running)
    
    def _start_live_feed(self):
        """Démarre la mise à jour du flux vidéo"""
        def update():
            if self.video_stream and self.video_stream.running:
                frame = self.video_stream.get_frame()
                if frame is not None and hasattr(self, 'measure_view'):
                    self.measure_view.update_live_feed(frame)
                
                if self.capture_mode_var.get() == "manuel" and self.camera_running:
                    pass
                
                self._after_id = self.after(30, update)
            else:
                if self._after_id:
                    self.after_cancel(self._after_id)
                    self._after_id = None
                self.last_captured_frame = None
                if hasattr(self, 'measure_view') and self.measure_view.live_label:
                    self.measure_view.live_label.config(image='',
                                                      text="Flux caméra (Hors-ligne)\nConfigurer dans Paramètres.")
        
        update()
    
    def _start_countdown(self):
        """Démarre le compte à rebours pour les captures automatiques"""
        def update():
            mode = self.capture_mode_var.get()
            
            if not self.camera_running:
                if self._countdown_id:
                    self.after_cancel(self._countdown_id)
                    self._countdown_id = None
                self.time_left_capture_var.set("--")
                return
            
            if mode == "manuel":
                self.time_left_capture_var.set("Mode manuel")
                if self._countdown_id:
                    self.after_cancel(self._countdown_id)
                    self._countdown_id = None
                return

            delay_seconds = self._get_capture_delay_seconds()
            if delay_seconds <= 0:
                self.time_left_capture_var.set("Immédiat")
                if hasattr(self, 'measure_view') and not self.measure_view.is_segmenting:
                    self.measure_view._perform_capture()
                self._countdown_id = self.after(1000, update)
                return

            time_elapsed = time.time() - self.last_capture_time
            time_left = delay_seconds - time_elapsed
      
            if time_left <= 0 and hasattr(self, 'measure_view') and not self.measure_view.is_segmenting:
                self.measure_view._perform_capture()
                self.last_capture_time = time.time()
            elif hasattr(self, 'measure_view') and self.measure_view.is_segmenting:
                self.time_left_capture_var.set(f"Capture en cours...")
            else:
                # print("self.last_capture_time = ",self.last_capture_time)
                self.time_left_capture_var.set(f"{max(0, int(time_left) + 1)} s")

            self._countdown_id = self.after(1000, update)
        
        update()
    
    def _get_capture_delay_seconds(self):
        """Calcule le délai de capture en secondes"""
        mode = self.capture_mode_var.get()
        if mode == "manuel":
            return 0
        
        try:
            val = float(self.capture_time_val_var.get().replace(",", "."))
            unit = self.capture_time_unit_var.get()
            if unit == "s":
                return val
            elif unit == "min":
                return val * 60
            elif unit == "h":
                return val * 3600
            return 0
        except ValueError:
            return 0
    
    def _is_within_operating_hours(self):
        """Vérifie si l'heure actuelle est dans les heures de fonctionnement"""
        try:
            now = datetime.now()
            day_name = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
            current_day = day_name[now.weekday()]
            
            if not self.days_vars[current_day].get():
                return False
            
            start_time = datetime.strptime(self.start_time_var.get(), "%H:%M").time()
            end_time = datetime.strptime(self.end_time_var.get(), "%H:%M").time()
            current_time = now.time()
            
            return start_time <= current_time <= end_time
            
        except Exception as e:
            return True