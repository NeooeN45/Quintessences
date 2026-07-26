"""Schémas du Recommendation Engine (`RECOMMENDATION_ENGINE.md` §5).

Le moteur propose des actions sylvicoles à partir d'un diagnostic. C'est le
dernier maillon de la chaîne avant l'humain, et le seul dont la sortie sera
lue comme une instruction. Un propriétaire abattra des arbres sur la foi de
ce qui s'affiche ici.

Les garanties du §6 sont donc encodées dans les types, pas rappelées en
commentaire (`CODE_QUALITY_STANDARD` §3.2) :

- `contournable` n'est pas un booléen que l'appelant renseigne : c'est une
  propriété calculée, toujours vraie. `GSIE-CON-001` n'est pas une valeur
  par défaut qu'un appelant distrait pourrait renverser.
- Une recommandation sans justification, sans source ou sans facteur
  limitant ne peut pas être construite : `JustificationRecommandation`
  exige ses champs, et une recommandation sans justification est un
  conseil sans fondement (`GSIE-CON-004`).
- Aucun champ ne permet d'étiqueter une recommandation comme « décision ».
  Le vocabulaire de la décision appartient à `ForestierDecision`, produit
  par l'humain.

Une garantie du §6 n'est **pas** encodée ici : « plusieurs alternatives sont
systématiquement proposées ». Elle dépend de `alternatives_demandees`, porté
par la requête, qu'un `RecommendationSet` ne connaît pas. La vérifier au
niveau du schéma exigerait de dupliquer le champ dans la sortie pour se
contrôler soi-même. Elle relève donc du moteur (tranche R2), et ce module ne
prétend pas l'assurer.

Ce module ne contient aucun seuil, densité, essence ni période codés en
dur : ces valeurs proviennent du diagnostic et des connaissances qualifiées
(`GSIE-CON-002`, `ADR-009`).
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from gsie_api.engines.evidence.schemas import SourceReference


class ObjectifForestier(StrEnum):
    """Objectif poursuivi par le forestier (`RECOMMENDATION_ENGINE.md` §5)."""

    PRODUCTION = "production"
    PROTECTION = "protection"
    BIODIVERSITE = "biodiversite"
    MIXTE = "mixte"
    REBOISEMENT = "reboisement"


class TypeAction(StrEnum):
    """Nature de l'action sylvicole proposée (`RECOMMENDATION_ENGINE.md` §5).

    `ATTENTE_SURVEILLANCE` est une recommandation à part entière : lorsque
    les connaissances disponibles ne permettent pas de proposer une
    intervention, ne rien faire et observer est un conseil honnête, pas une
    absence de réponse.
    """

    PLANTATION = "plantation"
    ECLAIRCIE = "eclaircie"
    COUPE_RASE = "coupe_rase"
    REGENERATION = "regeneration"
    PROTECTION = "protection"
    INTERVENTION_SANITAIRE = "intervention_sanitaire"
    ATTENTE_SURVEILLANCE = "attente_surveillance"


class DecisionForestier(StrEnum):
    """Suite donnée par le forestier à une recommandation (`§5`).

    Le vocabulaire de la décision n'existe que dans cette énumération :
    GSIE recommande, le forestier décide (`GSIE-CON-001`).
    """

    ACCEPTE = "accepte"
    REFUSE = "refuse"
    MODIFIE = "modifie"
    DEMANDE_ALTERNATIVE = "demande_alternative"


class JustificationRecommandation(BaseModel):
    """Fondement d'une recommandation — jamais optionnel (`GSIE-CON-004`).

    `facteurs_limitants` est obligatoire et non vide. Une recommandation
    présentée sans limite connue se lit comme une certitude ; or il en
    existe toujours au moins une, ne serait-ce que le périmètre du
    diagnostic dont elle provient. La déclarer force à l'expliciter plutôt
    qu'à la taire.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    diagnostic_ref: UUID
    connaissances_utilisees: list[UUID] = Field(default_factory=list)
    regles_appliquees: list[str] = Field(default_factory=list)
    sources: list[SourceReference] = Field(
        min_length=1,
        description=(
            "Au moins une source. Une recommandation sylvicole non sourcée "
            "n'existe pas (GSIE-CON-002)."
        ),
    )
    facteurs_limitants: list[str] = Field(
        min_length=1,
        description=(
            "Au moins un facteur limitant. Une recommandation sans limite "
            "affichée se lit comme une certitude (§6)."
        ),
    )
    moteurs_solicites: list[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    """Une action sylvicole proposée, justifiée et contournable (`§5`).

    Les alternatives sont des `Recommendation` de rang inférieur. Elles ne
    peuvent pas elles-mêmes porter d'alternatives : une arborescence de
    profondeur libre produirait un objet impossible à présenter à un
    forestier et à auditer.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    recommandation_id: UUID
    type_action: TypeAction
    description: str = Field(min_length=1, max_length=2000)
    essence_concernee: str | None = Field(default=None, max_length=200)
    parametres: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Paramètres opérationnels (densité, période, surface). Sérialisés "
            "en texte : leur valeur provient du diagnostic ou d'une "
            "connaissance qualifiée, jamais d'un calcul interne au moteur."
        ),
    )
    justification: JustificationRecommandation
    alternatives: list["Recommendation"] = Field(default_factory=list)
    niveau_confiance: float = Field(ge=0.0, le=1.0)
    scenario_projection: UUID | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def contournable(self) -> bool:
        """Toujours vrai — `GSIE-CON-001`, garanti par construction.

        Exposé en propriété calculée plutôt qu'en champ : un booléen
        renseignable pourrait être mis à `false`, ce qui transformerait une
        recommandation en instruction. Le contrat §5 exige que ce champ
        figure dans la sortie ; il figure, sans pouvoir être renversé.
        """
        return True

    @model_validator(mode="after")
    def _alternatives_sans_profondeur(self) -> "Recommendation":
        """Une alternative ne porte pas d'alternatives (profondeur maximale 1)."""
        for alternative in self.alternatives:
            if alternative.alternatives:
                raise ValueError("une alternative ne peut pas porter ses propres alternatives")
        return self

    @model_validator(mode="after")
    def _alternatives_distinctes(self) -> "Recommendation":
        """Une alternative ne peut être ni la recommandation elle-même, ni un doublon."""
        identifiants = [alternative.recommandation_id for alternative in self.alternatives]
        if self.recommandation_id in identifiants:
            raise ValueError("une recommandation ne peut pas être sa propre alternative")
        if len(set(identifiants)) != len(identifiants):
            raise ValueError("deux alternatives portent le même identifiant")
        return self


class RecommendationRequest(BaseModel):
    """Entrée du Recommendation Engine (`RECOMMENDATION_ENGINE.md` §5)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    requete_id: UUID
    diagnostic_id: UUID
    objectif_forestier: ObjectifForestier
    contraintes_forestier: list[str] = Field(
        default_factory=list,
        description="Préférences exprimées par le forestier, reprises telles quelles.",
    )
    alternatives_demandees: bool = True


class RecommendationSet(BaseModel):
    """Sortie du Recommendation Engine (`RECOMMENDATION_ENGINE.md` §5).

    Un ensemble vide est refusé : si aucune action n'est fondée, le moteur
    produit une recommandation `attente_surveillance` justifiée. Rendre un
    ensemble vide laisserait l'appelant interpréter le silence.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    ensemble_id: UUID
    requete_origine: UUID
    diagnostic_source: UUID
    recommandations: list[Recommendation] = Field(
        min_length=1,
        description=(
            "Au moins une recommandation. L'absence d'action fondée se dit "
            "par `attente_surveillance`, jamais par un ensemble vide."
        ),
    )
    date_generation: datetime

    @model_validator(mode="after")
    def _identifiants_uniques(self) -> "RecommendationSet":
        """Deux recommandations du même ensemble ne partagent pas d'identifiant."""
        identifiants = [reco.recommandation_id for reco in self.recommandations]
        if len(set(identifiants)) != len(identifiants):
            raise ValueError("deux recommandations portent le même identifiant")
        return self

    @model_validator(mode="after")
    def _justifications_du_meme_diagnostic(self) -> "RecommendationSet":
        """Toute justification référence le diagnostic déclaré comme source.

        Une recommandation justifiée par un autre diagnostic que celui de
        l'ensemble serait intraçable : le lecteur croirait remonter à une
        origine qui n'est pas la sienne.
        """
        for reco in self.recommandations:
            for candidate in [reco, *reco.alternatives]:
                if candidate.justification.diagnostic_ref != self.diagnostic_source:
                    raise ValueError(
                        "une justification référence un diagnostic autre que " "`diagnostic_source`"
                    )
        return self


class ForestierDecision(BaseModel):
    """Suite donnée par le forestier — trace d'apprentissage (`GSIE-CON-005`).

    Un refus ou une modification sans justification reste accepté : exiger
    une explication du forestier reviendrait à lui demander de se justifier
    devant l'outil. C'est lui qui décide (`GSIE-CON-001`).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    recommandation_id: UUID
    decision: DecisionForestier
    justification_forestier: str | None = Field(default=None, max_length=2000)
    modifications: dict[str, str] = Field(default_factory=dict)
    date_decision: datetime

    @model_validator(mode="after")
    def _modification_documentee(self) -> "ForestierDecision":
        """Une décision `modifie` sans modification déclarée est ininterprétable.

        Le moteur ne peut ni deviner ce qui a changé, ni l'ignorer : la trace
        servirait alors à documenter un écart dont le contenu est perdu
        (`GSIE-CON-005`).
        """
        if self.decision is DecisionForestier.MODIFIE and not self.modifications:
            raise ValueError("une décision `modifie` doit déclarer au moins une modification")
        if self.decision is not DecisionForestier.MODIFIE and self.modifications:
            raise ValueError("des modifications sont déclarées sans décision `modifie`")
        return self
