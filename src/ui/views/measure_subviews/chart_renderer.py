"""
Rendu graphique : affichage de la courbe granulométrique et des images.
"""

from io import BytesIO
import cv2  # pylint: disable=no-member
import numpy as np
from PIL import Image, ImageTk

import matplotlib

matplotlib.use("Agg")
# pylint: disable=wrong-import-position
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
# pylint: enable=wrong-import-position


class ChartRenderer:
    """
    Mixin pour MeasureView — rendu des courbes et images dans les labels.
    """
    # pylint: disable=no-member,attribute-defined-outside-init,too-few-public-methods
    def _update_display_label(self, label, frame, attribute_name):
        """Affiche un frame numpy dans un label tkinter en conservant les proportions."""
        try:
            if frame is None:
                label.config(image="", text="Image non disponible")
                return
            if frame.ndim == 3 and frame.shape[2] == 3:
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            elif frame.ndim == 3:
                cv2image = frame
            else:
                cv2image = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            pil_img = Image.fromarray(cv2image)
            container = label.image_container
            cw = container.winfo_width()
            ch = container.winfo_height()
            if cw > 10 and ch > 10:
                ratio = min(cw / pil_img.width, ch / pil_img.height)
                resized_img = pil_img.resize(
                    (int(pil_img.width * ratio), int(pil_img.height * ratio)),
                    Image.Resampling.LANCZOS,
                )
                tk_img = ImageTk.PhotoImage(resized_img)
                setattr(self, attribute_name, tk_img)
                label.config(image=tk_img, text="")
                label.image = tk_img
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Erreur affichage: {e}")
            label.config(image="", text=f"Erreur d'affichage\n({str(e)[:40]}...)")

    def _display_granulometric_curve(
        self, tamis_exp, cumulative_raw, cumulative_corrected=None
    ):
        """Dessine la courbe granulométrique et l'affiche dans self.curve_label."""
        # pylint: disable=too-many-locals,too-many-statements,broad-exception-caught
        diameters_vss = [0, 22.4, 31.5, 40, 50, 63, 100]
        cum_fraction_vss = [0, 4, 26, 70, 99, 99, 100]
        diameters_vsi = [0, 22.4, 31.5, 40, 50, 50, 50]
        cum_fraction_vsi = [0, 0, 0, 25, 70, 70, 70]
        if not tamis_exp or not cumulative_raw:
            self.curve_label.config(
                image="", text="Aucune donnée disponible\npour la granulométrie"
            )
            return
        try:
            fig = Figure(figsize=(16, 8), dpi=100, facecolor="#f5f5f5")
            ax = fig.add_subplot(111, facecolor="white")
            tamis_sizes = list(tamis_exp)
            cumul_raw = list(cumulative_raw)
            cumul_corrected = (
                list(cumulative_corrected) if cumulative_corrected else None
            )
            ax.plot(
                diameters_vss,
                cum_fraction_vss,
                color="#10b981",
                linewidth=5,
                linestyle="--",
                alpha=0.8,
                label="Courbe VSS (Référence)",
                marker="^",
                markersize=4,
                markerfacecolor="white",
                markeredgewidth=4,
                markeredgecolor="#10b981",
            )
            ax.plot(
                diameters_vsi,
                cum_fraction_vsi,
                color="#f59e0b",
                linewidth=5,
                linestyle="--",
                alpha=0.8,
                label="Courbe VSI (Référence)",
                marker="s",
                markersize=4,
                markerfacecolor="white",
                markeredgewidth=4,
                markeredgecolor="#f59e0b",
            )
            if (
                cumul_corrected
                and len(cumul_corrected) == len(tamis_sizes)
                and self.app.show_corrected_curve_var.get()
            ):
                ax.plot(
                    tamis_sizes,
                    cumul_corrected,
                    marker="s",
                    color="#dc2626",
                    linewidth=5,
                    label="Courbe corrigée (DNA)",
                    markerfacecolor="white",
                    markeredgewidth=4,
                    markeredgecolor="#dc2626",
                )

            ax.set_xlabel(
                "Taille du tamis (mm)", fontsize=22, fontweight="bold", color="#1f2937"
            )
            ax.set_xlim([0, 80])
            ax.set_xticks([0, 22.4, 31.5, 40, 50, 63, 80])
            ax.set_xticklabels(
                ["0", "22.4", "31.5", "40", "50", "63", "80"],
                fontsize=22,
                fontweight="bold",
                color="#374151",
            )
            ax.set_ylabel(
                "% passant cumulé", fontsize=22, fontweight="bold", color="#1f2937"
            )
            ax.set_ylim([0, 105])
            ax.set_yticks(np.arange(0, 101, 10))
            ax.set_yticklabels(
                [f"{int(y)}%" for y in np.arange(0, 101, 10)],
                fontsize=22,
                color="#374151",
            )
            ax.grid(
                True,
                which="major",
                linestyle="--",
                linewidth=0.7,
                color="#9ca3af",
            )
            ax.grid(
                True,
                which="minor",
                linestyle=":",
                linewidth=0.5,
                color="#d1d5db",
            )
            ax.minorticks_on()
            for spine in ax.spines.values():
                spine.set_linewidth(1.5)
                spine.set_color("#4b5563")
            ax.legend(
                loc="upper left",
                fontsize=20,
                framealpha=0.9,
                facecolor="white",
                edgecolor="#d1d5db",
                frameon=True,
                shadow=True,
            )
            for x, y in zip(tamis_sizes, cumul_raw):
                ax.annotate(
                    f"{y:.1f}%",
                    xy=(x, y),
                    xytext=(0, 8),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=16,
                    fontweight="bold",
                    color="#1e40af",
                    bbox={
                        "boxstyle": "round,pad=0.4",
                        "facecolor": "white",
                        "edgecolor": "#93c5fd",
                        "alpha": 0.9,
                    },
                )
            if cumul_corrected and self.app.show_corrected_curve_var.get():
                for x, y in zip(tamis_sizes, cumul_corrected):
                    ax.annotate(
                        f"{y:.1f}%",
                        xy=(x, y),
                        xytext=(0, -12),
                        textcoords="offset points",
                        ha="center",
                        va="top",
                        fontsize=16,
                        fontweight="bold",
                        color="#991b1b",
                        bbox={
                            "boxstyle": "round,pad=0.4",
                            "facecolor": "white",
                            "edgecolor": "#fca5a5",
                            "alpha": 0.9,
                        },
                    )
            info_text = f"Captures analysées: {self.app.captured_count}"
            ax.text(
                0.02,
                0.98,
                info_text,
                transform=ax.transAxes,
                fontsize=9,
                verticalalignment="top",
                bbox={
                    "boxstyle": "round",
                    "facecolor": "#fef3c7",
                    "edgecolor": "#f59e0b",
                    "alpha": 0.8,
                },
            )
            fig.tight_layout(pad=3.0)
            buf = BytesIO()
            fig.savefig(
                buf,
                format="png",
                bbox_inches="tight",
                pad_inches=0.3,
                dpi=100,
                facecolor=fig.get_facecolor(),
            )
            buf.seek(0)
            pil_img = Image.open(buf)
            container = self.curve_label.image_container
            cw = max(100, container.winfo_width())
            ch = max(100, container.winfo_height())
            ratio = min(cw / pil_img.width, ch / pil_img.height)
            resized_img = pil_img.resize(
                (int(pil_img.width * ratio), int(pil_img.height * ratio)),
                Image.Resampling.LANCZOS,
            )
            tk_img = ImageTk.PhotoImage(resized_img)
            self.curve_tk_img = tk_img
            self.curve_label.config(image=tk_img, text="")
            self.curve_label.image = tk_img
            plt.close(fig)
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Erreur création courbe: {e}")
            self.curve_label.config(
                image="", text=f"Erreur lors du tracé de la courbe\n({str(e)[:50]}...)"
            )
