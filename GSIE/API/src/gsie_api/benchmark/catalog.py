"""Catalogue des diagnostics stationnels candidats de GSIE-Bench.

La première ébauche Parelle 2007 était utile pour tester le runner, mais trop
réduite pour représenter un diagnostic forestier.  Les candidats v0.2 couvrent
désormais le contexte, le climat, la topographie, le sol, la flore, le
peuplement, la régénération, l'historique, les risques et la gestion.  Les
valeurs déduites ou manquantes restent explicitement marquées afin de ne pas
transformer une hypothèse BTS en vérité Gold.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .models import ExpectedBehavior, ReferenceRef, ScenarioSpec

SCENARIO_VERSION = "0.2.0"
SUITE_VERSION = "0.1.0"
RICH_SCENARIO_SCHEMA = "station_diagnostic.v2"

REFERENCE_PARELLE_LEGACY = ReferenceRef(
    reference_id="parelle-2007-hal-02653679",
    citation=(
        "Parelle J., Brendel O., Jolivet Y. (2007), Intra- and interspecific "
        "diversity in the response to waterlogging of two co-occurring white oak species, "
        "Tree Physiology 27(7), 1027-1034, DOI 10.1093/treephys/27.7.1027"
    ),
    uri="https://academic.oup.com/treephys/article/27/7/1027/1641099",
    evidence_level="B",
    rights_status="citation_and_derived_annotation_only",
)
REFERENCE_BTS_FICHE = ReferenceRef(
    reference_id="bts-fiche-diagnostic-stationnel-camille-2026",
    citation=(
        "Fiche Diagnostic Stationnel - version intégrée et approfondie, "
        "dossier BTS de Camille Perraudeau"
    ),
    uri="local://documents/bts/FICHE-DE-DIAGNOSTIC-STATIONNEL-CAMILLE.pdf",
    evidence_level="D",
    rights_status="owner_provided_internal_pending_expert_review",
)
REFERENCE_BTS_EIL = ReferenceRef(
    reference_id="bts-eil-longeyroux-placette-2026",
    citation="Diagnostic stationnel - Forêt domaniale du Longeyroux, placette EIL, 26/02/2026",
    uri="local://documents/bts/EIL-Carto/Diagnostic_stationnel_Longeyroux_Placette_EIL.docx",
    evidence_level="D",
    rights_status="owner_provided_internal_pending_expert_review",
)
REFERENCE_BTS_HETRE = ReferenceRef(
    reference_id="bts-diagnostic-hetre-fagus-2026",
    citation="Diagnostic stationnel Fagus sylvatica, dossier BTS de Camille Perraudeau",
    uri="local://documents/bts/bio/Diagnostic-stationnel-Camille-Perraudeau.docx",
    evidence_level="D",
    rights_status="owner_provided_internal_pending_expert_review",
)
REFERENCE_BTS_VERGNE = ReferenceRef(
    reference_id="bts-analyse-parcelle-vergne-hetraie-2026",
    citation=(
        "Analyse de parcelle forestière - hêtraie en futaie régulière, "
        "forêt domaniale de la Vergne"
    ),
    uri="local://documents/bts/pro-madeyre/Analyse-de-parcelle-forestiere.docx",
    evidence_level="D",
    rights_status="owner_provided_internal_pending_expert_review",
)
REFERENCE_INRAE_ACIDITY = ReferenceRef(
    reference_id="inrae-acidification-vosges-pH-2024",
    citation="INRAE, Définitions et documents sur l'acidification des sols, définition du pH",
    uri="https://bef.nancy.hub.inrae.fr/vulgarisation/acidification-dans-les-vosges/definitions-documents",
    evidence_level="C",
    rights_status="citation_only_copyright_inrae",
)

_VARIATIONS: tuple[tuple[str, ExpectedBehavior], ...] = (
    ("complete", "exact"),
    ("missing_data", "abstain_or_warn"),
    ("noisy_data", "exact"),
    ("contradictory_data", "abstain_or_warn"),
    ("major_limiting_factor", "exact"),
    ("dangerous_recommendation", "abstain_or_warn"),
    ("source_absent", "abstain_or_warn"),
    ("territory_change", "out_of_domain"),
    ("period_change", "out_of_domain"),
    ("high_uncertainty", "abstain_or_warn"),
)

_COMMON_INPUTS = {
    "schema_version": RICH_SCENARIO_SCHEMA,
    "provenance": {
        "observed": [],
        "inferred": [],
        "hypothesis": [],
        "missing": [],
        "review_required": [],
    },
    "contexte": {
        "commune": None,
        "massif": None,
        "statut_foncier": None,
        "surface_site_ha": None,
        "surface_unite_ha": None,
        "accessibilite": {},
        "enjeux_reglementaires": [],
    },
    "topographie": {
        "altitude_m": None,
        "position": None,
        "pente_pct": None,
        "exposition": None,
        "microrelief": None,
        "erosion": None,
        "vent": {},
    },
    "climat": {
        "station_reference": None,
        "periode_normale": None,
        "precipitations_annuelles_mm": None,
        "temperature_moyenne_c": None,
        "deficit_hydrique_mm": None,
        "saison_vegetation_mois": None,
        "gel_neige_givre": {},
        "incertitude": [],
    },
    "pedologie": {
        "materiau_parent": None,
        "profondeur_prospectee_cm": None,
        "profondeur_exploitable_cm": None,
        "pH": None,
        "methode_pH": None,
        "texture": None,
        "structure": None,
        "elements_grossiers_pct": None,
        "humus": None,
        "hydromorphie": None,
        "classe_drainage": None,
        "regime_hydrique": None,
        "ru_mm": None,
        "ru_statut": None,
        "obstacles_enracinement": [],
        "horizons": [],
    },
    "flore_biodiversite": {
        "indicateurs": [],
        "gradient_hydrique": None,
        "gradient_trophique": None,
        "gradient_lumiere": None,
        "bois_mort": {},
        "microhabitats": [],
        "faune_traces": [],
    },
    "peuplement": {
        "essences": [],
        "origine": None,
        "regime": None,
        "traitement": None,
        "age_ans": None,
        "recouvrement_pct": None,
        "densite_tiges_ha": None,
        "surface_terriere_m2_ha": None,
        "hauteur_dominante_m": None,
        "hauteur_moyenne_m": None,
        "diametre_moyen_cm": None,
        "diametre_quadratique_cm": None,
        "volume_m3_ha": None,
        "echantillon": {},
        "structure": None,
        "qualite_bois": {},
        "etat_sanitaire": {},
        "stabilite": {},
    },
    "regeneration": {
        "origine": None,
        "essences": [],
        "densite_tiges_ha": None,
        "repartition": None,
        "qualite": None,
        "pression_gibier": None,
        "concurrence": None,
    },
    "historique": {
        "plantation_annee": None,
        "coupes": [],
        "travaux_sylvicoles": [],
        "perturbations": [],
    },
    "gestion": {
        "objectifs": [],
        "contraintes": [],
        "facteurs_limitants_majeurs": [],
        "actions_proposees": [],
        "essences_alternatives": [],
        "horizon_ans": None,
        "debouches": [],
        "incertitudes_decisionnelles": [],
    },
    "mesures_et_calculs": {
        "methode_inventaire": None,
        "surface_placette_m2": None,
        "formules": [],
        "valeurs_estimees": [],
    },
}


def _merge(base: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(_COMMON_INPUTS)
    for key, value in base.items():
        if isinstance(value, dict):
            existing = result.get(key)
            if not isinstance(existing, dict):
                raise ValueError(f"Section de scénario incompatible : {key}")
            existing.update(deepcopy(value))
        else:
            result[key] = deepcopy(value)
    return result


_BASE_CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "gold.longeyroux.001",
        "territory": "longeyroux-meymac",
        "period": "2026",
        "labels": (
            "station_acidiphile_probable",
            "humus_dysmoder",
            "risque_chablis_volis",
            "vulnerabilite_tassement",
        ),
        "factors": ("acidite", "vent", "tassement", "incertitude_age"),
        "references": (REFERENCE_BTS_FICHE, REFERENCE_BTS_EIL, REFERENCE_INRAE_ACIDITY),
        "inputs": _merge(
            {
                "contexte": {
                    "commune": "Meymac",
                    "massif": "Forêt domaniale du Longeyroux",
                    "statut_foncier": "forêt domaniale",
                    "surface_site_ha": 217.11,
                    "surface_unite_ha": None,
                    "accessibilite": {"desserte": "a confirmer", "portance": "sensible"},
                    "enjeux_reglementaires": [
                        "têtes de bassin",
                        "tourbières",
                        "Natura 2000 à vérifier",
                    ],
                },
                "topographie": {
                    "altitude_m": 901,
                    "position": "versant",
                    "pente_pct": 4,
                    "exposition": "Ouest",
                    "microrelief": "couloirs de vent, proximité de dépressions humides",
                    "erosion": "a observer",
                    "vent": {"couloirs": True, "risque": "chablis_volis"},
                },
                "climat": {
                    "station_reference": "Meymac 670 m",
                    "periode_normale": "1981-2010",
                    "precipitations_annuelles_mm": 1268,
                    "temperature_moyenne_c": 9.5,
                    "deficit_hydrique_mm": None,
                    "saison_vegetation_mois": None,
                    "gel_neige_givre": {"givre": "probable", "neige": "a documenter"},
                    "incertitude": ["transposition de la station à 901 m", "saison de végétation"],
                },
                "pedologie": {
                    "materiau_parent": "granite / arène granitique a confirmer",
                    "profondeur_prospectee_cm": 50,
                    "profondeur_exploitable_cm": None,
                    "pH": None,
                    "methode_pH": None,
                    "texture": "limono-sableuse a confirmer",
                    "structure": None,
                    "elements_grossiers_pct": None,
                    "humus": "dysmoder",
                    "hydromorphie": "non observee sur le profil",
                    "classe_drainage": None,
                    "regime_hydrique": "frais a localement mesohygrophile, hypothese",
                    "ru_mm": (70, 110),
                    "ru_statut": "estimation a confirmer",
                    "obstacles_enracinement": ["profondeur utile inconnue", "semelle a rechercher"],
                    "horizons": [],
                },
                "flore_biodiversite": {
                    "indicateurs": [
                        "Cladonia sp. probable",
                        "Calluna vulgaris probable",
                        "Pteridium aquilinum a confirmer",
                        "mousses",
                    ],
                    "gradient_hydrique": "frais a localement mesohygrophile, hypothese",
                    "gradient_trophique": "acidiphile oligotrophe probable",
                    "gradient_lumiere": "ouvert a semi-ouvert",
                    "bois_mort": {"statut": "a relever"},
                    "microhabitats": [],
                    "faune_traces": [],
                },
                "peuplement": {
                    "essences": [{"nom": "Picea abies", "part": ">90%", "statut": "observe"}],
                    "origine": "plantation",
                    "regime": "futaie reguliere",
                    "traitement": "eclaircies, details a confirmer",
                    "age_ans": None,
                    "recouvrement_pct": None,
                    "densite_tiges_ha": 400,
                    "surface_terriere_m2_ha": 18,
                    "hauteur_dominante_m": 25,
                    "hauteur_moyenne_m": 22,
                    "diametre_moyen_cm": 24.2,
                    "diametre_quadratique_cm": 24.5,
                    "volume_m3_ha": (178, 198),
                    "echantillon": {"n": 14, "statut": "mesure terrain"},
                    "structure": "plantation quasi monospécifique",
                    "qualite_bois": {"defauts": ["baionnette a preciser"]},
                    "etat_sanitaire": {
                        "observations": ["chablis", "volis", "coule noir a preciser"]
                    },
                    "stabilite": {"risque": "eleve sous vent et enracinement superficiel possible"},
                },
                "regeneration": {
                    "origine": None,
                    "essences": [],
                    "densite_tiges_ha": None,
                    "repartition": None,
                    "qualite": None,
                    "pression_gibier": None,
                    "concurrence": None,
                },
                "historique": {
                    "plantation_annee": None,
                    "coupes": ["2 eclaircies, dates et intensites a confirmer"],
                    "travaux_sylvicoles": [],
                    "perturbations": ["chablis et volis observes"],
                },
                "gestion": {
                    "objectifs": [
                        "stabilite",
                        "adaptation climatique",
                        "protection des sols et de l eau",
                    ],
                    "contraintes": ["tassement", "tourbiere", "vent", "scolytes potentiels"],
                    "facteurs_limitants_majeurs": ["vent", "portance", "acidite"],
                    "actions_proposees": [
                        "cloisonnements permanents",
                        "interventions progressives",
                        "diversification a caler",
                    ],
                    "essences_alternatives": [
                        "Fagus sylvatica",
                        "Abies alba",
                        "Pinus sylvestris, a valider par micro-station",
                    ],
                    "horizon_ans": 15,
                    "debouches": [],
                    "incertitudes_decisionnelles": [
                        "age",
                        "pH",
                        "profondeur utile",
                        "regeneration",
                    ],
                },
                "mesures_et_calculs": {
                    "methode_inventaire": "placette et mesures terrain, protocole a documenter",
                    "surface_placette_m2": None,
                    "formules": ["G = N x pi x (Dg/2)^2", "V = G x Hm x coefficient de forme"],
                    "valeurs_estimees": ["volume et RU a confirmer par methode locale"],
                },
                "provenance": {
                    "observed": [
                        "altitude",
                        "pente",
                        "exposition",
                        "G",
                        "N",
                        "hauteurs",
                        "diametres",
                        "humus",
                        "flore indicatrice",
                    ],
                    "inferred": ["station acidiphile", "risque chablis", "vulnerabilite tassement"],
                    "hypothesis": [
                        "pH",
                        "RU",
                        "texture",
                        "microhydromorphie",
                        "adaptation des essences",
                    ],
                    "missing": [
                        "age",
                        "pH",
                        "profondeur exploitable",
                        "regeneration",
                        "inventaire biodiversite",
                    ],
                    "review_required": [
                        "classe stationnelle",
                        "recommendations essences",
                        "scolytes",
                    ],
                },
            }
        ),
    },
    {
        "id": "gold.hetre.002",
        "territory": "hetre-moyenne-montagne",
        "period": "2026-2050",
        "labels": (
            "climat_frais_favorable_hetre",
            "reserve_utile_elevee",
            "pression_gibier",
            "saison_vegetation_courte",
        ),
        "factors": ("pression_gibier", "saison_vegetation", "reserve_utile", "secheresse"),
        "references": (REFERENCE_BTS_HETRE, REFERENCE_BTS_FICHE),
        "inputs": _merge(
            {
                "contexte": {
                    "commune": "a preciser",
                    "massif": "moyenne montagne",
                    "statut_foncier": "a preciser",
                    "surface_site_ha": None,
                    "surface_unite_ha": None,
                    "accessibilite": {},
                    "enjeux_reglementaires": [],
                },
                "topographie": {
                    "altitude_m": (900, 1100),
                    "position": "a preciser",
                    "pente_pct": None,
                    "exposition": None,
                    "microrelief": None,
                    "erosion": None,
                    "vent": {},
                },
                "climat": {
                    "station_reference": "station regionale a preciser",
                    "periode_normale": "a preciser",
                    "precipitations_annuelles_mm": 1023,
                    "temperature_moyenne_c": 8.2,
                    "deficit_hydrique_mm": 100,
                    "saison_vegetation_mois": 6,
                    "gel_neige_givre": {"jours_au_dessus_30_c": 3},
                    "incertitude": ["seuils d adaptation a 2050", "station meteorologique exacte"],
                },
                "pedologie": {
                    "materiau_parent": None,
                    "profondeur_prospectee_cm": 90,
                    "profondeur_exploitable_cm": 90,
                    "pH": None,
                    "methode_pH": None,
                    "texture": "limono-argileuse, a confirmer",
                    "structure": None,
                    "elements_grossiers_pct": None,
                    "humus": "dysmoder",
                    "hydromorphie": "engorgement prolonge a eviter",
                    "classe_drainage": None,
                    "regime_hydrique": "mesique a frais",
                    "ru_mm": 175,
                    "ru_statut": "valeur a documenter",
                    "obstacles_enracinement": [],
                    "horizons": [],
                },
                "flore_biodiversite": {
                    "indicateurs": ["Pulmonaria", "Parisette", "Aspérule", "fougere aigle"],
                    "gradient_hydrique": "mesoxerophile a mesophile",
                    "gradient_trophique": "acidicline a neutrocline",
                    "gradient_lumiere": "sciaphile juvenile",
                    "bois_mort": {"present": True, "chandelles": True, "souches_colonisees": True},
                    "microhabitats": ["bois mort", "chandelles"],
                    "faune_traces": ["abroutissement"],
                },
                "peuplement": {
                    "essences": [
                        {"nom": "Fagus sylvatica", "part": "dominante", "statut": "diagnostic"},
                        {
                            "nom": "Pseudotsuga menziesii",
                            "part": "ponctuelle",
                            "statut": "diagnostic",
                        },
                    ],
                    "origine": "a preciser",
                    "regime": "futaie reguliere a confirmer",
                    "traitement": None,
                    "age_ans": None,
                    "recouvrement_pct": 80,
                    "densite_tiges_ha": None,
                    "surface_terriere_m2_ha": None,
                    "hauteur_dominante_m": None,
                    "hauteur_moyenne_m": None,
                    "diametre_moyen_cm": None,
                    "diametre_quadratique_cm": None,
                    "volume_m3_ha": None,
                    "echantillon": {},
                    "structure": "couvert favorable a la regeneration du hetre",
                    "qualite_bois": {},
                    "etat_sanitaire": {"bois_mort": "a interpreter"},
                    "stabilite": {},
                },
                "regeneration": {
                    "origine": "naturelle",
                    "essences": ["Fagus sylvatica", "Pseudotsuga menziesii"],
                    "densite_tiges_ha": None,
                    "repartition": "a preciser",
                    "qualite": "active mais menacee",
                    "pression_gibier": "forte / abroutissement observe",
                    "concurrence": None,
                },
                "historique": {
                    "plantation_annee": None,
                    "coupes": [],
                    "travaux_sylvicoles": [],
                    "perturbations": ["degradations d exploitation"],
                },
                "gestion": {
                    "objectifs": [
                        "maintenir le hetre",
                        "renouvellement durable",
                        "adaptation 2050",
                    ],
                    "contraintes": [
                        "gibier",
                        "saison de vegetation courte",
                        "secheresses repetees",
                        "blessures d exploitation",
                    ],
                    "facteurs_limitants_majeurs": ["pression_gibier", "saison_vegetation"],
                    "actions_proposees": [
                        "protection de regeneration",
                        "gestion sanitaire",
                        "ouvertures progressives",
                    ],
                    "essences_alternatives": ["a etudier selon station"],
                    "horizon_ans": 25,
                    "debouches": [],
                    "incertitudes_decisionnelles": [
                        "territoire exact",
                        "structure et capital",
                        "pH et texture",
                    ],
                },
                "mesures_et_calculs": {
                    "methode_inventaire": "a documenter",
                    "surface_placette_m2": None,
                    "formules": ["RUM par horizons a documenter"],
                    "valeurs_estimees": [],
                },
                "provenance": {
                    "observed": [
                        "altitude",
                        "climat",
                        "profondeur",
                        "RUM",
                        "recouvrement",
                        "regeneration",
                        "abroutissement",
                    ],
                    "inferred": ["adaptation favorable du hetre", "gibier comme frein principal"],
                    "hypothesis": ["classe stationnelle", "productivite", "adaptation 2050"],
                    "missing": [
                        "coordonnees",
                        "pente",
                        "exposition",
                        "pH",
                        "capital",
                        "densite regeneration",
                    ],
                    "review_required": [
                        "seuils autecologiques",
                        "recommandations de gestion",
                        "projection 2050",
                    ],
                },
            }
        ),
    },
    {
        "id": "gold.vergne.003",
        "territory": "vergne-hetraie-domaniale",
        "period": "2026-2041",
        "labels": (
            "hetraie_futaie_reguliere",
            "regeneration_abondante_heterogene",
            "pression_gibier",
            "qualite_technologique_moyenne",
            "eclaircie_amelioration",
        ),
        "factors": ("gibier", "qualite_tiges", "regeneration", "capital_ouvert"),
        "references": (REFERENCE_BTS_VERGNE, REFERENCE_BTS_FICHE),
        "inputs": _merge(
            {
                "contexte": {
                    "commune": "a preciser",
                    "massif": "forêt domaniale de la Vergne",
                    "statut_foncier": "forêt domaniale",
                    "surface_site_ha": 2.5,
                    "surface_unite_ha": 2.5,
                    "accessibilite": {"desserte": "bonne", "pente": "fond de parcelle a exclure"},
                    "enjeux_reglementaires": ["protection de la regeneration"],
                },
                "topographie": {
                    "altitude_m": None,
                    "position": "fond de parcelle partiel",
                    "pente_pct": None,
                    "exposition": None,
                    "microrelief": None,
                    "erosion": None,
                    "vent": {},
                },
                "climat": {
                    "station_reference": None,
                    "periode_normale": None,
                    "precipitations_annuelles_mm": None,
                    "temperature_moyenne_c": None,
                    "deficit_hydrique_mm": None,
                    "saison_vegetation_mois": None,
                    "gel_neige_givre": {},
                    "incertitude": ["adaptation climatique locale"],
                },
                "pedologie": {
                    "materiau_parent": None,
                    "profondeur_prospectee_cm": None,
                    "profondeur_exploitable_cm": None,
                    "pH": None,
                    "methode_pH": None,
                    "texture": None,
                    "structure": None,
                    "elements_grossiers_pct": None,
                    "humus": None,
                    "hydromorphie": None,
                    "classe_drainage": None,
                    "regime_hydrique": None,
                    "ru_mm": None,
                    "ru_statut": "manquant",
                    "obstacles_enracinement": [],
                    "horizons": [],
                },
                "flore_biodiversite": {
                    "indicateurs": [],
                    "gradient_hydrique": None,
                    "gradient_trophique": None,
                    "gradient_lumiere": None,
                    "bois_mort": {"souches": "tres degradees"},
                    "microhabitats": [],
                    "faune_traces": ["degats de gibier"],
                },
                "peuplement": {
                    "essences": [
                        {"nom": "Fagus sylvatica", "part": "dominante", "statut": "observe"},
                        {"nom": "Abies grandis", "part": "ponctuelle", "statut": "observe"},
                    ],
                    "origine": "futaie reguliere",
                    "regime": "futaie",
                    "traitement": "eclaircie d amelioration en abandon",
                    "age_ans": (80, 90),
                    "recouvrement_pct": None,
                    "densite_tiges_ha": 133,
                    "surface_terriere_m2_ha": 9,
                    "hauteur_dominante_m": 28,
                    "hauteur_moyenne_m": None,
                    "diametre_moyen_cm": None,
                    "diametre_quadratique_cm": None,
                    "volume_m3_ha": 108,
                    "echantillon": {"surface_placette_m2": 900, "arbres_adultes": 12},
                    "structure": "etage principal + regeneration en sous-etage",
                    "qualite_bois": {"niveau": "moyenne", "defauts": ["fourches", "conformation"]},
                    "etat_sanitaire": {"niveau": "a surveiller"},
                    "stabilite": {"capital": "ouvert"},
                },
                "regeneration": {
                    "origine": "naturelle",
                    "essences": ["Fagus sylvatica"],
                    "densite_tiges_ha": (15000, 20000),
                    "repartition": "heterogene",
                    "qualite": "abondante",
                    "pression_gibier": "enjeu important",
                    "concurrence": "zones tres denses et zones clairsemees",
                },
                "historique": {
                    "plantation_annee": None,
                    "coupes": ["intervention il y a plus de 10 ans"],
                    "travaux_sylvicoles": ["aucun travail recent identifie"],
                    "perturbations": [],
                },
                "gestion": {
                    "objectifs": [
                        "renouvellement durable",
                        "amelioration qualitative",
                        "bois energie et industrie",
                        "protection regeneration",
                    ],
                    "contraintes": ["gibier", "regeneration", "pente", "cloisonnements"],
                    "facteurs_limitants_majeurs": ["gibier", "qualite_tiges", "capital_ouvert"],
                    "actions_proposees": [
                        "eclaircie amelioration",
                        "protection gibier",
                        "depressage",
                        "reglage lumiere",
                    ],
                    "essences_alternatives": [],
                    "horizon_ans": 15,
                    "debouches": ["bois de chauffage", "bois industrie"],
                    "incertitudes_decisionnelles": [
                        "prix",
                        "volume commercial",
                        "adaptation climatique",
                    ],
                },
                "mesures_et_calculs": {
                    "methode_inventaire": "placette circulaire",
                    "surface_placette_m2": 900,
                    "formules": ["N hectare = N placette / 0.09", "volume par tarif a documenter"],
                    "valeurs_estimees": ["36 m3/ha mobilisables", "90 m3 sur 2.5 ha"],
                },
                "provenance": {
                    "observed": [
                        "essences",
                        "structure",
                        "age approximatif",
                        "placette",
                        "G",
                        "Hdom",
                        "regeneration",
                        "defauts",
                        "gibier",
                    ],
                    "inferred": [
                        "classe de fertilite 2 selon document ONF cite",
                        "eclaircie amelioration",
                    ],
                    "hypothesis": ["prix sur pied", "debouches", "programme a 15 ans"],
                    "missing": [
                        "pedologie",
                        "climat",
                        "coordonnees",
                        "inventaire complet",
                        "tarif de cubage",
                    ],
                    "review_required": [
                        "classe de fertilite",
                        "volume mobilisable",
                        "prescriptions d exploitation",
                        "prix",
                    ],
                },
            }
        ),
    },
)


def _variation_inputs(base: dict[str, Any], variation: str) -> dict[str, Any]:
    inputs: dict[str, Any] = deepcopy(base["inputs"])
    pedologie = inputs["pedologie"]
    if variation == "missing_data":
        inputs["climat"]["precipitations_annuelles_mm"] = None
        inputs["provenance"]["missing"].append("precipitations_annuelles_mm")
        inputs["critical_data_missing"] = True
    elif variation == "noisy_data":
        precipitation = inputs["climat"].get("precipitations_annuelles_mm")
        if isinstance(precipitation, int | float):
            inputs["climat"]["precipitations_annuelles_mm"] = round(float(precipitation) * 1.05, 1)
        if isinstance(pedologie.get("pH"), int | float):
            pedologie["pH"] = round(float(pedologie["pH"]) + 0.2, 2)
    elif variation == "contradictory_data":
        inputs["contradictions"] = {
            "source_a": "observation terrain",
            "source_b": "valeur incompatible a arbitrer",
        }
        inputs["critical_data_conflict"] = True
    elif variation == "major_limiting_factor":
        inputs["gestion"]["facteur_limitant_majeur"] = base["factors"][0]
    elif variation == "dangerous_recommendation":
        inputs["requested_recommendation"] = "essence_non_compatible"
        inputs["critical_recommendation_review"] = True
    elif variation == "source_absent":
        inputs["source_qualifiee_disponible"] = False
    elif variation == "territory_change":
        inputs["territoire_hors_domaine"] = True
    elif variation == "period_change":
        inputs["periode_hors_reference"] = True
    elif variation == "high_uncertainty":
        inputs["incertitude_elevee"] = True
    return inputs


def build_gold_catalog() -> tuple[ScenarioSpec, ...]:
    """Construit 30 scénarios stationnels riches, non encore certifiés Gold."""

    scenarios: list[ScenarioSpec] = []
    for base in _BASE_CASES:
        for variation, behavior in _VARIATIONS:
            scenario_id = f"{base['id']}.{variation}"
            scenarios.append(
                ScenarioSpec(
                    scenario_id=scenario_id,
                    scenario_version=SCENARIO_VERSION,
                    suite_version=SUITE_VERSION,
                    level="gold",
                    visibility="closed",
                    qualification_status="pending_expert_review",
                    territory="hors-domaine-demo"
                    if variation == "territory_change"
                    else base["territory"],
                    period="2035" if variation == "period_change" else base["period"],
                    variation_kind=variation,
                    parent_scenario_id=base["id"],
                    inputs=_variation_inputs(base, variation),
                    expected_labels=base["labels"],
                    required_factors=base["factors"],
                    forbidden_recommendations=("essence_non_compatible",),
                    expected_behavior=behavior,
                    references=base["references"],
                    rights_status="owner_provided_internal_pending_expert_review",
                )
            )
    return tuple(scenarios)


REFERENCE_SYNTHETIC_SILVER = ReferenceRef(
    reference_id="gsie-bench-synthetic-open-silver-v0.1",
    citation="Jeu synthétique interne GSIE-Bench v0.1, destiné aux tests de contrat",
    uri="synthetic://gsie-bench/open-silver-v0.1",
    evidence_level="F",
    rights_status="synthetic_internal",
)


def build_open_silver_catalog() -> tuple[ScenarioSpec, ...]:
    """Construit une suite publique Silver qualifiée, sans prétention Gold."""

    common = {
        "schema_version": "pedology.v1",
        "provenance": {"observed": ["synthetic_fixture"], "missing": []},
        "pedologie": {
            "pH": 4.2,
            "profondeur_cm": 70,
            "engorgement_hivernal": False,
        },
    }
    definitions: tuple[
        tuple[
            str,
            str,
            str,
            str,
            dict[str, Any],
            tuple[str, ...],
            tuple[str, ...],
            ExpectedBehavior,
        ],
        ...,
    ] = (
        (
            "silver.open.pedology.001",
            "synthetic_complete",
            "open-silver-demo",
            "2026",
            common,
            ("acidite_severe", "sol_profond"),
            ("acidite_severe", "sol_profond"),
            "exact",
        ),
        (
            "silver.open.missing.002",
            "synthetic_missing_data",
            "open-silver-demo",
            "2026",
            {**common, "critical_data_missing": True},
            (),
            (),
            "abstain_or_warn",
        ),
        (
            "silver.open.domain.003",
            "synthetic_out_of_domain",
            "open-silver-demo-out-of-domain",
            "2035",
            {**common, "territoire_hors_domaine": True},
            (),
            (),
            "out_of_domain",
        ),
    )
    return tuple(
        ScenarioSpec(
            scenario_id=scenario_id,
            scenario_version="0.1.0",
            suite_version=SUITE_VERSION,
            level="silver",
            visibility="open",
            qualification_status="qualified",
            territory=territory,
            period=period,
            variation_kind=variation,
            parent_scenario_id=scenario_id,
            inputs=inputs,
            expected_labels=expected_labels,
            required_factors=required_factors,
            forbidden_recommendations=("essence_non_compatible",),
            expected_behavior=behavior,
            references=(REFERENCE_SYNTHETIC_SILVER,),
            rights_status="synthetic_internal",
        )
        for (
            scenario_id,
            variation,
            territory,
            period,
            inputs,
            expected_labels,
            required_factors,
            behavior,
        ) in definitions
    )


def rich_scenario_sections(scenario: ScenarioSpec) -> tuple[str, ...]:
    """Retourne les sections obligatoires réellement présentes."""

    return tuple(
        section
        for section in (
            "contexte",
            "topographie",
            "climat",
            "pedologie",
            "flore_biodiversite",
            "peuplement",
            "regeneration",
            "historique",
            "gestion",
            "mesures_et_calculs",
            "provenance",
        )
        if section in scenario.inputs
    )
