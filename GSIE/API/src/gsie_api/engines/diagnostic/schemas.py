"""Schémas Pydantic pour le Diagnostic Engine.

Conforme à `DIAGNOSTIC_ENGINE.md` §5 (contrat d'interface).

Ce moteur produit la première sortie du système qu'un forestier lit
directement et sur laquelle il engage sa responsabilité. Tout ce qui
précède — calculs, corrélations, conclusions inférées — reste interne.
Un diagnostic, non.

Trois conséquences, encodées dans les types plutôt que rappelées en
commentaire.

**Le statut de validation est inséparable du contenu.** Le contrat §5 ne
prévoit aucun champ de statut : c'est une lacune, corrigée ici. Un
diagnostic naît `brouillon` et le reste tant qu'un humain nommé ne l'a pas
validé. `statut_validation` est le premier champ du modèle, obligatoire,
et systématiquement présent à la sérialisation. Le scénario qu'il ferme est
celui d'un export qui perdrait la mention « non validé » en route et
laisserait circuler un diagnostic provisoire comme s'il était établi.

**Une machine ne peut pas valider.** Passer au statut `valide` exige un
bloc `ValidationHumaine` nommant la personne et la date. Le système ne peut
pas se valider lui-même sans écrire noir sur blanc une identité humaine —
ce qui serait un mensonge traçable, non une omission silencieuse
(`GSIE-CON-001`).

**Un diagnostic n'est pas une décision.** Le modèle ne comporte
délibérément aucun champ d'action, de prescription ou de recommandation.
Cette absence est une garantie du §6, vérifiée par introspection dans les
tests : elle doit rester vraie après toute évolution du schéma.

**Sur `confiance`.** Comme pour le Reasoning Engine, ce module n'invente
aucune table de conversion entre niveau de preuve et confiance numérique :
elle serait un coefficient non sourcé, interdit par `GSIE-CON-002` et
`ADR-007`. La valeur est reprise des conclusions d'origine. Le champ
`evidence_level_plancher`, lui, est dérivé par simple ordonnancement de
l'échelle A–F.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_serializer, model_validator

from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference
from gsie_api.engines.reasoning.schemas import Conclusion, StationContexte, niveau_plancher
from gsie_api.infrastructure.models.enums import (
    DiagnosticGlobalState,
    DiagnosticType,
    DiagnosticValidationStatus,
)

# Depuis la persistance des diagnostics, ces trois énumérations sont aussi
# des types PostgreSQL et vivent dans `infrastructure.models.enums`. Elles
# sont réexportées ici sous leurs noms d'origine : une seconde définition
# finirait par diverger du type stocké, et un diagnostic relu autrement
# qu'il n'a été écrit est exactement l'erreur que ce module existe pour
# rendre impossible.
TypeDiagnostic = DiagnosticType
EtatGlobal = DiagnosticGlobalState
StatutValidation = DiagnosticValidationStatus


class DomaineElement(StrEnum):
    """Domaine scientifique d'une contrainte ou d'un atout (§5)."""

    pedologique = "pedologique"
    climatique = "climatique"
    topographique = "topographique"
    botanique = "botanique"
    sylvicole = "sylvicole"


class DomaineRisque(StrEnum):
    """Domaine d'un risque identifié (§5)."""

    climatique = "climatique"
    sanitaire = "sanitaire"
    sylvicole = "sylvicole"


class Domaine(StrEnum):
    """Domaine scientifique, tous rôles confondus.

    Union de `DomaineElement` et `DomaineRisque`. Le contrat §5 sépare les
    deux parce qu'un risque ne se rattache pas aux mêmes disciplines qu'une
    contrainte. Mais une contradiction, elle, oppose fréquemment un atout à
    un risque — « sol profond et fertile » contre « déficit hydrique
    croissant » est exactement le cas que la garantie §6 demande de mettre en
    évidence.

    Sans domaine commun, ces oppositions seraient inexprimables et donc
    invisibles. Ce type existe pour cela, et uniquement pour cela : les
    éléments et les risques conservent leurs énumérations d'origine.
    """

    pedologique = "pedologique"
    climatique = "climatique"
    topographique = "topographique"
    botanique = "botanique"
    sylvicole = "sylvicole"
    sanitaire = "sanitaire"


def domaine_commun(domaine: "DomaineElement | DomaineRisque") -> Domaine:
    """Projette un domaine d'élément ou de risque sur l'échelle commune.

    Fonction totale : toute valeur des deux énumérations a son équivalent.
    Une valeur inconnue lève plutôt que de retomber sur un défaut, faute de
    quoi une contradiction pourrait être rattachée au mauvais domaine.
    """
    try:
        return Domaine(domaine.value)
    except ValueError as exc:  # pragma: no cover — garde-fou d'évolution
        raise ValueError(
            f"domaine « {domaine.value} » sans équivalent commun : "
            f"l'énumération Domaine doit être étendue"
        ) from exc


class Probabilite(StrEnum):
    """Probabilité qualitative d'un risque (§5).

    Volontairement qualitative : une probabilité chiffrée exigerait un
    modèle sourcé que le moteur ne possède pas. Afficher un pourcentage
    non fondé donnerait une fausse précision, ce que `GSIE-CON-002`
    interdit.
    """

    faible = "faible"
    modere = "modere"
    eleve = "eleve"
    tres_eleve = "tres_eleve"


class ValidationHumaine(BaseModel):
    """Trace d'une relecture humaine (`GSIE-CON-001`, `GSIE-CON-005`).

    Sans identité ni date, une validation n'est pas auditable : on ne peut
    ni la contester, ni savoir ce qui a été relu.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    validateur: str = Field(
        min_length=1,
        max_length=255,
        description="Identité de la personne ayant relu, jamais un système",
    )
    date_validation: datetime = Field(description="Horodatage de la relecture, fuseau obligatoire")
    commentaire: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _date_avec_fuseau(self) -> "ValidationHumaine":
        """Une validation datée sans fuseau n'est pas auditable.

        Un diagnostic peut être relu à Chizé et contesté ailleurs, des
        années plus tard. « Validé le 3 mars à 14 h » sans fuseau ne permet
        pas d'établir l'antériorité d'une relecture sur un événement de
        terrain. `GSIE-CON-005` exige une traçabilité, pas une indication.
        """
        if self.date_validation.tzinfo is None:
            raise ValueError(
                "date_validation sans fuseau horaire : un horodatage ambigu "
                "ne constitue pas une trace de validation"
            )
        return self


class ElementDiagnostic(BaseModel):
    """Une contrainte ou un atout de la station (§5).

    `ADR-007` : inconstructible sans source ni niveau de preuve.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    description: str = Field(min_length=1, max_length=500)
    domaine: DomaineElement
    evidence_level: EvidenceLevel
    source: SourceReference


class RisqueDiagnostic(BaseModel):
    """Un risque identifié, avec sa probabilité qualitative et son horizon (§5)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    description: str = Field(min_length=1, max_length=500)
    probabilite: Probabilite
    horizon: str = Field(
        min_length=1,
        max_length=100,
        description="Horizon temporel du risque, ex. « 5 ans », « une révolution »",
    )
    domaine: DomaineRisque
    evidence_level: EvidenceLevel
    source: SourceReference


class ContradictionDomaines(BaseModel):
    """Deux affirmations qui s'opposent (§6).

    Exemples : sol favorable contre climat défavorable — deux domaines ; mais
    aussi « climat favorable à l'essence » contre « risque de sécheresse
    croissante », deux affirmations climatiques qui se contredisent bel et
    bien.

    Les domaines peuvent donc être identiques. Exiger qu'ils diffèrent, comme
    le faisait une version antérieure de ce modèle, rendait inexprimables les
    contradictions intra-domaine — précisément les plus fréquentes, puisque
    deux sources d'une même discipline se contredisent plus souvent que deux
    disciplines éloignées.

    L'identité qui compte est celle des conclusions, et elle est vérifiée en
    amont par `ContradictionDeclaree`. Comme pour le Reasoning Engine, aucun
    champ de résolution n'existe : une contradiction est présentée au
    forestier, jamais arbitrée par la machine
    (`SCIENTIFIC_CONSTITUTION.md` S-3).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    description: str = Field(min_length=1, max_length=1000)
    domaine_a: Domaine
    domaine_b: Domaine = Field(
        description=(
            "Peut être identique à `domaine_a` : une contradiction "
            "intra-domaine reste une contradiction."
        )
    )


class RoleDiagnostic(StrEnum):
    """Rôle d'une conclusion dans le diagnostic.

    Déclaré par l'appelant, jamais déduit. Décider qu'une conclusion est une
    contrainte plutôt qu'un atout est un jugement scientifique ; l'inférer du
    texte français de son énoncé serait de l'invention (`GSIE-CON-002`).
    """

    contrainte = "contrainte"
    atout = "atout"
    risque = "risque"


class QualificationConclusion(BaseModel):
    """Rôle et domaine attribués à une conclusion (extension v1).

    Le contrat §5 suppose que le moteur sait classer une conclusion. Il ne le
    sait pas et ne doit pas le deviner. Tant que le Knowledge Engine ne
    fournit pas de règles de qualification, l'appelant les déclare — sur le
    précédent assumé du Correlation Engine et du Reasoning Engine.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    conclusion_id: UUID
    role: RoleDiagnostic
    domaine_element: DomaineElement | None = Field(
        default=None, description="Obligatoire pour une contrainte ou un atout"
    )
    domaine_risque: DomaineRisque | None = Field(
        default=None, description="Obligatoire pour un risque"
    )
    probabilite: Probabilite | None = Field(default=None, description="Obligatoire pour un risque")
    horizon: str | None = Field(
        default=None, max_length=100, description="Obligatoire pour un risque"
    )

    @model_validator(mode="after")
    def _champs_coherents_avec_le_role(self) -> "QualificationConclusion":
        """Un risque sans probabilité ni horizon n'est pas un risque.

        Et une contrainte porteuse d'une probabilité laisserait croire à une
        prévision là où il n'y a qu'un constat.
        """
        if self.role is RoleDiagnostic.risque:
            manquants = [
                nom
                for nom, valeur in (
                    ("domaine_risque", self.domaine_risque),
                    ("probabilite", self.probabilite),
                    ("horizon", self.horizon),
                )
                if valeur is None
            ]
            if manquants:
                raise ValueError(f"risque incomplet, champs obligatoires manquants : {manquants}")
            if self.domaine_element is not None:
                raise ValueError("un risque ne porte pas de domaine_element")
            return self
        if self.domaine_element is None:
            raise ValueError(f"un rôle « {self.role} » exige un domaine_element")
        if any((self.domaine_risque, self.probabilite, self.horizon)):
            raise ValueError(
                f"un rôle « {self.role} » ne porte ni probabilité, ni horizon, "
                f"ni domaine_risque"
            )
        return self


class EtatGlobalDeclare(BaseModel):
    """État global déclaré par l'appelant, avec sa justification.

    Déduire « dépérissement » d'un ensemble de contraintes exigerait une
    fonction de score que le moteur ne possède pas et ne peut pas inventer.
    L'état est donc déclaré et sourcé comme n'importe quelle affirmation.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    etat: EtatGlobal
    justification: str = Field(min_length=1, max_length=1000)
    source: SourceReference
    evidence_level: EvidenceLevel


class ContradictionDeclaree(BaseModel):
    """Deux conclusions déclarées incompatibles par l'appelant.

    Le moteur ne compare aucun énoncé pour deviner une opposition. Une
    contradiction est déclarée ou n'existe pas — même règle que le Reasoning
    Engine.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    conclusion_a: UUID
    conclusion_b: UUID
    description: str = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def _conclusions_distinctes(self) -> "ContradictionDeclaree":
        if self.conclusion_a == self.conclusion_b:
            raise ValueError("une conclusion ne peut pas se contredire elle-même")
        return self


class DiagnosticRequest(BaseModel):
    """Entrée du Diagnostic Engine (`DIAGNOSTIC_ENGINE.md` §5)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    requete_id: UUID
    station_id: UUID
    peuplement_id: UUID | None = None
    conclusions: list[Conclusion] = Field(
        min_length=1,
        description=(
            "Conclusions du Reasoning Engine. Au moins une est exigée : "
            "un diagnostic sans conclusion n'a rien à synthétiser, et en "
            "produire un reviendrait à conclure sans prémisse."
        ),
    )
    qualifications: list[QualificationConclusion] = Field(
        min_length=1,
        description=(
            "Une qualification par conclusion, ni plus ni moins. Le moteur "
            "refuse une conclusion non qualifiée plutôt que de l'écarter en "
            "silence : une conclusion oubliée est une preuve perdue."
        ),
    )
    etat_global: EtatGlobalDeclare
    contradictions: list[ContradictionDeclaree] = Field(default_factory=list)
    contexte: StationContexte
    type_diagnostic: TypeDiagnostic

    @model_validator(mode="after")
    def _qualifications_bijectives(self) -> "DiagnosticRequest":
        """Exactement une qualification par conclusion, et réciproquement."""
        ids_conclusions = [conclusion.conclusion_id for conclusion in self.conclusions]
        ids_qualifiees = [qualif.conclusion_id for qualif in self.qualifications]
        if len(set(ids_qualifiees)) != len(ids_qualifiees):
            raise ValueError("deux qualifications visent la même conclusion")
        manquantes = set(ids_conclusions) - set(ids_qualifiees)
        if manquantes:
            raise ValueError(f"conclusions non qualifiées : {sorted(manquantes)}")
        orphelines = set(ids_qualifiees) - set(ids_conclusions)
        if orphelines:
            raise ValueError(
                f"qualifications sans conclusion correspondante : {sorted(orphelines)}"
            )
        return self

    @model_validator(mode="after")
    def _contradictions_referencent_des_conclusions(self) -> "DiagnosticRequest":
        connues = {conclusion.conclusion_id for conclusion in self.conclusions}
        for contradiction in self.contradictions:
            inconnues = {contradiction.conclusion_a, contradiction.conclusion_b} - connues
            if inconnues:
                raise ValueError(
                    f"contradiction visant des conclusions absentes : {sorted(inconnues)}"
                )
        return self


class Diagnostic(BaseModel):
    """Sortie du Diagnostic Engine (`DIAGNOSTIC_ENGINE.md` §5, §6).

    Première sortie du système destinée à un lecteur humain. Le statut de
    validation ouvre le modèle et accompagne toute sérialisation.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    statut_validation: StatutValidation = Field(
        default=StatutValidation.brouillon,
        description=(
            "Toujours `brouillon` à la production. Un moteur ne peut pas "
            "produire un diagnostic validé (`GSIE-CON-001`)."
        ),
    )
    validation: ValidationHumaine | None = Field(
        default=None,
        description="Obligatoire dès que le statut n'est plus `brouillon`",
    )
    diagnostic_id: UUID
    requete_origine: UUID
    station_id: UUID
    type_diagnostic: TypeDiagnostic
    etat_global: EtatGlobal
    contraintes: list[ElementDiagnostic] = Field(default_factory=list)
    atouts: list[ElementDiagnostic] = Field(default_factory=list)
    risques: list[RisqueDiagnostic] = Field(default_factory=list)
    contradictions: list[ContradictionDomaines] = Field(default_factory=list)
    confiance: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Bornes du contrat §5. Reprise des conclusions d'origine, jamais "
            "calculée par une table inventée — voir la docstring du module."
        ),
    )
    evidence_level_plancher: EvidenceLevel = Field(
        description="Plus faible niveau de preuve parmi les éléments et risques"
    )
    incertitudes: list[str] = Field(
        default_factory=list,
        description="Ce que le diagnostic ne sait pas, formulé pour le lecteur",
    )
    conclusions_source: list[UUID] = Field(min_length=1)
    date_diagnostic: datetime

    @model_validator(mode="after")
    def _validation_coherente(self) -> "Diagnostic":
        """Un statut autre que `brouillon` exige une trace humaine nommée.

        C'est la barrière qui empêche une machine de se déclarer validée :
        elle devrait inscrire une identité humaine, acte traçable et
        contestable, là où une simple omission passerait inaperçue.
        """
        if self.statut_validation is StatutValidation.brouillon:
            if self.validation is not None:
                raise ValueError("un diagnostic brouillon ne peut pas porter de validation humaine")
            return self
        if self.validation is None:
            raise ValueError(
                f"statut « {self.statut_validation} » sans trace de validation "
                f"humaine : un diagnostic ne se valide pas tout seul"
            )
        return self

    @model_validator(mode="after")
    def _contenu_non_vide(self) -> "Diagnostic":
        """Un diagnostic sans contrainte, atout ni risque ne dit rien.

        Produire un objet vide donnerait l'apparence d'une analyse là où il
        n'y en a pas. Mieux vaut ne pas produire de diagnostic du tout.
        """
        if not (self.contraintes or self.atouts or self.risques):
            raise ValueError("diagnostic vide : aucune contrainte, aucun atout, aucun risque")
        return self

    @model_validator(mode="after")
    def _plancher_coherent(self) -> "Diagnostic":
        """Le plancher déclaré est le plus faible maillon réellement présent."""
        niveaux = [element.evidence_level for element in self.contraintes]
        niveaux += [element.evidence_level for element in self.atouts]
        niveaux += [risque.evidence_level for risque in self.risques]
        attendu = niveau_plancher(niveaux)
        if self.evidence_level_plancher != attendu:
            raise ValueError(
                f"plancher incohérent : déclaré {self.evidence_level_plancher}, "
                f"calculé {attendu} depuis les éléments"
            )
        return self

    @model_validator(mode="after")
    def _sources_conclusions_uniques(self) -> "Diagnostic":
        if len(self.conclusions_source) != len(set(self.conclusions_source)):
            raise ValueError("conclusions_source contient un doublon")
        return self

    @model_serializer(mode="wrap")
    def _toujours_avec_statut(self, gestionnaire: Any) -> dict[str, Any]:
        """Garantit que le statut accompagne toute sérialisation.

        Un export qui perdrait la mention « brouillon » laisserait circuler
        un diagnostic provisoire comme s'il était établi — le scénario que
        ce modèle existe pour empêcher. La garantie est donc portée par le
        sérialiseur, pas seulement par la présence du champ.
        """
        donnees: dict[str, Any] = gestionnaire(self)
        donnees["statut_validation"] = self.statut_validation.value
        return donnees

    def mention_statut(self) -> str:
        """Mention lisible à apposer sur toute présentation humaine.

        Destinée aux exports et aux vues du Hub : un rendu qui n'appelle pas
        cette méthode doit être considéré comme incomplet.
        """
        if self.statut_validation is StatutValidation.brouillon:
            return "DIAGNOSTIC NON VALIDÉ — analyse produite par le système, non relue"
        if self.statut_validation is StatutValidation.refuse:
            return "DIAGNOSTIC REFUSÉ à la relecture — conservé pour mémoire"
        valideur = self.validation.validateur if self.validation else "inconnu"
        return f"Diagnostic validé par {valideur}"
