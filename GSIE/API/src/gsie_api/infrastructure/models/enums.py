"""Enums PostgreSQL pour le métamodèle v6.2 (§3 du métamodèle).

Tous les enums sont définis comme des enums Python (StrEnum) pour
SQLAlchemy 2.0 + Pydantic v2. En DB, ils sont créés comme des types
ENUM PostgreSQL par la migration Alembic 0002.

Source : GSIE/ARCHITECTURE/ECOSYSTEM_METAMODEL.md §3.3 à §3.22
"""

from enum import StrEnum


# §3.3 — Assertion.claim_kind
class ClaimKind(StrEnum):
    observation = "observation"
    relation = "relation"
    rule = "rule"
    threshold = "threshold"
    model = "model"
    classification = "classification"
    absence = "absence"


# §3.4 — Assertion.lifecycle_status (réutilisé par Correlation)
class LifecycleStatus(StrEnum):
    draft = "draft"
    proposed = "proposed"
    accepted = "accepted"
    superseded = "superseded"
    rejected = "rejected"
    deprecated = "deprecated"


# §3.5 — Result.value_type
class ValueType(StrEnum):
    numeric = "numeric"
    term = "term"
    media_ref = "media_ref"
    entity_ref = "entity_ref"
    computed = "computed"
    absence = "absence"


# §3.6 — Source.source_nature
class SourceNature(StrEnum):
    data_provider = "data_provider"
    knowledge_provider = "knowledge_provider"
    reference = "reference"
    expert_statement = "expert_statement"
    regulatory = "regulatory"
    model_output = "model_output"


# §3.6b — Source.subtype
class SourceSubtype(StrEnum):
    publication = "publication"
    dataset = "dataset"
    api = "api"
    person = "person"
    organisation = "organisation"
    regulatory_text = "regulatory_text"
    expert_statement = "expert_statement"


# §3.7 — Distribution.access_method
class AccessMethod(StrEnum):
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
class ScaleLevel(StrEnum):
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
class PhenomenonType(StrEnum):
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
class EcologicalProcessType(StrEnum):
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
class RelationCategory(StrEnum):
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
class CorrelationMethod(StrEnum):
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
class CapabilityType(StrEnum):
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
class RuleSubtype(StrEnum):
    inference = "inference"
    scientific = "scientific"
    business = "business"
    regulatory = "regulatory"


# §3.15 — Dataset.purpose
class DatasetPurpose(StrEnum):
    production = "production"
    training = "training"
    evaluation = "evaluation"
    reference = "reference"


# §3.16 — Sample.sample_type
class SampleType(StrEnum):
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
class LegalBasis(StrEnum):
    consent = "consent"
    contract = "contract"
    legal_obligation = "legal_obligation"
    vital_interest = "vital_interest"
    public_interest = "public_interest"
    legitimate_interest = "legitimate_interest"
    research = "research"


# §3.18 — PersistentIdentifier.pid_type
class PIDType(StrEnum):
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
class FlowType(StrEnum):
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
class GoalType(StrEnum):
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
class ConstraintType(StrEnum):
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
class ScenarioSubtype(StrEnum):
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


class ScenarioType(StrEnum):
    sylvicultural = "sylvicultural"
    climatic = "climatic"
    management = "management"
    disturbance = "disturbance"
    baseline = "baseline"


class AgentType(StrEnum):
    person = "person"
    organisation = "organisation"
    software = "software"


class ActivityType(StrEnum):
    extraction = "extraction"
    transformation = "transformation"
    ingestion = "ingestion"
    validation = "validation"
    revision = "revision"
    simulation = "simulation"


class MediaType(StrEnum):
    image = "image"
    audio = "audio"
    video = "video"
    document = "document"


class ModelType(StrEnum):
    growth = "growth"
    dynamics = "dynamics"
    propagation = "propagation"
    climate = "climate"
    ml = "ml"


class EvidenceLevel(StrEnum):
    a = "A"
    b = "B"
    c = "C"
    d = "D"
    e = "E"
    f = "F"


class TemporalGranularity(StrEnum):
    instant = "instant"
    day = "day"
    month = "month"
    year = "year"
    period = "period"
    range = "range"


class ParticipantRole(StrEnum):
    subject = "subject"
    object = "object"
    context = "context"


class CitationRole(StrEnum):
    primary = "primary"
    supporting = "supporting"
    contradicting = "contradicting"
    cited = "cited"


class QualityDimension(StrEnum):
    completeness = "completeness"
    positional_accuracy = "positional_accuracy"
    temporal_accuracy = "temporal_accuracy"
    thematic_accuracy = "thematic_accuracy"
    logical_consistency = "logical_consistency"


class UncertaintyType(StrEnum):
    confidence_interval = "confidence_interval"
    standard_error = "standard_error"
    range = "range"
    qualitative = "qualitative"


class UsageRights(StrEnum):
    open = "open"
    restricted = "restricted"
    private = "private"


class SensitivityLevel(StrEnum):
    public = "public"
    restricted = "restricted"
    sensitive = "sensitive"
    critical = "critical"


class ConflictStatus(StrEnum):
    open = "open"
    resolved_by_consensus = "resolved_by_consensus"
    resolved_by_arbitrage = "resolved_by_arbitrage"
    unresolved = "unresolved"


class CorrelationStrength(StrEnum):
    negligible = "negligible"
    weak = "weak"
    moderate = "moderate"
    strong = "strong"
    very_strong = "very_strong"


class QuestionType(StrEnum):
    scientific = "scientific"
    operational = "operational"
    diagnostic = "diagnostic"
    predictive = "predictive"


class HypothesisStatus(StrEnum):
    proposed = "proposed"
    testing = "testing"
    supported = "supported"
    refuted = "refuted"
    inconclusive = "inconclusive"


class ProviderType(StrEnum):
    engine = "engine"
    application = "application"


class ConsentScope(StrEnum):
    full = "full"
    anonymized_only = "anonymized_only"
    aggregated_only = "aggregated_only"


class FlowDirection(StrEnum):
    source_to_sink = "source_to_sink"
    bidirectional = "bidirectional"


class StateType(StrEnum):
    health = "health"
    vitality = "vitality"
    risk = "risk"
    resilience = "resilience"
    biodiversity = "biodiversity"
    productivity = "productivity"
    integrity = "integrity"


class EcologicalGrade(StrEnum):
    excellent = "excellent"
    good = "good"
    moderate = "moderate"
    poor = "poor"
    critical = "critical"


class Trend(StrEnum):
    improving = "improving"
    stable = "stable"
    declining = "declining"
    unknown = "unknown"


class FeatureSourceType(StrEnum):
    observation = "observation"
    trait = "trait"
    computed = "computed"
    external = "external"


class RelationDirection(StrEnum):
    sortant = "sortant"
    entrant = "entrant"
    bidirectionnel = "bidirectionnel"


# --- Enums supplémentaires identifiés lors de l'audit ---


class EcosystemServiceCategory(StrEnum):
    regulation = "regulation"
    support = "support"
    provisioning = "provisioning"
    cultural = "cultural"


class GoalPriority(StrEnum):
    primary = "primary"
    secondary = "secondary"
    tertiary = "tertiary"


class ConstraintSeverity(StrEnum):
    blocking = "blocking"
    limiting = "limiting"
    conditional = "conditional"


class PropagationMethod(StrEnum):
    bayesian = "bayesian"
    weighted_average = "weighted_average"
    dempster_shafer = "dempster_shafer"
    fuzzy = "fuzzy"


class ProductionMethod(StrEnum):
    inference = "inference"
    correlation = "correlation"
    synthesis = "synthesis"
    expert_judgment = "expert_judgment"
    model_output = "model_output"
    extraction = "extraction"
    validation = "validation"


class TerrainSessionType(StrEnum):
    inventory = "inventory"
    martelage = "martelage"
    monitoring = "monitoring"
    diagnosis = "diagnosis"
    research = "research"
    calibration = "calibration"


class SyncStatus(StrEnum):
    synced = "synced"
    partial = "partial"
    pending = "pending"
    failed = "failed"


class Permission(StrEnum):
    """Permissions pour AccessPolicy (type 38)."""

    read = "read"
    write = "write"
    delete = "delete"
    export = "export"
    admin = "admin"


# --- Enums métier (types 74-79 — audit métier ONF/CNPF) ---


class ManagementPlanType(StrEnum):
    """Type de plan de gestion forestier."""

    psg = "psg"  # Plan Simple de Gestion (CNPF)
    amf = "amf"  # Aménagement Forestier (ONF)
    rtg = "rtg"  # Règlement Type de Gestion
    custom = "custom"


class PlanStatus(StrEnum):
    """Statut d'un plan de gestion."""

    draft = "draft"
    submitted = "submitted"
    approved = "approved"
    active = "active"
    revision = "revision"
    expired = "expired"
    cancelled = "cancelled"


class InterventionType(StrEnum):
    """Type d'intervention sylvicole."""

    planting = "planting"
    thinning = "thinning"
    clear_cut = "clear_cut"
    selective_cut = "selective_cut"
    shelterwood = "shelterwood"
    coppicing = "coppicing"
    pruning = "pruning"
    clearing = "clearing"
    fertilization = "fertilization"
    drainage = "drainage"
    road_work = "road_work"
    protection = "protection"
    inventory = "inventory"
    other = "other"


class InterventionStatus(StrEnum):
    """Statut d'une intervention."""

    planned = "planned"
    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    delayed = "delayed"


class EconomicCategory(StrEnum):
    """Catégorie économique."""

    cost = "cost"
    revenue = "revenue"
    subsidy = "subsidy"
    investment = "investment"
    market_price = "market_price"


class RegulationDomain(StrEnum):
    """Domaine réglementaire."""

    forest_code = "forest_code"
    psg_obligations = "psg_obligations"
    natura_2000 = "natura_2000"
    water_protection = "water_protection"
    biodiversity_protection = "biodiversity_protection"
    urban_planning = "urban_planning"
    environmental_impact = "environmental_impact"
    other = "other"


class ComplianceStatus(StrEnum):
    """Statut de conformité réglementaire."""

    compliant = "compliant"
    non_compliant = "non_compliant"
    pending_check = "pending_check"
    waiver = "waiver"
    not_applicable = "not_applicable"


class OutcomeStatus(StrEnum):
    """Statut du suivi de résultat (post-recommandation)."""

    pending = "pending"
    in_progress = "in_progress"
    achieved = "achieved"
    partially_achieved = "partially_achieved"
    not_achieved = "not_achieved"
    abandoned = "abandoned"


class SilviculturalSystemCategory(StrEnum):
    """Catégorie de système sylvicole (RFC-0016 §3.1, tranche 3/10)."""

    futaie_reguliere = "futaie_reguliere"
    futaie_irreguliere = "futaie_irreguliere"
    taillis = "taillis"
    taillis_sous_futaie = "taillis_sous_futaie"
    conversion = "conversion"
    autre = "autre"


class AdministrativeLevel(StrEnum):
    """Niveau d'unité administrative."""

    national = "national"
    regional = "regional"
    departmental = "departmental"
    forest_domain = "forest_domain"  # Forêt domaniale
    triage = "triage"
    canton = "canton"
    parcel = "parcel"  # Parcelle cadastrale
    series = "series"  # Série forestière
