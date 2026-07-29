"""Knowledge Engine — centralisation, structuration et versionnement des connaissances.

Responsabilité (KNOWLEDGE_ENGINE.md §1) :
- Centraliser toutes les connaissances scientifiques qualifiées de GSIE
- Structurer dans un graphe de connaissances interrogeable
- Versionner chaque connaissance (CON-010 — aucune connaissance supprimée silencieusement)
- Fournir les connaissances aux moteurs de raisonnement (source unique de vérité)

Garanties (KNOWLEDGE_ENGINE.md §6) :
- Source unique de vérité — aucun autre moteur ne stocke de connaissance
- Toute connaissance est versionnée et son historique est conservé (CON-010)
- Aucune logique d'inférence — le moteur stocke et fournit, il ne raisonne pas (CON-007)
- Toute connaissance est traçable jusqu'à sa source (CON-005)
- Le graphe est interrogeable hors-ligne (article T-8)
- Une connaissance dont la source est invalidée est révisée, jamais supprimée

Implémentation : persistance PostgreSQL réelle (resource + assertion +
evidence_assessment + revision, schéma v6.2 — RFC-0011). Remplace le
stockage en mémoire de la Vague 1, qui ne survivait pas à un redémarrage
et n'était pas partagé entre workers Gunicorn.

Le contenu du KnowledgeObject qui n'a pas encore de colonne dédiée dans le
schéma v6.2 (titre, description, domaine_scientifique, contenu, source,
domaines_validite, moteurs_consommateurs, relations, mots_cles, conflits)
est conservé dans `resource.metadata_json` — la même convention que la
migration 0003 pour les données v6.1 déjà migrées, afin que les deux
sources restent interrogeables de façon uniforme. Le type d'origine
(KnowledgeType) et le statut d'origine (KnowledgeStatus) sont eux aussi
conservés tels quels dans metadata_json plutôt que reconstruits depuis
claim_kind/lifecycle_status, car ce mapping est à sens unique (concept ET
classification convergent tous deux vers claim_kind=classification —
RFC-0011 §3.3) et ne permettrait pas un aller-retour exact.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from gsie_api.core.logging import get_logger
from gsie_api.engines.evidence.schemas import (
    ConflitBibliographique,
    KnowledgeStatus,
    SourceReference,
    SourceType,
)
from gsie_api.engines.evidence.schemas import EvidenceLevel as EvidenceLevelSchema
from gsie_api.engines.knowledge.regles import DerivationImpossibleError, deriver_regle
from gsie_api.engines.knowledge.schemas import (
    DomaineScientifique,
    DomaineValidite,
    KnowledgeIngestRequest,
    KnowledgeObject,
    KnowledgeQuery,
    KnowledgeQueryResult,
    KnowledgeRevisionRequest,
    KnowledgeType,
    QueryType,
    RelationRef,
    VersionEntry,
)
from gsie_api.engines.reasoning.schemas import RegleInference
from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.models.assertion import (
    AssertionModel,
    AssertionQualifierModel,
    EvidenceAssessmentModel,
)
from gsie_api.infrastructure.models.enums import (
    CitationRole,
    ClaimKind,
    EvidenceLevel,
    LifecycleStatus,
)
from gsie_api.infrastructure.models.prov import CitationModel, SourceModel
from gsie_api.infrastructure.models.spatial_temporal import PlaceModel
from gsie_api.infrastructure.models.temporal_engine import RevisionModel

logger = get_logger("gsie_api.knowledge.engine")

# Rangs des niveaux de preuve pour le filtrage (A=meilleur, F=pire)
_EVIDENCE_RANKS: dict[str, int] = {"A": 6, "B": 5, "C": 4, "D": 3, "E": 2, "F": 1}

# Mapping KnowledgeType (v6.1, 6 valeurs) -> ClaimKind (v6.2, RFC-0011 §3.3).
# Même mapping que celui utilisé par la migration 0003 pour les données v6.1
# existantes — concept et classification convergent tous deux vers
# claim_kind=classification (mapping à sens unique, voir docstring du module).
_TYPE_TO_CLAIM_KIND: dict[KnowledgeType, ClaimKind] = {
    KnowledgeType.concept: ClaimKind.classification,
    KnowledgeType.relation: ClaimKind.relation,
    KnowledgeType.regle: ClaimKind.rule,
    KnowledgeType.seuil: ClaimKind.threshold,
    KnowledgeType.modele: ClaimKind.model,
    KnowledgeType.classification: ClaimKind.classification,
}

_STATUS_TO_LIFECYCLE: dict[KnowledgeStatus, LifecycleStatus] = {
    KnowledgeStatus.accepte: LifecycleStatus.accepted,
    KnowledgeStatus.quarantine: LifecycleStatus.proposed,
    KnowledgeStatus.refuse: LifecycleStatus.rejected,
}


class KnowledgeEngineError(Exception):
    """Erreur de base du Knowledge Engine."""


class KnowledgeNotFoundError(KnowledgeEngineError):
    """La connaissance demandée n'existe pas dans le graphe."""


# Correspondance `source_nature` (base) -> `SourceType` (citation). Elle est
# explicite et exhaustive : deduire le niveau d'une source par ressemblance
# reviendrait a inventer sa qualite scientifique (ADR-009). Une nature non
# couverte fait echouer la conversion plutot que de retomber sur une valeur
# prudente qui masquerait le trou.
_NATURE_VERS_TYPE_SOURCE: dict[str, SourceType] = {
    "data_provider": SourceType.referentiel_officiel,
    "knowledge_provider": SourceType.referentiel_officiel,
    "reference": SourceType.referentiel_officiel,
    "regulatory": SourceType.referentiel_officiel,
    "expert_statement": SourceType.expert_identifie,
    "model_output": SourceType.observation_terrain,
}


class SourceIncitableError(ValueError):
    """La source en base ne peut pas produire une citation complete."""


def _source_reference(source: SourceModel) -> SourceReference:
    """Construit la citation a partir de la source enregistree.

    Une source sans auteur ou sans date n'est pas citable : la revision
    20260728_0009 les exige a l'ecriture, mais les lignes anterieures peuvent
    encore en manquer. On refuse alors, plutot que de citer un document sans
    dire qui l'a ecrit (CON-005).
    """
    manques = [
        nom
        for nom, valeur in (
            ("auteur", source.auteur),
            ("date_publication", source.date_publication),
        )
        if not valeur
    ]
    if manques:
        raise SourceIncitableError(
            f"source {source.id} non citable : {', '.join(manques)} absent(s)"
        )

    nature = source.source_nature.value
    type_source = _NATURE_VERS_TYPE_SOURCE.get(nature)
    if type_source is None:
        raise SourceIncitableError(
            f"source {source.id} : nature « {nature} » sans correspondance de type de source"
        )

    reference = source.doi or source.url or source.title
    return SourceReference(
        type_source=type_source,
        auteur=source.auteur or "",
        date_publication=source.date_publication,
        reference=reference,
    )


class KnowledgeEngine:
    """Moteur de base de connaissances — stockage, requête, versionnement.

    Persistance PostgreSQL. Une instance est créée par requête HTTP avec la
    session DB de la requête (voir knowledge/router.py), suivant le même
    schéma que ResourceService — pas de singleton, pas d'état en mémoire.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --- API publique ---

    @staticmethod
    def version() -> str:
        """Version du moteur."""
        return "0.2.0"

    async def ingest(self, request: KnowledgeIngestRequest) -> KnowledgeObject:
        """Ingère une connaissance qualifiée dans le graphe.

        Le Knowledge Engine ne reçoit que les connaissances au statut
        « accepte » depuis l'Evidence Engine (KNOWLEDGE_ENGINE.md §5).
        Les statuts « quarantine » et « refuse » sont rejetés.
        """
        if request.statut == KnowledgeStatus.refuse:
            raise KnowledgeEngineError(
                f"Connaissance {request.connaissance_id} refusée par l'Evidence Engine "
                f"— les connaissances refusées ne peuvent pas être ingérées (CON-001)"
            )
        if request.statut == KnowledgeStatus.quarantine:
            raise KnowledgeEngineError(
                f"Connaissance {request.connaissance_id} en quarantaine — "
                f"validation humaine requise avant ingestion (CON-001)"
            )

        existing = await self._session.get(ResourceModel, request.connaissance_id)
        if existing is not None:
            raise KnowledgeEngineError(
                f"La connaissance {request.connaissance_id} existe déjà dans le graphe "
                f"— utilisez revise() pour la mettre à jour (CON-010)"
            )

        now = datetime.now(UTC)
        metadata = self._build_metadata(request)

        resource = ResourceModel(
            id=request.connaissance_id,
            type="assertion",
            gsie_id=f"gsie:assertion:{request.connaissance_id}",
            metadata_json=metadata,
        )
        self._session.add(resource)
        evidence_resource_id = uuid4()
        self._session.add(
            ResourceModel(
                id=evidence_resource_id,
                type="evidence_assessment",
                gsie_id=f"gsie:evidence:{request.connaissance_id}",
                metadata_json={},
            )
        )
        # Flush les deux `resource` avant les tables satellites qui les
        # référencent (assertion.id, evidence_assessment.id sont des FK vers
        # resource.id) — l'ordre de flush automatique de SQLAlchemy entre
        # classes mappées indépendantes (sans relationship() déclarée) n'est
        # pas garanti, vérifié empiriquement (ForeignKeyViolationError sans
        # ce flush intermédiaire).
        await self._session.flush()

        assertion = AssertionModel(
            id=request.connaissance_id,
            claim_kind=_TYPE_TO_CLAIM_KIND[request.type],
            lifecycle_status=_STATUS_TO_LIFECYCLE[request.statut],
            version=1,
        )
        self._session.add(assertion)

        evidence = EvidenceAssessmentModel(
            id=evidence_resource_id,
            assertion_id=request.connaissance_id,
            level=EvidenceLevel(request.evidence_level.value),
            method="knowledge_engine_ingest",
            evaluated_at=now,
        )
        self._session.add(evidence)

        self._session.add(
            RevisionModel(
                target_id=request.connaissance_id,
                version=1,
                justification="Ingestion initiale (Evidence Engine -> Knowledge Engine)",
                valid_time_start=now,
                transaction_time=now,
            )
        )

        await self._session.flush()
        logger.info(
            "knowledge_ingested",
            connaissance_id=str(request.connaissance_id),
            type=request.type.value,
            version=1,
        )

        return self._to_knowledge_object(
            connaissance_id=request.connaissance_id,
            metadata=metadata,
            evidence_level=request.evidence_level,
            version=1,
            date_integration=now,
            historique=[],
        )

    async def query(self, query: KnowledgeQuery) -> KnowledgeQueryResult:
        """Interroge le graphe de connaissances.

        `evidence_assessment` est une relation 1-N append-only : réviser le
        niveau de preuve d'une connaissance ajoute une ligne sans effacer la
        précédente (CON-010). Une jointure directe dupliquait donc la
        connaissance autant de fois qu'elle avait été révisée, gonflait
        `total`, faussait la pagination, et surtout présentait le niveau de
        preuve **périmé** comme une connaissance à part entière. On ne retient
        que la dernière évaluation de chaque assertion.
        """
        derniere_evaluation = select(
            EvidenceAssessmentModel,
            func.row_number()
            .over(
                partition_by=EvidenceAssessmentModel.assertion_id,
                order_by=(
                    EvidenceAssessmentModel.evaluated_at.desc(),
                    EvidenceAssessmentModel.id.desc(),
                ),
            )
            .label("rang"),
        ).subquery()
        evaluation_courante = aliased(EvidenceAssessmentModel, derniere_evaluation)

        result = await self._session.execute(
            select(ResourceModel, AssertionModel, evaluation_courante)
            .join(AssertionModel, AssertionModel.id == ResourceModel.id)
            .join(
                derniere_evaluation,
                derniere_evaluation.c.assertion_id == ResourceModel.id,
            )
            .where(ResourceModel.type == "assertion", derniere_evaluation.c.rang == 1)
        )

        objects = [
            self._to_knowledge_object(
                connaissance_id=resource.id,
                metadata=resource.metadata_json or {},
                evidence_level=None,
                version=assertion.version,
                date_integration=resource.updated_at,
                historique=None,
                evidence_model=evidence,
            )
            for resource, assertion, evidence in result.all()
        ]

        objects = self._filter_by_query_type(objects, query)

        if query.evidence_min is not None:
            min_rank = _EVIDENCE_RANKS[query.evidence_min.value]
            objects = [o for o in objects if _EVIDENCE_RANKS[o.evidence_level.value] >= min_rank]

        objects = self._filter_by_custom_filters(objects, query.filtres)
        objects.sort(key=lambda o: o.date_integration, reverse=True)

        total = len(objects)
        start = (query.page - 1) * query.page_size
        end = start + query.page_size
        page_objects = objects[start:end]

        # Historique chargé seulement pour la page retournée (évite de charger
        # tout l'historique de toutes les connaissances pour une simple liste).
        for obj in page_objects:
            obj.historique = await self._load_historique(obj.connaissance_id, obj.version)

        return KnowledgeQueryResult(
            requete_id=query.requete_id,
            connaissances=page_objects,
            total=total,
            version_graph=self.version(),
            page=query.page,
            page_size=query.page_size,
        )

    async def revise(self, request: KnowledgeRevisionRequest) -> KnowledgeObject:
        """Révise une connaissance existante (CON-010).

        Crée une nouvelle Revision (append-only) plutôt que de modifier
        silencieusement — l'ancienne version reste reconstructible via
        l'historique des Revision.
        """
        resource = await self._session.get(ResourceModel, request.connaissance_id)
        assertion = await self._session.get(AssertionModel, request.connaissance_id)
        if resource is None or assertion is None:
            raise KnowledgeNotFoundError(
                f"Connaissance {request.connaissance_id} introuvable dans le graphe"
            )

        if (
            request.nouveau_contenu is None
            and request.nouveau_evidence_level is None
            and request.nouvelle_source is None
            and request.nouveaux_domaines_validite is None
        ):
            raise KnowledgeEngineError(
                "Aucun champ modifié dans la révision — au moins un champ requis"
            )

        evidence = (
            (
                await self._session.execute(
                    select(EvidenceAssessmentModel)
                    .where(EvidenceAssessmentModel.assertion_id == request.connaissance_id)
                    .order_by(EvidenceAssessmentModel.evaluated_at.desc())
                )
            )
            .scalars()
            .first()
        )

        metadata = dict(resource.metadata_json or {})
        if request.nouveau_contenu is not None:
            metadata["contenu"] = request.nouveau_contenu
        if request.nouvelle_source is not None:
            metadata["source"] = request.nouvelle_source.model_dump(mode="json")
        if request.nouveaux_domaines_validite is not None:
            metadata["domaines_validite"] = [
                dv.model_dump(mode="json") for dv in request.nouveaux_domaines_validite
            ]

        now = datetime.now(UTC)
        new_version = assertion.version + 1

        justification = request.justification
        if request.rfc_reference:
            justification = f"{justification} (RFC: {request.rfc_reference})"

        self._session.add(
            RevisionModel(
                target_id=request.connaissance_id,
                version=new_version,
                justification=justification,
                valid_time_start=now,
                transaction_time=now,
            )
        )

        resource.metadata_json = metadata
        assertion.version = new_version

        new_evidence_level = request.nouveau_evidence_level
        if new_evidence_level is not None and evidence is not None:
            evidence_resource_id = uuid4()
            self._session.add(
                ResourceModel(
                    id=evidence_resource_id,
                    type="evidence_assessment",
                    gsie_id=f"gsie:evidence:{request.connaissance_id}:{new_version}",
                    metadata_json={},
                )
            )
            # Même contrainte d'ordre que dans ingest() — flush avant la FK.
            await self._session.flush()
            self._session.add(
                EvidenceAssessmentModel(
                    id=evidence_resource_id,
                    assertion_id=request.connaissance_id,
                    level=EvidenceLevel(new_evidence_level.value),
                    method="knowledge_engine_revise",
                    evaluated_at=now,
                )
            )

        await self._session.flush()
        logger.info(
            "knowledge_revised",
            connaissance_id=str(request.connaissance_id),
            new_version=new_version,
            justification=request.justification[:100],
        )

        result = self._to_knowledge_object(
            connaissance_id=request.connaissance_id,
            metadata=metadata,
            evidence_level=None,
            version=new_version,
            date_integration=now,
            historique=None,
            evidence_model=evidence if new_evidence_level is None else None,
        )
        if new_evidence_level is not None:
            result.evidence_level = new_evidence_level
        result.historique = await self._load_historique(request.connaissance_id, new_version)
        return result

    async def stats(self) -> dict[str, int]:
        """Retourne les statistiques du graphe."""
        result = await self._session.execute(
            select(AssertionModel.claim_kind, ResourceModel.metadata_json).join(
                ResourceModel, ResourceModel.id == AssertionModel.id
            )
        )
        type_counts: dict[str, int] = {}
        total = 0
        for claim_kind, metadata in result.all():
            total += 1
            original_type = (metadata or {}).get("type", claim_kind.value)
            type_counts[original_type] = type_counts.get(original_type, 0) + 1

        return {
            "total_objects": total,
            **{f"type_{k}": v for k, v in type_counts.items()},
        }

    # --- Reconstruction / helpers internes ---

    def _build_metadata(self, request: KnowledgeIngestRequest) -> dict[str, Any]:
        """Construit le metadata_json à partir d'une requête d'ingestion."""
        return {
            "type": request.type.value,
            "statut": request.statut.value,
            "titre": request.titre,
            "description": request.description,
            "domaine_scientifique": request.domaine_scientifique.value,
            "contenu": request.contenu_normalise,
            "source": request.source.model_dump(mode="json"),
            "domaines_validite": [dv.model_dump(mode="json") for dv in request.domaines_validite],
            "moteurs_consommateurs": list(request.moteurs_consommateurs),
            "relations": [r.model_dump(mode="json") for r in request.relations],
            "mots_cles": list(request.mots_cles),
            "conflits": [c.model_dump(mode="json") for c in request.conflits],
        }

    def _to_knowledge_object(
        self,
        connaissance_id: UUID,
        metadata: dict[str, Any],
        evidence_level: Any,
        version: int,
        date_integration: datetime,
        historique: list[VersionEntry] | None,
        evidence_model: EvidenceAssessmentModel | None = None,
    ) -> KnowledgeObject:
        """Reconstruit un KnowledgeObject depuis resource.metadata_json + colonnes typées."""
        from gsie_api.engines.evidence.schemas import EvidenceLevel as PydanticEvidenceLevel

        if evidence_level is None:
            evidence_level = (
                PydanticEvidenceLevel(evidence_model.level.value)
                if evidence_model is not None
                else PydanticEvidenceLevel.F
            )

        for required_field in ("type", "domaine_scientifique"):
            if metadata.get(required_field) is None:
                raise KnowledgeEngineError(
                    f"Connaissance {connaissance_id} : metadata_json ne contient pas "
                    f"« {required_field} » (ou vaut null) — resource.metadata_json corrompu "
                    f"ou incomplet, impossible de reconstruire ce KnowledgeObject"
                )

        return KnowledgeObject(
            connaissance_id=connaissance_id,
            type=KnowledgeType(metadata["type"]),
            titre=metadata.get("titre", ""),
            description=metadata.get("description", ""),
            domaine_scientifique=DomaineScientifique(metadata["domaine_scientifique"]),
            contenu=metadata.get("contenu", {}),
            evidence_level=evidence_level,
            source=SourceReference.model_validate(metadata.get("source", {})),
            statut=KnowledgeStatus(metadata.get("statut", KnowledgeStatus.accepte.value)),
            version=version,
            date_integration=date_integration,
            historique=historique or [],
            domaines_validite=[
                DomaineValidite.model_validate(dv) for dv in metadata.get("domaines_validite", [])
            ],
            moteurs_consommateurs=list(metadata.get("moteurs_consommateurs", [])),
            relations=[RelationRef.model_validate(r) for r in metadata.get("relations", [])],
            mots_cles=list(metadata.get("mots_cles", [])),
            conflits=[
                ConflitBibliographique.model_validate(c) for c in metadata.get("conflits", [])
            ],
        )

    async def _load_historique(
        self, connaissance_id: UUID, current_version: int
    ) -> list[VersionEntry]:
        """Reconstruit l'historique (CON-010) depuis les Revision antérieures.

        Sémantique héritée de l'implémentation en mémoire (Vague 1) : une
        entrée d'historique « version N » porte la date de création de la
        version N, mais la JUSTIFICATION de la révision qui l'a fait passer
        à N+1 (« pourquoi on a quitté cette version »), pas celle de sa
        propre création. On associe donc row(version=N).valid_time_start à
        row(version=N+1).justification — vérifié empiriquement (le test
        should_create_new_version_when_revising attend exactement ce couplage).

        Note : RevisionModel n'a pas de colonne rfc_reference dédiée — elle est
        embarquée dans `justification` (« ... (RFC: xxx) ») par revise(), et
        n'est pas re-décomposée ici (limitation connue, sans perte d'information
        puisque le texte complet est conservé).
        """
        if current_version <= 1:
            return []
        rows = (
            (
                await self._session.execute(
                    select(RevisionModel)
                    .where(
                        RevisionModel.target_id == connaissance_id,
                        RevisionModel.version <= current_version,
                    )
                    .order_by(RevisionModel.version)
                )
            )
            .scalars()
            .all()
        )
        by_version = {row.version: row for row in rows}
        return [
            VersionEntry(
                version=v,
                date=by_version[v].valid_time_start,
                justification=by_version[v + 1].justification,
                rfc_reference=None,
            )
            for v in range(1, current_version)
            if v in by_version and (v + 1) in by_version
        ]

    # --- Filtres internes (inchangés — opèrent sur des KnowledgeObject déjà
    # reconstruits, indépendants de la source de stockage) ---

    def _filter_by_query_type(
        self,
        objects: list[KnowledgeObject],
        query: KnowledgeQuery,
    ) -> list[KnowledgeObject]:
        """Filtre les objets selon le type de requête."""
        if query.type == QueryType.par_concept:
            return [o for o in objects if o.type == KnowledgeType.concept]
        if query.type == QueryType.par_relation:
            return [o for o in objects if o.type == KnowledgeType.relation]
        if query.type == QueryType.par_domaine:
            domaine = query.filtres.get("domaine_scientifique")
            if domaine:
                return [o for o in objects if o.domaine_scientifique.value == domaine]
            return objects
        if query.type == QueryType.par_essence:
            essence = query.filtres.get("essence", "").lower()
            if essence:
                return [o for o in objects if any(essence in mc.lower() for mc in o.mots_cles)]
            return objects
        if query.type == QueryType.par_station:
            return [
                o
                for o in objects
                if any("station" in dv.parametre.lower() for dv in o.domaines_validite)
            ]
        return objects

    def _filter_by_custom_filters(
        self,
        objects: list[KnowledgeObject],
        filtres: dict[str, object],
    ) -> list[KnowledgeObject]:
        """Applique les filtres clé-valeur supplémentaires."""
        if not filtres:
            return objects

        result = objects

        if "connaissance_id" in filtres:
            target_id = UUID(str(filtres["connaissance_id"]))
            result = [o for o in result if o.connaissance_id == target_id]

        if "mots_cles" in filtres:
            keywords = filtres["mots_cles"]
            if isinstance(keywords, list):
                keyword_set = {str(k).lower() for k in keywords}
                result = [o for o in result if any(mc.lower() in keyword_set for mc in o.mots_cles)]

        if "titre" in filtres:
            titre_search = str(filtres["titre"]).lower()
            result = [o for o in result if titre_search in o.titre.lower()]

        if "domaine_scientifique" in filtres:
            domaine = str(filtres["domaine_scientifique"])
            result = [o for o in result if o.domaine_scientifique.value == domaine]

        return result

    # --- Recuperation des regles par contexte (RFC-0028 §4.3) ---

    async def regles_applicables(
        self,
        territoire_id: UUID,
        *,
        variables_connues: frozenset[str],
        evidence_min: EvidenceLevelSchema | None = None,
    ) -> tuple[list[RegleInference], list[str]]:
        """Retourne les règles applicables à un territoire, et ce qui a été écarté.

        Une règle est retenue si, et seulement si :

        * son `claim_kind` est `rule` ou `threshold` ;
        * son `lifecycle_status` vaut `accepted` — une règle en brouillon ou
          dépréciée ne raisonne pas ;
        * **son domaine de validité est renseigné et contient le territoire**.
          Un domaine absent vaut « nulle part », jamais « partout »
          (`DEC-000038`) : une règle tirée d'un catalogue régional appliquée
          hors de sa zone produirait une conclusion fausse citant une source
          réelle, avec une chaîne d'inférence complète — invisible ;
        * elle cite une source, par une `citation` de rôle `primary`. Une règle
          non sourcée n'influence pas un diagnostic ;
        * son niveau de preuve atteint le plancher demandé, s'il en est un.

        Ce qui est écarté est **retourné**, pas tu : une règle rejetée parce
        qu'elle est mal formée doit pouvoir être corrigée, et le silence
        laisserait croire à une absence de connaissance.

        Args:
            territoire_id: `place` dont on cherche les règles applicables.
            variables_connues: codes du vocabulaire contrôlé. Une règle portant
                une variable hors vocabulaire est écartée.
            evidence_min: plancher de preuve. Aucun par défaut (`DEC-000038`) —
                c'est à l'appelant de déclarer son exigence.

        Returns:
            Les règles dérivées, et la liste des motifs d'écartement.
        """
        territoire = aliased(PlaceModel)
        domaine = aliased(PlaceModel)

        # Derniere evaluation de preuve seulement : `evidence_assessment` est
        # une relation 1-N append-only, et joindre sans fenetrage ferait
        # apparaitre une regle autant de fois qu'elle a ete revisee, avec des
        # niveaux contradictoires.
        derniere = select(
            EvidenceAssessmentModel.assertion_id.label("assertion_id"),
            EvidenceAssessmentModel.level.label("level"),
            func.row_number()
            .over(
                partition_by=EvidenceAssessmentModel.assertion_id,
                order_by=(
                    EvidenceAssessmentModel.evaluated_at.desc(),
                    EvidenceAssessmentModel.id.desc(),
                ),
            )
            .label("rang"),
        ).subquery()

        requete = (
            select(AssertionModel, derniere.c.level, SourceModel)
            .join(domaine, domaine.id == AssertionModel.spatial_scope_id)
            .join(territoire, territoire.id == territoire_id)
            .join(derniere, derniere.c.assertion_id == AssertionModel.id)
            .join(CitationModel, CitationModel.target_id == AssertionModel.id)
            .join(SourceModel, SourceModel.id == CitationModel.source_id)
            .where(
                AssertionModel.claim_kind.in_([ClaimKind.rule, ClaimKind.threshold]),
                AssertionModel.lifecycle_status == LifecycleStatus.accepted,
                # Domaine renseigne : la jointure sur `domaine` l'impose deja,
                # `spatial_scope_id` etant nullable.
                CitationModel.citation_role == CitationRole.primary,
                derniere.c.rang == 1,
                func.ST_Contains(domaine.geometry, territoire.geometry),
            )
        )

        lignes = (await self._session.execute(requete)).all()
        if not lignes:
            return [], []

        qualificateurs = await self._qualificateurs_par_assertion([ligne[0].id for ligne in lignes])

        regles: list[RegleInference] = []
        ecartees: list[str] = []
        for assertion, niveau, source in lignes:
            if (
                evidence_min is not None
                and _EVIDENCE_RANKS[niveau.value] < _EVIDENCE_RANKS[evidence_min.value]
            ):
                ecartees.append(
                    f"{assertion.id} : niveau de preuve {niveau.value} sous le plancher "
                    f"{evidence_min.value}"
                )
                continue
            try:
                derivee = deriver_regle(
                    str(assertion.id),
                    qualificateurs.get(assertion.id, {}),
                    variables_connues=variables_connues,
                )
            except DerivationImpossibleError as exc:
                ecartees.append(f"{assertion.id} : {', '.join(exc.manques)}")
                continue

            regles.append(
                RegleInference(
                    identifiant=derivee.identifiant,
                    condition=derivee.condition,
                    enonce_conclusion=derivee.enonce_conclusion,
                    source=_source_reference(source),
                    evidence_level=EvidenceLevelSchema(niveau.value),
                    niveau_confiance=derivee.niveau_confiance,
                )
            )

        logger.info(
            "regles_applicables",
            territoire_id=str(territoire_id),
            retenues=len(regles),
            ecartees=len(ecartees),
        )
        return regles, ecartees

    async def _qualificateurs_par_assertion(
        self, assertion_ids: list[UUID]
    ) -> dict[UUID, dict[str, str]]:
        """Charge les qualificateurs des assertions en une requête."""
        lignes = (
            await self._session.execute(
                select(
                    AssertionQualifierModel.assertion_id,
                    AssertionQualifierModel.key,
                    AssertionQualifierModel.value,
                ).where(AssertionQualifierModel.assertion_id.in_(assertion_ids))
            )
        ).all()

        par_assertion: dict[UUID, dict[str, str]] = {}
        for assertion_id, cle, valeur in lignes:
            par_assertion.setdefault(assertion_id, {})[cle] = valeur
        return par_assertion
