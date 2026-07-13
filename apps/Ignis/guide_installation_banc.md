# GSIE-Feu — Guide d'installation du banc de simulation
## Adapté à ta machine : HP i5-11300H (4c/8t), 32 Go RAM, RTX 3050 4 Go, Windows 11 + WSL2

> Version 1.0.0 — 2026-07-12
> Objectif de ce guide : à la fin, tu auras (A) un feu ForeFire qui se propage sur le relief corse, et (B) un drone PX4 simulé qui vole dans Gazebo — les deux briques fondatrices du banc.
> Durée estimée : 1h30-2h en tout (dont téléchargements). Chaque étape a un point de contrôle ✅.

---

## Étape 0 — Préparer le terrain (15 min)

### 0.1 Libérer et organiser l'espace disque
Ton C: n'a que ~87 Go libres et WSL2 y met son disque virtuel par défaut. On déplace tout sur E: (291 Go libres).

Ouvre **PowerShell en administrateur** :

```powershell
# Vérifier l'état actuel de WSL
wsl --version
wsl -l -v
```

Si une distribution Ubuntu existe déjà et que tu veux la garder, on la déplacera. Sinon (ou si la liste est vide), on installe proprement sur E: directement :

```powershell
# Créer le dossier d'accueil sur E:
mkdir E:\WSL\Ubuntu-24.04

# Installer Ubuntu 24.04 (la version de référence du projet)
wsl --install -d Ubuntu-24.04
```

Au premier lancement, choisis ton nom d'utilisateur/mot de passe Linux. Puis, toujours en PowerShell admin, **déplacement sur E:** :

```powershell
# Arrêter WSL
wsl --shutdown

# Exporter la distribution
wsl --export Ubuntu-24.04 E:\WSL\ubuntu2404.tar

# La désenregistrer de C:
wsl --unregister Ubuntu-24.04

# La réimporter depuis E: (le disque virtuel vivra ici)
wsl --import Ubuntu-24.04 E:\WSL\Ubuntu-24.04 E:\WSL\ubuntu2404.tar --version 2

# Nettoyer l'archive
del E:\WSL\ubuntu2404.tar
```

⚠️ Après un `--import`, WSL démarre en root par défaut. Pour rétablir ton utilisateur :

```powershell
# Remplace "camille" par ton nom d'utilisateur Linux choisi
ubuntu2404 config --default-user camille 2>$null
# Si la commande ci-dessus n'existe pas, méthode universelle :
wsl -d Ubuntu-24.04 -u root bash -c "printf '[user]\ndefault=camille\n' > /etc/wsl.conf"
wsl --shutdown
```

### 0.2 Limiter la RAM de WSL (important avec 32 Go)
Par défaut WSL peut manger jusqu'à 50 % de la RAM. On lui donne un budget clair : crée le fichier `C:\Users\camil\.wslconfig` (Bloc-notes) :

```ini
[wsl2]
memory=20GB
processors=6
swap=8GB
```

6 processeurs logiques sur tes 8 : Windows garde de quoi respirer. Puis `wsl --shutdown` pour appliquer.

### 0.3 Hygiène de session simulation
- **Désactive Smart Game Booster** (et tout "optimiseur") pendant les sessions : ces outils tuent des processus d'arrière-plan et peuvent casser Docker/WSL.
- Branche le PC sur secteur, mode d'alimentation « Performances ».

✅ **Contrôle** : `wsl -l -v` affiche `Ubuntu-24.04  Running/Stopped  2`, et dans WSL `free -h` affiche ~20 Go de RAM totale.

---

## Étape 1 — Socle logiciel dans WSL (15 min)

Ouvre Ubuntu (menu Démarrer → Ubuntu 24.04) :

```bash
# Mise à jour
sudo apt update && sudo apt upgrade -y

# Outils de base + compilation + Python
sudo apt install -y build-essential cmake git curl wget unzip \
    python3 python3-pip python3-venv \
    libnetcdf-dev libnetcdf-c++4-dev

# Environnement virtuel Python du projet (on ne pollue pas le système)
mkdir -p ~/gsie-feu && cd ~/gsie-feu
python3 -m venv .venv
echo 'source ~/gsie-feu/.venv/bin/activate' >> ~/.bashrc
source .venv/bin/activate
pip install --upgrade pip
```

✅ **Contrôle** : `cmake --version` (≥3.22), `python --version` (3.12), le prompt affiche `(.venv)`.

---

## Étape 2 — ForeFire : ton premier feu simulé (30 min)

### 2.1 Compilation

```bash
cd ~/gsie-feu
git clone https://github.com/forefireAPI/forefire.git
cd forefire

# Compilation (le -j4 exploite tes 4 cœurs)
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j4

# Rendre l'exécutable accessible partout
echo 'export PATH=$PATH:~/gsie-feu/forefire/build/bin' >> ~/.bashrc
source ~/.bashrc
```

*(Si la compilation échoue sur une dépendance, le dépôt fournit une image Docker de secours — voir §2.4. Mais la compilation native est préférable : plus simple pour nos futurs développements.)*

### 2.2 Lancer la démo Aullène (Corse)

Le dépôt inclut des cas de test, dont un feu réel corse :

```bash
cd ~/gsie-feu/forefire/examples/aullene
forefire -i aullene.ff
```

Le fichier `.ff` est un script : il charge le paysage (NetCDF : relief + combustible), définit le point d'ignition, le vent, et fait avancer la simulation par pas de temps en sauvegardant les contours du front.

### 2.3 Visualiser ton feu

```bash
pip install matplotlib numpy netcdf4 geojson
```

Les sorties sont des contours de front (GeoJSON/KML selon la config du script). Petit script de visualisation rapide — crée `~/gsie-feu/scripts/plot_front.py` :

```python
import json, glob, matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 8))
files = sorted(glob.glob("*.geojson") + glob.glob("output*.json"))
cmap = plt.cm.hot_r
for i, f in enumerate(files):
    with open(f) as fh:
        data = json.load(fh)
    for feat in data.get("features", [data]):
        geom = feat.get("geometry", feat)
        if geom.get("type") == "Polygon":
            for ring in geom["coordinates"]:
                xs, ys = zip(*ring)
                ax.plot(xs, ys, color=cmap(i / max(len(files)-1, 1)), lw=1.2)
ax.set_title("Propagation du front — contours successifs")
ax.set_aspect("equal")
plt.savefig("propagation.png", dpi=150, bbox_inches="tight")
print("→ propagation.png")
```

*(Selon la version du dépôt, le format de sortie exact peut varier — si tu obtiens du KML, dis-le-moi et je te fournis la variante. L'important à ce stade : voir des contours concentriques qui suivent le relief.)*

### 2.4 Plan B : Docker (si la compilation résiste)

```bash
# Docker dans WSL (sans Docker Desktop, plus léger)
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# Ferme et rouvre le terminal, puis :
cd ~/gsie-feu/forefire
docker build -t forefire .
docker run -it -v $(pwd)/examples:/examples forefire bash
```

### 2.5 Les bindings Python (pour la suite du projet)

```bash
cd ~/gsie-feu/forefire
pip install ./bindings/python 2>/dev/null || pip install pyforefire 2>/dev/null || echo "→ on vérifiera le chemin exact des bindings ensemble"
```

✅ **Contrôle d'étape (le moment important)** : tu as un `propagation.png` avec des contours de feu qui s'étirent selon le vent et le relief corse. **Prends une capture — c'est la première image du projet GSIE-Feu.**

---

## Étape 3 — PX4 SITL + Gazebo : ton premier drone simulé (30-40 min)

### 3.1 Installation PX4 (script officiel)

```bash
cd ~/gsie-feu
git clone https://github.com/PX4/PX4-Autopilot.git --recursive
bash ./PX4-Autopilot/Tools/setup/ubuntu.sh
# Installe toolchain + Gazebo moderne ("Gz"). Long (~15-20 min). Redémarre le terminal après.
```

### 3.2 Premier vol

```bash
cd ~/gsie-feu/PX4-Autopilot

# Premier lancement : compilation (~10-15 min sur ton i5) puis Gazebo s'ouvre
make px4_sitl gz_x500
```

Une fenêtre Gazebo apparaît (WSLg l'affiche nativement sous Windows 11) avec un quadricoptère x500. Dans la console PX4 :

```
commander takeoff
```

Le drone décolle et se met en vol stationnaire. `commander land` pour atterrir.

**Adaptations à ta machine** :
- Si l'affichage rame (ton iGPU Iris Xe fait le rendu par défaut dans WSLg), le mode **headless** donne des performances parfaites — et c'est de toute façon le mode des futures campagnes automatisées :
```bash
HEADLESS=1 make px4_sitl gz_x500
```
- Décollage géolocalisé (exemple : Landiras) :
```bash
PX4_HOME_LAT=44.5667 PX4_HOME_LON=-0.4167 PX4_HOME_ALT=50 make px4_sitl gz_x500
```

### 3.3 Contrôle par script : MAVSDK-Python

```bash
pip install mavsdk aioconsole
```

Crée `~/gsie-feu/scripts/premier_vol.py` :

```python
import asyncio
from mavsdk import System

async def run():
    drone = System()
    await drone.connect(system_address="udpin://0.0.0.0:14540")
    print("Connexion au drone simulé...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("✓ Drone connecté")
            break

    print("Armement + décollage...")
    await drone.action.arm()
    await drone.action.set_takeoff_altitude(30.0)
    await drone.action.takeoff()
    await asyncio.sleep(15)

    print("Position actuelle :")
    async for pos in drone.telemetry.position():
        print(f"  lat={pos.latitude_deg:.6f} lon={pos.longitude_deg:.6f} alt={pos.relative_altitude_m:.1f} m")
        break

    print("Atterrissage...")
    await drone.action.land()

asyncio.run(run())
```

Avec la simulation lancée dans un premier terminal, exécute dans un second :

```bash
python ~/gsie-feu/scripts/premier_vol.py
```

✅ **Contrôle** : le script arme, fait décoller, lit la télémétrie et fait atterrir le drone **sans que tu touches à rien**. C'est exactement ce code qui pilotera le drone réel plus tard.

### 3.4 (Optionnel) QGroundControl côté Windows
Télécharge QGroundControl pour Windows (qgroundcontrol.com) et lance-le pendant une simulation : il se connecte automatiquement au SITL via le réseau WSL et t'affiche carte, télémétrie, planification de mission. Utile pour visualiser — et c'est l'outil que ton GCS-Lite remplacera.

---

## Étape 4 — Structure du projet (5 min)

```bash
mkdir -p ~/gsie-feu/{data/{landiras,corse},scripts,notes,gcs-lite,assimilation}
```

```
~/gsie-feu/
├── forefire/          # moteur (dépôt cloné — service GPL isolé)
├── PX4-Autopilot/     # autopilote simulé
├── data/              # paysages, MNT, météo (landiras/, corse/)
├── scripts/           # nos scripts Python (MAVSDK, visualisation)
├── assimilation/      # LA brique GSIE (à venir)
├── gcs-lite/          # interface MapLibre (à venir)
└── notes/             # journal de bord
```

Conseil : initialise un dépôt git dès maintenant sur `scripts/`, `assimilation/`, `gcs-lite/` et `notes/` (pas sur les dépôts clonés). Premier commit = premier jour du code GSIE-Feu.

---

## Récapitulatif des points de contrôle

| # | Vérification | Preuve |
|---|---|---|
| 0 | WSL sur E:, 20 Go RAM, user par défaut OK | `wsl -l -v`, `free -h` |
| 1 | Toolchain + venv | `(.venv)` au prompt |
| 2 | **Feu corse simulé et visualisé** | `propagation.png` 🔥 |
| 3 | **Drone qui vole par script** | `premier_vol.py` déroule armement→décollage→télémétrie→atterrissage 🚁 |
| 4 | Arborescence projet + git | `git log` (1 commit) |

## Limites connues de ta machine (et parades)

| Limite | Impact | Parade |
|---|---|---|
| 4 cœurs / 8 threads | Compilations lentes ; 1 seul drone simulé confortable | `-j4`, headless, `PX4_SIM_SPEED_FACTOR` <1 si besoin ; multi-drones attendra la station |
| C: presque plein | Risque de saturation système | Tout le banc vit sur E: (fait en étape 0) |
| RTX 3050 4 Go non exposée par défaut au rendu WSLg | Gazebo rendu par l'iGPU | Headless pour les campagnes ; le GPU NVIDIA servira plus tard pour l'inférence (CUDA fonctionne dans WSL2) |
| Optimiseurs (Smart Game Booster) | Peuvent tuer Docker/WSL | Désactiver en session simulation |

## Et après ?

Une fois les ✅ 2 et 3 obtenus, les prochains jalons du banc (dans l'ordre) :
1. **Paysage Landiras** : télécharger MNT (RGE ALTI/LiDAR HD) + BD Forêt de la zone, construire le NetCDF paysage, premier feu sur relief girondin réel.
2. **Le pont feu↔drone** : script qui interroge ForeFire (« que voit le drone à sa position ? ») et renvoie des détections bruitées — le détecteur virtuel.
3. **Première boucle d'assimilation** : le jumeau (ForeFire n°2, paramètres différents) se recale sur les détections. Le cœur de GSIE-Feu naît là.
