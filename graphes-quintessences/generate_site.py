#!/usr/bin/env python3
"""Génère `public/index.html` à partir des diagrammes Mermaid de `diagrams/`.

Usage :
    python generate_site.py

Aucune dépendance externe (stdlib uniquement). Le script est idempotent :
il régénère entièrement `public/index.html` à chaque exécution à partir de
`diagrams/meta.json` (ordre, titres, catégories, descriptions, sources,
dates) et des fichiers `.mmd` correspondants.

Fonctionnalités du site généré :
- Barre latérale de navigation groupée par catégorie, avec compteur par
  catégorie et surbrillance de la section visible (IntersectionObserver).
- Filtres par catégorie (puces) + recherche instantanée combinée.
- Bascule thème clair/sombre, persistée dans `localStorage`.
- Zoom/pan par diagramme (molette Ctrl/Cmd + boutons +/-/reset).
- Vue plein écran par diagramme (superposition modale).
- Bouton « Copier le code Mermaid » et bascule « Voir le code source ».
- Téléchargement du rendu en SVG.
- Ancres stables par diagramme (`#<id>`) pour partager un lien direct.

Ce script est invoqué par le skill `.devin/skills/graphes-progression/`
après toute mise à jour d'un fichier `.mmd` ou de `meta.json`.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
DIAGRAMS_DIR = ROOT / "diagrams"
PUBLIC_DIR = ROOT / "public"
META_PATH = DIAGRAMS_DIR / "meta.json"

MERMAID_VERSION = "11.16.1"
MERMAID_INTEGRITY = (
    "sha384-aBQXj4hK6Jm05i7aQAsUV3bLdSUrHX1BGYfMB0166TtWt/RRaw+h0Eelme9OCOvy"
)

# Préfixe du code Mermaid → étiquette lisible affichée en badge de carte.
TYPES_DIAGRAMME = (
    ("sequenceDiagram", "Séquence"),
    ("stateDiagram", "États"),
    ("classDiagram", "Classes"),
    ("erDiagram", "Entité-relation"),
    ("timeline", "Chronologie"),
    ("gantt", "Gantt"),
    ("pie", "Camembert"),
    ("mindmap", "Mindmap"),
    ("journey", "Parcours utilisateur"),
    ("flowchart", "Flowchart"),
    ("graph", "Graphe"),
)


def charger_diagrammes() -> list[dict[str, str]]:
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    diagrammes = []
    for entree in meta:
        chemin_mmd = DIAGRAMS_DIR / f"{entree['id']}.mmd"
        if not chemin_mmd.exists():
            raise FileNotFoundError(f"Diagramme manquant : {chemin_mmd}")
        code = chemin_mmd.read_text(encoding="utf-8").strip()
        diagrammes.append(
            {
                "id": entree["id"],
                "titre": entree["titre"],
                "categorie": entree.get("categorie", "Autres"),
                "description": entree.get("description", ""),
                "source": entree.get("source", ""),
                "date_maj": entree.get("date_maj", ""),
                "code": code,
                "type": detecter_type(code),
            }
        )
    return diagrammes


def detecter_type(code: str) -> str:
    premiere_ligne = next(
        (ligne.strip() for ligne in code.splitlines() if ligne.strip()), ""
    )
    premiere_ligne = premiere_ligne.lower()
    for prefixe, libelle in TYPES_DIAGRAMME:
        if premiere_ligne.startswith(prefixe.lower()):
            return libelle
    return "Diagramme"


def echapper_html(texte: str) -> str:
    return (
        texte.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def slug(texte: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in texte.lower()).strip("-")


def grouper_par_categorie(
    diagrammes: list[dict[str, str]],
) -> dict[str, list[dict[str, str]]]:
    groupes: dict[str, list[dict[str, str]]] = {}
    for diagramme in diagrammes:
        groupes.setdefault(diagramme["categorie"], []).append(diagramme)
    return groupes


def rendre_sidebar(groupes: dict[str, list[dict[str, str]]]) -> str:
    blocs = []
    for categorie, diagrammes in groupes.items():
        liens = "\n".join(
            f'          <li><a href="#{d["id"]}" data-nav-id="{d["id"]}" '
            f'data-titre="{echapper_html(d["titre"].lower())}" '
            f'data-categorie="{slug(categorie)}">{echapper_html(d["titre"])}</a></li>'
            for d in diagrammes
        )
        blocs.append(
            f"""        <div class="nav-groupe" data-groupe="{slug(categorie)}">
          <h3>{echapper_html(categorie)} <span class="nav-compteur">{len(diagrammes)}</span></h3>
          <ul>
{liens}
          </ul>
        </div>"""
        )
    return "\n".join(blocs)


def rendre_puces_filtre(groupes: dict[str, list[dict[str, str]]]) -> str:
    puces = [
        '      <button type="button" class="puce actif" data-filtre-categorie="tout">'
        "Toutes</button>"
    ]
    for categorie, diagrammes in groupes.items():
        puces.append(
            f'      <button type="button" class="puce" data-filtre-categorie="{slug(categorie)}">'
            f"{echapper_html(categorie)} ({len(diagrammes)})</button>"
        )
    return "\n".join(puces)


def rendre_carte(diagramme: dict[str, str]) -> str:
    code_json = json.dumps(diagramme["code"])
    description = (
        f'<p class="description">{echapper_html(diagramme["description"])}</p>'
        if diagramme["description"]
        else ""
    )
    return f"""
    <section class="carte" id="{diagramme['id']}"
             data-titre="{echapper_html(diagramme['titre'].lower())}"
             data-categorie="{slug(diagramme['categorie'])}">
      <header class="carte-entete">
        <div>
          <span class="badge">{echapper_html(diagramme['categorie'])}</span>
          <span class="badge badge-type">{echapper_html(diagramme['type'])}</span>
          <h2>{echapper_html(diagramme['titre'])}</h2>
          {description}
          <p class="source">Source : {echapper_html(diagramme['source'])}
            &middot; Mise à jour : {echapper_html(diagramme['date_maj'])}</p>
        </div>
        <div class="carte-actions">
          <button type="button" class="btn-icone" data-action="zoom-in" data-cible="{diagramme['id']}" title="Zoomer">+</button>
          <button type="button" class="btn-icone" data-action="zoom-out" data-cible="{diagramme['id']}" title="Dézoomer">&minus;</button>
          <button type="button" class="btn-icone" data-action="zoom-reset" data-cible="{diagramme['id']}" title="Réinitialiser le zoom">&#8634;</button>
          <button type="button" class="btn-icone" data-action="plein-ecran" data-cible="{diagramme['id']}" title="Plein écran">&#9974;</button>
          <button type="button" class="btn-icone" data-action="telecharger-svg" data-cible="{diagramme['id']}" title="Télécharger en SVG">&#11015;</button>
          <button type="button" class="btn-copier" data-action="basculer-code" data-cible="{diagramme['id']}">Voir le code</button>
          <button type="button" class="btn-copier" data-action="copier" data-cible="{diagramme['id']}">Copier</button>
          <a class="btn-lien" href="#{diagramme['id']}" title="Lien direct">#</a>
        </div>
      </header>
      <div class="diagram-viewport" data-viewport="{diagramme['id']}">
        <div class="diagram-scale" data-scale="{diagramme['id']}">
          <pre class="mermaid" data-diagram-id="{diagramme['id']}">
{echapper_html(diagramme['code'])}
          </pre>
        </div>
      </div>
      <pre class="code-source" data-code-affiche="{diagramme['id']}" hidden><code>{echapper_html(diagramme['code'])}</code></pre>
      <script type="application/json" data-code-source="{diagramme['id']}">{code_json}</script>
    </section>
"""


def generer_html(diagrammes: list[dict[str, str]]) -> str:
    date_generation = date.today().isoformat()
    groupes = grouper_par_categorie(diagrammes)
    sidebar = rendre_sidebar(groupes)
    puces = rendre_puces_filtre(groupes)
    cartes = "\n".join(rendre_carte(d) for d in diagrammes)
    nb_categories = len(groupes)
    return f"""<!DOCTYPE html>
<html lang="fr" data-theme="clair">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Graphes — Quintessences / GSIE</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/main.css">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
</head>
<body>
  <div class="mise-en-page">
    <aside class="sidebar" id="sidebar">
      <div class="sidebar-entete">
        <p class="sidebar-titre">Quintessences</p>
        <p class="sidebar-soustitre">Graphes GSIE</p>
      </div>
      <div class="sidebar-recherche">
        <input type="search" id="recherche" placeholder="Rechercher un graphe… (/)" aria-label="Rechercher un graphe">
      </div>
      <nav class="sidebar-nav" id="sidebar-nav">
{sidebar}
      </nav>
      <div class="sidebar-pied">
        <button type="button" id="bascule-theme" class="btn-theme">Thème sombre</button>
      </div>
    </aside>

    <div class="contenu">
      <header class="hero">
        <h1>Graphes du projet Quintessences / GSIE</h1>
        <p class="tagline">
          {len(diagrammes)} diagrammes Mermaid répartis en {nb_categories} catégories,
          générés depuis <code>README.md</code>, <code>ROADMAP.md</code>,
          <code>PROJECT_MEMORY.md</code> et les architectures GSIE. Régénérés à
          chaque grosse progression du projet — voir
          <code>.devin/skills/graphes-progression/</code>.
        </p>
        <p class="meta">Dernière génération : {date_generation}</p>
        <div class="puces-filtre" id="puces-filtre">
{puces}
        </div>
      </header>

      <main id="contenu-principal">
{cartes}
      </main>

      <p class="aucun-resultat" id="aucun-resultat" hidden>
        Aucun graphe ne correspond à la recherche.
      </p>

      <footer>
        <p>© 2026 Quintessences. Généré par <code>generate_site.py</code> —
        voir <code>graphes-quintessences/README.md</code>.</p>
      </footer>
    </div>
  </div>

  <div class="modale" id="modale-plein-ecran" hidden>
    <div class="modale-barre">
      <span id="modale-titre"></span>
      <button type="button" id="modale-fermer" title="Fermer (Échap)">&times;</button>
    </div>
    <div class="modale-corps" id="modale-corps"></div>
  </div>

  <script
    src="https://cdn.jsdelivr.net/npm/mermaid@{MERMAID_VERSION}/dist/mermaid.min.js"
    integrity="{MERMAID_INTEGRITY}"
    crossorigin="anonymous"
  ></script>
  <script src="/js/site.js"></script>
</body>
</html>
"""


def main() -> None:
    diagrammes = charger_diagrammes()
    html = generer_html(diagrammes)
    (PUBLIC_DIR / "index.html").write_text(html, encoding="utf-8")
    print(f"{len(diagrammes)} diagramme(s) rendus dans public/index.html")


if __name__ == "__main__":
    main()
