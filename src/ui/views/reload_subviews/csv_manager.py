# -*- coding: utf-8 -*-
"""
Gestionnaire des courbes CSV : chargement, affichage, suppression, export.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import pandas as pd
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.ui.widgets.ui_utils import (
    COLOR_CARD_BG, COLOR_STAT_BAD
)


class CsvManager:
    """
    Mixin pour ReloadView — gère les courbes CSV et l'affichage de la courbe granulométrique.
    """

    def _load_csv_curve(self):
        """Charge une courbe de tamisage depuis un fichier CSV/Excel."""
        file_path = filedialog.askopenfilename(
            parent=self.frame,
            title="Sélectionner un fichier de courbe granulométrique",
            filetypes=[
                ("Fichiers Excel", "*.xlsx *.xls"),
                ("Fichiers CSV",   "*.csv"),
                ("Fichiers texte", "*.txt"),
                ("Tous les fichiers", "*.*"),
            ]
        )
        if not file_path:
            return

        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in [".xlsx", ".xls"]:
                df = pd.read_excel(file_path, decimal=",")
            else:
                try:
                    df = pd.read_csv(file_path, sep=";", decimal=",", encoding="utf-8")
                except Exception:
                    try:
                        df = pd.read_csv(file_path, sep=",", decimal=".", encoding="utf-8")
                    except Exception:
                        df = pd.read_csv(file_path, encoding="utf-8")

            if df.empty:
                messagebox.showerror("Erreur", "Le fichier est vide ou ne contient pas de données.")
                return

            column_names = [str(col).lower().strip() for col in df.columns]
            diameter_col = cumulative_col = None

            for idx, col_name in enumerate(column_names):
                if any(k in col_name for k in ["diamètre", "diametre", "diameter", "tamis", "size", "mm", "granulo"]):
                    diameter_col = df.columns[idx]
                    break

            for idx, col_name in enumerate(column_names):
                if any(k in col_name for k in ["cumulatif", "cumulative", "passant", "pourcentage", "%", "cumul"]):
                    cumulative_col = df.columns[idx]
                    break

            if diameter_col is None and len(df.columns) >= 1:
                diameter_col = df.columns[0]
            if cumulative_col is None and len(df.columns) >= 2:
                cumulative_col = df.columns[1]

            if diameter_col is None or cumulative_col is None:
                messagebox.showerror(
                    "Format non reconnu",
                    f"Impossible d'identifier les colonnes de diamètre et pourcentage.\n"
                    f"Colonnes disponibles: {df.columns.tolist()}"
                )
                return

            def to_float(series):
                return series.astype(str).str.replace(",", ".").astype(float, errors="ignore")

            diameters   = pd.to_numeric(to_float(df[diameter_col]),   errors="coerce").dropna().values
            cumulatives = pd.to_numeric(to_float(df[cumulative_col]), errors="coerce").dropna().values

            if len(diameters) == 0 or len(cumulatives) == 0:
                messagebox.showerror("Données manquantes", "Aucune donnée numérique valide trouvée.")
                return

            n = min(len(diameters), len(cumulatives))
            diameters   = diameters[:n]
            cumulatives = cumulatives[:n]

            sorted_idx  = np.argsort(diameters)
            diameters   = diameters[sorted_idx]
            cumulatives = cumulatives[sorted_idx]

            if diameters[0] > 0:
                diameters   = np.insert(diameters,   0, 0)
                cumulatives = np.insert(cumulatives, 0, 0)
            if cumulatives[-1] < 100 and diameters[-1] > 0:
                diameters   = np.append(diameters,   diameters[-1] * 1.5)
                cumulatives = np.append(cumulatives, 100)

            curve_name = os.path.basename(file_path)
            if len(curve_name) > 20:
                curve_name = curve_name[:17] + "..."

            self.csv_curves.append(np.column_stack((diameters, cumulatives)))
            self.csv_curve_names.append(curve_name)
            self._update_csv_curves_list()

            if self.current_reload_capture:
                self._show_loaded_curve(self.current_reload_capture)

            messagebox.showinfo(
                "Succès",
                f"✅ Courbe chargée avec succès !\n\n"
                f"📁 Fichier: {curve_name}\n"
                f"📊 Points: {len(diameters)}"
            )
            return True

        except Exception as e:
            messagebox.showerror(
                "Erreur de chargement",
                f"❌ Impossible de charger le fichier.\n⚠️ Erreur: {str(e)}"
            )
            return False

    def _clear_all_csv_curves(self):
        if not self.csv_curves:
            messagebox.showinfo("Information", "Aucune courbe CSV à supprimer.")
            return
        if messagebox.askyesno(
            "Confirmation",
            f"Voulez-vous vraiment supprimer toutes les {len(self.csv_curves)} courbes CSV ?"
        ):
            self.csv_curves.clear()
            self.csv_curve_names.clear()
            self._update_csv_curves_list()
            if self.current_reload_capture:
                self._show_loaded_curve(self.current_reload_capture)
            messagebox.showinfo("Succès", "Toutes les courbes CSV ont été supprimées.")

    def _update_csv_curves_list(self):
        for widget in self.csv_list_container.winfo_children():
            widget.destroy()

        if not self.csv_curves:
            self.csv_status_label.config(text="Aucune courbe CSV chargée")
            return

        self.csv_status_label.config(text=f"{len(self.csv_curves)} courbe(s) CSV chargée(s) :")

        for idx, (curve_data, curve_name) in enumerate(zip(self.csv_curves, self.csv_curve_names)):
            curve_frame = tk.Frame(self.csv_list_container, bg=COLOR_CARD_BG)
            curve_frame.pack(fill="x", pady=2)

            tk.Label(curve_frame, text=f"{curve_name} ({len(curve_data)} points)",
                     bg=COLOR_CARD_BG, font=("Segoe UI", 9), anchor="w").pack(side="left", padx=(5, 0))

            tk.Button(curve_frame, text="✕", font=("Segoe UI", 8, "bold"),
                      bg=COLOR_STAT_BAD, fg="white", width=2, height=1,
                      command=lambda i=idx: self._remove_csv_curve(i)).pack(side="right", padx=(5, 0))

    def _remove_csv_curve(self, index):
        if 0 <= index < len(self.csv_curves):
            self.csv_curves.pop(index)
            self.csv_curve_names.pop(index)
            self._update_csv_curves_list()
            if self.current_reload_capture:
                self._show_loaded_curve(self.current_reload_capture)
            messagebox.showinfo("Succès", "Courbe supprimée.")

    def _show_loaded_curve(self, capture_data):
        """Affiche la courbe granulométrique avec les courbes CSV superposées."""
        for widget in self.reload_curve_frame.winfo_children():
            widget.destroy()

        if not capture_data.get("tamis_exp") or not capture_data.get("cumulative_raw"):
            tk.Label(self.reload_curve_frame,
                     text="Aucune donnée granulométrique disponible",
                     bg=COLOR_CARD_BG, fg="#666", font=("Segoe UI", 12)).pack(expand=True)
            return

        try:
            fig = Figure(figsize=(18, 9), dpi=100, facecolor="#f5f5f5")
            ax  = fig.add_subplot(111, facecolor="white")

            ax.plot([0, 22.4, 31.5, 40, 50, 63, 100],
                    [0, 4, 26, 70, 99, 99, 100],
                    "g--", linewidth=2, alpha=0.7, label="VSS")
            ax.plot([0, 22.4, 31.5, 40, 50, 50, 50],
                    [0, 0, 0, 25, 70, 70, 70],
                    color="orange", linestyle="--", linewidth=2, alpha=0.7, label="VSI")

            tamis = capture_data["tamis_exp"]
            cumul = capture_data["cumulative_raw"]
            cumul_corr = capture_data["cumulative_corrected"]

            ax.plot(tamis, cumul, "b-o", linewidth=2, markersize=6,
                    label="Courbe numérique", zorder=5)
            ax.plot(tamis, cumul_corr, "o-", color="brown", linewidth=2, markersize=6,
                    label="Courbe numérique corrigée", zorder=5)

            colors = ["red", "purple", "brown", "pink", "gray", "olive", "cyan"]
            for idx, (csv_data, cname) in enumerate(zip(self.csv_curves, self.csv_curve_names)):
                if len(csv_data) >= 2:
                    ax.plot(csv_data[:, 0], csv_data[:, 1],
                            color=colors[idx % len(colors)],
                            linestyle="-", linewidth=2, marker="s", markersize=4,
                            alpha=0.8, label=f"CSV: {cname}")

            max_tamis = max(max(tamis), 80) if tamis else 80
            for csv_data in self.csv_curves:
                if len(csv_data) >= 2 and len(csv_data[:, 0]) > 0:
                    max_tamis = max(max_tamis, max(csv_data[:, 0]))

            ax.set_xlabel("Taille du tamis (mm)", fontsize=12, fontweight="bold")
            ax.set_ylabel("% passant cumulé", fontsize=12, fontweight="bold")
            ax.set_title("Courbe Granulométrique", fontsize=14, fontweight="bold")
            ax.set_xlim([0, max_tamis + 10])
            ax.set_ylim([0, 105])
            ax.set_yticks(np.arange(0, 101, 10))
            ax.grid(True, alpha=0.3, linestyle="--")
            ax.legend(loc="upper left", fontsize=10)
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=self.reload_curve_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

            export_frame = tk.Frame(self.reload_curve_frame, bg=COLOR_CARD_BG)
            export_frame.pack(fill="x", pady=(10, 0))

            ttk.Button(export_frame, text="💾 Sauvegarder cette courbe",
                       style="Secondary.TButton",
                       command=lambda: self._save_reload_curve(fig)).pack(side="left")
            ttk.Button(export_frame, text="📊 Exporter toutes les données",
                       style="Secondary.TButton",
                       command=lambda: self._export_all_curves_data(capture_data)).pack(
                           side="left", padx=(10, 0))

        except Exception as e:
            tk.Label(self.reload_curve_frame,
                     text=f"Erreur lors de l'affichage de la courbe:\n{str(e)}",
                     bg=COLOR_CARD_BG, fg=COLOR_STAT_BAD,
                     font=("Segoe UI", 10)).pack(expand=True)
            print(f"Erreur affichage courbe: {e}")

    def _save_reload_curve(self, fig):
        file_path = filedialog.asksaveasfilename(
            parent=self.frame, defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Sauvegarder la courbe granulométrique"
        )
        if file_path:
            try:
                fig.savefig(file_path, dpi=300, bbox_inches="tight")
                messagebox.showinfo("Succès", f"Courbe sauvegardée : {file_path}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur de sauvegarde : {str(e)}")

    def _export_all_curves_data(self, capture_data):
        if not self.csv_curves and not capture_data.get("tamis_exp"):
            messagebox.showwarning("Avertissement", "Aucune donnée à exporter.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Fichiers Excel", "*.xlsx"), ("Fichiers CSV", "*.csv"),
                       ("Tous les fichiers", "*.*")],
            title="Exporter toutes les données de courbes"
        )
        if not file_path:
            return

        try:
            data_frames = {}
            if capture_data.get("tamis_exp"):
                data_frames["Courbe_Numerique"] = pd.DataFrame({
                    "Diametre_mm":           capture_data["tamis_exp"],
                    "Pourcentage_Cumulatif": capture_data["cumulative_raw"],
                })
            for idx, (csv_data, cname) in enumerate(zip(self.csv_curves, self.csv_curve_names)):
                sheet_name = f"CSV_{idx+1}_{cname[:25]}"
                sheet_name = "".join(c for c in sheet_name if c.isalnum() or c in " _")
                data_frames[sheet_name] = pd.DataFrame({
                    "Diametre_mm":           csv_data[:, 0],
                    "Pourcentage_Cumulatif": csv_data[:, 1],
                })

            if file_path.endswith(".xlsx"):
                with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                    for sheet_name, df in data_frames.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
            else:
                first = list(data_frames.keys())[0]
                data_frames[first].to_csv(file_path, index=False)

            messagebox.showinfo("Succès", f"Données exportées avec succès : {file_path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'export : {str(e)}")
