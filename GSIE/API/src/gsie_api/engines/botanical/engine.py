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
(ADR-009).

Garantie : un nom introuvable dans GBIF (`matchType: NONE`) retourne
une liste d'espèces vide, jamais un taxon inventé.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.logging import get_logger
from gsie_api.engines.botanical.gbif_client import GBIFClient, GBIFClientError
from gsie_api.engines.botanical.indigenat_loader import IndigenatLoader, IndigenatLoaderError
from gsie_api.engines.botanical.plantnet_client import PlantNetClient, PlantNetClientError
from gsie_api.engines.botanical.schemas import (
    BotanicalData,
    BotanicalIngestResponse,
    BotanicalIngestResult,
    BotanicalQuery,
    EspeceData,
    IndigenatQuery,
    IndigenatResult,
    PlantNetIdentificationResult,
    PlantNetIngestResponse,
    PlantNetIngestResult,
    StatutIndigenatFrance,
    StatutIndigenatRegion,
    TaxonStatus,
    TaxrefIngestResponse,
    TaxrefIngestResult,
    TaxrefQuery,
    TaxrefResult,
)
from gsie_api.engines.botanical.taxref_client import TaxrefClient, TaxrefClientError
from gsie_api.engines.evidence.schemas import (
    ContentType,
    RawKnowledgeSubmission,
    SourceReference,
    SourceType,
)
from gsie_api.engines.knowledge.engine import KnowledgeEngine
from gsie_api.engines.knowledge.schemas import DomaineScientifique, KnowledgeType
from gsie_api.engines.pipeline import EvidenceKnowledgePipeline
from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.models.provenance import EntityAliasModel, EntityModel

logger = get_logger("gsie_api.botanical.engine")

_GBIF_SOURCE = SourceReference(
    type_source=SourceType.referentiel_officiel,
    auteur="GBIF",
    reference="GBIF Backbone Taxonomy (api.gbif.org/v1/species/match)",
)

_INDIGENAT_SOURCE = SourceReference(
    type_source=SourceType.peer_reviewed,
    auteur="Bellifa M. et al. (2026)",
    date_publication="2026",
    reference=(
        "Indigénat des espèces arborées de France à l'échelle des "
        "sylvoécorégions, Journal de Botanique de la Société Botanique "
        "de France, 124(002) — dataset DOI 10.57745/DHJHGS"
    ),
)

_PLANTNET_SOURCE = SourceReference(
    type_source=SourceType.referentiel_officiel,
    auteur="PlantNet",
    reference="https://my.plantnet.org/ — identification par image (78 810 espèces)",
)

_TAXREF_SOURCE = SourceReference(
    type_source=SourceType.referentiel_officiel,
    auteur="MNHN — TAXREF",
    reference=(
        "Référentiel taxonomique TAXREF (via miroir GBIF datasetKey "
        "0e61f8fe-7d25-4f81-ada7-d970bbb2c6d6 — infrastructure MNHN "
        "directe dégradée depuis le piratage de septembre 2025)"
    ),
)


class BotanicalEngineError(Exception):
    """Erreur de base du Botanical Engine."""


class BotanicalEngine:
    """Moteur Botanical — persistance PostgreSQL.

    Une instance par requête HTTP avec la session DB de la requête
    (même schéma que GISEngine/CorrelationEngine).
    """

    def __init__(
        self,
        session: AsyncSession,
        gbif_client: GBIFClient | None = None,
        indigenat_loader: IndigenatLoader | None = None,
        taxref_client: TaxrefClient | None = None,
        plantnet_client: PlantNetClient | None = None,
    ) -> None:
        self._session = session
        self._gbif_client = gbif_client or GBIFClient()
        self._indigenat_loader = indigenat_loader or IndigenatLoader()
        self._taxref_client = taxref_client or TaxrefClient()
        self._plantnet_client = plantnet_client or PlantNetClient()

    @staticmethod
    def version() -> str:
        """Version du moteur."""
        return "0.1.0"

    async def query(self, request: BotanicalQuery) -> BotanicalData:
        """Résout une essence vers son taxon GBIF et le persiste.

        Aucune espèce n'est retournée si GBIF ne trouve aucune
        correspondance (`matchType: NONE`) — jamais de taxon inventé
        en remplacement (ADR-009).

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

    async def query_and_ingest(
        self, request: BotanicalQuery, knowledge_engine: KnowledgeEngine
    ) -> BotanicalIngestResponse:
        """Résout une essence vers son taxon GBIF et l'ingère dans le Knowledge Engine.

        Réutilise `query()` (même persistance `entity`/`entity_alias`,
        aucune double requête GBIF) puis fait passer le taxon résolu par
        `EvidenceKnowledgePipeline` (Gate 5 — maillon amont
        ingestion→Evidence→Knowledge, ROADMAP.md).

        GBIF Backbone Taxonomy est un référentiel taxonomique officiel
        consulté directement (pas une inférence ni une mesure brute) :
        `ContentType.referentiel` + `SourceType.referentiel_officiel`
        plafonnent à `evidence_level=B` dans la matrice de décision —
        statut `accepte`, ingestion automatique, comme SoilGrids.

        Returns:
            `resultats` vide si GBIF ne trouve aucune correspondance —
            jamais un taxon inventé (ADR-009).

        Raises:
            BotanicalEngineError: si l'API GBIF est indisponible.
        """
        donnees = await self.query(request)
        pipeline = EvidenceKnowledgePipeline(knowledge_engine)

        resultats: list[BotanicalIngestResult] = []
        for espece in donnees.especes:
            submission = RawKnowledgeSubmission(
                soumission_id=uuid4(),
                type_contenu=ContentType.referentiel,
                contenu={
                    "nom_scientifique": espece.nom_scientifique,
                    "nom_vernaculaire": espece.nom_vernaculaire,
                    "famille": espece.famille,
                    "statut": espece.statut.value,
                    "synonymes": espece.synonymes,
                    "gbif_taxon_key": espece.gbif_taxon_key,
                },
                source_candidate=_GBIF_SOURCE,
                date_soumission=datetime.now(UTC),
                soumetteur="botanical_engine.gbif",
            )
            resultat = await pipeline.process(
                submission,
                type_=KnowledgeType.concept,
                titre=f"Taxonomie GBIF — {espece.nom_scientifique}",
                description=(
                    f"Taxon accepté {espece.nom_scientifique} "
                    f"(clé GBIF {espece.gbif_taxon_key}), famille "
                    f"{espece.famille}, statut {espece.statut.value} "
                    f"(GBIF Backbone Taxonomy)."
                ),
                domaine_scientifique=DomaineScientifique.botanique,
                mots_cles=["botanique", "gbif", "taxonomie", espece.nom_scientifique],
                moteurs_consommateurs=["botanical", "correlation", "diagnostic"],
            )
            resultats.append(
                BotanicalIngestResult(
                    nom_scientifique=espece.nom_scientifique,
                    statut=resultat.status,
                    evidence_level=resultat.qualified.evidence_level,
                    connaissance_id=resultat.qualified.connaissance_id,
                    version=resultat.knowledge_object.version
                    if resultat.knowledge_object
                    else None,
                    raison=resultat.reason,
                )
            )
            logger.info(
                "botanical_gbif_ingest",
                nom_scientifique=espece.nom_scientifique,
                statut=resultat.status,
                connaissance_id=str(resultat.qualified.connaissance_id),
            )

        return BotanicalIngestResponse(requete_id=request.requete_id, resultats=resultats)

    async def _get_or_create_taxon(self, gbif_taxon_key: int) -> UUID:
        """Retrouve la resource `entity` existante pour ce taxon GBIF, ou la crée.

        Évite de dupliquer une entité à chaque requête sur le même taxon
        (déduplication par `entity_alias.namespace='gbif'` +
        `external_id`, CON-010 — pas de doublon silencieux).
        """
        existing = await self._lire_alias_taxon(gbif_taxon_key)
        if existing is not None:
            return existing

        # `gsie_id` est déterministe (dérivé du taxon GBIF) : deux requêtes
        # concurrentes sur la même essence encore inconnue lisent toutes deux
        # « absent », puis insèrent — la seconde violait l'unicité de
        # `resource.gsie_id` et remontait en 500. Le SAVEPOINT permet de
        # rattraper cette course sans perdre la transaction de la requête.
        try:
            async with self._session.begin_nested():
                entity_id = await self._inserer_taxon(gbif_taxon_key)
        except IntegrityError:
            concurrent = await self._lire_alias_taxon(gbif_taxon_key)
            if concurrent is None:
                raise
            logger.info(
                "taxon_cree_par_requete_concurrente",
                gbif_taxon_key=gbif_taxon_key,
                entity_id=str(concurrent),
            )
            return concurrent
        return entity_id

    async def _lire_alias_taxon(self, gbif_taxon_key: int) -> UUID | None:
        """Retourne l'`entity_id` déjà associé à ce taxon GBIF, s'il existe."""
        resultat = await self._session.execute(
            select(EntityAliasModel.entity_id).where(
                EntityAliasModel.namespace == "gbif",
                EntityAliasModel.external_id == str(gbif_taxon_key),
            )
        )
        return resultat.scalars().first()

    async def _inserer_taxon(self, gbif_taxon_key: int) -> UUID:
        """Insère la resource `entity`, sa ligne type et son alias GBIF."""
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

    def get_indigenat(self, request: IndigenatQuery) -> IndigenatResult | None:
        """Statut d'indigénat réel d'une essence pour une sylvoécorégion (Bellifa et al. 2026).

        Returns:
            None si le taxon est absent du dataset ou si `code_ser` ne
            correspond à aucune colonne réelle — jamais un statut
            approximé (ADR-009).

        Raises:
            BotanicalEngineError: si le dataset local est introuvable.
        """
        try:
            row = self._indigenat_loader.find(request.cd_nom, request.nom_scientifique)
        except IndigenatLoaderError as exc:
            raise BotanicalEngineError(str(exc)) from exc

        if row is None:
            logger.info(
                "botanical_indigenat_taxon_not_found",
                cd_nom=request.cd_nom,
                nom_scientifique=request.nom_scientifique,
            )
            return None

        statut_ser_raw = row.get(request.code_ser)
        if statut_ser_raw is None:
            logger.info("botanical_indigenat_code_ser_unknown", code_ser=request.code_ser)
            return None

        try:
            statut_france = StatutIndigenatFrance(row["Indigenat FR"])
            statut_ser = StatutIndigenatRegion(statut_ser_raw.strip())
        except ValueError as exc:
            raise BotanicalEngineError(
                f"Valeur de statut d'indigénat inattendue dans le dataset : {exc}"
            ) from exc

        cd_nom_raw = (row.get("CD_NOM_TaxRefv18.0") or "").strip()
        cd_nom = int(cd_nom_raw) if cd_nom_raw and cd_nom_raw.upper() != "NA" else None

        return IndigenatResult(
            requete_id=request.requete_id,
            nom_scientifique=row["Nom_scientifique"],
            nom_vernaculaire=row.get("Nom_vernaculaire") or None,
            cd_nom=cd_nom,
            famille=row.get("Famille") or None,
            statut_france=statut_france,
            code_ser=request.code_ser,
            statut_ser=statut_ser,
            source=_INDIGENAT_SOURCE,
        )

    async def resolve_taxref(self, request: TaxrefQuery) -> TaxrefResult | None:
        """Résout un nom scientifique vers son entrée TAXREF réelle (SCI-003).

        Returns:
            None si aucune entrée TAXREF ne correspond — jamais un
            cd_nom inventé (ADR-009).

        Raises:
            BotanicalEngineError: si le miroir GBIF de TAXREF est indisponible.
        """
        try:
            result = await self._taxref_client.search(request.nom_scientifique)
        except TaxrefClientError as exc:
            raise BotanicalEngineError(str(exc)) from exc

        if result is None:
            logger.info("botanical_taxref_no_match", nom_scientifique=request.nom_scientifique)
            return None

        try:
            statut = TaxonStatus(result["taxonomicStatus"])
        except (KeyError, ValueError):
            statut = TaxonStatus.doubtful

        vernacular_names = result.get("vernacularNames", [])
        nom_vernaculaire = next(
            (v["vernacularName"] for v in vernacular_names if v.get("language") == "fra"),
            None,
        )

        return TaxrefResult(
            requete_id=request.requete_id,
            cd_nom=int(result["taxonID"]),
            nom_scientifique=result.get("species") or result["canonicalName"],
            nom_scientifique_complet=result["scientificName"],
            nom_vernaculaire=nom_vernaculaire,
            famille=result.get("family"),
            statut=statut,
            source=_TAXREF_SOURCE,
        )

    async def resolve_taxref_and_ingest(
        self, request: TaxrefQuery, knowledge_engine: KnowledgeEngine
    ) -> TaxrefIngestResponse:
        """Résout une entrée TAXREF et l'ingère dans le Knowledge Engine.

        Réutilise `resolve_taxref()` (aucune double requête) puis fait
        passer l'entrée résolue par `EvidenceKnowledgePipeline` (Gate 5 —
        maillon amont ingestion→Evidence→Knowledge, ROADMAP.md).

        TAXREF (MNHN) est un référentiel taxonomique officiel consulté
        directement : `ContentType.referentiel` +
        `SourceType.referentiel_officiel` plafonnent à
        `evidence_level=B` dans la matrice de décision — statut
        `accepte`, ingestion automatique, comme GBIF et SoilGrids.

        Returns:
            `resultat=None` si aucune entrée TAXREF ne correspond —
            jamais un cd_nom inventé (ADR-009).

        Raises:
            BotanicalEngineError: si le miroir GBIF de TAXREF est indisponible.
        """
        taxref = await self.resolve_taxref(request)
        if taxref is None:
            return TaxrefIngestResponse(requete_id=request.requete_id, resultat=None)

        pipeline = EvidenceKnowledgePipeline(knowledge_engine)
        submission = RawKnowledgeSubmission(
            soumission_id=uuid4(),
            type_contenu=ContentType.referentiel,
            contenu={
                "cd_nom": taxref.cd_nom,
                "nom_scientifique": taxref.nom_scientifique,
                "nom_scientifique_complet": taxref.nom_scientifique_complet,
                "nom_vernaculaire": taxref.nom_vernaculaire,
                "famille": taxref.famille,
                "statut": taxref.statut.value,
            },
            source_candidate=_TAXREF_SOURCE,
            date_soumission=datetime.now(UTC),
            soumetteur="botanical_engine.taxref",
        )
        resultat = await pipeline.process(
            submission,
            type_=KnowledgeType.concept,
            titre=f"Taxonomie TAXREF — {taxref.nom_scientifique_complet}",
            description=(
                f"Entrée TAXREF cd_nom={taxref.cd_nom}, "
                f"{taxref.nom_scientifique_complet}, famille "
                f"{taxref.famille}, statut {taxref.statut.value} "
                f"(MNHN, via miroir GBIF)."
            ),
            domaine_scientifique=DomaineScientifique.botanique,
            mots_cles=["botanique", "taxref", "taxonomie", taxref.nom_scientifique],
            moteurs_consommateurs=["botanical", "correlation", "diagnostic"],
        )
        logger.info(
            "botanical_taxref_ingest",
            cd_nom=taxref.cd_nom,
            statut=resultat.status,
            connaissance_id=str(resultat.qualified.connaissance_id),
        )

        return TaxrefIngestResponse(
            requete_id=request.requete_id,
            resultat=TaxrefIngestResult(
                cd_nom=taxref.cd_nom,
                nom_scientifique=taxref.nom_scientifique,
                statut=resultat.status,
                evidence_level=resultat.qualified.evidence_level,
                connaissance_id=resultat.qualified.connaissance_id,
                version=resultat.knowledge_object.version if resultat.knowledge_object else None,
                raison=resultat.reason,
            ),
        )

    async def identify_and_ingest(
        self, image_bytes: bytes, filename: str, knowledge_engine: KnowledgeEngine
    ) -> PlantNetIngestResponse | None:
        """Identifie une plante par image (PlantNet) et ingère les candidats.

        Réutilise le même client que `/botanical/identify` (aucune double
        requête PlantNet) puis fait passer chaque espèce candidate par
        `EvidenceKnowledgePipeline` (Gate 5 — maillon amont
        ingestion→Evidence→Knowledge, ROADMAP.md).

        Contrairement à SoilGrids (produit modélisé peer-reviewed), une
        identification PlantNet est une inférence par apprentissage
        automatique sur une photo précise : `ContentType.observation` +
        `SourceType.referentiel_officiel` plafonnent à `evidence_level=D`
        dans la matrice de décision — statut `quarantine`, validation
        humaine requise (CON-001) avant réutilisation par les autres
        moteurs. C'est la matrice de l'Evidence Engine qui en décide, pas
        ce module.

        Returns:
            None si PlantNet ne retourne aucune identification — jamais
            une espèce inventée (ADR-009).

        Raises:
            BotanicalEngineError: si l'API PlantNet est indisponible ou
                la clé API manquante.
        """
        try:
            data = await self._plantnet_client.identify(image_bytes, filename=filename)
        except PlantNetClientError as exc:
            raise BotanicalEngineError(str(exc)) from exc

        if data is None:
            return None

        candidats = parse_plantnet_results(data)
        pipeline = EvidenceKnowledgePipeline(knowledge_engine)

        resultats: list[PlantNetIngestResult] = []
        for candidat in candidats:
            submission = RawKnowledgeSubmission(
                soumission_id=uuid4(),
                type_contenu=ContentType.observation,
                contenu={
                    "nom_scientifique": candidat.scientific_name_without_author,
                    "score": candidat.score,
                    "genre": candidat.genus,
                    "famille": candidat.family,
                    "noms_vernaculaires": candidat.common_names,
                    "gbif_id": candidat.gbif_id,
                },
                source_candidate=_PLANTNET_SOURCE,
                date_soumission=datetime.now(UTC),
                soumetteur="botanical_engine.plantnet",
            )
            resultat = await pipeline.process(
                submission,
                type_=KnowledgeType.concept,
                titre=f"Identification PlantNet — {candidat.scientific_name_without_author}",
                description=(
                    f"Score de confiance {candidat.score:.2f}, genre "
                    f"{candidat.genus}, famille {candidat.family} (PlantNet)."
                ),
                domaine_scientifique=DomaineScientifique.botanique,
                mots_cles=["botanique", "plantnet", candidat.scientific_name_without_author],
                moteurs_consommateurs=["botanical", "correlation", "diagnostic"],
            )
            resultats.append(
                PlantNetIngestResult(
                    nom_scientifique=candidat.scientific_name_without_author,
                    score=candidat.score,
                    statut=resultat.status,
                    evidence_level=resultat.qualified.evidence_level,
                    connaissance_id=resultat.qualified.connaissance_id,
                    version=resultat.knowledge_object.version
                    if resultat.knowledge_object
                    else None,
                    raison=resultat.reason,
                )
            )
            logger.info(
                "botanical_plantnet_ingest",
                nom_scientifique=candidat.scientific_name_without_author,
                statut=resultat.status,
                connaissance_id=str(resultat.qualified.connaissance_id),
            )

        return PlantNetIngestResponse(
            best_match=data.get("bestMatch"),
            resultats=resultats,
        )


def parse_plantnet_results(data: dict[str, Any]) -> list[PlantNetIdentificationResult]:
    """Convertit la réponse brute PlantNet en résultats typés.

    Factorisé entre `/botanical/identify` (routeur) et
    `identify_and_ingest` (ci-dessus) — un seul endroit qui sait lire le
    format de réponse PlantNet.
    """
    results: list[PlantNetIdentificationResult] = []
    for r in data.get("results", []):
        species = r.get("species", {})
        genus = species.get("genus", {})
        family = species.get("family", {})
        results.append(
            PlantNetIdentificationResult(
                score=r.get("score", 0.0),
                scientific_name=species.get("scientificName", ""),
                scientific_name_without_author=species.get("scientificNameWithoutAuthor", ""),
                genus=genus.get("scientificNameWithoutAuthor", genus.get("scientificName", "")),
                family=family.get("scientificNameWithoutAuthor", family.get("scientificName", "")),
                common_names=species.get("commonNames", []),
                gbif_id=str(r.get("gbif", {}).get("id", "")) or None,
            )
        )
    return results
