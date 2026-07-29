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
    # `niveau_de_confiance_derive` a ete retiree ici : elle verrouillait la
    # valeur `0.70` du moteur de recommandation, c'est-a-dire le defaut
    # lui-meme — une confiance propre au moteur, sans lien avec le diagnostic
    # invoque. Verrouiller un nombre invente le rend durable. Les mutations
    # `diagnostic_jamais_lu` et `confiance_alternatives_codee_en_dur`
    # (fin de liste) portent desormais l'exigence : la confiance vient du
    # diagnostic lu, et aucun litteral ne subsiste dans le moteur.
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
    Mutation(
        cle="source_de_grandeur_derivee",
        fichier="gsie_api/seeds/variables_mesurables_data.py",
        ancien='            "Réservoir utile des sols de la France métropolitaine, version 2.0, "',
        nouveau='            "Reserve utile, source a preciser, "',
        defaut_reproduit=(
            "la source qui definit une grandeur mesurable derive sans etre "
            "remarquee — la definition devient citable sans etre verifiable"
        ),
        tests=("tests/unit/test_variables_mesurables.py",),
    ),
    Mutation(
        cle="source_incitable_admise",
        fichier="gsie_api/resources/validators.py",
        ancien='    "source": ["title", "subtype", "source_nature", "auteur", "date_publication"],',
        nouveau='    "source": ["title", "subtype", "source_nature"],',
        defaut_reproduit=(
            "une source sans auteur ni date entre en base — une conclusion la "
            "citerait sans pouvoir dire qui l'a ecrite"
        ),
        tests=("tests/integration/test_resources_fiabilite.py",),
    ),
    Mutation(
        cle="regle_hors_domaine_retournee",
        fichier="gsie_api/engines/knowledge/engine.py",
        ancien="                func.ST_Contains(domaine.geometry, territoire.geometry),",
        nouveau='                literal_column("true"),',
        defaut_reproduit=(
            "une regle tiree d'un catalogue regional sort hors de sa zone — "
            "conclusion fausse citant une source reelle, invisible"
        ),
        tests=("tests/integration/test_regles_applicables.py",),
    ),
    Mutation(
        cle="regle_non_sourcee_retournee",
        fichier="gsie_api/engines/knowledge/engine.py",
        # La jointure `citation` seule ne suffit pas : la jointure `source` qui
        # suit reste interne et filtrerait quand meme. C'est le role `primary`
        # qui porte l'exigence — une regle citee « en passant » ne vaut pas
        # une regle sourcee.
        ancien="                CitationModel.citation_role == CitationRole.primary,",
        nouveau='                literal_column("true"),',
        defaut_reproduit=(
            "une citation de role secondaire suffit a faire sortir une regle — "
            "la source citee n'est plus celle qui la fonde"
        ),
        tests=("tests/integration/test_regles_applicables.py",),
    ),
    Mutation(
        cle="plancher_ignore_les_faits",
        fichier="gsie_api/engines/reasoning/engine.py",
        ancien="niveau_plancher([regle.evidence_level, *niveaux_des_faits])",
        nouveau="regle.evidence_level",
        defaut_reproduit=(
            "une conclusion tiree d'un releve terrain isole (F) via une regle "
            "de catalogue (B) est annoncee comme B — surestimation silencieuse"
        ),
        tests=("tests/integration/test_regles_applicables.py",),
    ),
    # --- Recommendation Engine : ne pas conseiller sans avoir lu le diagnostic
    Mutation(
        cle="diagnostic_absent_tolere",
        fichier="gsie_api/engines/recommendation/engine.py",
        ancien="        if diagnostic is None:\n            raise DiagnosticIntrouvableError(",
        nouveau="        if diagnostic is None and False:\n            raise DiagnosticIntrouvableError(",  # noqa: E501
        defaut_reproduit=(
            "un conseil sylvicole complet — type d'action, prelevement chiffre, "
            "confiance — est rendu en citant un diagnostic qui n'existe pas"
        ),
        tests=("tests/integration/test_recommendation_diagnostic.py",),
    ),
    Mutation(
        cle="diagnostic_jamais_lu",
        fichier="gsie_api/engines/recommendation/engine.py",
        # Retour a l'etat sans etat : la confiance redevient une constante du
        # moteur, et `diagnostic_id` n'est plus qu'une chaine recopiee dans la
        # justification.
        ancien=(
            "        diagnostic = await self._diagnostic(request.diagnostic_id)\n"
            "        confiance = float(diagnostic.confiance)"
        ),
        nouveau="        confiance = 0.70",
        defaut_reproduit=(
            "le moteur cite `diagnostic_id` dans sa justification sans jamais "
            "le consulter — reference verifiable en apparence, vide en fait"
        ),
        tests=("tests/integration/test_recommendation_diagnostic.py",),
    ),
    Mutation(
        cle="confiance_alternatives_codee_en_dur",
        fichier="gsie_api/engines/recommendation/engine.py",
        # Une seule des quatre confiances remise en dur. Un test qui ne
        # verifierait que la recommandation principale survivrait a cette
        # mutation : les alternatives sont imbriquees sous elle.
        ancien="            niveau_confiance=confiance,\n        )\n        alternatives.append(alt_attente)",  # noqa: E501
        nouveau="            niveau_confiance=0.60,\n        )\n        alternatives.append(alt_attente)",  # noqa: E501
        defaut_reproduit=(
            "une alternative s'annonce plus ou moins assuree que le diagnostic "
            "qui la fonde — l'ecart ne vient d'aucune source"
        ),
        tests=(
            "tests/integration/test_recommendation_diagnostic.py",
            "tests/unit/test_constantes_scientifiques.py",
        ),
    ),
    Mutation(
        cle="refus_diagnostic_en_erreur_serveur",
        fichier="gsie_api/engines/recommendation/router.py",
        # Un 500 dirait « panne » la ou le refus est un jugement du moteur :
        # l'appelant conclurait a un incident et reessaierait la meme requete.
        # L'ancrage sur le decorateur suivant evite de muter aussi le
        # gestionnaire de `/decision`, qui porte un bloc `except` identique.
        ancien='    except RecommendationEngineError as exc:\n        raise HTTPException(status_code=400, detail=str(exc)) from exc\n\n\n@router.post(\n    "/decision",',  # noqa: E501
        nouveau='    except RecommendationEngineError as exc:\n        raise HTTPException(status_code=500, detail="erreur interne") from exc\n\n\n@router.post(\n    "/decision",',  # noqa: E501
        defaut_reproduit=(
            "le refus d'un diagnostic introuvable remonte en 500 sans nommer "
            "le diagnostic manquant — l'appelant ne peut pas corriger"
        ),
        tests=("tests/integration/test_recommendation_diagnostic.py",),
    ),
    Mutation(
        cle="accuse_de_conservation_mensonger",
        fichier="gsie_api/engines/recommendation/engine.py",
        ancien='            "statut": "recu_non_persiste",',
        nouveau='            "statut": "enregistre",',
        defaut_reproduit=(
            "le forestier lit un accuse de conservation pour une decision que "
            "rien ne persiste — il cesse alors de tenir sa propre trace"
        ),
        tests=("tests/unit/test_recommendation_engine.py",),
    ),
    Mutation(
        cle="station_non_enregistree_refusee",
        fichier="gsie_api/engines/reasoning/engine.py",
        # `station_id` est facultatif et n'est pas contractuellement une
        # `place`. Laisser remonter `TerritoireInconnuError` refuse une requete
        # dont le contexte suffit a raisonner — regression constatee.
        ancien="        except TerritoireInconnuError:",
        nouveau="        except ZeroDivisionError:",
        defaut_reproduit=(
            "une station decrite integralement par le contexte de la requete "
            "fait refuser l'inference parce qu'aucune `place` ne l'enregistre"
        ),
        tests=("tests/integration/test_reasoning.py",),
    ),
    Mutation(
        cle="taux_arbitraire_sans_aveu",
        fichier="gsie_api/engines/simulation_backend.py",
        ancien='            "taux_annuel_arbitraire": annual_rate,',
        nouveau="",
        defaut_reproduit=(
            "une projection de volume circule avec une citation documentaire "
            "(dont ADR-009) pour un taux que rien ne source"
        ),
        tests=("tests/unit/test_growth_models.py",),
    ),
    Mutation(
        cle="description_de_colonne_invisible_en_base",
        fichier="gsie_api/infrastructure/models/forestry.py",
        # `doc=` est de la documentation Python : PostgreSQL ne la voit pas. La
        # faute a ete commise trois fois dans ce depot, dont deux fois par moi
        # a 24 h d'intervalle. Seul le controle de derive strict la rattrape —
        # le modele ne declare plus le commentaire que la migration a pose.
        ancien='        comment="Nom/qualité du validateur humain',
        nouveau='        doc="Nom/qualité du validateur humain',
        defaut_reproduit=(
            "une contrainte metier — human_validator obligatoire des que le "
            "statut passe a accepted — n'existe plus que dans le code Python"
        ),
        tests=("tests/integration/test_migration_baseline.py",),
    ),
    Mutation(
        cle="etat_du_peuplement_ignore",
        fichier="gsie_api/engines/recommendation/engine.py",
        # Retour a la derivation par le seul objectif forestier : un peuplement
        # critique recevait alors mot pour mot le conseil du peuplement sain.
        ancien="        if diagnostic.etat_global in _ETATS_HORS_MAPPING_V1:",
        nouveau="        if False:",
        defaut_reproduit=(
            "un peuplement diagnostique critique recoit « eclaircie moderee, "
            "prelevement 25 % » — le conseil du peuplement sain, a l'identique"
        ),
        tests=(
            "tests/unit/test_recommendation_engine.py",
            "tests/integration/test_recommendation_diagnostic.py",
        ),
    ),
    Mutation(
        cle="etat_degrade_absent_du_perimetre",
        fichier="gsie_api/engines/recommendation/engine.py",
        # Un seul des deux etats retire. Un test qui ne verifierait que
        # `critique` survivrait — `deperissement` est tout aussi incompatible
        # avec le mapping objectif -> action.
        ancien="        DiagnosticGlobalState.deperissement,\n        DiagnosticGlobalState.critique,",  # noqa: E501
        nouveau="        DiagnosticGlobalState.critique,",
        defaut_reproduit=(
            "un peuplement deperissant repasse par le mapping nominal et recoit "
            "une intervention qu'aucune regle sourcee ne fonde"
        ),
        tests=("tests/unit/test_recommendation_engine.py",),
    ),
    Mutation(
        cle="motif_du_refus_muet",
        fichier="gsie_api/engines/recommendation/engine.py",
        # Le type d'action seul ne suffit pas : c'est le forestier qui decide
        # (`GSIE-CON-001`), il lui faut le pourquoi, en clair.
        ancien='                f"Peuplement diagnostiqué « {etat_global.value} ». Aucune règle "',
        nouveau='                f"Aucune règle "',
        defaut_reproduit=(
            "le forestier lit « pas d'intervention » sans savoir que l'etat de "
            "son peuplement en est le motif"
        ),
        tests=("tests/unit/test_recommendation_engine.py",),
    ),
    # --- Fail-closed : ni l'autorisation ni la disponibilite ne s'accordent
    #     par omission
    Mutation(
        cle="action_non_evaluee_accordee",
        fichier="gsie_api/core/rbac.py",
        # Retour a la sortie ouverte : toute action qu'aucune branche n'evalue
        # ressortait autorisee. `admin` etait dans ce cas.
        ancien="    if action not in _ACTIONS_EVALUEES:",
        nouveau="    if False:",
        defaut_reproduit=(
            "un porteur de JWT sans aucun role obtient l'action `admin` sur " "tout type non-RGPD"
        ),
        tests=("tests/unit/test_rbac.py",),
    ),
    Mutation(
        cle="readiness_toujours_disponible",
        fichier="gsie_api/infrastructure/health.py",
        # Le corps disait `degraded`, le code disait 200. Kubernetes lit le code.
        ancien='    return status.HTTP_200_OK if statut == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE',  # noqa: E501
        nouveau="    return status.HTTP_200_OK",
        defaut_reproduit=(
            "un pod dont la base est inaccessible reste en rotation : la sonde "
            "readiness rend 200 avec un corps `degraded`"
        ),
        tests=("tests/unit/test_health.py",),
    ),
    Mutation(
        cle="code_du_cache_non_recalcule",
        fichier="gsie_api/infrastructure/health.py",
        # Le chemin avec cache doit rendre le meme code que le chemin sans
        # cache, sinon un `degraded` en cache rejoue un 200 pendant 5 s.
        ancien="            response.status_code = _code_http(en_cache.status)\n            return en_cache",  # noqa: E501
        nouveau="            return en_cache",
        defaut_reproduit=(
            "cinq secondes de trafic vers un pod tombe, parce que le code n'est "
            "pas recalcule sur le chemin avec cache"
        ),
        tests=("tests/unit/test_health.py",),
    ),
    Mutation(
        cle="secret_du_broker_dans_last_error",
        fichier="gsie_api/outbox_worker.py",
        # Interdiction posee des le premier brief : jamais de secret ni de
        # traceback brute dans `last_error`. Le message d'une exception de
        # connexion transporte l'URL du broker, donc son mot de passe
        # (`redis://:motdepasse@...`), et `last_error_code` est persiste.
        ancien='    code = _ERROR_CODE_PATTERN.sub("_", type(exc).__name__)',
        nouveau="    code = str(exc)",
        defaut_reproduit=(
            "le mot de passe du broker est ecrit en base dans "
            "outbox_event.last_error_code, puis expose par les metriques"
        ),
        tests=(
            "tests/unit/test_infra_coverage.py",
            "tests/integration/test_outbox_concurrence.py",
        ),
    ),
    Mutation(
        cle="joker_origine_accepte_en_production",
        fichier="gsie_api/websocket/router.py",
        # Le joker `*` ne vaut qu'en developpement. L'accepter partout ouvrirait
        # le hub a toute page web : le jeton passe en parametre de requete, une
        # origine tierce suffirait alors a etablir la connexion.
        ancien='    if "*" in allowed:\n        return _settings.environment == "development"',
        nouveau='    if "*" in allowed:\n        return True',
        defaut_reproduit=(
            "une configuration laissee a `*` ouvre le hub WebSocket a toute "
            "origine, y compris en production"
        ),
        tests=("tests/unit/test_infra_coverage.py",),
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
