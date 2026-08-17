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
# Windows : .venv/Scripts/python.exe — Linux/macOS : .venv/bin/python
PYTHON = (
    RACINE / ".venv" / "Scripts" / "python.exe"
    if sys.platform == "win32"
    else RACINE / ".venv" / "bin" / "python"
)


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
        tests=(
            "tests/unit/test_resources_service_coverage.py",
            "tests/integration/test_resources_fiabilite.py",
        ),
    ),
    Mutation(
        cle="diff_sans_ligne_racine",
        fichier="gsie_api/resources/service.py",
        ancien='        diff_resource = ResourceModel(\n            type="resource_diff",',
        nouveau='        diff_resource = ResourceModel(\n            type="entity",',
        defaut_reproduit="le ResourceDiff n'est plus rattaché au type 61 du métamodèle",
        tests=(
            "tests/unit/test_resources_service_coverage.py",
            "tests/integration/test_resources_fiabilite.py",
        ),
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
        tests=(
            "tests/unit/test_routers_coverage.py",
            "tests/integration/test_resources_fiabilite.py",
        ),
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
        tests=(
            "tests/unit/test_coercion.py",
            "tests/integration/test_resources_fiabilite.py",
        ),
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
        tests=(
            "tests/unit/test_correlation_engine_extended.py",
            "tests/integration/test_moteurs_fiabilite.py",
        ),
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
        tests=(
            "tests/unit/test_resources.py",
            "tests/integration/test_resources_fiabilite.py",
        ),
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
        tests=(
            "tests/unit/test_knowledge_engine.py",
            "tests/integration/test_regles_applicables.py",
        ),
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
        tests=(
            "tests/unit/test_knowledge_engine.py",
            "tests/integration/test_regles_applicables.py",
        ),
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
        tests=(
            "tests/unit/test_reasoning_engine.py",
            "tests/integration/test_regles_applicables.py",
        ),
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
        tests=(
            "tests/unit/test_recommendation_engine.py",
            "tests/integration/test_recommendation_diagnostic.py",
        ),
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
        tests=(
            "tests/unit/test_recommendation_engine.py",
            "tests/integration/test_recommendation_diagnostic.py",
        ),
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
        tests=(
            "tests/unit/test_routers_coverage.py",
            "tests/integration/test_recommendation_diagnostic.py",
        ),
    ),
    Mutation(
        cle="accuse_de_conservation_mensonger",
        fichier="gsie_api/engines/recommendation/engine.py",
        # Cette mutation visait auparavant le statut lui-meme — `enregistre`
        # alors que rien n'etait ecrit. Le statut est maintenant vrai, et son
        # motif a disparu du code. Le meme mensonge reste atteignable, plus
        # bas : ne pas ecrire la ligne `decision` tout en repondant
        # « enregistre », avec un `decision_id` qui ne mene a rien.
        #
        # C'est la forme durable de cette exigence : elle ne porte plus sur une
        # chaine de caractere, mais sur l'ecriture que la chaine affirme.
        ancien="            DecisionModel(\n                id=decision_id,",
        nouveau="            DecisionModel(\n                id=uuid4(),",
        defaut_reproduit=(
            "l'accuse rend un `decision_id` qui ne correspond a aucune ligne : "
            "le forestier ne peut pas retrouver sa trace, et croit l'avoir"
        ),
        tests=(
            "tests/unit/test_recommendation_engine.py",
            "tests/integration/test_recommendation_persistance.py",
        ),
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
        tests=(
            "tests/unit/test_reasoning_engine.py",
            "tests/integration/test_reasoning.py",
        ),
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
        tests=(
            "tests/unit/test_models.py",
            "tests/integration/test_migration_baseline.py",
        ),
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
    Mutation(
        cle="cause_de_blocage_par_defaut",
        fichier="gsie_api/engines/validation/engine.py",
        # Retour au repli : tout controle non repertorie etait etiquete
        # `explicabilite_insuffisante`. La specification exige « la cause
        # precise de blocage » (VALIDATION_ENGINE.md §6).
        ancien="        if nom_controle not in mapping:",
        nouveau="        if False:",
        defaut_reproduit=(
            "le forestier lit une cause de blocage fausse — plausible et "
            "verifiable en apparence — et cherche le defaut au mauvais endroit"
        ),
        tests=("tests/unit/test_validation_engine.py",),
    ),
    Mutation(
        cle="etat_global_hors_du_plancher",
        fichier="gsie_api/engines/diagnostic/engine.py",
        # Le niveau de preuve de l'etat global etait exige a l'entree puis
        # jamais lu : un diagnostic annoncait un plancher B alors que son etat
        # global reposait sur une observation isolee F.
        ancien="        niveaux.append(request.etat_global.evidence_level)",
        nouveau="",
        defaut_reproduit=(
            "le forestier lit une fondation plus solide qu'elle ne l'est : le "
            "plancher ignore l'affirmation qui oriente la recommandation"
        ),
        tests=("tests/unit/test_diagnostic_engine.py",),
    ),
    Mutation(
        cle="non_contournable_seulement_partiel",
        fichier="gsie_api/engines/validation/engine.py",
        # `GSIE-CON-001` est l'article fondateur. Une recommandation non
        # contournable retire au forestier la seule chose qu'il garantit ;
        # la laisser sortir en `partiellement_valide` la fait parvenir a
        # l'utilisateur.
        ancien='            "recommandation_contournable",\n',
        nouveau="",
        defaut_reproduit=(
            "une recommandation non contournable atteint l'utilisateur en "
            "`partiellement_valide` — violation de l'article fondateur"
        ),
        tests=("tests/unit/test_validation_engine.py",),
    ),
    Mutation(
        cle="documentation_publique_en_production",
        fichier="gsie_api/app.py",
        # Mesure OWASP A05 revendiquee par le module, que rien ne surveillait :
        # le schema OpenAPI enumere chaque chemin, chaque modele, chaque champ.
        ancien='        openapi_url=None if is_production else f"{_settings.api_v1_prefix}/openapi.json",',  # noqa: E501
        nouveau='        openapi_url=f"{_settings.api_v1_prefix}/openapi.json",',
        defaut_reproduit=(
            "la surface complete de l'API redevient publique en production, "
            "dans un format directement exploitable"
        ),
        tests=("tests/unit/test_divulgation_production.py",),
    ),
    Mutation(
        cle="lecture_hors_racine_de_stockage",
        fichier="gsie_api/infrastructure/object_storage.py",
        # Contournement de `_resolve_key` sur la seule methode de lecture :
        # c'est exactement le refactoring que seul `put` surveillait.
        ancien=(
            "    async def get(self, key: str, start: int | None = None, "
            "end: int | None = None) -> BinaryIO:\n"
            "        path = self._resolve_key(key)"
        ),
        nouveau=(
            "    async def get(self, key: str, start: int | None = None, "
            "end: int | None = None) -> BinaryIO:\n"
            "        path = self._base / key"
        ),
        defaut_reproduit=(
            "une cle `../../etc/passwd` fait lire un fichier hors du repertoire "
            "de stockage — traversee de repertoire en lecture"
        ),
        tests=("tests/unit/test_object_storage.py",),
    ),
    # --- Tracabilite : « aucune decision perdue » (GSIE-CON-005)
    Mutation(
        cle="recommandations_non_persistees",
        fichier="gsie_api/engines/recommendation/engine.py",
        ancien="        await self._persister_recommandations(recommandations)",
        nouveau="",
        defaut_reproduit=(
            "aucune decision ne peut plus citer la recommandation a laquelle "
            "elle repond : la ligne n'existe pas"
        ),
        tests=(
            "tests/unit/test_recommendation_engine.py",
            "tests/integration/test_recommendation_persistance.py",
        ),
    ),
    Mutation(
        cle="alternatives_non_persistees",
        fichier="gsie_api/engines/recommendation/engine.py",
        # Seule la principale ecrite. Un forestier qui retient une alternative
        # voit alors sa decision refusee, ou intracable.
        ancien="            candidate for reco in recommandations for candidate in (reco, *reco.alternatives)",  # noqa: E501
        nouveau="            candidate for reco in recommandations for candidate in (reco,)",
        defaut_reproduit=(
            "le choix d'une alternative par le forestier devient intracable, "
            "alors que proposer des alternatives est un principe fondateur"
        ),
        tests=(
            "tests/unit/test_recommendation_engine.py",
            "tests/integration/test_recommendation_persistance.py",
        ),
    ),
    Mutation(
        cle="jonction_decision_perdue",
        fichier="gsie_api/engines/recommendation/engine.py",
        # La decision subsiste, mais on ne sait plus a quoi elle repondait.
        ancien="            insert(decision_recommendation).values(",
        nouveau=(
            "            insert(decision_recommendation).values(\n"
            "                decision_id=decision_id,\n"
            "                recommendation_id=decision_id,"
        ),
        defaut_reproduit=(
            "la decision pointe sur elle-meme : on sait qu'un forestier a "
            "refuse quelque chose, sans pouvoir dire quoi"
        ),
        tests=(
            "tests/unit/test_recommendation_engine.py",
            "tests/integration/test_recommendation_persistance.py",
        ),
    ),
    Mutation(
        cle="rationale_inventee",
        fichier="gsie_api/engines/recommendation/engine.py",
        # Le pire des deux mondes : une explication plausible, relue comme la
        # parole du forestier, qu'il n'a jamais donnee (`ADR-009`).
        ancien='            "Aucune justification fournie par le forestier — non exigée "',
        nouveau='            "Recommandation jugée inadaptée à la station par le forestier. "',
        defaut_reproduit=(
            "une explication inventee est consignee et relue comme celle du "
            "forestier, qui n'en a fourni aucune"
        ),
        tests=(
            "tests/unit/test_recommendation_engine.py",
            "tests/integration/test_recommendation_persistance.py",
        ),
    ),
    Mutation(
        cle="decision_sans_recommandation_toleree",
        fichier="gsie_api/engines/recommendation/engine.py",
        ancien=(
            "        if recommandation is None:\n"
            "            raise RecommandationIntrouvableError("
        ),
        nouveau=(
            "        if recommandation is None and False:\n"
            "            raise RecommandationIntrouvableError("
        ),
        defaut_reproduit=(
            "une trace inexploitable est ecrite, puis PostgreSQL refuse la "
            "jonction en erreur serveur au lieu d'un refus metier nomme"
        ),
        tests=(
            "tests/unit/test_recommendation_engine.py",
            "tests/integration/test_recommendation_persistance.py",
        ),
    ),
    # --- Passages de main entre moteurs
    #
    # La suite eprouvait la chaine sur des `Diagnostic` et `Conclusion` ecrits a
    # la main : aucun test ne prenait la sortie *reelle* d'un moteur pour
    # alimenter le suivant. Ces mutations cassent les jointures que
    # `tests/integration/test_chaine_reelle.py` etablit.
    Mutation(
        cle="diagnostic_detache_de_ses_conclusions",
        fichier="gsie_api/engines/diagnostic/engine.py",
        ancien="            conclusions_source=conclusions_source_triees,",
        nouveau="            conclusions_source=conclusions_source_triees[:1],",
        defaut_reproduit=(
            "le diagnostic ne cite plus toutes les conclusions dont il est "
            "issu : la chaine d'inference devient incomplete a la relecture"
        ),
        tests=(
            "tests/unit/test_diagnostic_engine.py",
            "tests/integration/test_chaine_reelle.py",
        ),
    ),
    Mutation(
        cle="ensemble_sans_verification_croisee",
        fichier="gsie_api/engines/validation_pipeline.py",
        # La seule verification croisee de la chaine : un ensemble qui melange
        # un diagnostic et des recommandations issues d'un autre serait presente
        # au forestier comme coherent.
        ancien="    if reco_set.diagnostic_source != diagnostic.diagnostic_id:",
        nouveau="    if False:",
        defaut_reproduit=(
            "un ensemble melangeant un diagnostic et des recommandations issues "
            "d'un autre est valide sans que rien ne le signale"
        ),
        tests=("tests/unit/test_pipeline_cross_engine.py",),
    ),
    # --- Hydratation stationnelle : la quarantaine reste etanche (DEC-000072)
    Mutation(
        cle="quarantaine_lue_pour_ses_valeurs",
        fichier="gsie_api/engines/orchestration/hydration.py",
        ancien='        acceptees = [s for s in soumissions if s.status == "accepted"]',
        nouveau='        acceptees = [s for s in soumissions if s.status != "accepted"]',
        defaut_reproduit=(
            "une soumission en quarantaine est lue pour ses valeurs — la "
            "quarantaine n'est plus etanche et alimente le raisonnement"
        ),
        tests=(
            "tests/integration/test_station_hydration.py",
            "tests/unit/test_station_hydration.py",
        ),
    ),
    # --- Orchestration : brancher, jamais decider
    Mutation(
        cle="conclusion_qualifiee_d_office",
        fichier="gsie_api/engines/orchestration/service.py",
        # Le coeur de l'exigence : une conclusion sans qualification declaree
        # doit faire refuser. La combler par un role par defaut serait classer
        # a la place du forestier, et le conseil sylvicole qui en decoule
        # porterait une chaine complete — invisible.
        ancien="        if manquantes:",
        nouveau="        if False:",
        defaut_reproduit=(
            "une conclusion est classee par la machine, et le diagnostic qui en "
            "decoule paraît complet (GSIE-CON-001, ADR-009)"
        ),
        tests=(
            "tests/unit/test_orchestration_engine.py",
            "tests/integration/test_orchestration.py",
        ),
    ),
    Mutation(
        cle="qualification_rapprochee_par_ressemblance",
        fichier="gsie_api/engines/orchestration/service.py",
        # Rattachement par la derivation partagee du Reasoning Engine. Le
        # remplacer par un rapprochement positionnel classerait une conclusion
        # sous un role qui n'est pas le sien, sans que rien ne le signale.
        ancien="            identifiant = conclusion_id_pour(requete.requete_id, declaree.identifiant_regle)",  # noqa: E501
        nouveau="            identifiant = conclusion_id_pour(requete.requete_id, requete.regles[0].identifiant)",  # noqa: E501
        defaut_reproduit=(
            "toutes les qualifications se rattachent a la meme conclusion : les "
            "autres sont classees au hasard ou manquantes"
        ),
        tests=(
            "tests/unit/test_orchestration_engine.py",
            "tests/integration/test_orchestration.py",
        ),
    ),
    Mutation(
        cle="raisonnement_sterile_rendu_en_succes",
        fichier="gsie_api/engines/orchestration/service.py",
        ancien="        if not inference.conclusions:",
        nouveau="        if False:",
        defaut_reproduit=(
            "un diagnostic vide est produit la ou « aucune regle ne s'applique » "
            "est une reponse — l'appelant interprete le silence"
        ),
        tests=(
            "tests/unit/test_orchestration_engine.py",
            "tests/integration/test_orchestration.py",
        ),
    ),
    Mutation(
        cle="echelle_pedologique_supposee",
        fichier="gsie_api/engines/pedology/soilgrids_client.py",
        # Retour au repli sur l'identite. SoilGrids renvoie le pH multiplie par
        # dix ; supposer un facteur de 1 sort un pH de 52, hors de l'echelle
        # physique 0-14. La regle `pedologie_pH < 5.5` evalue alors 52 < 5.5 —
        # Faux — et un sol acide se diagnostique basique, sans erreur levee.
        ancien="    if facteur is None:",
        nouveau="    if False:",
        defaut_reproduit=(
            "une valeur pedologique sort mise a l'echelle brute, d'un facteur "
            "dix, et inverse silencieusement le diagnostic qui en depend"
        ),
        tests=("tests/unit/test_soilgrids_client.py",),
    ),
    Mutation(
        cle="mesure_hors_definition_admise",
        fichier="gsie_api/engines/climate/schemas.py",
        # Bornes definitionnelles, jamais empiriques : une humidite relative de
        # 250 % n'est pas un record, c'est un pourcentage de saturation
        # depassant la saturation.
        ancien="    humidite_pct: float | None = Field(default=None, ge=0.0, le=100.0)\n    pression_hpa: float | None = Field(default=None, gt=0.0)\n    vent_direction_deg: float | None = Field(default=None, ge=0.0, le=360.0)\n    vent_vitesse_ms: float | None = Field(default=None, ge=0.0)\n    precipitations_1h_mm: float | None = Field(default=None, ge=0.0)\n    source: SourceReference\n\n\nclass ClimateIngestResult",  # noqa: E501
        nouveau="    humidite_pct: float | None = None\n    pression_hpa: float | None = None\n    vent_direction_deg: float | None = None\n    vent_vitesse_ms: float | None = None\n    precipitations_1h_mm: float | None = None\n    source: SourceReference\n\n\nclass ClimateIngestResult",  # noqa: E501
        defaut_reproduit=(
            "une humidite de 250 %, un azimut de 999 degres ou une vitesse de "
            "vent negative alimentent un diagnostic sans objection"
        ),
        tests=("tests/unit/test_climate_bornes_physiques.py",),
    ),
    Mutation(
        cle="zero_absolu_ignore",
        fichier="gsie_api/engines/climate/schemas.py",
        ancien="    temperature_c: float | None = Field(default=None, ge=_ZERO_ABSOLU_C)\n    humidite_pct",  # noqa: E501
        nouveau="    temperature_c: float | None = None\n    humidite_pct",
        defaut_reproduit=(
            "une temperature sous le zero absolu traverse le schema — la "
            "conversion Kelvin appliquee a une valeur hivernale deja en Celsius"
        ),
        tests=("tests/unit/test_climate_bornes_physiques.py",),
    ),
    Mutation(
        cle="valeur_pedologique_hors_unite_admise",
        fichier="gsie_api/engines/pedology/schemas.py",
        # Seconde ligne de defense, independante du client. Elle attrape le
        # defaut `d_factor` quel que soit le producteur de la valeur.
        ancien="        if not minimum <= self.valeur <= maximum:",
        nouveau="        if False:",
        defaut_reproduit=(
            "un pH de 52 ou une teneur en argile de 500 % alimentent un "
            "diagnostic pedologique sans objection"
        ),
        tests=("tests/unit/test_pedology_bornes_unites.py",),
    ),
    # --- Isolement RGPD : la protection tient par la base, pas par le code
    Mutation(
        cle="mecanisme_de_reversion_avec_les_consentements",
        fichier="gsie_api/infrastructure/models/fair_rgpd.py",
        # `data_subject` porte pseudonyme, agent_id et courriel chiffre : c'est
        # la table qui DEFAIT le pseudonymat. La placer avec les consentements
        # donnerait l'apparence de la conformite sans sa propriete principale —
        # un role capable de lire le schema reconstituerait les identites
        # (RGPD art. 32, lignes directrices EDPB 01/2025).
        ancien='    __table_args__ = {"schema": "gsie_rgpd_identites"}',
        nouveau='    __table_args__ = {"schema": "gsie_rgpd"}',
        defaut_reproduit=(
            "le gestionnaire des consentements peut lever le pseudonymat : les "
            "deux pouvoirs se cumulent au lieu de rester distincts"
        ),
        # Le controle de derive, et non les tests d'isolement : la mutation
        # porte sur le MODELE, tandis que les tests d'isolement eprouvent la
        # base construite par la migration. Attribues aux seconds, ces deux
        # mutations ont survecu — le harnais l'a etabli.
        tests=(
            "tests/unit/test_models.py",
            "tests/integration/test_migration_baseline.py",
            "tests/integration/test_isolement_rgpd.py",
        ),
    ),
    Mutation(
        cle="droits_public_conserves_sur_donnees_personnelles",
        fichier="gsie_api/infrastructure/models/governance.py",
        # Sans schema declare, la table retombe dans `public` — atteignable par
        # tout role, comme avant la migration.
        ancien='    __table_args__ = {"schema": "gsie_rgpd"}\n\n    id: Mapped[UUID]',
        nouveau="    id: Mapped[UUID]",
        defaut_reproduit=(
            "une table de donnees personnelles retombe dans `public`, ou tout "
            "moteur de domaine la lit"
        ),
        tests=(
            "tests/unit/test_models.py",
            "tests/integration/test_migration_baseline.py",
            "tests/integration/test_isolement_rgpd.py",
        ),
    ),
    Mutation(
        cle="application_connectee_en_proprietaire",
        fichier="gsie_api/core/config.py",
        # Un proprietaire PostgreSQL conserve des droits implicites que `REVOKE`
        # n'ote pas : l'isolement des donnees personnelles ne s'applique pas a
        # lui. Sans cette garde, il est **disponible sans etre en vigueur** —
        # ce qui etait le cas avant `20260728_0012`, et n'avait ete vu par
        # aucun des douze tests d'isolement.
        ancien="            if utilisateur in _ROLES_PROPRIETAIRES:",
        nouveau="            if False:",
        defaut_reproduit=(
            "l'application demarre en production sous le proprietaire de la "
            "base et lit le mecanisme de reversion du pseudonymat"
        ),
        tests=(
            "tests/unit/test_config.py",
            "tests/integration/test_auth_dev_production_blocker.py",
        ),
    ),
    # `suppression_physique_redevenue_possible` a ete retiree : elle visait
    # `alembic/versions/20260728_0012_role_applicatif.py`, hors du perimetre
    # `src/` que le harnais copie. Elle a ete appliquee au depot lui-meme,
    # ajoutant `DELETE` aux droits du role applicatif — contre `CON-010` — sous
    # un commentaire affirmant le contraire.
    #
    # L'absence de `DELETE` est verifiee la ou elle doit l'etre :
    # `test_isolement_rgpd.py::test_le_role_applicatif_ne_peut_pas_supprimer`,
    # qui joue la migration reelle. `_verifier_perimetre` empeche desormais
    # qu'une mutation sorte de `src/`.
    Mutation(
        cle="schema_botanique_retire",
        fichier="gsie_api/infrastructure/models/ecology.py",
        # Le schema de domaine gsie_botanique est porte par __table_args__ sur
        # chaque modele. Le retirer fait revenir la table dans `public` pour le
        # registre, tandis que la base la conserve dans `gsie_botanique` — le
        # controle de derive detecte l'ecart.
        ancien='    __table_args__ = {"schema": "gsie_botanique"}\n\n\n@register_type("trait_value")',  # noqa: E501
        nouveau='    __table_args__ = {}\n\n\n@register_type("trait_value")',
        defaut_reproduit=(
            "trait_definition revient dans `public` pour le registre SQLAlchemy "
            "mais reste dans `gsie_botanique` en base — derive invisible"
        ),
        tests=(
            "tests/unit/test_models.py",
            "tests/integration/test_migration_baseline.py",
        ),
    ),
    Mutation(
        cle="schema_foret_retire",
        fichier="gsie_api/infrastructure/models/business.py",
        # Même garde pour gsie_foret — le domaine le plus volumineux.
        ancien='    __table_args__ = {"schema": "gsie_foret"}\n\n\n@register_type("intervention")',
        nouveau='    __table_args__ = {}\n\n\n@register_type("intervention")',
        defaut_reproduit=(
            "management_plan revient dans `public` pour le registre mais reste "
            "dans `gsie_foret` en base — derive invisible"
        ),
        tests=(
            "tests/unit/test_models.py",
            "tests/integration/test_migration_baseline.py",
        ),
    ),
    Mutation(
        cle="schema_gouvernance_retire",
        fichier="gsie_api/infrastructure/models/business.py",
        # Même garde pour gsie_gouvernance — la chaîne de décision.
        ancien='    __table_args__ = {"schema": "gsie_gouvernance"}\n\n\n@register_type("compliance_check")',  # noqa: E501
        nouveau='    __table_args__ = {}\n\n\n@register_type("compliance_check")',
        defaut_reproduit=(
            "regulation revient dans `public` pour le registre mais reste dans "
            "`gsie_gouvernance` en base — derive invisible"
        ),
        tests=(
            "tests/unit/test_models.py",
            "tests/integration/test_migration_baseline.py",
        ),
    ),
    Mutation(
        cle="fk_intra_foret_dequalifiee",
        fichier="gsie_api/infrastructure/models/forestry.py",
        # Les FK intra-domaine doivent être qualifiées avec le schema : une
        # reference nue `"site_index_model.id"` ne trouve plus sa table quand
        # elle a changé de schema. La qualification est la garde qui empêche
        # NoReferencedTableError au chargement du registre.
        ancien='ForeignKey("gsie_foret.site_index_model.id")',
        nouveau='ForeignKey("site_index_model.id")',
        defaut_reproduit=(
            "fertility_class ne trouve plus site_index_model — "
            "NoReferencedTableError au chargement du registre"
        ),
        tests=(
            "tests/unit/test_models.py",
            "tests/integration/test_migration_baseline.py",
        ),
    ),
    Mutation(
        cle="garde_anti_invention_desactivee",
        fichier="gsie_api/engines/evidence/anti_invention.py",
        # La garde RFC-0014 force les donnees AI-sourced en evidence_level D +
        # quarantine. La desactiver laisse une extraction LLM (Claude, GPT,
        # Treekipedia) etre ingeree au niveau B — contournant CON-002 (la
        # science avant tout) et CON-001 (l'IA assiste, ne decide jamais).
        ancien="    if not est_ai_sourced(submission):\n        return qualified",
        nouveau="    if True:\n        return qualified",
        defaut_reproduit=(
            "une soumission AI-sourced (auteur='Claude') qualifiee a B par la "
            "matrice est ingeree au niveau B sans quarantine — "
            "contournement de RFC-0014 et CON-002"
        ),
        tests=("tests/unit/test_anti_invention.py",),
    ),
    Mutation(
        cle="rate_limit_bulk_non_differecie",
        fichier="gsie_api/resources/router.py",
        # L'endpoint bulk doit avoir un rate limit plus permissif (600/min)
        # que le unitaire (30/min). Sans cela, l'ingestion de Treekipedia
        # (67 928 especes) prendrait ~200 jours au lieu de ~7 minutes.
        # La mutation remplace la config par le meme rate limit que le unitaire.
        ancien="@_limiter.limit(_settings.rate_limit_bulk)",
        nouveau='@_limiter.limit("30/minute")',
        defaut_reproduit=(
            "l'endpoint bulk herite du rate limit unitaire (30/min) — "
            "l'ingestion de Treekipedia prend ~200 jours au lieu de ~7 min"
        ),
        tests=("tests/unit/test_rate_limit_bulk.py",),
    ),
    Mutation(
        cle="parsing_xml_capabilities_non_garde",
        fichier="gsie_api/engines/gis/telechargement_client.py",
        # L'API de téléchargement IGN retourne du Atom XML, pas du JSON.
        # Si le XML est malformé (réponse tronquée, erreur proxy), ET.ParseError
        # doit être capturé et wrapé dans TelechargementClientError — sans cette
        # garde, l'exception Python brute fuit vers l'appelant (500 non géré).
        ancien="""        try:
            root = ET.fromstring(body)
        except ET.ParseError as exc:
            raise TelechargementClientError(
                f"Échec du parsing XML GetCapabilities : {exc}"
            ) from exc""",
        nouveau="        root = ET.fromstring(body)",
        defaut_reproduit=(
            "un XML malformé fait fuir ET.ParseError au lieu de "
            "TelechargementClientError — l'appelant voit un 500 non géré"
        ),
        tests=("tests/unit/test_telechargement_client.py",),
    ),
    # --- Bot protection : Turnstile (OWASP A07)
    Mutation(
        cle="turnstile_non_verifie_login",
        fichier="gsie_api/auth/router.py",
        ancien=(
            "    turnstile = TurnstileClient(_settings)\n"
            "    if not await turnstile.verify(credentials.turnstile_token, client_ip):"
        ),
        nouveau="    # garde Turnstile désactivée temporairement\n    if False:",
        defaut_reproduit=(
            "un login avec un token Turnstile rejeté passe quand même "
            "— la bot protection est inactive"
        ),
        tests=("tests/unit/test_auth.py",),
    ),
    # --- Protection SSRF egress (RFC-0021 §4.3)
    Mutation(
        cle="ssrf_egress_desactive",
        fichier="gsie_api/shared/http_client.py",
        ancien=(
            "        try:\n"
            "            valider_url_egress(url)\n"
            "        except ValueError as exc:\n"
            '            raise self.exception_class(f"Échec {label} : {exc}") from exc'
        ),
        nouveau=("        # protection SSRF désactivée\n" "        pass"),
        defaut_reproduit=(
            "une requête vers http://169.254.169.254/ (metadata AWS) passe "
            "sans blocage — un client compromis peut accéder aux services internes"
        ),
        tests=("tests/unit/test_ssrf_egress.py",),
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


def _verifier_perimetre(mutation: Mutation) -> None:
    """Refuse une mutation qui viserait un fichier hors de `src/`.

    Le harnais mute une **copie** de `src/` dans un dossier temporaire. Une
    mutation designant un fichier hors de ce perimetre — une migration Alembic,
    un test, un outil — ne trouve rien a muter dans la copie, et rien ne
    garantit qu'un appelant maladroit ne lui passera pas la racine reelle.

    C'est arrive : une mutation visant `alembic/versions/` a ete appliquee au
    depot lui-meme, ajoutant `DELETE` aux droits du role applicatif et
    contredisant `CON-010` — avec, deux lignes plus bas, un commentaire
    affirmant l'inverse. Le degat etait mecanique, invisible au `git diff`
    tant qu'on ne le cherchait pas.

    Le contenu des migrations se verifie par les tests d'integration, qui les
    jouent reellement. Le harnais couvre `src/`, et le declarer ici empeche de
    l'etendre par inadvertance.
    """
    if not (SOURCE / mutation.fichier).exists():
        raise SystemExit(
            f"[{mutation.cle}] `{mutation.fichier}` n'existe pas sous `src/`. "
            "Le harnais ne mute que le code source : une migration ou un test "
            "se verifie par les tests d'integration, jamais par mutation."
        )


def _appliquer(mutation: Mutation, racine_source: Path) -> None:
    _verifier_perimetre(mutation)
    if racine_source.resolve() == SOURCE.resolve():
        raise SystemExit(
            "refus d'appliquer une mutation sur l'arborescence reelle : le "
            "harnais travaille sur une copie temporaire, jamais sur `src/`."
        )
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
