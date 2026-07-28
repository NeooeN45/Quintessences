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

logger = get_logger("gsie_api.validation.engine")


class ValidationEngineError(Exception):
    """Erreur de base du Validation Engine."""


class ValidationEngine:
    """Moteur de validation — pas de persistance en v1.

    Le moteur est stateless : chaque validation est indépendante et
    tracée par l'appelant (journal d'audit). Une future version
    pourra persister les résultats bloqués pour alimentation du
    Learning Engine (§3 — sorties vers LEARNING_ENGINE).
    """

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

        return ValidationResult(
            validation_id=uuid4(),
            requete_origine=request.requete_id,
            statut=statut,
            controles=controles,
            causes_blocage=causes_blocage if statut != ValidationStatut.valide else [],
            date_validation=datetime.now(UTC),
        )

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
        """Mappe un nom de contrôle à sa cause de blocage."""
        mapping = {
            "presence_niveau_preuve": TypeCauseBlocage.sans_niveau_preuve,
            "presence_source": TypeCauseBlocage.sans_source,
            "presence_chaine_inference": TypeCauseBlocage.sans_chaine_inference,
            "recommandation_contournable": TypeCauseBlocage.recommandation_non_contournable,
            "explicabilite": TypeCauseBlocage.explicabilite_insuffisante,
        }
        return mapping.get(nom_controle, TypeCauseBlocage.explicabilite_insuffisante)

    @staticmethod
    def _tous_non_critiques(non_conformes: list[ControleResultat]) -> bool:
        """Détermine si tous les contrôles non conformes sont non critiques.

        Un contrôle critique bloque l'ensemble ; un contrôle non critique
        autorise `partiellement_valide`. En v1, `presence_source` et
        `presence_niveau_preuve` sont critiques (GSIE-CON-002).
        """
        critiques = {"presence_source", "presence_niveau_preuve"}
        return all(c.nom_controle not in critiques for c in non_conformes)
