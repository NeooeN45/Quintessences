"""Registre des sources scientifiques, licences et droits (SCI-001).

Corpus sylvicole scientifique (`GSIE/RESEARCH/CORPUS_SYLVICOLE_
SCIENTIFIQUE_QUINTESSENCES_2026-07-18.md` §7 étape A) : aucun document
ou jeu de données ne doit entrer dans un moteur GSIE, un RAG ou un pack
hors ligne sans statut juridique explicite. Ce registre catalogue
chaque source déjà intégrée (ou évaluée) dans GSIE avec son statut,
et fournit une porte programmatique (`require_ingestible`) pour éviter
qu'une intégration future contourne silencieusement cette règle.

Ce registre est un catalogue **déclaratif** : il documente une
décision déjà prise (quelle licence, quel statut), il ne l'évalue pas
lui-même — la revue juridique reste humaine (RFC-0014 §3.3 : l'IA
assiste, ne décide jamais).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class SourceLegalStatus(StrEnum):
    """Statut juridique d'une source (corpus sylvicole §7, étape A)."""

    open_confirmed = "OPEN_CONFIRMED"
    public_document_reuse_confirmed = "PUBLIC_DOCUMENT_REUSE_CONFIRMED"
    permission_required = "PERMISSION_REQUIRED"
    licensed_partner = "LICENSED_PARTNER"
    metadata_only = "METADATA_ONLY"
    do_not_ingest = "DO_NOT_INGEST"
    legal_review_pending = "LEGAL_REVIEW_PENDING"


class IngestionMode(StrEnum):
    """Mode d'ingestion technique opérationnel d'une source.

    Reprend la note juridique du Fondateur (19_LEGAL/STRATEGIE_ACCES_
    SOURCES_PROTEGEES_2026-07-18.md) : le statut juridique (ci-dessus)
    qualifie la source, le mode d'ingestion dicte ce que le pipeline a
    techniquement le droit de faire avec elle.
    """

    open_copy = "OPEN_COPY"  # copie et redistribution autorisées
    tdm_ephemeral = "TDM_EPHEMERAL"  # fouille temporaire, source non redistribuée
    local_user_only = "LOCAL_USER_ONLY"  # importé et indexé uniquement sur l'appareil
    metadata_link = "METADATA_LINK"  # titre, version, citation et lien uniquement
    partner_license = "PARTNER_LICENSE"  # selon accord CNPF/ONF
    forbidden = "FORBIDDEN"  # aucune ingestion


# Seul OPEN_COPY autorise le pipeline d'ingestion automatique complet
# (téléchargement, structuration, indexation RAG, pack offline). Les
# autres modes exigent soit une action humaine (TDM_EPHEMERAL —
# destruction des copies après fouille, LOCAL_USER_ONLY — jamais côté
# serveur), soit restent bloqués (METADATA_LINK, PARTNER_LICENSE,
# FORBIDDEN).
_INGESTIBLE_MODES = frozenset({IngestionMode.open_copy})


class ScientificSourceEntry(BaseModel):
    """Une entrée du registre — un jeu de données ou service externe."""

    model_config = ConfigDict(extra="forbid")

    identifiant: str = Field(description="Identifiant stable, ex. 'meteofrance-portail-api'")
    organisme: str
    url: str
    licence: str
    statut_juridique: SourceLegalStatus
    mode_ingestion: IngestionMode = Field(
        description="Ce que le pipeline a le droit de faire techniquement avec cette source"
    )
    usage_commercial_autorise: bool | None = None
    droit_indexation: bool | None = Field(
        default=None, description="Peut être indexé dans un RAG/index vectoriel"
    )
    droit_derives: bool | None = Field(
        default=None, description="Peut être transformé en connaissance structurée dérivée"
    )
    droit_redistribution_offline: bool | None = Field(
        default=None, description="Peut être inclus dans un pack GeoSylva hors ligne"
    )
    attribution_requise: str | None = None
    territoire: str | None = None
    version_ou_date: str | None = None
    contact: str | None = None
    notes: str | None = None


class SourceIngestionForbiddenError(Exception):
    """Levée par `require_ingestible` — statut juridique insuffisant pour ingestion directe."""


# Catalogue des sources déjà intégrées ou évaluées dans GSIE (sessions
# 2026-07-17/18). Ajouter une entrée ici avant toute intégration
# technique d'une nouvelle source (client HTTP, connecteur Forge, ou
# document versé dans GSIE/RESEARCH ou GSIE/DATASETS).
SCIENTIFIC_SOURCES: dict[str, ScientificSourceEntry] = {
    entry.identifiant: entry
    for entry in [
        ScientificSourceEntry(
            identifiant="meteofrance-portail-api",
            organisme="Météo-France",
            url="https://portail-api.meteofrance.fr",
            licence="Licence Ouverte / Etalab 2.0",
            statut_juridique=SourceLegalStatus.open_confirmed,
            mode_ingestion=IngestionMode.open_copy,
            usage_commercial_autorise=True,
            droit_indexation=True,
            droit_derives=True,
            droit_redistribution_offline=True,
            attribution_requise="Météo-France",
            territoire="France",
            notes=(
                "Couvre SYNOP, Météo des forêts, DPClim, Vigilance, "
                "Package Observations, AROME — clé de compte requise, "
                "licence identique pour toutes les APIs souscrites."
            ),
        ),
        ScientificSourceEntry(
            identifiant="gbif",
            organisme="GBIF (Global Biodiversity Information Facility)",
            url="https://api.gbif.org",
            licence="CC0 / CC-BY selon jeu de données constitutif",
            statut_juridique=SourceLegalStatus.open_confirmed,
            mode_ingestion=IngestionMode.open_copy,
            usage_commercial_autorise=True,
            droit_indexation=True,
            droit_derives=True,
            droit_redistribution_offline=True,
            attribution_requise="GBIF.org",
            territoire="Mondial",
        ),
        ScientificSourceEntry(
            identifiant="taxref-via-gbif",
            organisme="MNHN (TAXREF), miroir GBIF",
            url="https://www.gbif.org/dataset/0e61f8fe-7d25-4f81-ada7-d970bbb2c6d6",
            licence="Licence Ouverte / Etalab (TAXREF)",
            statut_juridique=SourceLegalStatus.open_confirmed,
            mode_ingestion=IngestionMode.open_copy,
            usage_commercial_autorise=True,
            droit_indexation=True,
            droit_derives=True,
            droit_redistribution_offline=True,
            attribution_requise="MNHN — TAXREF",
            territoire="France",
            notes="Infrastructure MNHN directe dégradée depuis le piratage de 2025-09.",
        ),
        ScientificSourceEntry(
            identifiant="soilgrids",
            organisme="ISRIC",
            url="https://www.isric.org/explore/soilgrids",
            licence="CC-BY 4.0",
            statut_juridique=SourceLegalStatus.open_confirmed,
            mode_ingestion=IngestionMode.open_copy,
            usage_commercial_autorise=True,
            droit_indexation=True,
            droit_derives=True,
            droit_redistribution_offline=True,
            attribution_requise="Poggio, L. et al. (2021), SoilGrids 2.0",
            territoire="Mondial",
        ),
        ScientificSourceEntry(
            identifiant="ign-apicarto-geopf",
            organisme="IGN",
            url="https://apicarto.ign.fr",
            licence="Licence Ouverte / Etalab 2.0",
            statut_juridique=SourceLegalStatus.open_confirmed,
            mode_ingestion=IngestionMode.open_copy,
            usage_commercial_autorise=True,
            droit_indexation=True,
            droit_derives=True,
            droit_redistribution_offline=True,
            attribution_requise="IGN",
            territoire="France",
        ),
        ScientificSourceEntry(
            identifiant="ifn-donnees-brutes",
            organisme="IGN — Inventaire Forestier National",
            url="https://inventaire-forestier.ign.fr/dataifn/",
            licence="Licence Ouverte / Etalab 2.0",
            statut_juridique=SourceLegalStatus.open_confirmed,
            mode_ingestion=IngestionMode.open_copy,
            usage_commercial_autorise=True,
            droit_indexation=True,
            droit_derives=True,
            droit_redistribution_offline=True,
            attribution_requise="IGN — Inventaire Forestier National",
            territoire="France",
            notes=(
                "Avertissement IGN à relayer systématiquement : ne peut pas "
                "produire de résultats d'inventaire sans les poids "
                "statistiques officiels (voir ifn_connector.py Forge)."
            ),
        ),
        ScientificSourceEntry(
            identifiant="indigenat-bellifa-2026",
            organisme="Bellifa M. et al. — Recherche Data Gouv",
            url="https://doi.org/10.57745/DHJHGS",
            licence="Etalab Open License 2.0",
            statut_juridique=SourceLegalStatus.open_confirmed,
            mode_ingestion=IngestionMode.open_copy,
            usage_commercial_autorise=True,
            droit_indexation=True,
            droit_derives=True,
            droit_redistribution_offline=True,
            attribution_requise="Bellifa M. et al. (2026), Journal de Botanique SBF 124(002)",
            territoire="France hexagonale + Corse",
            version_ou_date="2026",
        ),
        ScientificSourceEntry(
            identifiant="climessences",
            organisme="ONF / CNPF",
            url="https://climessences.fr",
            licence="CGU ClimEssences — propriétaire",
            statut_juridique=SourceLegalStatus.permission_required,
            mode_ingestion=IngestionMode.metadata_link,
            usage_commercial_autorise=False,
            droit_indexation=False,
            droit_derives=False,
            droit_redistribution_offline=False,
            territoire="France",
            notes=(
                "Corpus sylvicole scientifique §3 : autorisation écrite "
                "requise avant copie massive, indexation RAG ou "
                "redistribution hors ligne — ne pas scraper."
            ),
        ),
        ScientificSourceEntry(
            identifiant="bioclimsol",
            organisme="CNPF",
            url="https://www.cnpf.fr/decouvrez-bioclimsol",
            licence="Licence certifiante CNPF",
            statut_juridique=SourceLegalStatus.licensed_partner,
            mode_ingestion=IngestionMode.partner_license,
            usage_commercial_autorise=False,
            droit_indexation=False,
            droit_derives=False,
            droit_redistribution_offline=False,
            territoire="France",
            notes="Partenariat ou module sous licence requis — pas de scraping ni de clone.",
        ),
        ScientificSourceEntry(
            identifiant="cnpf-itineraires-guides",
            organisme="CNPF",
            url="https://www.cnpf.fr/gestion-durable-des-forets/mise-en-oeuvre/fiches-itineraires-techniques-par-essence",
            licence="Mentions légales CNPF — propriétaire",
            statut_juridique=SourceLegalStatus.permission_required,
            mode_ingestion=IngestionMode.metadata_link,
            usage_commercial_autorise=False,
            droit_indexation=False,
            droit_derives=False,
            droit_redistribution_offline=False,
            territoire="France",
            notes=(
                "Autorisation CNPF requise pour réutilisation/redistribution "
                "au-delà des usages permis."
            ),
        ),
        ScientificSourceEntry(
            identifiant="hal-depot-auteur",
            organisme="HAL (CCSD/CNRS) — dépôts sous licence d'auteur",
            url="https://hal.science",
            licence="Licence de dépôt HAL par défaut — droits conservés par l'auteur/éditeur",
            statut_juridique=SourceLegalStatus.legal_review_pending,
            mode_ingestion=IngestionMode.tdm_ephemeral,
            usage_commercial_autorise=None,
            droit_indexation=False,
            droit_derives=True,
            droit_redistribution_offline=False,
            territoire="France",
            notes=(
                "Fouille de textes et données (article L122-5-3 CPI) : accès "
                "licite, extraction de faits atomiques cités puis destruction "
                "de la copie locale — jamais de redistribution du PDF/texte "
                "intégral. Voir 19_LEGAL/STRATEGIE_ACCES_SOURCES_PROTEGEES_"
                "2026-07-18.md. Premier pilote réel (2026-07-18) : Parelle J., "
                "Brendel O., Jolivet Y. (2007), hal-02653679 — 29 faits "
                "vérifiés, PDF détruit après extraction, voir "
                "GSIE/KNOWLEDGE/pilotes_extraction/."
            ),
        ),
        ScientificSourceEntry(
            identifiant="onf-guides-sylviculture",
            organisme="ONF",
            url="https://www.onf.fr/onf/recherche-pour-les-tags-et-les-collections?collection=Guides+de+sylviculture",
            licence="À qualifier document par document",
            statut_juridique=SourceLegalStatus.legal_review_pending,
            mode_ingestion=IngestionMode.metadata_link,
            territoire="France",
            notes=(
                "Collection d'au moins 51 guides/mémentos — les documents "
                "publics/officiels et les contenus éditoriaux n'ont pas "
                "nécessairement le même régime de réutilisation."
            ),
        ),
    ]
}


def get_source(identifiant: str) -> ScientificSourceEntry | None:
    """Retourne l'entrée du registre pour cet identifiant, ou None si inconnue."""
    return SCIENTIFIC_SOURCES.get(identifiant)


def require_ingestible(identifiant: str) -> ScientificSourceEntry:
    """Vérifie qu'une source peut être ingérée automatiquement (pipeline complet).

    Seul le mode `OPEN_COPY` passe cette porte. `TDM_EPHEMERAL` et
    `LOCAL_USER_ONLY` restent des modes d'usage légitimes mais exigent
    un traitement différent (fouille non redistribuée, import côté
    client) — voir `19_LEGAL/STRATEGIE_ACCES_SOURCES_PROTEGEES_
    2026-07-18.md` — pas une ingestion serveur automatique.

    Raises:
        SourceIngestionForbiddenError: si la source est absente du
            registre, ou si son mode d'ingestion n'autorise pas le
            pipeline automatique complet.
    """
    entry = SCIENTIFIC_SOURCES.get(identifiant)
    if entry is None:
        raise SourceIngestionForbiddenError(
            f"Source '{identifiant}' absente du registre — l'ajouter à "
            "SCIENTIFIC_SOURCES avant toute intégration technique (SCI-001)"
        )
    if entry.mode_ingestion not in _INGESTIBLE_MODES:
        raise SourceIngestionForbiddenError(
            f"Source '{identifiant}' a le mode d'ingestion {entry.mode_ingestion.value} — "
            "pipeline automatique interdit sans démarche complémentaire"
        )
    return entry
