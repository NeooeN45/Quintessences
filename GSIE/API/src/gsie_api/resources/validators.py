"""Validation dynamique des données par type de resource.

Valide les champs obligatoires et les enums pour chaque type avant
l'insertion en DB. Évite d'envoyer n'importe quoi dans `data`.

Deux portes distinctes, volontairement séparées (P0 2026-07-26) :

- `validate_resource_payload` — bornes du **message reçu** (longueur des
  chaînes, nombre de champs). Elles protègent l'API contre un corps abusif
  et ne s'appliquent donc qu'à ce que l'appelant envoie.
- `validate_resource_state` — invariants de l'**état complet** de la
  resource (champs obligatoires, enums, règles métier conditionnelles).
  Ils décrivent ce qu'une resource a le droit d'être une fois écrite, et
  doivent donc être vérifiés sur l'état final, création comme mise à jour.

`validate_resource_data` reste la composition des deux, pour le chemin de
création et pour les appelants historiques.
"""

import re
from collections.abc import Callable
from enum import Enum
from typing import Any
from urllib.parse import urlsplit

from gsie_api.data.contracts import normalize_keywords, normalize_slug, validate_domain
from gsie_api.infrastructure.models.enums import (
    AccessMethod,
    ActivityType,
    AgentType,
    CapabilityType,
    ClaimKind,
    ConsentScope,
    ConstraintType,
    CorrelationMethod,
    CorrelationStrength,
    DatasetHealthStatus,
    DatasetPurpose,
    DatasetStatus,
    DiagnosticGlobalState,
    DiagnosticType,
    DiagnosticValidationStatus,
    EcologicalProcessType,
    EvidenceLevel,
    FeatureSourceType,
    FlowDirection,
    FlowType,
    GoalType,
    HealthRiskSeverity,
    HypothesisStatus,
    IdentificationDecisionStatus,
    LegalBasis,
    LifecycleStatus,
    MaterielBaseCategory,
    MediaType,
    ModelType,
    PhenomenonType,
    PIDType,
    ProviderType,
    QualityDimension,
    QuestionType,
    RelationCategory,
    RuleSubtype,
    SampleType,
    ScaleLevel,
    ScenarioSubtype,
    ScenarioType,
    SilviculturalSystemCategory,
    SourceNature,
    SourceSubtype,
    StateType,
    TemporalGranularity,
    UncertaintyType,
    UsageRights,
    ValueType,
)

# Mappe type_name → {champ: enum_class}
# Seuls les champs enum sont validés ici. Les champs obligatoires (non-None) sont listés séparément.
_ENUM_FIELDS: dict[str, dict[str, type[Enum]]] = {
    "assertion": {
        "claim_kind": ClaimKind,
        "lifecycle_status": LifecycleStatus,
        "rule_subtype": RuleSubtype,
    },
    "observation": {},
    "result": {"value_type": ValueType},
    "uncertainty": {"type": UncertaintyType},
    "quality_assessment": {"dimension": QualityDimension},
    "activity": {"type": ActivityType},
    "agent": {"type": AgentType},
    "source": {"subtype": SourceSubtype, "source_nature": SourceNature},
    "media": {"type": MediaType},
    "temporal_context": {"granularity": TemporalGranularity},
    "model": {"type": ModelType},
    "dataset": {"purpose": DatasetPurpose},
    "dataset_version": {
        "status": DatasetStatus,
        "evidence_level": EvidenceLevel,
    },
    "distribution": {"access_method": AccessMethod},
    "feature": {"source_type": FeatureSourceType},
    "scale_context": {"level": ScaleLevel},
    "phenomenon": {"phenomenon_type": PhenomenonType},
    "ecological_process": {"process_type": EcologicalProcessType},
    "relation_type": {"category": RelationCategory},
    "correlation": {
        "method": CorrelationMethod,
        "strength": CorrelationStrength,
        "lifecycle_status": LifecycleStatus,
    },
    "capability": {
        "capability_type": CapabilityType,
        "provider_type": ProviderType,
    },
    # Diagnostic Engine — persistance des diagnostics (P0 technique 2026-07-26).
    "diagnostic": {
        "type_diagnostic": DiagnosticType,
        "etat_global": DiagnosticGlobalState,
        "statut_validation": DiagnosticValidationStatus,
        "evidence_level_plancher": EvidenceLevel,
    },
    "scenario": {
        "scenario_type": ScenarioType,
        "scenario_subtype": ScenarioSubtype,
    },
    "question": {"question_type": QuestionType},
    "hypothesis": {"status": HypothesisStatus},
    "rights_statement": {"usage_rights": UsageRights},
    "data_rights_statement": {"usage_rights": UsageRights},
    "dataset_health": {"health_status": DatasetHealthStatus},
    "conflict_cluster": {},  # status est un enum ConflictStatus mais pas dans la mappe encore
    "flow": {"flow_type": FlowType, "direction": FlowDirection},
    "goal": {"goal_type": GoalType},
    "constraint": {"constraint_type": ConstraintType},
    "sample": {"sample_type": SampleType},
    "consent": {"scope": ConsentScope, "legal_basis": LegalBasis},
    "persistent_identifier": {"pid_type": PIDType},
    "evidence_assessment": {"level": EvidenceLevel},
    "ecological_state": {
        "state_type": StateType,
    },
    # RFC-0016 — schéma forestier spécialisé (types 81-90, tranches 1-5/10)
    "autecology_profile": {"evidence_level": EvidenceLevel},
    "site_index_model": {},
    "fertility_class": {},
    "station_type": {},
    "station_observation": {},
    "silvicultural_system": {"category": SilviculturalSystemCategory},
    "silvicultural_rule": {"evidence_level": EvidenceLevel},
    "provenance_material": {"base_material_category": MaterielBaseCategory},
    "diagnostic_protocol": {},
    "health_risk": {"severity": HealthRiskSeverity},
    # RFC-0018 — identification botanique assistée Pl@ntNet (tranche 1/N, DEC-000030)
    "botanical_identification_request": {},
    "botanical_identification_result": {},
    "botanical_identification_decision": {"status": IdentificationDecisionStatus},
}

# Champs obligatoires (non-None) par type
_REQUIRED_FIELDS: dict[str, list[str]] = {
    "assertion": ["claim_kind", "lifecycle_status"],
    "observation": ["subject_id"],
    "result": ["observation_id", "value_type"],
    "method": ["name", "description"],
    "instrument": ["name", "type"],
    "uncertainty": ["type"],
    "quality_assessment": [
        "target_id",
        "dimension",
        "score",
        "method",
        "assessed_at",
        "assessment_run_id",
        "policy_version",
        "weight",
    ],
    "activity": ["type", "started_at"],
    "agent": ["name", "type"],
    # Auteur et date obligatoires : une source qui ne peut pas etre citee
    # n'est pas une source (CON-005). `SourceReference` les exige, et une
    # conclusion doit pouvoir nommer qui a ecrit ce qu'elle invoque.
    "source": ["title", "subtype", "source_nature", "auteur", "date_publication"],
    "citation": ["source_id", "target_id", "citation_role"],
    "unit": ["symbol", "name"],
    "temporal_context": [
        "valid_time_start",
        "transaction_time_start",
        "granularity",
    ],
    "media": ["type", "url", "mime_type"],
    "model": ["name", "type", "description"],
    "model_run": ["model_version_id", "started_at"],
    "dataset": ["title", "description"],
    "model_version": ["model_id", "version"],
    "dataset_version": ["dataset_id", "version"],
    "data_rights_statement": ["licence", "usage_rights"],
    "dataset_health": [
        "dataset_version_id",
        "distribution_id",
        "checked_at",
        "health_status",
    ],
    "data_asset": [
        "dataset_version_id",
        "format",
        "size_bytes",
        "checksum",
        "archived_at",
    ],
    "distribution": ["dataset_version_id", "access_method", "licence"],
    "feature": ["name", "description", "source_type"],
    "feature_set": ["name", "description"],
    "inference": [
        "model_version_id",
        "feature_set_id",
        "confidence",
        "inferred_at",
    ],
    "scale_context": ["level"],
    "phenomenon": ["phenomenon_type", "name"],
    "ecological_process": ["process_type", "name"],
    "relation_type": ["category", "label", "description"],
    "sampling_event": ["name", "spatial_design"],
    "trait_definition": ["name", "description"],
    "trait_value": ["trait_definition_id", "entity_id"],
    "question": ["text", "question_type", "asked_at"],
    "hypothesis": ["question_id", "text", "status"],
    "decision": ["decided_by", "decision_text", "rationale", "decided_at"],
    "recommendation": [
        "recommended_by",
        "recommendation_text",
        "confidence",
    ],
    "scenario": ["name", "scenario_type", "description"],
    "correlation": ["method", "strength", "confidence"],
    # `contenu` est obligatoire : un diagnostic dont le corps manque serait
    # une ligne citable mais illisible, donc incontestable (GSIE-CON-004).
    "diagnostic": [
        "requete_origine",
        "station_id",
        "type_diagnostic",
        "etat_global",
        "statut_validation",
        "confiance",
        "evidence_level_plancher",
        "date_diagnostic",
        "contenu",
    ],
    "ecosystem_service": ["name", "description"],
    "capability": [
        "name",
        "capability_type",
        "provider_type",
        "provider_id",
    ],
    "rights_statement": ["licence", "usage_rights"],
    "access_policy": ["target_id", "principal", "permission"],
    "sensitivity_classification": ["target_id", "level", "reason"],
    "conflict_cluster": ["description"],
    "flow": [
        "flow_type",
        "source_id",
        "sink_id",
        "magnitude",
        "magnitude_unit_id",
    ],
    "confidence_graph": ["root_resource_id", "computed_at"],
    "goal": ["goal_type", "name", "description"],
    "constraint": ["constraint_type", "name", "description"],
    "knowledge_lineage": ["root_id", "computed_at"],
    "experiment": ["name", "conducted_by"],
    "terrain_session": ["name", "session_type", "started_at"],
    "ecological_state": ["spatial_scope_id", "state_type"],
    "sample": ["sample_type", "subject_id", "material"],
    "consent": [
        "data_subject_id",
        "purpose",
        "granted_at",
        "legal_basis",
    ],
    "data_subject": ["agent_id", "pseudonymized_id"],
    "persistent_identifier": [
        "target_id",
        "pid_type",
        "value",
        "authority",
        "registered_at",
    ],
    "concept": ["preferred_label", "description"],
    "vocabulary": ["name", "namespace", "description"],
    "controlled_term": ["vocabulary_id", "code", "label"],
    "instance": ["concept_id"],
    "predicate": ["label"],
    "evidence_assessment": ["assertion_id", "level", "method", "evaluated_at"],
    # RFC-0016 — schéma forestier spécialisé (§3.1, §5 Phase A point 3 : porte
    # de validation, aucune de ces entités sans ses champs non négociables,
    # même à travers l'API générique de resources, pas seulement via les
    # schémas Pydantic des engines).
    "autecology_profile": [
        "species_entity_id",
        "variable",
        # Domaine de validite obligatoire (DEC-000038) : une connaissance
        # autecologique sans territoire declare serait appliquee partout, y
        # compris hors de la zone que sa source couvre. Le silence ne vaut pas
        # universalite — la declarer est un acte explicite.
        "territory_description",
        "evidence_level",
        "source_id",
    ],
    "site_index_model": [
        "species_entity_id",
        "name",
        "method",
        "reference_age_years",
        "age_convention",
        "calibration_region",
        "source_id",
    ],
    "fertility_class": [
        "species_entity_id",
        "site_index_model_id",
        "class_label",
        "reference_age_years",
        "calibration_region",
        "source_id",
    ],
    "station_type": ["guide", "guide_version", "validity_zone_description", "source_id"],
    "station_observation": ["plot_reference", "observed_at", "source_id"],
    "silvicultural_system": ["name", "category", "source_id"],
    "silvicultural_rule": [
        "required_context",
        # Domaine de validite geographique obligatoire (DEC-000038). Distinct
        # de `required_context`, qui decrit un contexte sylvicole et non une
        # zone : les deux ne sont pas interchangeables.
        "validity_zone_description",
        "trigger",
        "action",
        "intensity",
        "evidence_level",
        "source_id",
    ],
    "provenance_material": [
        "species_entity_id",
        "provenance_region",
        "base_material",
        "base_material_category",
        "aid_eligible",
        "decree_version",
        "source_id",
    ],
    "diagnostic_protocol": [
        "name",
        "version",
        "criteria_description",
        "thresholds_description",
        "source_id",
    ],
    "health_risk": ["subject_id", "symptom_observed", "observed_at", "source_id"],
    # RFC-0018 — identification botanique assistée Pl@ntNet (tranche 1/N, DEC-000030)
    "botanical_identification_request": ["requested_by_id", "photos", "captured_at"],
    "botanical_identification_result": [
        "request_id",
        "provider",
        "provider_engine_version",
        "candidates",
        "received_at",
    ],
    "botanical_identification_decision": ["result_id", "status"],
}


def _validate_autecology_profile_conditional(data: dict[str, Any]) -> list[str]:
    """`value_numeric` ou `value_text` requis (au moins l'un des deux).

    Reflète la contrainte SQL `ck_autecology_profile_value_present` et
    `AutecologyProfileCreate.model_post_init` — même règle imposée ici
    pour l'API générique de resources (RFC-0016 §4).
    """
    if data.get("value_numeric") is None and data.get("value_text") is None:
        return ["value_numeric ou value_text requis (au moins l'un des deux)"]
    return []


def _validate_station_observation_conditional(data: dict[str, Any]) -> list[str]:
    """`determination_uncertainty` obligatoire si `station_type_id` est absent.

    Une observation qui ne résout aucun `StationType` avec certitude
    doit le dire explicitement, jamais forcer un rattachement arbitraire
    (RFC-0016 §4).
    """
    if data.get("station_type_id") is None and not data.get("determination_uncertainty"):
        return [
            "determination_uncertainty requis quand station_type_id est absent "
            "(une observation non résolue doit expliciter son incertitude)"
        ]
    return []


def _validate_silvicultural_rule_conditional(data: dict[str, Any]) -> list[str]:
    """`human_validator` requis si `status` vaut `accepted`.

    Reflète la contrainte SQL `ck_silvicultural_rule_human_validation_required`
    — jamais d'auto-validation par le pipeline d'extraction (RFC-0016 §3.2).
    """
    if data.get("status") == "accepted" and not data.get("human_validator"):
        return ["human_validator requis quand status='accepted'"]
    return []


def _validate_health_risk_conditional(data: dict[str, Any]) -> list[str]:
    """`confirmation_method` requis si `confirmed_causal_agent` est renseigné.

    Reflète la contrainte SQL `ck_health_risk_confirmation_requires_method`
    — un agent « confirmé » sans méthode citée serait une invention
    silencieuse (ADR-009).
    """
    if data.get("confirmed_causal_agent") and not data.get("confirmation_method"):
        return ["confirmation_method requis quand confirmed_causal_agent est renseigné"]
    return []


_CHECKSUM_HEX = re.compile(r"^[0-9a-fA-F]+$")
_CHECKSUM_ALGORITHMS = frozenset({"md5", "sha1", "sha-1", "sha256", "sha-256", "sha512", "sha-512"})


def _validate_data_asset_size(data: dict[str, Any]) -> list[str]:
    """Refuse toute taille ambiguë, tronquée ou négative."""
    size = data.get("size_bytes")
    if isinstance(size, bool):
        size_value: int | None = None
    elif isinstance(size, int):
        size_value = size
    elif isinstance(size, str):
        try:
            size_value = int(size.strip())
        except ValueError:
            size_value = None
    else:
        size_value = None
    if size_value is None or size_value < 0:
        return ["size_bytes doit être un entier supérieur ou égal à zéro"]
    return []


def _validate_data_asset_text_fields(data: dict[str, Any]) -> list[str]:
    """Valide les champs courts avant leur persistance SQL."""
    errors: list[str] = []
    for field, maximum in {
        "format": 50,
        "checksum": 200,
        "checksum_algorithm": 50,
    }.items():
        value = data.get(field)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} doit être une chaîne non vide")
        elif len(value) > maximum:
            errors.append(f"{field} dépasse la taille maximale de {maximum} caractères")
    return errors


def _validate_data_asset_checksum(data: dict[str, Any]) -> list[str]:
    """Vérifie la cohérence entre algorithme déclaré et empreinte."""
    errors: list[str] = []
    checksum = data.get("checksum")
    algorithm = data.get("checksum_algorithm")
    if algorithm is None:
        return errors
    if not isinstance(algorithm, str) or not algorithm.strip():
        return ["checksum_algorithm doit être un algorithme non vide"]
    normalized_algorithm = algorithm.strip().lower()
    if normalized_algorithm not in _CHECKSUM_ALGORITHMS:
        return [f"Algorithme de checksum inconnu : {algorithm}"]
    normalized_digest = normalized_algorithm.replace("-", "")
    expected_length = {"sha256": 64, "sha512": 128}.get(normalized_digest)
    if expected_length is None:
        return errors
    if not isinstance(checksum, str) or not _CHECKSUM_HEX.fullmatch(checksum):
        errors.append("checksum doit être hexadécimal pour l'algorithme déclaré")
    elif len(checksum) != expected_length:
        errors.append(
            f"checksum doit contenir {expected_length} caractères hexadécimaux pour {algorithm}"
        )
    return errors


def _validate_data_asset_uri(
    field: str, value: object, allowed_schemes: frozenset[str]
) -> list[str]:
    """Valide une URI sans identifiant ni schéma implicite."""
    if value is None:
        return []
    if not isinstance(value, str) or not value.strip():
        return [f"{field} doit être une URI non vide"]
    if len(value) > 500:
        return [f"{field} dépasse la taille maximale de 500 caractères"]
    try:
        parsed = urlsplit(value)
    except ValueError:
        return [f"{field} est une URI malformée"]
    scheme = parsed.scheme.lower()
    if scheme not in allowed_schemes:
        return [f"{field} utilise un schéma interdit : {scheme or '(absent)'}"]
    errors: list[str] = []
    if parsed.username is not None or parsed.password is not None:
        errors.append(f"{field} ne doit pas contenir d'identifiants")
    if scheme == "s3" and not parsed.netloc:
        errors.append(f"{field} doit indiquer un bucket S3")
    if scheme in {"http", "https"} and not parsed.netloc:
        errors.append(f"{field} doit indiquer un hôte")
    if scheme == "local" and not parsed.path:
        errors.append(f"{field} doit indiquer une clé locale")
    return errors


def _validate_data_asset_storage_uris(data: dict[str, Any]) -> list[str]:
    """Valide séparément les URI interne et fournisseur."""
    errors = _validate_data_asset_uri(
        "storage_uri", data.get("storage_uri"), frozenset({"local", "s3"})
    )
    errors.extend(
        _validate_data_asset_uri(
            "original_uri",
            data.get("original_uri"),
            frozenset({"http", "https", "s3"}),
        )
    )
    return errors


def _validate_data_asset_conditional(data: dict[str, Any]) -> list[str]:
    """Compose les validations indépendantes d'un actif archivé."""
    errors = _validate_data_asset_size(data)
    errors.extend(_validate_data_asset_text_fields(data))
    errors.extend(_validate_data_asset_checksum(data))
    errors.extend(_validate_data_asset_storage_uris(data))

    return errors


def _validate_dataset_conditional(data: dict[str, Any]) -> list[str]:
    """Valide l'identité et le vocabulaire contrôlé d'un Dataset."""
    errors: list[str] = []
    slug = data.get("slug")
    if slug is not None:
        try:
            normalize_slug(slug)
        except ValueError as exc:
            errors.append(str(exc))

    primary_domain = data.get("primary_domain")
    if primary_domain is not None:
        try:
            primary_domain = validate_domain(primary_domain)
        except ValueError as exc:
            errors.append(str(exc))

    domains = data.get("domains")
    if domains is not None:
        if not isinstance(domains, list):
            errors.append("domains doit être une liste")
        else:
            try:
                normalized_domains = [validate_domain(value) for value in domains]
                if primary_domain is not None and primary_domain in normalized_domains:
                    errors.append("primary_domain ne doit pas être répété dans domains")
            except (TypeError, ValueError) as exc:
                errors.append(str(exc))

    tags = data.get("tags")
    if tags is not None:
        if not isinstance(tags, list):
            errors.append("tags doit être une liste")
        else:
            try:
                normalize_keywords(tags)
            except ValueError as exc:
                errors.append(str(exc))

    if (primary_domain is not None or domains) and not data.get("domain_vocabulary_version"):
        errors.append("domain_vocabulary_version requis quand un domaine est renseigné")
    return errors


def _validate_dataset_version_temporal(data: dict[str, Any]) -> list[str]:
    """Vérifie l'ordre de la couverture temporelle quand il est comparable."""
    start = data.get("temporal_coverage_start")
    end = data.get("temporal_coverage_end")
    if start is None or end is None:
        return []
    try:
        if start > end:
            return ["temporal_coverage_start doit précéder temporal_coverage_end"]
    except TypeError:
        # La couche de schéma produira ensuite une erreur 422 stable pour une
        # date malformée ; cette porte ne doit pas provoquer un 500.
        return []
    return []


def _dataset_version_status_value(data: dict[str, Any]) -> object:
    """Normalise un statut Python ou JSON sans le valider deux fois."""
    status = data.get("status", DatasetStatus.discovered)
    return status.value if isinstance(status, DatasetStatus) else status


def _validate_dataset_version_release(data: dict[str, Any]) -> list[str]:
    """Exige une date de publication aux statuts qualifiés."""
    status_value = _dataset_version_status_value(data)
    requires_release = {
        DatasetStatus.validated.value,
        DatasetStatus.staging.value,
        DatasetStatus.production.value,
    }
    if status_value in requires_release and data.get("release_date") is None:
        return ["release_date requis avant la publication qualifiée"]
    return []


def _validate_dataset_version_schema(data: dict[str, Any]) -> list[str]:
    """Exige l'empreinte du schéma après son analyse."""
    status_value = _dataset_version_status_value(data)
    requires_schema = {
        DatasetStatus.schema_analyzed.value,
        DatasetStatus.security_checked.value,
        DatasetStatus.validated.value,
        DatasetStatus.staging.value,
        DatasetStatus.production.value,
    }
    if status_value in requires_schema and not data.get("schema_hash"):
        return ["schema_hash requis à partir de SCHEMA_ANALYZED"]
    return []


def _validate_dataset_version_evidence(data: dict[str, Any]) -> list[str]:
    """Exige une base de preuve traçable uniquement en production."""
    if _dataset_version_status_value(data) != DatasetStatus.production.value:
        return []
    errors: list[str] = []
    if data.get("evidence_level") is None:
        errors.append("evidence_level requis en production")
    if data.get("evidence_assessed_at") is None:
        errors.append("evidence_assessed_at requis en production")
    basis = data.get("evidence_basis")
    if not isinstance(basis, dict) or not basis.get("justification"):
        errors.append("evidence_basis.justification requis en production")
    if isinstance(basis, dict) and not (basis.get("source_ids") or basis.get("citation_ids")):
        errors.append("evidence_basis doit référencer des sources ou citations")
    return errors


def _validate_dataset_version_conditional(data: dict[str, Any]) -> list[str]:
    """Compose les portes indépendantes de qualification d'une version."""
    errors = _validate_dataset_version_temporal(data)
    errors.extend(_validate_dataset_version_release(data))
    errors.extend(_validate_dataset_version_schema(data))
    errors.extend(_validate_dataset_version_evidence(data))
    return errors


def _validate_dataset_health_conditional(data: dict[str, Any]) -> list[str]:
    """Valide les bornes d'un contrôle de santé append-only."""
    errors: list[str] = []
    latency = data.get("latency_ms")
    if latency is not None and (
        isinstance(latency, bool) or not isinstance(latency, int | float) or latency < 0
    ):
        errors.append("latency_ms doit être un nombre supérieur ou égal à zéro")
    http_status = data.get("http_status")
    if http_status is not None and (
        isinstance(http_status, bool)
        or not isinstance(http_status, int)
        or not 100 <= http_status <= 599
    ):
        errors.append("http_status doit être un entier HTTP entre 100 et 599")
    return errors


# Règles métier conditionnelles (au-delà des champs simplement obligatoires ou
# des enums) — chacune reflète une contrainte SQL déjà en place, appliquée ici
# également à l'API générique de resources (même porte de validation que les
# champs obligatoires de `fertility_class`, RFC-0016 §5 Phase A point 3).
_CONDITIONAL_RULES: dict[str, Callable[[dict[str, Any]], list[str]]] = {
    "autecology_profile": _validate_autecology_profile_conditional,
    "station_observation": _validate_station_observation_conditional,
    "silvicultural_rule": _validate_silvicultural_rule_conditional,
    "health_risk": _validate_health_risk_conditional,
    "data_asset": _validate_data_asset_conditional,
    "dataset": _validate_dataset_conditional,
    "dataset_version": _validate_dataset_version_conditional,
    "dataset_health": _validate_dataset_health_conditional,
}


MAX_STRING_LENGTH = 10000
MAX_FIELDS = 50


class ResourceValidationError(ValueError):
    """Erreur métier de validation d'une resource.

    Distincte d'un `ValueError` nu : elle transporte la liste complète des
    erreurs et le type concerné, pour que la couche HTTP produise une
    réponse 422 stable sans reformater un message libre.
    """

    def __init__(self, type_name: str, errors: list[str]) -> None:
        self.type_name = type_name
        self.errors = list(errors)
        super().__init__(f"Validation échouée : {'; '.join(self.errors)}")


def _normalise_valeur_enum(value: Any) -> Any:
    """Ramène un membre d'Enum à sa valeur brute.

    L'état relu depuis la base expose des membres d'Enum Python, alors qu'un
    corps JSON expose des chaînes. Les deux doivent être jugés à l'identique.
    """
    return value.value if isinstance(value, Enum) else value


def validate_resource_payload(data: dict[str, Any]) -> list[str]:
    """Valide les bornes du message reçu (protection DoS, OWASP A04).

    Ne s'applique qu'aux champs effectivement envoyés par l'appelant : ce
    sont des limites de transport, jamais des invariants de la resource.
    """
    errors: list[str] = []

    for field, value in data.items():
        if isinstance(value, str) and len(value) > MAX_STRING_LENGTH:
            errors.append(f"Champ {field} trop long : {len(value)} chars (max {MAX_STRING_LENGTH})")

    if len(data) > MAX_FIELDS:
        errors.append(f"Trop de champs : {len(data)} (max {MAX_FIELDS})")

    return errors


def validate_resource_state(type_name: str, state: dict[str, Any]) -> list[str]:
    """Valide les invariants de l'état complet d'une resource.

    Args:
        type_name: Type de resource (ex. "assertion", "observation").
        state: État complet du type — pas un patch partiel.

    Returns:
        Liste des erreurs de validation (vide si OK).
    """
    errors: list[str] = []

    # 1. Champs obligatoires
    required = _REQUIRED_FIELDS.get(type_name, [])
    for field in required:
        if field not in state or state[field] is None:
            errors.append(f"Champ obligatoire manquant : {field}")

    # 2. Validation des enums
    enum_fields = _ENUM_FIELDS.get(type_name, {})
    for field, enum_cls in enum_fields.items():
        if field in state and state[field] is not None:
            value = _normalise_valeur_enum(state[field])
            valid_values = {e.value for e in enum_cls}
            if value not in valid_values:
                errors.append(
                    f"Valeur invalide pour {field} : '{value}'. "
                    f"Valeurs acceptées : {sorted(valid_values)}"
                )

    # 3. Règles métier conditionnelles (reflètent les contraintes SQL)
    conditional_rule = _CONDITIONAL_RULES.get(type_name)
    if conditional_rule is not None:
        errors.extend(conditional_rule(_normalise_etat(state)))

    return errors


def _normalise_etat(state: dict[str, Any]) -> dict[str, Any]:
    """Normalise les membres d'Enum d'un état avant les règles conditionnelles.

    `_validate_silvicultural_rule_conditional` compare `status` à la chaîne
    `"accepted"` : relu depuis la base, ce champ est un membre d'Enum.
    """
    return {key: _normalise_valeur_enum(value) for key, value in state.items()}


def validate_resource_data(type_name: str, data: dict[str, Any]) -> list[str]:
    """Valide les données d'une resource selon son type.

    Composition des deux portes — utilisée à la création, où le message reçu
    est aussi l'état final.

    Args:
        type_name: Type de resource (ex. "assertion", "observation").
        data: Champs spécifiques au type.

    Returns:
        Liste des erreurs de validation (vide si OK).
    """
    return validate_resource_state(type_name, data) + validate_resource_payload(data)
