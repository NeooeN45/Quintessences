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

Implémentation Vague 1 : stockage en mémoire (dict indexé par UUID).
La persistance PostgreSQL/Neo4j est une évolution future (pistes §8).
"""

from datetime import UTC, datetime
from uuid import UUID

from gsie_api.core.logging import get_logger
from gsie_api.engines.evidence.schemas import KnowledgeStatus
from gsie_api.engines.knowledge.schemas import (
    KnowledgeIngestRequest,
    KnowledgeObject,
    KnowledgeQuery,
    KnowledgeQueryResult,
    KnowledgeRevisionRequest,
    KnowledgeType,
    QueryType,
    VersionEntry,
)

logger = get_logger("gsie_api.knowledge.engine")

# Rangs des niveaux de preuve pour le filtrage (A=meilleur, F=pire)
_EVIDENCE_RANKS: dict[str, int] = {"A": 6, "B": 5, "C": 4, "D": 3, "E": 2, "F": 1}


class KnowledgeEngineError(Exception):
    """Erreur de base du Knowledge Engine."""


class KnowledgeNotFoundError(KnowledgeEngineError):
    """La connaissance demandée n'existe pas dans le graphe."""


class KnowledgeEngine:
    """Moteur de base de connaissances — stockage, requête, versionnement.

    Thread-safety : l'implémentation en mémoire n'est pas thread-safe.
    En production (multi-worker), utiliser la persistance PostgreSQL.
    Pour la Vague 1 (single-worker Gunicorn), c'est suffisant.
    """

    def __init__(self) -> None:
        self._store: dict[UUID, KnowledgeObject] = {}
        self._version: str = "0.1.0"

    # --- API publique ---

    @staticmethod
    def version() -> str:
        """Version du moteur."""
        return "0.1.0"

    def ingest(self, request: KnowledgeIngestRequest) -> KnowledgeObject:
        """Ingère une connaissance qualifiée dans le graphe.

        Le Knowledge Engine ne reçoit que les connaissances au statut
        « accepte » depuis l'Evidence Engine (KNOWLEDGE_ENGINE.md §5).
        Les statuts « quarantine » et « refuse » sont rejetés.

        Args:
            request: Requête d'ingestion avec métadonnées complètes.

        Returns:
            Le KnowledgeObject créé et stocké.

        Raises:
            KnowledgeEngineError: Si l'UUID existe déjà ou si le statut n'est pas « accepte ».
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

        if request.connaissance_id in self._store:
            raise KnowledgeEngineError(
                f"La connaissance {request.connaissance_id} existe déjà dans le graphe "
                f"— utilisez revise() pour la mettre à jour (CON-010)"
            )

        now = datetime.now(UTC)
        obj = KnowledgeObject(
            connaissance_id=request.connaissance_id,
            type=request.type,
            titre=request.titre,
            description=request.description,
            domaine_scientifique=request.domaine_scientifique,
            contenu=request.contenu_normalise,
            evidence_level=request.evidence_level,
            source=request.source,
            statut=request.statut,
            version=1,
            date_integration=now,
            historique=[],
            domaines_validite=request.domaines_validite,
            moteurs_consommateurs=request.moteurs_consommateurs,
            relations=request.relations,
            mots_cles=request.mots_cles,
            conflits=request.conflits,
        )

        self._store[request.connaissance_id] = obj
        logger.info(
            "knowledge_ingested",
            connaissance_id=str(request.connaissance_id),
            type=request.type.value,
            version=1,
        )
        return obj

    def query(self, query: KnowledgeQuery) -> KnowledgeQueryResult:
        """Interroge le graphe de connaissances.

        Args:
            query: Requête typée (par_concept, par_relation, par_domaine, etc.)

        Returns:
            KnowledgeQueryResult avec les connaissances correspondantes (paginées).
        """
        objects = list(self._store.values())

        # Filtre par type selon le QueryType
        objects = self._filter_by_query_type(objects, query)

        # Filtre par evidence_min
        if query.evidence_min is not None:
            min_rank = _EVIDENCE_RANKS[query.evidence_min.value]
            objects = [
                o for o in objects
                if _EVIDENCE_RANKS[o.evidence_level.value] >= min_rank
            ]

        # Filtres additionnels (clé-valeur)
        objects = self._filter_by_custom_filters(objects, query.filtres)

        # Tri par date_integration (plus récent d'abord)
        objects.sort(key=lambda o: o.date_integration, reverse=True)

        total = len(objects)

        # Pagination
        start = (query.page - 1) * query.page_size
        end = start + query.page_size
        page_objects = objects[start:end]

        return KnowledgeQueryResult(
            requete_id=query.requete_id,
            connaissances=page_objects,
            total=total,
            version_graph=self._version,
            page=query.page,
            page_size=query.page_size,
        )

    def revise(self, request: KnowledgeRevisionRequest) -> KnowledgeObject:
        """Révise une connaissance existante (CON-010).

        Archive l'ancienne version dans l'historique et crée une nouvelle
        version. La connaissance n'est jamais supprimée silencieusement.

        Args:
            request: Requête de révision avec justification obligatoire.

        Returns:
            Le KnowledgeObject révisé (nouvelle version).

        Raises:
            KnowledgeNotFoundError: Si l'UUID n'existe pas.
            KnowledgeEngineError: Si aucun champ n'est modifié.
        """
        if request.connaissance_id not in self._store:
            raise KnowledgeNotFoundError(
                f"Connaissance {request.connaissance_id} introuvable dans le graphe"
            )

        current = self._store[request.connaissance_id]

        # Vérifier qu'au moins un champ est modifié
        if (
            request.nouveau_contenu is None
            and request.nouveau_evidence_level is None
            and request.nouvelle_source is None
            and request.nouveaux_domaines_validite is None
        ):
            raise KnowledgeEngineError(
                "Aucun champ modifié dans la révision — au moins un champ requis"
            )

        # Archiver la version courante dans l'historique (CON-010)
        history_entry = VersionEntry(
            version=current.version,
            date=current.date_integration,
            justification=request.justification,
            rfc_reference=request.rfc_reference,
        )

        # Construire la nouvelle version
        new_version = current.version + 1
        revised = current.model_copy(update={
            "version": new_version,
            "date_integration": datetime.now(UTC),
            "historique": [*current.historique, history_entry],
            "contenu": (
                request.nouveau_contenu
                if request.nouveau_contenu is not None
                else current.contenu
            ),
            "evidence_level": (
                request.nouveau_evidence_level
                if request.nouveau_evidence_level is not None
                else current.evidence_level
            ),
            "source": (
                request.nouvelle_source
                if request.nouvelle_source is not None
                else current.source
            ),
            "domaines_validite": (
                request.nouveaux_domaines_validite
                if request.nouveaux_domaines_validite is not None
                else current.domaines_validite
            ),
        })

        self._store[request.connaissance_id] = revised
        logger.info(
            "knowledge_revised",
            connaissance_id=str(request.connaissance_id),
            old_version=current.version,
            new_version=new_version,
            justification=request.justification[:100],
        )
        return revised

    def stats(self) -> dict[str, int]:
        """Retourne les statistiques du graphe."""
        type_counts: dict[str, int] = {}
        for obj in self._store.values():
            type_counts[obj.type.value] = type_counts.get(obj.type.value, 0) + 1

        return {
            "total_objects": len(self._store),
            **{f"type_{k}": v for k, v in type_counts.items()},
        }

    # --- Filtres internes ---

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
            # Filtre par mots_cles contenant le nom d'essence
            essence = query.filtres.get("essence", "").lower()
            if essence:
                return [
                    o for o in objects
                    if any(essence in mc.lower() for mc in o.mots_cles)
                ]
            return objects
        if query.type == QueryType.par_station:
            # Filtre par domaines_validite contenant « station »
            return [
                o for o in objects
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

        # Filtre par connaissance_id (recherche directe)
        if "connaissance_id" in filtres:
            target_id = UUID(str(filtres["connaissance_id"]))
            result = [o for o in result if o.connaissance_id == target_id]

        # Filtre par mots_cles (intersection non vide)
        if "mots_cles" in filtres:
            keywords = filtres["mots_cles"]
            if isinstance(keywords, list):
                keyword_set = {str(k).lower() for k in keywords}
                result = [
                    o for o in result
                    if any(mc.lower() in keyword_set for mc in o.mots_cles)
                ]

        # Filtre par titre (recherche substring)
        if "titre" in filtres:
            titre_search = str(filtres["titre"]).lower()
            result = [o for o in result if titre_search in o.titre.lower()]

        # Filtre par domaine_scientifique
        if "domaine_scientifique" in filtres:
            domaine = str(filtres["domaine_scientifique"])
            result = [o for o in result if o.domaine_scientifique.value == domaine]

        return result
