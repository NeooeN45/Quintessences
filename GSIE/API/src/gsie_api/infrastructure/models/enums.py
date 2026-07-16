"""Enums PostgreSQL pour le métamodèle v6.2 (§3 du métamodèle).

Tous les enums sont définis comme des enums Python (str, Enum) pour
SQLAlchemy 2.0 + Pydantic v2. En DB, ils sont créés comme des types
ENUM PostgreSQL par la migration Alembic 0002.

Source : GSIE/ARCHITECTURE/ECOSYSTEM_METAMODEL.md §3.3 à §3.22
"""

from enum import Enum


# §3.3 — Assertion.claim_kind
class ClaimKind(str, Enum):
    observation = "observation"
    relation = "relation"
    rule = "rule"
    threshold = "threshold"
    model = "model"
    classification = "classification"
    absence = "absence"


# §3.4 — Assertion.lifecycle_status (réutilisé par Correlation)
class LifecycleStatus(str, Enum):
    draft = "draft"
    proposed = "proposed"
    accepted = "accepted"
    superseded = "superseded"
    rejected = "rejected"
    deprecated = "deprecated"


# §3.5 — Result.value_type
class ValueType(str, Enum):
    numeric = "numeric"
    term = "term"
    media_ref = "media_ref"
    entity_ref = "entity_ref"
    computed = "computed"
    absence = "absence"


# §3.6 — Source.source_nature
class SourceNature(str, Enum):
    data_provider = "data_provider"
    knowledge_provider = "knowledge_provider"
    reference = "reference"
    expert_statement = "expert_statement"
    regulatory = "regulatory"
    model_output = "model_output"


# §3.6b — Source.subtype
class SourceSubtype(str, Enum):
    publication = "publication"
    dataset = "dataset"
    api = "api"
    person = "person"
    organisation = "organisation"
    regulatory_text = "regulatory_text"
    expert_statement = "expert_statement"


# §3.7 — Distribution.access_method
class AccessMethod(str, Enum):
    api_rest = "api_rest"
    api_graphql = "api_graphql"
    ogc_wms = "ogc_wms"
    ogc_wfs = "ogc_wfs"
    ogc_wmts = "ogc_wmts"
    ogc_wcs = "ogc_wcs"
    stac_api = "stac_api"
    file_download = "file_download"
    file_import = "file_import"
    publication_text = "publication_text"
    knowledge_extraction = "knowledge_extraction"


# §3.8 — ScaleContext.level
class ScaleLevel(str, Enum):
    leaf = "leaf"
    tree = "tree"
    plot = "plot"
    stand = "stand"
    forest = "forest"
    massif = "massif"
    landscape = "landscape"
    region = "region"
    country = "country"
    biome = "biome"
    earth = "earth"


# §3.9 — Phenomenon.phenomenon_type
class PhenomenonType(str, Enum):
    drought = "drought"
    storm = "storm"
    pest_outbreak = "pest_outbreak"
    pathogen_outbreak = "pathogen_outbreak"
    wildfire = "wildfire"
    flood = "flood"
    succession = "succession"
    migration = "migration"
    competition = "competition"
    invasion = "invasion"
    decline = "decline"
    regeneration = "regeneration"
    phenology_shift = "phenology_shift"
    other = "other"


# §3.10 — EcologicalProcess.process_type
class EcologicalProcessType(str, Enum):
    photosynthesis = "photosynthesis"
    transpiration = "transpiration"
    respiration = "respiration"
    growth = "growth"
    decomposition = "decomposition"
    nutrient_cycling = "nutrient_cycling"
    mycorrhization = "mycorrhization"
    nitrogen_fixation = "nitrogen_fixation"
    pollination = "pollination"
    seed_dispersal = "seed_dispersal"
    herbivory = "herbivory"
    predation = "predation"
    competition = "competition"
    facilitation = "facilitation"
    succession = "succession"
    carbon_sequestration = "carbon_sequestration"
    water_cycling = "water_cycling"
    other = "other"


# §3.11 — RelationType.category
class RelationCategory(str, Enum):
    causal = "causal"
    spatial = "spatial"
    temporal = "temporal"
    ecological = "ecological"
    taxonomic = "taxonomic"
    hydrological = "hydrological"
    genetic = "genetic"
    trophic = "trophic"
    competition = "competition"
    facilitation = "facilitation"
    host_pathogen = "host_pathogen"
    predator_prey = "predator_prey"
    other = "other"


# §3.12 — Correlation.method
class CorrelationMethod(str, Enum):
    pearson = "pearson"
    spearman = "spearman"
    kendall = "kendall"
    bayesian = "bayesian"
    mutual_information = "mutual_information"
    ai = "ai"
    expert = "expert"
    literature = "literature"
    meta_analysis = "meta_analysis"


# §3.13 — Capability.capability_type
class CapabilityType(str, Enum):
    observe = "observe"
    predict = "predict"
    inventory = "inventory"
    diagnose = "diagnose"
    simulate = "simulate"
    recommend = "recommend"
    correlate = "correlate"
    reason = "reason"
    validate = "validate"
    learn = "learn"
    extract = "extract"
    assess_evidence = "assess_evidence"


# §3.14 — Assertion.rule_subtype (quand claim_kind=rule)
class RuleSubtype(str, Enum):
    inference = "inference"
    scientific = "scientific"
    business = "business"
    regulatory = "regulatory"


# §3.15 — Dataset.purpose
class DatasetPurpose(str, Enum):
    production = "production"
    training = "training"
    evaluation = "evaluation"
    reference = "reference"


# §3.16 — Sample.sample_type
class SampleType(str, Enum):
    soil = "soil"
    leaf = "leaf"
    bark = "bark"
    wood_core = "wood_core"
    water = "water"
    root = "root"
    seed = "seed"
    tissue = "tissue"
    soil_water = "soil_water"
    litter = "litter"
    other = "other"


# §3.17 — Consent.legal_basis (RGPD art. 6)
class LegalBasis(str, Enum):
    consent = "consent"
    contract = "contract"
    legal_obligation = "legal_obligation"
    vital_interest = "vital_interest"
    public_interest = "public_interest"
    legitimate_interest = "legitimate_interest"
    research = "research"


# §3.18 — PersistentIdentifier.pid_type
class PIDType(str, Enum):
    doi = "doi"
    purl = "purl"
    orcid = "orcid"
    ror = "ror"
    gbif_taxonkey = "gbif_taxonkey"
    wikidata_qid = "wikidata_qid"
    inpn_taxref = "inpn_taxref"
    issn = "issn"
    handle = "handle"
    ark = "ark"
    urn = "urn"
    gsie_uri = "gsie_uri"


# §3.19 — Flow.flow_type
class FlowType(str, Enum):
    carbon = "carbon"
    water = "water"
    nitrogen = "nitrogen"
    phosphorus = "phosphorus"
    nutrient = "nutrient"
    energy = "energy"
    seed = "seed"
    pollen = "pollen"
    gene = "gene"
    pathogen = "pathogen"
    spore = "spore"
    biomass = "biomass"
    sediment = "sediment"
    other = "other"


# §3.20 — Goal.goal_type
class GoalType(str, Enum):
    biodiversity = "biodiversity"
    production = "production"
    risk_reduction = "risk_reduction"
    conservation = "conservation"
    restoration = "restoration"
    carbon_sequestration = "carbon_sequestration"
    water_protection = "water_protection"
    soil_protection = "soil_protection"
    recreation = "recreation"
    research = "research"
    regulatory = "regulatory"
    other = "other"


# §3.21 — Constraint.constraint_type
class ConstraintType(str, Enum):
    regulatory = "regulatory"
    budget = "budget"
    accessibility = "accessibility"
    weather = "weather"
    equipment = "equipment"
    ecological = "ecological"
    temporal = "temporal"
    social = "social"
    technical = "technical"
    other = "other"


# §3.22 — Scenario.scenario_subtype
class ScenarioSubtype(str, Enum):
    rcp_2_6 = "rcp_2.6"
    rcp_4_5 = "rcp_4.5"
    rcp_8_5 = "rcp_8.5"
    ssp1_2_6 = "ssp1_2.6"
    ssp3_7_0 = "ssp3_7.0"
    ssp5_8_5 = "ssp5_8.5"
    drias_2020 = "drias_2020"
    clear_cut = "clear_cut"
    selective_thinning = "selective_thinning"
    shelterwood = "shelterwood"
    coppice = "coppice"
    no_intervention = "no_intervention"
    adaptive = "adaptive"
    wildfire = "wildfire"
    storm = "storm"
    pest_outbreak = "pest_outbreak"
    baseline = "baseline"


# Enums supplémentaires (non numérotés §3 mais définis dans le métamodèle)

class ScenarioType(str, Enum):
    sylvicultural = "sylvicultural"
    climatic = "climatic"
    management = "management"
    disturbance = "disturbance"
    baseline = "baseline"


class AgentType(str, Enum):
    person = "person"
    organisation = "organisation"
    software = "software"


class ActivityType(str, Enum):
    extraction = "extraction"
    transformation = "transformation"
    ingestion = "ingestion"
    validation = "validation"
    revision = "revision"
    simulation = "simulation"


class MediaType(str, Enum):
    image = "image"
    audio = "audio"
    video = "video"
    document = "document"


class ModelType(str, Enum):
    growth = "growth"
    dynamics = "dynamics"
    propagation = "propagation"
    climate = "climate"
    ml = "ml"


class EvidenceLevel(str, Enum):
    a = "A"
    b = "B"
    c = "C"
    d = "D"
    e = "E"
    f = "F"


class TemporalGranularity(str, Enum):
    instant = "instant"
    day = "day"
    month = "month"
    year = "year"
    period = "period"
    range = "range"


class ParticipantRole(str, Enum):
    subject = "subject"
    object = "object"
    context = "context"


class CitationRole(str, Enum):
    primary = "primary"
    supporting = "supporting"
    contradicting = "contradicting"
    cited = "cited"


class QualityDimension(str, Enum):
    completeness = "completeness"
    positional_accuracy = "positional_accuracy"
    temporal_accuracy = "temporal_accuracy"
    thematic_accuracy = "thematic_accuracy"
    logical_consistency = "logical_consistency"


class UncertaintyType(str, Enum):
    confidence_interval = "confidence_interval"
    standard_error = "standard_error"
    range = "range"
    qualitative = "qualitative"


class UsageRights(str, Enum):
    open = "open"
    restricted = "restricted"
    private = "private"


class SensitivityLevel(str, Enum):
    public = "public"
    restricted = "restricted"
    sensitive = "sensitive"
    critical = "critical"


class ConflictStatus(str, Enum):
    open = "open"
    resolved_by_consensus = "resolved_by_consensus"
    resolved_by_arbitrage = "resolved_by_arbitrage"
    unresolved = "unresolved"


class CorrelationStrength(str, Enum):
    negligible = "negligible"
    weak = "weak"
    moderate = "moderate"
    strong = "strong"
    very_strong = "very_strong"


class QuestionType(str, Enum):
    scientific = "scientific"
    operational = "operational"
    diagnostic = "diagnostic"
    predictive = "predictive"


class HypothesisStatus(str, Enum):
    proposed = "proposed"
    testing = "testing"
    supported = "supported"
    refuted = "refuted"
    inconclusive = "inconclusive"


class ProviderType(str, Enum):
    engine = "engine"
    application = "application"


class ConsentScope(str, Enum):
    full = "full"
    anonymized_only = "anonymized_only"
    aggregated_only = "aggregated_only"


class FlowDirection(str, Enum):
    source_to_sink = "source_to_sink"
    bidirectional = "bidirectional"


class StateType(str, Enum):
    health = "health"
    vitality = "vitality"
    risk = "risk"
    resilience = "resilience"
    biodiversity = "biodiversity"
    productivity = "productivity"
    integrity = "integrity"


class EcologicalGrade(str, Enum):
    excellent = "excellent"
    good = "good"
    moderate = "moderate"
    poor = "poor"
    critical = "critical"


class Trend(str, Enum):
    improving = "improving"
    stable = "stable"
    declining = "declining"
    unknown = "unknown"


class FeatureSourceType(str, Enum):
    observation = "observation"
    trait = "trait"
    computed = "computed"
    external = "external"


class RelationDirection(str, Enum):
    sortant = "sortant"
    entrant = "entrant"
    bidirectionnel = "bidirectionnel"


# --- Enums supplémentaires identifiés lors de l'audit ---

class EcosystemServiceCategory(str, Enum):
    regulation = "regulation"
    support = "support"
    provisioning = "provisioning"
    cultural = "cultural"


class GoalPriority(str, Enum):
    primary = "primary"
    secondary = "secondary"
    tertiary = "tertiary"


class ConstraintSeverity(str, Enum):
    blocking = "blocking"
    limiting = "limiting"
    conditional = "conditional"


class PropagationMethod(str, Enum):
    bayesian = "bayesian"
    weighted_average = "weighted_average"
    dempster_shafer = "dempster_shafer"
    fuzzy = "fuzzy"


class ProductionMethod(str, Enum):
    inference = "inference"
    correlation = "correlation"
    synthesis = "synthesis"
    expert_judgment = "expert_judgment"
    model_output = "model_output"
    extraction = "extraction"
    validation = "validation"


class TerrainSessionType(str, Enum):
    inventory = "inventory"
    martelage = "martelage"
    monitoring = "monitoring"
    diagnosis = "diagnosis"
    research = "research"
    calibration = "calibration"


class SyncStatus(str, Enum):
    synced = "synced"
    partial = "partial"
    pending = "pending"
    failed = "failed"


class Permission(str, Enum):
    """Permissions pour AccessPolicy (type 38)."""
    read = "read"
    write = "write"
    delete = "delete"
    export = "export"
    admin = "admin"
