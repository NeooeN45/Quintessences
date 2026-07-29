"""Harnais de mutation — mesure si la suite de tests *mord* vraiment.

Une couverture de 99 % dit quelles lignes ont été exécutées, jamais si un
comportement faux aurait été détecté. L'audit de fiabilité l'a montré : dix-huit
défauts réels, dont plusieurs cassaient toute écriture authentifiée, ont
traversé une suite de plus de mille tests sans en faire tomber un seul.

Le principe est simple et impitoyable : on casse volontairement le code, on
relance la suite, et on regarde si elle proteste. Une mutation qui **survit**
— aucun test ne tombe — désigne un comportement que rien ne surveille.

Chaque mutation ci-dessous reproduit une classe de défaut réellement rencontrée
dans ce dépôt, pas une faute imaginaire :

* la garde qui matérialise l'Agent auteur (défaut P0 : toute écriture
  authentifiée échouait en violation de clé étrangère) ;
* la ligne racine du ResourceDiff (défaut P0 : toute mise à jour échouait) ;
* la normalisation du filtre de type vide (défaut P0 : fuite RGPD) ;
* le contrôle de type des jetons JWT (garde présente mais non testée) ;
* la coercition des dates ISO (défaut P0 : 19 types incréables) ;
* la garde NaN du moteur de corrélation (défaut P2 : 500 sur variable constante).

Usage :

    ./.venv/Scripts/python.exe tests/mutation/harnais.py            # rapide
    ./.venv/Scripts/python.exe tests/mutation/harnais.py --complet  # + intégration

Sortie : une mutation TUEE est une bonne nouvelle, une mutation SURVIVANTE est
une zone aveugle à couvrir.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
SOURCE = RACINE / "src"
PYTHON = RACINE / ".venv" / "Scripts" / "python.exe"


@dataclass(frozen=True)
class Mutation:
    """Une altération ciblée du code source, et le test censé la détecter."""

    cle: str
    fichier: str
    ancien: str
    nouveau: str
    defaut_reproduit: str
    tests: tuple[str, ...] = field(default=())


# Chaque mutation cible une garde ajoutée en réponse à un défaut constaté.
MUTATIONS: tuple[Mutation, ...] = (
    Mutation(
        cle="auteur_non_materialise",
        fichier="gsie_api/resources/service.py",
        ancien="        if author_id is None:\n            return",
        nouveau="        if author_id is not None:\n            return",
        defaut_reproduit=(
            "revision.author_id référence une resource inexistante — "
            "toute écriture authentifiée échoue en 500"
        ),
        tests=("tests/integration/test_resources_fiabilite.py",),
    ),
    Mutation(
        cle="diff_sans_ligne_racine",
        fichier="gsie_api/resources/service.py",
        ancien='        diff_resource = ResourceModel(\n            type="resource_diff",',
        nouveau='        diff_resource = ResourceModel(\n            type="entity",',
        defaut_reproduit="le ResourceDiff n'est plus rattaché au type 61 du métamodèle",
        tests=("tests/integration/test_resources_fiabilite.py",),
    ),
    Mutation(
        cle="filtre_type_vide",
        fichier="gsie_api/resources/router.py",
        # Le défaut d'origine portait sur la *condition*, pas sur l'affectation :
        # `if type is not None` traitait la chaîne vide comme un filtre explicite
        # et sautait donc l'exclusion RGPD.
        ancien="    type_filter = type.strip() if type else None\n    if type_filter:",
        nouveau="    type_filter = type\n    if type_filter is not None:",
        defaut_reproduit=(
            "GET /resources?type= désactive l'exclusion RGPD — "
            "un simple lecteur liste consent et data_subject"
        ),
        tests=("tests/integration/test_resources_fiabilite.py",),
    ),
    Mutation(
        cle="type_de_jeton_non_verifie",
        fichier="gsie_api/core/auth.py",
        ancien='    if payload.get("type") != expected_type:',
        nouveau="    if False:",
        defaut_reproduit="un jeton de rafraîchissement est accepté comme jeton d'accès",
        tests=("tests/unit/test_auth_type_jeton.py",),
    ),
    Mutation(
        cle="coercition_desactivee",
        fichier="gsie_api/resources/coercion.py",
        ancien="        try:\n            converti[champ] = _coercer_valeur(valeur, colonne)",
        nouveau="        try:\n            converti[champ] = valeur",
        defaut_reproduit="une date ISO part telle quelle vers un timestamptz — 500",
        tests=("tests/integration/test_resources_fiabilite.py",),
    ),
    Mutation(
        cle="constante_ign_derivee",
        fichier="gsie_api/engines/growth_models.py",
        ancien="        accroissement_moyen_annuel_volume=7.0,",
        nouveau="        accroissement_moyen_annuel_volume=0.7,",
        defaut_reproduit=(
            "un accroissement moyen annuel sourcé IGN glisse d'un facteur 10 "
            "sans que rien ne le signale"
        ),
        tests=("tests/unit/test_constantes_scientifiques.py",),
    ),
    Mutation(
        cle="niveau_de_confiance_derive",
        fichier="gsie_api/engines/recommendation/engine.py",
        ancien="            niveau_confiance=0.70,",
        nouveau="            niveau_confiance=0.01,",
        defaut_reproduit=("la confiance annoncée au forestier passe de 0,70 à 0,01 en silence"),
        tests=("tests/unit/test_constantes_scientifiques.py",),
    ),
    Mutation(
        cle="nan_correlation_non_garde",
        fichier="gsie_api/engines/correlation/engine.py",
        ancien="        if math.isnan(coefficient) or math.isnan(p_valeur):",
        nouveau="        if False:",
        defaut_reproduit="une variable constante fait rendre 500 au lieu d'une erreur métier",
        tests=("tests/integration/test_moteurs_fiabilite.py",),
    ),
    # =================================================================
    # GSIE-PROMPT-0023/0024 — résilience des clients d'API externes
    # GSIE-PROMPT-0023 a ajouté les gardes dans chaque client individuel.
    # GSIE-PROMPT-0024 les a déplacées vers ResilientHttpClient._get_json
    # (http_client.py) — les mutations ciblent maintenant la base class.
    # Chaque mutation vérifie qu'un test de client spécifique mord quand
    # la garde JSON est supprimée de la base class partagée.
    # =================================================================
    Mutation(
        cle="gbif_json_invalide_non_garde",
        fichier="gsie_api/shared/http_client.py",
        ancien='        except json.JSONDecodeError as exc:\n            raise self.exception_class(f"Échec {label} : {exc}") from exc',  # noqa: E501
        nouveau='        except RuntimeError as exc:\n            raise self.exception_class(f"Échec {label} : {exc}") from exc',  # noqa: E501
        defaut_reproduit=(
            "un JSON malformé de l'API GBIF Species Match fait planter le "
            "client en JSONDecodeError non wrappé au lieu de lever GBIFClientError"
        ),
        tests=("tests/unit/test_gbif_client.py",),
    ),
    Mutation(
        cle="taxref_json_invalide_non_garde",
        fichier="gsie_api/shared/http_client.py",
        ancien='        except json.JSONDecodeError as exc:\n            raise self.exception_class(f"Échec {label} : {exc}") from exc',  # noqa: E501
        nouveau='        except RuntimeError as exc:\n            raise self.exception_class(f"Échec {label} : {exc}") from exc',  # noqa: E501
        defaut_reproduit=(
            "un JSON malformé du miroir GBIF de TAXREF fait planter le "
            "client en JSONDecodeError non wrappé au lieu de lever TaxrefClientError"
        ),
        tests=("tests/unit/test_botanical_taxref.py",),
    ),
    Mutation(
        cle="soilgrids_json_invalide_non_garde",
        fichier="gsie_api/shared/http_client.py",
        ancien='        except json.JSONDecodeError as exc:\n            raise self.exception_class(f"Échec {label} : {exc}") from exc',  # noqa: E501
        nouveau='        except RuntimeError as exc:\n            raise self.exception_class(f"Échec {label} : {exc}") from exc',  # noqa: E501
        defaut_reproduit=(
            "un JSON malformé de l'API SoilGrids fait planter le client en "
            "JSONDecodeError non wrappé au lieu de lever SoilGridsClientError"
        ),
        tests=("tests/unit/test_soilgrids_client.py",),
    ),
    Mutation(
        cle="ign_cadastre_json_invalide_non_garde",
        fichier="gsie_api/shared/http_client.py",
        ancien='        except json.JSONDecodeError as exc:\n            raise self.exception_class(f"Échec {label} : {exc}") from exc',  # noqa: E501
        nouveau='        except RuntimeError as exc:\n            raise self.exception_class(f"Échec {label} : {exc}") from exc',  # noqa: E501
        defaut_reproduit=(
            "un JSON malformé de l'API Carto Cadastre IGN fait planter le "
            "client en JSONDecodeError non wrappé au lieu de lever IGNClientError"
        ),
        tests=("tests/unit/test_ign_client_extended.py",),
    ),
    Mutation(
        cle="ign_altitude_non_numerique_non_garde",
        fichier="gsie_api/engines/gis/ign_client.py",
        ancien=(
            "        try:\n"
            "            return float(elevations[0])\n"
            "        except (TypeError, ValueError) as exc:\n"
            "            raise IGNClientError(\n"
            '                f"Réponse altimétrique sans élévation exploitable : {data}"\n'
            "            ) from exc"
        ),
        nouveau="        return float(elevations[0])",
        defaut_reproduit=(
            "une élévation non-numérique (string) de l'API altimétrique IGN "
            "fait planter le client en ValueError non wrappé au lieu de lever IGNClientError"
        ),
        tests=("tests/unit/test_ign_client_extended.py",),
    ),
    Mutation(
        cle="vigilance_json_invalide_non_garde",
        fichier="gsie_api/shared/http_client.py",
        ancien='        except json.JSONDecodeError as exc:\n            raise self.exception_class(f"Échec {label} : {exc}") from exc',  # noqa: E501
        nouveau='        except RuntimeError as exc:\n            raise self.exception_class(f"Échec {label} : {exc}") from exc',  # noqa: E501
        defaut_reproduit=(
            "un JSON malformé de l'API Vigilance Météo-France fait planter "
            "le client en JSONDecodeError non wrappé au lieu de lever VigilanceClientError"
        ),
        tests=("tests/unit/test_vigilance_client.py",),
    ),
    Mutation(
        cle="dpclim_liste_stations_json_invalide_non_garde",
        fichier="gsie_api/shared/http_client.py",
        ancien='        except json.JSONDecodeError as exc:\n            raise self.exception_class(f"Échec {label} : {exc}") from exc',  # noqa: E501
        nouveau='        except RuntimeError as exc:\n            raise self.exception_class(f"Échec {label} : {exc}") from exc',  # noqa: E501
        defaut_reproduit=(
            "un JSON malformé de l'API DPClim liste-stations fait planter "
            "le client en JSONDecodeError non wrappé au lieu de lever DPClimClientError"
        ),
        tests=("tests/unit/test_resilience_factory.py", "tests/unit/test_dpclim_client.py"),
    ),
    Mutation(
        cle="champ_csv_obligatoire_non_garde",
        fichier="gsie_api/engines/climate/engine.py",
        # Motif sur une seule ligne : la garde qui refuse une cellule absente.
        ancien="    if value is None or not value.strip():",
        nouveau="    if False:",
        defaut_reproduit=(
            "une ligne CSV amont tronquée passe en valeur vide au lieu d'être "
            "refusée — le moteur invente une donnée manquante (ADR-009)"
        ),
        tests=("tests/unit/test_climate_arome_edge_cases.py",),
    ),
    Mutation(
        cle="territoire_non_exige",
        fichier="gsie_api/resources/validators.py",
        # Motif sur une seule ligne : le champ obligatoire lui-meme.
        ancien='        "territory_description",',
        nouveau="",
        defaut_reproduit=(
            "une connaissance autecologique entre sans territoire declare — "
            "elle sera appliquee hors de la zone que sa source couvre (DEC-000038)"
        ),
        tests=("tests/unit/test_forestry_schemas.py",),
    ),
    Mutation(
        cle="vocabulaire_non_controle",
        fichier="gsie_api/engines/knowledge/regles.py",
        ancien="    if variables_connues is not None and variable not in variables_connues:",
        nouveau="    if False:",
        defaut_reproduit=(
            "une variable hors vocabulaire passe : « RUM » et reserve_utile_mm "
            "cohabitent, la regle echoue ensuite en silence"
        ),
        tests=("tests/unit/test_regles_derivees.py",),
    ),
    Mutation(
        cle="valeur_non_numerique_admise",
        fichier="gsie_api/engines/knowledge/regles.py",
        ancien="    nombre = _nombre_lisible(valeur)",
        nouveau="    nombre = valeur.strip()",
        defaut_reproduit=(
            "une valeur non numerique entre dans la condition derivee — "
            "surface d'execution ouverte"
        ),
        tests=("tests/unit/test_regles_derivees.py",),
    ),
)


def _cibles(mutation: Mutation, complet: bool) -> list[str]:
    """Tests à jouer : ceux déclarés, ou la suite unitaire en mode rapide."""
    if not mutation.tests:
        return ["tests/unit"]
    if complet:
        return list(mutation.tests)
    return [chemin for chemin in mutation.tests if chemin.startswith("tests/unit")] or [
        "tests/unit"
    ]


def _jouer(cibles: list[str], racine_source: Path) -> bool:
    """Retourne True si la suite passe (donc si la mutation a survécu)."""
    environnement = {
        "PYTHONPATH": str(racine_source),
        "TESTCONTAINERS_RYUK_DISABLED": "true",
    }
    resultat = subprocess.run(  # noqa: S603
        [str(PYTHON), "-m", "pytest", *cibles, "-q", "--no-cov", "-x"],
        cwd=RACINE,
        capture_output=True,
        env={**_environnement_de_base(), **environnement},
        check=False,
    )
    return resultat.returncode == 0


def _environnement_de_base() -> dict[str, str]:
    import os

    return dict(os.environ)


def _appliquer(mutation: Mutation, racine_source: Path) -> None:
    chemin = racine_source / mutation.fichier
    source = chemin.read_text(encoding="utf-8")
    if mutation.ancien not in source:
        raise SystemExit(
            f"[{mutation.cle}] motif introuvable dans {mutation.fichier} — "
            "le harnais est périmé, mettre à jour la mutation"
        )
    chemin.write_text(source.replace(mutation.ancien, mutation.nouveau, 1), encoding="utf-8")


def executer(complet: bool) -> int:
    survivantes: list[Mutation] = []

    print(
        f"Harnais de mutation — {len(MUTATIONS)} mutations, mode "
        f"{'complet' if complet else 'rapide'}\n"
    )

    for mutation in MUTATIONS:
        with tempfile.TemporaryDirectory(prefix="gsie-mutation-") as travail:
            racine_source = Path(travail) / "src"
            shutil.copytree(SOURCE, racine_source)
            _appliquer(mutation, racine_source)
            cibles = _cibles(mutation, complet)
            survit = _jouer(cibles, racine_source)

        if survit:
            survivantes.append(mutation)
            print(f"  SURVIVANTE  {mutation.cle}")
            print(f"              {mutation.defaut_reproduit}")
            print(f"              tests joués : {' '.join(cibles)}")
        else:
            print(f"  tuée        {mutation.cle}")

    total = len(MUTATIONS)
    tuees = total - len(survivantes)
    print(f"\nScore : {tuees}/{total} mutations détectées")
    if survivantes:
        print("\nZones aveugles — un comportement que rien ne surveille :")
        for mutation in survivantes:
            print(f"  - {mutation.cle} : {mutation.defaut_reproduit}")
        return 1
    return 0


def main() -> int:
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument(
        "--complet",
        action="store_true",
        help="joue aussi les tests d'intégration (nécessite Docker, bien plus lent)",
    )
    return executer(analyseur.parse_args().complet)


if __name__ == "__main__":
    sys.exit(main())
