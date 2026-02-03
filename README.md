# Visualiseur CSV de mesures

Application graphique pour visualiser et analyser des fichiers CSV contenant des mesures.

## 📥 Téléchargement Windows

**Pas besoin d'installer Python !** Téléchargez simplement l'exécutable :

➡️ [**Télécharger VisualiseurCSV.exe**](https://github.com/YanChab/CourbeCsv/releases/latest/download/VisualiseurCSV.exe)

Double-cliquez sur le fichier pour lancer l'application.

## Fonctionnalités

- **Chargement de fichiers CSV** : Supporte les séparateurs `,` et `;` ainsi que les décimales avec `.` ou `,` (format français)
- **Visualisation de données** : Graphiques interactifs avec Matplotlib
- **Sélection d'axes** : Choix des colonnes pour les axes X et Y
- **Zoom interactif** : Clic gauche + glisser pour zoomer, clic droit pour réinitialiser la vue
- **Sélection de plage** : Cliquez sur les points pour sélectionner une plage de données (début/fin)
- **Filtre passe-bas Butterworth** : Application d'un filtre avec fréquence de coupure configurable
- **Export CSV** : Export des données sélectionnées, avec option de filtrage

## Installation (développeurs)

Installer les dépendances :

```bash
pip install -r requirements.txt
```

## Lancement

```bash
python3 main.py
```

## Utilisation

1. Cliquez sur **Charger CSV** pour ouvrir un fichier
2. Sélectionnez les colonnes X et Y dans les menus déroulants
3. Le graphique s'affiche automatiquement
4. Utilisez le **zoom** (clic gauche + glisser) pour explorer les données
5. Appliquez un **filtre** en entrant une fréquence de coupure et en cliquant sur "Appliquer filtre"
6. **Exportez** les données sélectionnées avec le bouton "Exporter CSV"

## Dépendances

- Python 3.9+
- pandas
- numpy
- scipy
- matplotlib
- tkinter (inclus avec Python)

