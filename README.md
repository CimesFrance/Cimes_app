# CIMES - Analyse Granulométrique par Vision Artificielle

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8-green)
![Framework](https://img.shields.io/badge/Framework-Tkinter-orange)

## 📋 Présentation

**CIMES** (Captation et Imagerie pour la Mesure et l'Évaluation des Solides) est une application professionnelle de **granulométrie par vision artificielle**. Elle permet d'analyser en temps réel ou de manière différée la distribution de taille des particules à partir d'un flux vidéo (caméra IP/RTSP) ou d'images enregistrées.

Le logiciel utilise des algorithmes d'apprentissage profond (Deep Learning) via **Cellpose** pour segmenter les particules avec une précision exceptionnelle, même dans des conditions de superposition ou de textures complexes.

---

## ✨ Fonctionnalités Clés

*   **Flux Vidéo Temps Réel :** Connexion stable aux flux RTSP avec gestion des tampons pour une latence minimale.
*   **Segmentation Avancée :** Intégration de modèles Cellpose (compatible GPU) pour une détection précise des contours.
*   **Analyse Morphologique :** Calcul automatique des axes majeurs/mineurs, aires et périmètres via scikit-image.
*   **Correction Empirique :** Système de correction ADN (empirique) pour ajuster les mesures aux standards physiques.
*   **Visualisation Dynamique :** Courbes granulométriques interactives (passant et distribution) mises à jour en direct.
*   **Gestion de l'Historique :** Rechargement et comparaison de sessions de mesure passées.
*   **Rapports PDF Professionnels :** Génération automatique de rapports complets incluant statistiques, images segmentées et courbes.
*   **Calibration Caméra :** Outils intégrés pour la correction de distorsion et la transformation d'homographie (conversion mm/pixel).

---

## 🏗️ Architecture du Projet

Le projet suit une structure modulaire pour faciliter la maintenance et l'évolution :

```text
Cimes_app/
├── main.py              # Point d'entrée de l'application
├── requirements.txt     # Dépendances du projet
├── assets/              # Logos, icônes et fichiers de calibration (.npz)
├── src/
│   ├── core/            # Moteurs de calcul (segmentation, stats, granulométrie)
│   ├── ui/              # Interface graphique (Tkinter)
│   │   ├── views/       # Vues principales (Mesure, Courbe, Paramètres, etc.)
│   │   ├── widgets/     # Composants UI réutilisables et utilitaires
│   │   └── app_init/    # Logique d'initialisation et variables d'état
│   └── utils/           # Gestion des fichiers, config et logs
└── modules/             # Sous-applications et outils externes
```

---

## 🚀 Installation

### Prérequis
- Python 3.10 ou supérieur
- Une carte graphique NVIDIA (recommandé pour la segmentation par GPU)
- Pilotes CUDA installés (si utilisation GPU)

### Procédure

1.  **Cloner le dépôt :**
    ```bash
    git clone https://github.com/CimesFrance/Cimes_app.git
    cd Cimes_app
    ```

2.  **Créer un environnement virtuel :**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # ou
    venv\Scripts\activate     # Windows
    ```

3.  **Installer les dépendances :**
    ```bash
    pip install -r requirements.txt
    ```

---

## 🛠️ Utilisation

Pour lancer l'application :

```bash
python main.py
```

1.  **Configuration :** Allez dans l'onglet **Paramètres** pour configurer l'URL RTSP de votre caméra et les chemins de sauvegarde.
2.  **Calibration :** Assurez-vous d'importer vos fichiers de calibration (`.npz`) pour obtenir des mesures précises en millimètres.
3.  **Mesure :** Dans l'onglet **Mesure**, lancez le flux et utilisez le mode automatique ou manuel pour capturer et analyser les images.
4.  **Rapports :** Une fois les mesures effectuées, générez un rapport PDF depuis la vue des courbes.

---

## 🧪 Technologies Utilisées

*   **Interface :** Tkinter (Python Standard Library)
*   **Traitement d'Image :** OpenCV, PIL, Scikit-Image
*   **IA / Segmentation :** Cellpose (Deep Learning)
*   **Analyse de Données :** Pandas, NumPy
*   **Visualisation :** Matplotlib
*   **Reporting :** ReportLab

---

## 📝 Auteurs & Licence

Développé par l'équipe **Cimes France**.
Tous droits réservés.
