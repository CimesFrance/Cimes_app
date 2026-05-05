# -*- coding: utf-8 -*-
import os
import tkinter as tk
from tkinter import ttk

COLOR_BG_DARK = "#2C3E50"
COLOR_NAV_HOVER = "#34495E"
COLOR_ACCENT = "#F76F00"
COLOR_TEXT_LIGHT = "white"
COLOR_FRAME_BG ="#2C3E50"
COLOR_CARD_BG = "white"
COLOR_STATUS_RUNNING = "#10b981"
COLOR_STATUS_STOPPED = "#dc2626"
COLOR_READONLY_BG = "#DCDDE0"
COLOR_STAT_GOOD = "#10b981"
COLOR_STAT_WARN = "#f59e0b"
COLOR_STAT_BAD = "#ef4444"

from PIL import Image, ImageTk

# Racine du projet
from src.utils.file_manager import get_project_root
proj_root = get_project_root()
# On cherche le logo dans assets
LOGO_PATH = os.path.join(proj_root, "assets", "logo.png")
if not os.path.exists(LOGO_PATH):
    # Fallback vers un chemin courant ou celui par défaut si le fichier n'existe pas
    LOGO_PATH = r"C:\Users\Arezki.boukhalfa\Desktop\logo.png"

def load_icon(name, size=(24, 24)):
    """Charge et redimensionne une icône depuis le dossier assets."""
    icon_path = os.path.join(proj_root, "assets", name)
    try:
        if os.path.exists(icon_path):
            img = Image.open(icon_path)
            img = img.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        else:
            raise FileNotFoundError(f"Fichier non trouvé: {icon_path}")
    except Exception as e:
        print(f"Erreur lors du chargement de l'icône {name}: {e}")
        # Retourner un carré de couleur unie comme placeholder
        placeholder = Image.new("RGBA", size, color=(200, 200, 200, 100))
        return ImageTk.PhotoImage(placeholder)

def creer_dossier(path):
    os.makedirs(path, exist_ok=True)
    return path

def configure_styles(root):
    """Configure tous les styles tkinter"""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except:
        pass

    # Style pour les boutons de navigation
    style.configure("Nav.TButton", font=("Segoe UI", 10, "bold"), padding=(15, 5),
                    background=COLOR_BG_DARK, foreground="white", relief="flat")
    style.map("Nav.TButton",
              background=[("active", COLOR_NAV_HOVER), ("pressed", COLOR_NAV_HOVER)],
              foreground=[("active", "white"), ("pressed", "white")],
              relief=[("pressed", "flat")])

    # Utilisation d'un style spécifique pour l'état actif
    style.configure("NavActive.TButton", font=("Segoe UI", 10, "bold"), padding=(15, 5),
                    background=COLOR_BG_DARK, foreground="white", relief="flat")
    style.map("NavActive.TButton",
              background=[("active", COLOR_NAV_HOVER), ("pressed", COLOR_NAV_HOVER)],
              foreground=[("active", "white"), ("pressed", "white")],
              relief=[("pressed", "flat")])
    style.configure("Secondary.TButton", font=("Segoe UI", 10), padding=(10, 5),
                    background="#e5e5e5", relief="flat")

    # Style pour les boutons Start/Stop
    style.configure("Start.TButton", font=("Segoe UI", 12, "bold"),
                    background=COLOR_STATUS_RUNNING, foreground=COLOR_TEXT_LIGHT,
                    padding=(15, 10), relief="flat")
    style.map("Start.TButton",
              background=[('active', COLOR_STATUS_RUNNING), ('disabled', '#4b5563')],
              foreground=[('disabled', '#f3f4f6')])

    style.configure("Stop.TButton", font=("Segoe UI", 12, "bold"),
                    background=COLOR_STATUS_STOPPED, foreground=COLOR_TEXT_LIGHT,
                    padding=(15, 10), relief="flat")
    style.map("Stop.TButton",
              background=[('active', COLOR_STATUS_STOPPED), ('disabled', '#4b5563')],
              foreground=[('disabled', '#f3f4f6')])

    # Style pour les cartes
    style.configure("Card.TFrame", background=COLOR_CARD_BG, borderwidth=0)
    
    # Style pour la navigation des paramètres
    style.configure("ParamNav.TButton", font=("Segoe UI", 10, "bold"),
                    padding=(15, 10), background=COLOR_CARD_BG,
                    foreground="#4b5563", relief="flat", anchor="w")
    style.map("ParamNav.TButton",
              background=[("active", "#f3f4f6"), ("pressed", "#f3f4f6")],
              foreground=[("active", "#111827")])
    
    style.configure("ParamNavActive.TButton", font=("Segoe UI", 10, "bold"),
                    padding=(15, 10), background="#fff7ed",
                    foreground=COLOR_ACCENT, relief="flat", anchor="w")
    style.map("ParamNavActive.TButton",
              background=[("active", "#fff7ed"), ("pressed", "#fff7ed")],
              foreground=[("active", COLOR_ACCENT)])
    
    # Style pour les actions des paramètres (Parcourir, Appliquer, etc.)
    style.configure("ParamAction.TButton", font=("Segoe UI", 10, "bold"),
                    padding=(15, 6), background=COLOR_ACCENT,
                    foreground="white", relief="flat")
    style.map("ParamAction.TButton",
              background=[("active", "#d95f00"), ("pressed", "#d95f00")])
              
    # Style pour les boutons de sauvegarde des paramètres
    style.configure("ParamSave.TButton", font=("Segoe UI", 10, "bold"),
                    padding=(15, 6), background=COLOR_BG_DARK,
                    foreground="white", relief="flat")
    style.map("ParamSave.TButton",
              background=[("active", COLOR_NAV_HOVER), ("pressed", COLOR_NAV_HOVER)])

    # Style pour les petits boutons
    style.configure("SmallSecondary.TButton", font=("Segoe UI", 9), padding=(6, 4),
                    background="#e5e5e5", relief="flat")

def create_display_card(parent, title, row, col, padx_tuple, default_text=None):
    """Crée une carte d'affichage standard"""
    card = ttk.Frame(parent, style="Card.TFrame")
    default_text = default_text if default_text is not None else "En attente de flux..."
    pady_tuple = (5, 5)
    if row == 0:
        pady_tuple = (0, 5)
    elif row == 1:
        pady_tuple = (5, 0)

    card.grid(row=row, column=col, sticky="nsew", padx=padx_tuple, pady=pady_tuple)

    widget = tk.Label(card, text=title, bg="#e5e7eb", fg=COLOR_ACCENT,
                      anchor="w", padx=10, font=("Segoe UI", 11, "bold"), pady=5)
    widget.pack(fill="x")

    image_container = tk.Frame(card, bg="#f9fafb", padx=10, pady=10)
    image_container.pack(fill="both", expand=True)
    image_container.pack_propagate(False)

    label = tk.Label(image_container, bg="#f9fafb", text=default_text,
                     fg="#4b5563", font=("Segoe UI", 10))
    label.pack(expand=True)
    label.image_container = image_container

    return card

def display_read_only_param(parent, label_text, value, value_color=None):
    """Affiche un paramètre en lecture seule"""
    row = tk.Frame(parent, bg=COLOR_CARD_BG)
    row.pack(fill="x", pady=2)

    tk.Label(row, text=label_text, bg=COLOR_CARD_BG, font=("Segoe UI", 10),
             width=15, anchor="w").pack(side="left")

    color = value_color if value_color else "#1f2937"
    tk.Label(row, text=value, bg=COLOR_READONLY_BG, fg=color,
             font=("Segoe UI", 10, "bold"), padx=5, pady=2,
             anchor="w").pack(side="left", fill="x", expand=True)
    
    return row

def create_setting_header(parent, title):
    """Crée un en-tête pour les sections de paramètres"""
    header_frame = tk.Frame(parent, bg=COLOR_CARD_BG)
    header_frame.pack(fill="x")
    tk.Label(header_frame, text=title, bg=COLOR_CARD_BG, fg="#111827",
             anchor="w", font=("Segoe UI", 16, "bold"),
             padx=30, pady=10).pack(fill="x", pady=(10, 0))
    ttk.Separator(header_frame, orient="horizontal").pack(fill="x", padx=30)
