# -*- coding: utf-8 -*-
import os
import tkinter as tk
from tkinter import ttk

COLOR_BG_DARK = "#191D35"
COLOR_ACCENT = "#F76F00"
COLOR_TEXT_LIGHT = "white"
COLOR_FRAME_BG ="#191D35"
COLOR_CARD_BG = "white"
COLOR_STATUS_RUNNING = "#10b981"
COLOR_STATUS_STOPPED = "#dc2626"
COLOR_READONLY_BG = "#DCDDE0"
COLOR_STAT_GOOD = "#10b981"
COLOR_STAT_WARN = "#f59e0b"
COLOR_STAT_BAD = "#ef4444"

# Racine du projet
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# On cherche le logo dans assets
LOGO_PATH = os.path.join(proj_root, "assets", "logo.png")
if not os.path.exists(LOGO_PATH):
    # Fallback vers un chemin courant ou celui par défaut si le fichier n'existe pas
    LOGO_PATH = r"C:\Users\Arezki.boukhalfa\Desktop\logo.png"

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
    style.configure("Nav.TButton", font=("Segoe UI", 11, "bold"), padding=(20, 8),
                    background=COLOR_BG_DARK, foreground=COLOR_TEXT_LIGHT, relief="flat")
    style.configure("NavActive.TButton", font=("Segoe UI", 11, "bold"), padding=(20, 8),
                    background=COLOR_ACCENT, foreground=COLOR_TEXT_LIGHT, relief="flat")
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
    style.configure("ParamNav.TButton", font=("Segoe UI", 10, "normal"),
                    padding=(10, 8), background=COLOR_BG_DARK,
                    foreground=COLOR_TEXT_LIGHT, relief="flat")
    style.configure("ParamNavActive.TButton", font=("Segoe UI", 10, "bold"),
                    padding=(10, 8), background=COLOR_ACCENT,
                    foreground=COLOR_TEXT_LIGHT, relief="flat")
    
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

    widget = tk.Label(card, text=title, bg="#e5e7eb",
                      anchor="w", padx=10, font=("Segoe UI", 11, "bold"))
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
    tk.Label(parent, text=title, bg="#e5e7eb",
             anchor="w", font=("Segoe UI", 11, "bold"),
             padx=10, pady=5).pack(fill="x")