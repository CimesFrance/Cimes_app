# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime
from tkinter import messagebox

def load_sensor_settings(app):
    """Charge les paramètres du capteur"""
    try:
        current_scale = app.scale_var.get()
        if "B" in str(current_scale) or "," in str(current_scale) or current_scale == "1,728B":
            app.scale_var.set("0.10")
            app.calibration_scale_var.set("0.10")
    
        settings_file = os.path.join(os.path.expanduser("~"), "CIMES_Settings", "sensor_settings.json")
    
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        
            file_scale = settings.get("scale", "0.10")
            if isinstance(file_scale, str) and ("B" in file_scale or file_scale == "1,728B"):
                file_scale = "0.10"
        
            # Mettre à jour les variables d'échelle
            app.scale_var.set(file_scale)
            app.calibration_scale_var.set(file_scale)
        
            # Charger les autres paramètres
            app.url_var.set(settings.get("url", app.url_var.get()))
            app.results_path_var.set(settings.get("results_path", app.results_path_var.get()))
            app.start_time_var.set(settings.get("start_time", app.start_time_var.get()))
            app.end_time_var.set(settings.get("end_time", app.end_time_var.get()))
            app.show_corrected_curve_var.set(settings.get("dna_correction_enabled", True))
            app.capture_mode_var.set(settings.get("capture_mode", "automatique"))
         
            days_active = settings.get("days_active", {})
            for day, var in app.days_vars.items():
                var.set(days_active.get(day, var.get()))
         
            interval = settings.get("capture_interval", {})
            app.capture_time_val_var.set(interval.get("value", app.capture_time_val_var.get()))
            app.capture_time_unit_var.set(interval.get("unit", app.capture_time_unit_var.get()))
         
            # Mettre à jour l'affichage
            if hasattr(app, 'measure_view'):
                app.measure_view.update_active_params_display()
        
        else:
            # Valeurs par défaut
            app.scale_var.set("0.10")
            app.calibration_scale_var.set("0.10")
            app.show_corrected_curve_var.set(True)
            app.capture_mode_var.set("automatique")
            
    except Exception as e:
        messagebox.showwarning("Paramètres Capteur", f"Erreur lors du chargement des paramètres du capteur (valeurs par défaut appliquées).\n\nDétails : {e}")
        # Valeurs par défaut en cas d'erreur
        app.scale_var.set("0.10")
        app.calibration_scale_var.set("0.10")
        app.show_corrected_curve_var.set(True)
        app.capture_mode_var.set("automatique")

def load_report_configuration(app):
    """Charge la configuration du rapport PDF"""
    try:
        config_file = os.path.join(os.path.expanduser("~"), "CIMES_Settings", "report_configuration.json")
        
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Appliquer les configurations
            app.report_options["include_captured_image"].set(config.get("include_captured_image", True))
            app.report_options["include_segmented_image"].set(config.get("include_segmented_image", True))
            app.report_options["include_granulometric_curve"].set(config.get("include_granulometric_curve", True))
            app.report_options["include_distribution_curve"].set(config.get("include_distribution_curve", True))
            app.report_options["include_statistics"].set(config.get("include_statistics", True))
            app.show_corrected_curve_var.set(config.get("dna_correction_enabled", True))
            
            # Mettre à jour le commentaire
            if "custom_comment" in config:
                app.report_options["custom_comment"].set(config.get("custom_comment", ""))
                
    except Exception as e:
        messagebox.showwarning("Configuration Rapport", f"Erreur lors du chargement de la configuration du rapport.\n\nDétails : {e}")

def save_configuration(app, config_type="all"):
    """Sauvegarde la configuration selon le type"""
    try:
        save_dir = os.path.join(os.path.expanduser("~"), "CIMES_Settings")
        os.makedirs(save_dir, exist_ok=True)
        
        if config_type in ["sensor", "all"]:
            # Sauvegarder les paramètres du capteur
            sensor_settings = {
                "url": app.url_var.get(),
                "results_path": app.results_path_var.get(),
                "start_time": app.start_time_var.get(),
                "end_time": app.end_time_var.get(),
                "days_active": {day: var.get() for day, var in app.days_vars.items()},
                "capture_interval": {
                    "value": app.capture_time_val_var.get(),
                    "unit": app.capture_time_unit_var.get()
                },
                "capture_mode": app.capture_mode_var.get(),
                "scale": app.scale_var.get(),
                "dna_correction_enabled": app.show_corrected_curve_var.get()
            }
            
            sensor_file = os.path.join(save_dir, "sensor_settings.json")
            with open(sensor_file, 'w', encoding='utf-8') as f:
                json.dump(sensor_settings, f, indent=4, ensure_ascii=False)
        
        if config_type in ["report", "all"]:
            # Sauvegarder la configuration du rapport
            report_config = {
                "include_captured_image": app.report_options["include_captured_image"].get(),
                "include_segmented_image": app.report_options["include_segmented_image"].get(),
                "include_granulometric_curve": app.report_options["include_granulometric_curve"].get(),
                "include_distribution_curve": app.report_options["include_distribution_curve"].get(),
                "include_statistics": app.report_options["include_statistics"].get(),
                "custom_comment": app.report_options["custom_comment"].get(),
                "dna_correction_enabled": app.show_corrected_curve_var.get()
            }
            
            report_file = os.path.join(save_dir, "report_configuration.json")
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_config, f, indent=4, ensure_ascii=False)
        
        if config_type in ["calibration", "all"]:
            # Sauvegarder les paramètres de calibration
            calibration_settings = {
                "scale": app.scale_var.get(),
                "use_undistortion": app.use_undistortion_var.get(),
                "use_homography": app.use_homography_var.get(),
                "calibration_files_loaded": {
                    "camera_params": app.mtx is not None,
                    "homography": app.homo_matrix is not None
                },
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            calibration_file = os.path.join(save_dir, "calibration_settings.json")
            with open(calibration_file, 'w', encoding='utf-8') as f:
                json.dump(calibration_settings, f, indent=4, ensure_ascii=False)
        
        # print(f"[CONFIG] Configuration sauvegardée: {config_type}")
        return True
        
    except Exception as e:
        messagebox.showerror("Erreur Sauvegarde", f"Échec de la sauvegarde de la configuration : {config_type}\n\nDétails : {e}")
        return False

def load_calibration_settings(app):
    """Charge les paramètres de calibration"""
    try:
        calibration_file = os.path.join(os.path.expanduser("~"), "CIMES_Settings", "calibration_settings.json")
        
        if os.path.exists(calibration_file):
            with open(calibration_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # Appliquer les paramètres de calibration
            scale = settings.get("scale", "0.10")
            if isinstance(scale, str) and ("B" in scale or scale == "1,728B"):
                scale = "0.10"
            
            app.scale_var.set(scale)
            app.calibration_scale_var.set(scale)
            app.use_undistortion_var.set(settings.get("use_undistortion", False))
            app.use_homography_var.set(settings.get("use_homography", False))
            
    except Exception as e:
        messagebox.showwarning("Calibration Settings", f"Erreur lors du chargement des paramètres de calibration.\n\nDétails : {e}")
