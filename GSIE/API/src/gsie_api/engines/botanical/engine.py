"""Botanical Engine — taxonomie et nomenclature, sourcées et vérifiables.

Responsabilité (BOTANICAL_ENGINE.md §1) : gérer la taxonomie et la
nomenclature des espèces forestières, avec résolution des synonymes
vers le taxon accepté (GSIE-CON-010 — traçabilité des évolutions
taxonomiques).

Périmètre v1 (voir docstring schemas.py) : taxonomie/nomenclature via
GBIF Backbone Taxonomy uniquement — pas d'autécologie (optimum pH,
tolérance gel, etc.), qui nécessite des connaissances sourcées
(Rameau et al.) pas encore ingérées dans le Knowledge Engine. Un
`EspeceData` v1 a `autecologie=None`, jamais une valeur approximée
(ADR-007).

Garantie : un nom introuvable dans GBIF (`matchType: NONE`) retourne
une liste d'espèces vide, jamais un taxon inventé.
"""

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.logging import get_logger
from gsie_api.engines.botanical.gbif_client import GBIFClient, GBIFClientError
from gsie_api.engines.botanical.schemas import (
    BotanicalData,
    BotanicalQuery,
    EspeceData,
    TaxonStatus,
)
from gsie_api.engines.evidence.schemas import SourceReference, SourceType
from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.models.provenance import EntityAliasModel, EntityModel

logger = get_logger("gsie_api.botanical.engine")

_GBIF_SOURCE = SourceReference(
    type_source=SourceType.referentiel_officiel,
    auteur="GBIF",
    reference="GBIF Backbone Taxonomy (api.gbif.org/v1/species/match)",
)


class BotanicalEngineError(Exception):
    """Erreur de base du Botanical Engine."""


class BotanicalEngine:
    """Moteur Botanical — persistance PostgreSQL.

    Une instance par requête HTTP avec la session DB de la requête
    (même schéma que GISEngine/CorrelationEngine).
    """

    def __init__(self, session: AsyncSession, gbif_client: GBIFClient | None = None) -> None:
        self._session = session
        self._gbif_client = gbif_client or GBIFClient()

    @staticmethod
    def version() -> str:
        """Version du moteur."""
        return "0.1.0"

    async def query(self, request: BotanicalQuery) -> BotanicalData:
        """Résout une essence vers son taxon GBIF et le persiste.

        Aucune espèce n'est retournée si GBIF ne trouve aucune
        correspondance (`matchType: NONE`) — jamais de taxon inventé
        en remplacement (ADR-007).

        Raises:
            BotanicalEngineError: si l'API GBIF est indisponible.
        """
        try:
            match = await self._gbif_client.match_species(request.essence)
        except GBIFClientError as exc:
            raise BotanicalEngineError(str(exc)) from exc

        if match is None:
            logger.info("botanical_no_match", essence=request.essence)
            return BotanicalData(requete_id=request.requete_id, especes=[], source=_GBIF_SOURCE)

        accepted_key = match.get("acceptedUsageKey") or match["usageKey"]
        nom_scientifique = match.get("species") or match["canonicalName"]
        try:
            statut = TaxonStatus(match["status"])
        except ValueError:
            statut = TaxonStatus.doubtful
        synonymes: list[str] = []
        if statut == TaxonStatus.synonym:
            synonymes.append(match["scientificName"])

        try:
            nom_vernaculaire = await self._gbif_client.get_vernacular_name(accepted_key)
        except GBIFClientError as exc:
            raise BotanicalEngineError(str(exc)) from exc

        taxon_id = await self._get_or_create_taxon(accepted_key)

        espece = EspeceData(
            taxon_id=taxon_id,
            gbif_taxon_key=accepted_key,
            nom_scientifique=nom_scientifique,
            nom_vernaculaire=nom_vernaculaire,
            synonymes=synonymes,
            famille=match.get("family"),
            statut=statut,
            source=_GBIF_SOURCE,
        )

        logger.info(
            "botanical_taxon_resolved",
            essence=request.essence,
            gbif_taxon_key=accepted_key,
            statut=statut.value,
        )

        return BotanicalData(
            requete_id=request.requete_id,
            especes=[espece],
            source=_GBIF_SOURCE,
        )

    async def _get_or_create_taxon(self, gbif_taxon_key: int) -> UUID:
        """Retrouve la resource `entity` existante pour ce taxon GBIF, ou la crée.

        Évite de dupliquer une entité à chaque requête sur le même taxon
        (déduplication par `entity_alias.namespace='gbif'` +
        `external_id`, CON-010 — pas de doublon silencieux).
        """
        existing = (
            await self._session.execute(
                select(EntityAliasModel.entity_id).where(
                    EntityAliasModel.namespace == "gbif",
                    EntityAliasModel.external_id == str(gbif_taxon_key),
                )
            )
        ).scalars().first()
        if existing is not None:
            return existing

        entity_id = uuid4()
        self._session.add(
            ResourceModel(
                id=entity_id,
                type="entity",
                gsie_id=f"gsie:entity:taxon:{gbif_taxon_key}",
                metadata_json={},
            )
        )
        await self._session.flush()
        self._session.add(EntityModel(id=entity_id, entity_subtype="taxon"))

        alias_id = uuid4()
        self._session.add(
            ResourceModel(
                id=alias_id,
                type="entity_alias",
                gsie_id=f"gsie:entity_alias:gbif:{gbif_taxon_key}",
                metadata_json={},
            )
        )
        await self._session.flush()
        self._session.add(
            EntityAliasModel(
                id=alias_id,
                entity_id=entity_id,
                namespace="gbif",
                external_id=str(gbif_taxon_key),
                external_url=f"https://www.gbif.org/species/{gbif_taxon_key}",
            )
        )
        await self._session.flush()
        return entity_id
