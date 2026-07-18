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


# Statuts qui autorisent une ingestion technique (appel API, téléchargement,
# indexation) sans démarche juridique préalable supplémentaire.
_INGESTIBLE_STATUSES = frozenset(
    {SourceLegalStatus.open_confirmed, SourceLegalStatus.public_document_reuse_confirmed}
)


class ScientificSourceEntry(BaseModel):
    """Une entrée du registre — un jeu de données ou service externe."""

    model_config = ConfigDict(extra="forbid")

    identifiant: str = Field(description="Identifiant stable, ex. 'meteofrance-portail-api'")
    organisme: str
    url: str
    licence: str
    statut_juridique: SourceLegalStatus
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
            usage_commercial_autorise=False,
            droit_indexation=False,
            droit_derives=False,
            droit_redistribution_offline=False,
            territoire="France",
            notes="Autorisation CNPF requise pour réutilisation/redistribution au-delà des usages permis.",
        ),
        ScientificSourceEntry(
            identifiant="onf-guides-sylviculture",
            organisme="ONF",
            url="https://www.onf.fr/onf/recherche-pour-les-tags-et-les-collections?collection=Guides+de+sylviculture",
            licence="À qualifier document par document",
            statut_juridique=SourceLegalStatus.legal_review_pending,
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
    """Vérifie qu'une source peut être ingérée techniquement sans démarche juridique préalable.

    Raises:
        SourceIngestionForbiddenError: si la source est absente du
            registre, ou si son statut n'autorise pas l'ingestion
            directe (`PERMISSION_REQUIRED`, `LICENSED_PARTNER`,
            `DO_NOT_INGEST`, `LEGAL_REVIEW_PENDING`, `METADATA_ONLY`).
    """
    entry = SCIENTIFIC_SOURCES.get(identifiant)
    if entry is None:
        raise SourceIngestionForbiddenError(
            f"Source '{identifiant}' absente du registre — l'ajouter à "
            "SCIENTIFIC_SOURCES avant toute intégration technique (SCI-001)"
        )
    if entry.statut_juridique not in _INGESTIBLE_STATUSES:
        raise SourceIngestionForbiddenError(
            f"Source '{identifiant}' a le statut {entry.statut_juridique.value} — "
            "ingestion directe interdite sans démarche juridique préalable"
        )
    return entry
