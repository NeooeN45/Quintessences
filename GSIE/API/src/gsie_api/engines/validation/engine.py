"""Validation Engine — contrôle final avant présentation à l'utilisateur.

Responsabilité (VALIDATION_ENGINE.md §1) : vérifier la cohérence, la
conformité constitutionnelle et la complétude des diagnostics et
recommandations avant leur présentation, en bloquant toute sortie non
conforme.

Le moteur ne produit **pas** de contenu — il valide et filtre
(séparation des responsabilités, §6). Il applique une série de
contrôles déclaratifs et retourne un `ValidationResult` :

- `valide` : tous les contrôles sont conformes, la sortie peut être
  présentée ;
- `bloque` : au moins un contrôle critique est non conforme, la sortie
  est bloquée avec cause ;
- `partiellement_valide` : certains contrôles non critiques échouent
  sur une partie de l'ensemble (ensemble complet mixte).

Contrôles implémentés en v1 (VALIDATION_ENGINE.md §5-§6) :
1. `presence_niveau_preuve` — toute recommandation/diagnostic doit
   porter un niveau de preuve (GSIE-CON-002).
2. `presence_source` — toute sortie doit citer au moins une source
   identifiable (GSIE-CON-002).
3. `presence_chaine_inference` — un diagnostic doit référencer au
   moins une chaîne d'inférence (GSIE-CON-004).
4. `recommandation_contournable` — toute recommandation doit être
   contournable (GSIE-CON-001).
5. `explicabilite` — la sortie doit comporter une justification
   lisible (GSIE-CON-004).
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.logging import get_logger
from gsie_api.engines.validation.schemas import (
    CauseBlocage,
    ControleResultat,
    ResultatControle,
    TypeCauseBlocage,
    TypeSortie,
    ValidationRequest,
    ValidationResult,
    ValidationStatut,
)
from gsie_api.infrastructure.models.base import ResourceModel
from gsie_api.infrastructure.models.enrichment import ValidationResultModel
from gsie_api.infrastructure.models.temporal_engine import RevisionModel

logger = get_logger("gsie_api.validation.engine")


class ValidationEngineError(Exception):
    """Erreur de base du Validation Engine."""


class ValidationEngine:
    """Moteur de validation — persistance des résultats bloqués.

    Le moteur persiste les résultats `bloque` et `partiellement_valide`
    en base pour alimentation du Learning Engine (§3 — sorties vers
    LEARNING_ENGINE). Les résultats `valide` ne sont pas persistés
    (pas d'information d'apprentissage).
    """

    def __init__(self, session: AsyncSession | None = None) -> None:
        self._session = session

    @staticmethod
    def version() -> str:
        """Version du moteur."""
        return "0.1.0"

    async def validate(self, request: ValidationRequest) -> ValidationResult:
        """Valide une sortie (diagnostic, recommandation ou ensemble complet).

        Applique les contrôles déclaratifs et retourne un ValidationResult.
        Ne lève jamais d'exception pour une sortie non conforme : le
        blocage est un résultat normal, pas une erreur (§6).
        """
        controles: list[ControleResultat] = []
        causes_blocage: list[CauseBlocage] = []

        # Contrôle 1 — présence d'un niveau de preuve (GSIE-CON-002)
        controles.append(self._controle_niveau_preuve(request))

        # Contrôle 2 — présence d'une source (GSIE-CON-002)
        controles.append(self._controle_source(request))

        # Contrôle 3 — présence d'une chaîne d'inférence (GSIE-CON-004)
        # Non applicable pour une recommandation seule
        controles.append(self._controle_chaine_inference(request))

        # Contrôle 4 — recommandation contournable (GSIE-CON-001)
        controles.append(self._controle_contournable(request))

        # Contrôle 5 — explicabilité (GSIE-CON-004)
        controles.append(self._controle_explicabilite(request))

        # Collecte des causes de blocage
        for controle in controles:
            if controle.resultat == ResultatControle.non_conforme:
                causes_blocage.append(
                    CauseBlocage(
                        type_cause=self._cause_pour_controle(controle.nom_controle),
                        element_concerne=request.requete_id,
                        description=controle.details,
                    )
                )

        # Détermination du statut
        non_conformes = [c for c in controles if c.resultat == ResultatControle.non_conforme]
        if not non_conformes:
            statut = ValidationStatut.valide
        elif request.type_sortie == TypeSortie.ensemble_complet and self._tous_non_critiques(
            non_conformes
        ):
            statut = ValidationStatut.partiellement_valide
        else:
            statut = ValidationStatut.bloque

        logger.info(
            "validation_complete",
            requete_id=str(request.requete_id),
            statut=statut.value,
            n_controles=len(controles),
            n_causes=len(causes_blocage),
        )

        result = ValidationResult(
            validation_id=uuid4(),
            requete_origine=request.requete_id,
            statut=statut,
            controles=controles,
            causes_blocage=causes_blocage if statut != ValidationStatut.valide else [],
            date_validation=datetime.now(UTC),
        )

        # Persistance des résultats bloqués/partiels pour le Learning Engine
        # (RFC-0028, migration 0028). Un ValidationEngine construit sans
        # session ne peut pas remplir ce contrat — on journalise au lieu
        # d'avaler silencieusement le pattern de blocage, sans pour autant
        # bloquer l'utilisation du moteur en validation seule (tests unitaires,
        # intégration sans resource origine). Le warning reste visible dans les
        # journaux de production — un déploiement sans session serait repéré.
        if statut != ValidationStatut.valide:
            if self._session is None:
                logger.warning(
                    "validation_result_non_persiste",
                    statut=statut.value,
                    requete_id=str(request.requete_id),
                    raison=(
                        "aucune session DB fournie — "
                        "le Learning Engine perd ce pattern de blocage"
                    ),
                )
            else:
                await self._persist_result(request, result)

        return result

    async def _persist_result(self, request: ValidationRequest, result: ValidationResult) -> None:
        """Persiste un résultat bloqué/partiel pour alimentation du Learning Engine.

        La ligne ``validation_result`` est un attribut de la resource validée
        (``requete_id``), pas une resource à part entière — conforme à la
        docstring de ``models/enrichment.py`` qui exclut ces tables du
        métamodèle (pas de ``register_type``). La FK ``requete_origine`` pointe
        donc vers la resource existante, pas vers une resource fantôme.

        Invariant CON-010 : une Revision v1 est créée sur la resource origine,
        comme pour toute insertion de resource (``ResourceService.create``,
        ``KnowledgeEngine``). Sans cela, le chemin d'écriture contourne
        l'invariant documenté dans ``ingestion/bulk.py``.
        """
        session = self._session
        if session is None:
            return  # garde-fou — le caller (validate) a déjà levé si besoin

        resource_id = request.requete_id

        # Invariant CON-010 : une Revision est créée pour toute resource
        # affectée. Ici la resource origine reçoit une revision traçant
        # le passage en validation.
        #
        # Verrou sur la resource origine (SELECT ... FOR UPDATE) pour sérialiser
        # l'allocation du numéro de version : sans ce verrou, deux validations
        # concurrentes de la même resource calculeraient toutes deux max()+1 et
        # produiraient deux révisions de même numéro (audit 2026-08-02, 3ᵉ passe).
        await session.execute(
            select(ResourceModel).where(ResourceModel.id == resource_id).with_for_update()
        )
        next_version = (
            await session.execute(
                select(func.max(RevisionModel.version)).where(
                    RevisionModel.target_id == resource_id
                )
            )
        ).scalar_one()
        version = (next_version or 0) + 1
        now = datetime.now(UTC)
        session.add(
            RevisionModel(
                target_id=resource_id,
                version=version,
                justification=(
                    f"Validation {result.statut.value}" f" — {len(result.causes_blocage)} cause(s)"
                ),
                valid_time_start=now,
                transaction_time=now,
            )
        )
        await session.flush()

        session.add(
            ValidationResultModel(
                id=result.validation_id,
                requete_origine=resource_id,
                statut=result.statut.value,
                type_sortie=request.type_sortie.value,
                controles=[c.model_dump(mode="json") for c in result.controles],
                causes_blocage=[c.model_dump(mode="json") for c in result.causes_blocage],
                date_validation=result.date_validation,
            )
        )
        await session.flush()

    # --- Contrôles individuels ---

    def _controle_niveau_preuve(self, request: ValidationRequest) -> ControleResultat:
        """Vérifie la présence d'un niveau de preuve (GSIE-CON-002)."""
        contenu = request.contenu
        if "evidence_level" in contenu or any(
            "evidence_level" in r for r in contenu.get("recommandations", []) if isinstance(r, dict)
        ):
            return ControleResultat(
                nom_controle="presence_niveau_preuve",
                resultat=ResultatControle.conforme,
                details="Niveau de preuve présent sur la sortie.",
            )
        return ControleResultat(
            nom_controle="presence_niveau_preuve",
            resultat=ResultatControle.non_conforme,
            details="Aucun niveau de preuve trouvé — violation GSIE-CON-002.",
        )

    def _controle_source(self, request: ValidationRequest) -> ControleResultat:
        """Vérifie la présence d'au moins une source (GSIE-CON-002)."""
        contenu = request.contenu
        sources = self._collecter_sources(contenu)
        if sources:
            return ControleResultat(
                nom_controle="presence_source",
                resultat=ResultatControle.conforme,
                details=f"{len(sources)} source(s) identifiée(s).",
            )
        return ControleResultat(
            nom_controle="presence_source",
            resultat=ResultatControle.non_conforme,
            details="Aucune source identifiable — violation GSIE-CON-002.",
        )

    def _controle_chaine_inference(self, request: ValidationRequest) -> ControleResultat:
        """Vérifie la présence d'une chaîne d'inférence (GSIE-CON-004).

        Non applicable pour une recommandation seule (le contrat §5
        rend `chaines_inference` optionnel pour ce type).
        """
        if request.type_sortie == TypeSortie.recommandation:
            return ControleResultat(
                nom_controle="presence_chaine_inference",
                resultat=ResultatControle.non_applicable,
                details="Chaîne d'inférence non requise pour une recommandation seule.",
            )
        if request.chaines_inference:
            return ControleResultat(
                nom_controle="presence_chaine_inference",
                resultat=ResultatControle.conforme,
                details=f"{len(request.chaines_inference)} chaîne(s) d'inférence fournie(s).",
            )
        return ControleResultat(
            nom_controle="presence_chaine_inference",
            resultat=ResultatControle.non_conforme,
            details="Aucune chaîne d'inférence — violation GSIE-CON-004.",
        )

    def _controle_contournable(self, request: ValidationRequest) -> ControleResultat:
        """Vérifie que toute recommandation est contournable (GSIE-CON-001)."""
        if request.type_sortie == TypeSortie.diagnostic:
            return ControleResultat(
                nom_controle="recommandation_contournable",
                resultat=ResultatControle.non_applicable,
                details="Contrôle non applicable à un diagnostic seul.",
            )
        recommandations = request.contenu.get("recommandations", [])
        if not isinstance(recommandations, list):
            return ControleResultat(
                nom_controle="recommandation_contournable",
                resultat=ResultatControle.non_conforme,
                details="Champ 'recommandations' invalide — pas une liste.",
            )
        non_contournables = [
            r for r in recommandations if isinstance(r, dict) and r.get("contournable") is False
        ]
        if non_contournables:
            return ControleResultat(
                nom_controle="recommandation_contournable",
                resultat=ResultatControle.non_conforme,
                details=(
                    f"{len(non_contournables)} recommandation(s) non contournable(s) "
                    "— violation GSIE-CON-001."
                ),
            )
        return ControleResultat(
            nom_controle="recommandation_contournable",
            resultat=ResultatControle.conforme,
            details=f"{len(recommandations)} recommandation(s) toutes contournables.",
        )

    def _controle_explicabilite(self, request: ValidationRequest) -> ControleResultat:
        """Vérifie la présence d'une justification lisible (GSIE-CON-004)."""
        contenu = request.contenu
        has_justification = (
            "justification" in contenu
            or "justifications" in contenu
            or any(
                isinstance(r, dict) and "justification" in r
                for r in contenu.get("recommandations", [])
            )
        )
        if has_justification:
            return ControleResultat(
                nom_controle="explicabilite",
                resultat=ResultatControle.conforme,
                details="Justification présente et lisible.",
            )
        return ControleResultat(
            nom_controle="explicabilite",
            resultat=ResultatControle.non_conforme,
            details="Aucune justification trouvée — explicabilité insuffisante (GSIE-CON-004).",
        )

    # --- Helpers ---

    @staticmethod
    def _collecter_sources(contenu: dict[str, Any]) -> list[Any]:
        """Collecte récursivement les sources dans une structure de sortie."""
        sources: list[Any] = []
        if "source" in contenu:
            sources.append(contenu["source"])
        if "sources" in contenu and isinstance(contenu["sources"], list):
            sources.extend(contenu["sources"])
        for reco in contenu.get("recommandations", []):
            if isinstance(reco, dict):
                just = reco.get("justification", {})
                if isinstance(just, dict) and "sources" in just:
                    sources.extend(just["sources"])
        return sources

    @staticmethod
    def _cause_pour_controle(nom_controle: str) -> TypeCauseBlocage:
        """Mappe un nom de contrôle à sa cause de blocage.

        Aucun repli par défaut. La correspondance retombait sur
        `explicabilite_insuffisante` pour tout contrôle non répertorié : un
        contrôle ajouté sans son entrée aurait donc annoncé au forestier une
        cause **fausse**, plausible et vérifiable en apparence. Il aurait
        cherché un défaut d'explicabilité là où le blocage venait d'ailleurs.

        La spécification l'exclut explicitement : « Toute sortie bloquée est
        journalisée avec la cause précise de blocage »
        (`VALIDATION_ENGINE.md` §6). Une cause approchée n'est pas une cause
        précise.

        `KeyError` plutôt qu'un statut : un contrôle sans cause est une erreur
        de programmation, pas une sortie non conforme. `validate` ne lève jamais
        pour une sortie non conforme — cette garantie-là est intacte.
        """
        mapping = {
            "presence_niveau_preuve": TypeCauseBlocage.sans_niveau_preuve,
            "presence_source": TypeCauseBlocage.sans_source,
            "presence_chaine_inference": TypeCauseBlocage.sans_chaine_inference,
            "recommandation_contournable": TypeCauseBlocage.recommandation_non_contournable,
            "explicabilite": TypeCauseBlocage.explicabilite_insuffisante,
        }
        if nom_controle not in mapping:
            raise ValidationEngineError(
                f"contrôle « {nom_controle} » sans cause de blocage déclarée : "
                "la cause rapportée serait fausse"
            )
        return mapping[nom_controle]

    # Controles dont l'echec bloque, sans degradation possible en
    # `partiellement_valide`.
    #
    # `recommandation_contournable` a ete ajoute. L'ensemble ne retenait que
    # `presence_source` et `presence_niveau_preuve` en citant `GSIE-CON-002` —
    # en laissant donc de cote `GSIE-CON-001`, l'article **fondateur** : « l'IA
    # assiste, ne decide jamais ». Une recommandation qui se declare non
    # contournable retire au forestier la seule chose que cet article lui
    # garantit. La faire parvenir a l'utilisateur en `partiellement_valide`
    # revient a laisser passer la violation de l'article que la validation
    # existe pour faire respecter — elle est le dernier rempart.
    #
    # Enforcer un article derive tout en tolerant la violation de l'article
    # fondateur etait une incoherence, pas une exclusion pesee.
    _CONTROLES_CRITIQUES: frozenset[str] = frozenset(
        {
            "presence_source",
            "presence_niveau_preuve",
            "recommandation_contournable",
        }
    )

    @classmethod
    def _tous_non_critiques(cls, non_conformes: list[ControleResultat]) -> bool:
        """Détermine si tous les contrôles non conformes sont non critiques.

        Un contrôle critique bloque l'ensemble ; un contrôle non critique
        autorise `partiellement_valide`.
        """
        return all(c.nom_controle not in cls._CONTROLES_CRITIQUES for c in non_conformes)
