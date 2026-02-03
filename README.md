# Visualiseur CSV de mesures

Application graphique pour visualiser et analyser des fichiers CSV contenant des mesures.

## Fonctionnalités

- **Chargement de fichiers CSV** : Supporte les séparateurs `,` et `;` ainsi que les décimales avec `.` ou `,` (format français)
- **Visualisation de données** : Graphiques interactifs avec Matplotlib
- **Sélection d'axes** : Choix des colonnes pour les axes X et Y
- **Zoom interactif** : Clic gauche + glisser pour zoomer, clic droit pour réinitialiser la vue
- **Sélection de plage** : Cliquez sur les points pour sélectionner une plage de données (début/fin)
- **Filtre passe-bas Butterworth** : Application d'un filtre avec fréquence de coupure configurable
- **Export CSV** : Export des données sélectionnées, avec option de filtrage

## Installation

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

## Docker

### Prérequis

L'application utilise une interface graphique (Tkinter). Pour l'afficher depuis Docker, vous devez configurer le forwarding X11.

#### macOS

1. Installer XQuartz :
```bash
brew install --cask xquartz
```

2. Ouvrir XQuartz, aller dans Préférences > Sécurité et cocher "Autoriser les connexions depuis les clients réseau"

3. Redémarrer XQuartz

4. Lancer l'application :
```bash
chmod +x run-docker-mac.sh
./run-docker-mac.sh
```

#### Linux

```bash
xhost +local:docker
docker-compose up --build
```

#### Windows

1. Installer VcXsrv ou Xming
2. Lancer le serveur X avec "Disable access control"
3. Définir `DISPLAY=host.docker.internal:0` et lancer :
```bash
docker-compose up --build
```

### Fichiers CSV

Placez vos fichiers CSV dans le dossier `data/` pour y accéder depuis le conteneur.

