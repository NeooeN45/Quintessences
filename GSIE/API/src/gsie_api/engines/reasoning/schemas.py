"""Schémas Pydantic pour le Reasoning Engine.

Conforme à `REASONING_ENGINE.md` §5 (contrat d'interface).

Principe directeur de ce module : les garanties du §6 ne sont pas des
commentaires, ce sont des invariants de type. Une structure qui violerait
une garantie ne doit pas pouvoir être construite.

- *Aucun raisonnement sans chaîne documentée* → `chaine_inference` non vide,
  rangs contigus depuis 1.
- *Le moteur n'invente aucune règle* (`GSIE-CON-002`) → `source_regle`
  obligatoire sur chaque étape ; `niveau_confiance` fourni par la règle et
  jamais calculé ici.
- *Toute conclusion est explicable* (`GSIE-CON-004`) → prémisses non vides,
  sources déclarées et fermées sur la chaîne.
- *Les contradictions sont signalées, jamais résolues* →
  `ContradictionDetectee` ne porte aucun champ de résolution.

**Réduction de périmètre v1, assumée et documentée.** Le contrat §5 prévoit
que `StationContexte` soit alimenté par sept moteurs domaine. Quatre d'entre
eux existent (GIS, Climate, Pedology, Botanical, Forest Dynamics) et deux
n'ont pas encore d'API de contexte stationnel. En v1, le contexte est donc
fourni dans la requête, chaque bloc conservant sa provenance déclarée — le
branchement direct sur les moteurs se fera sans rupture de contrat.

**Sur le déterminisme.** L'exigence exacte est : à contexte, règles et horloge
identiques, la sortie est identique. `date_inference` est donc une **entrée du
moteur**, injectée par l'appelant, et non une lecture d'horloge interne :
autrement le moteur ne serait pas testable. `resultat_id` est dérivé du contenu
par `uuid5`, jamais tiré au hasard — deux inférences identiques portent le même
identifiant, ce qui est une propriété utile et non un défaut.

**Sur `niveau_confiance`.** Le contrat impose un décimal entre 0,0 et 1,0.
Ce module ne contient aucune table de conversion entre niveau de preuve et
confiance numérique : une telle table serait un coefficient inventé, interdit
par `GSIE-CON-002` et par `ADR-007`. La valeur est donc **fournie par la règle
d'inférence issue du Knowledge Engine**, avec sa propre source. Le moteur
expose en complément `evidence_level_plancher`, dérivé par simple ordonnancement
de l'échelle A–F déjà définie par l'Evidence Engine.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference

# Ordonnancement de l'échelle de preuve, du plus fort au plus faible.
# Source : `SCIENTIFIC_CONSTITUTION.md` article S-2 et
# `gsie_api.engines.evidence.schemas.EvidenceLevel` (« A=meilleur, F=pire »).
# Aucune valeur numérique n'est introduite ici : seul l'ordre est utilisé.
_ORDRE_NIVEAUX: tuple[EvidenceLevel, ...] = (
    EvidenceLevel.A,
    EvidenceLevel.B,
    EvidenceLevel.C,
    EvidenceLevel.D,
    EvidenceLevel.E,
    EvidenceLevel.F,
)


def niveau_plancher(niveaux: list[EvidenceLevel]) -> EvidenceLevel:
    """Retourne le niveau de preuve le plus faible d'un ensemble.

    Une conclusion ne peut pas être mieux établie que le plus faible des
    maillons qui la soutiennent. Fonction pure et totale sur l'échelle A–F.
    """
    if not niveaux:
        raise ValueError("aucun niveau de preuve fourni")
    return max(niveaux, key=_ORDRE_NIVEAUX.index)


class MethodeConfiance(StrEnum):
    """Origine de `niveau_confiance` — jamais une invention du moteur."""

    fournie_par_regle = "fournie_par_regle"
    """La règle d'inférence du Knowledge Engine porte sa propre confiance."""

    heritee_premisse = "heritee_premisse"
    """Confiance reprise telle quelle d'une conclusion antérieure."""


class SourceMoteurContexte(StrEnum):
    """Moteur domaine ayant fourni un bloc de `StationContexte` (§2)."""

    gis = "GIS"
    climate = "CLIMATE"
    pedology = "PEDOLOGY"
    botanical = "BOTANICAL"
    forest_dynamics = "FOREST_DYNAMICS"
    correlation = "CORRELATION"
    terrain = "TERRAIN"


class BlocContexte(BaseModel):
    """Un bloc de contexte stationnel, avec sa provenance obligatoire.

    `ADR-007` : aucune valeur ne circule sans provenance résolvable. Le bloc
    est donc inconstructible sans `source_moteur`, `source` et
    `evidence_level`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_moteur: SourceMoteurContexte
    source: SourceReference
    evidence_level: EvidenceLevel
    valeurs: dict[str, float | int | str | bool] = Field(
        min_length=1,
        description="Variables observées du bloc, unités portées par la clé",
    )
    date_observation: datetime | None = Field(
        default=None, description="Horodatage de l'observation lorsqu'il existe"
    )


class StationContexte(BaseModel):
    """Contexte stationnel complet (`REASONING_ENGINE.md` §5).

    Chaque bloc est optionnel — une station peut être partiellement
    caractérisée — mais au moins un bloc est exigé : on ne raisonne pas
    sur le vide.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    geographie: BlocContexte | None = None
    climat: BlocContexte | None = None
    pedologie: BlocContexte | None = None
    botanique: BlocContexte | None = None
    peuplement: BlocContexte | None = None
    correlations: list[BlocContexte] = Field(default_factory=list)

    @model_validator(mode="after")
    def _au_moins_un_bloc(self) -> "StationContexte":
        blocs = [
            self.geographie,
            self.climat,
            self.pedologie,
            self.botanique,
            self.peuplement,
        ]
        if not any(blocs) and not self.correlations:
            raise ValueError("StationContexte vide : au moins un bloc de contexte est requis")
        return self

    def blocs_presents(self) -> list[BlocContexte]:
        """Tous les blocs renseignés, ordre stable pour le déterminisme."""
        ordonnes = [
            self.geographie,
            self.climat,
            self.pedologie,
            self.botanique,
            self.peuplement,
        ]
        return [bloc for bloc in ordonnes if bloc is not None] + list(self.correlations)


class RegleInference(BaseModel):
    """Une règle d'inférence fournie par l'appelant (extension v1).

    Le contrat §5 prévoit que les règles proviennent du Knowledge Engine.
    Tant que ce branchement n'existe pas, elles sont portées par la requête,
    exactement comme le Correlation Engine porte ses valeurs numériques.

    Ce type vit dans le module de contrat, et non dans le moteur, parce que
    `ReasoningRequest` en dépend : une requête qui ne transporterait pas ses
    règles serait ininterprétable par l'API.

    La condition est une expression restreinte portant sur les variables du
    `StationContexte` aplati. Elle est évaluée par un parcours d'arbre à liste
    blanche, jamais par `eval`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    identifiant: str = Field(
        min_length=1,
        max_length=200,
        description="Identifiant unique, support du tri déterministe des règles",
    )
    condition: str = Field(
        min_length=1,
        max_length=1000,
        description=(
            "Expression restreinte sur les variables du StationContexte. "
            "Opérateurs autorisés : ==, !=, <, <=, >, >=, and, or, not."
        ),
    )
    enonce_conclusion: str = Field(min_length=1, max_length=500)
    source: SourceReference = Field(
        description="Source scientifique de la règle (`GSIE-CON-002`, `ADR-007`)"
    )
    evidence_level: EvidenceLevel
    niveau_confiance: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Confiance portée par la règle. Bornes du contrat §5. Jamais "
            "calculée par le moteur — voir la docstring du module."
        ),
    )
    contredit_regle_id: str | None = Field(
        default=None,
        max_length=200,
        description=(
            "Règle explicitement contredite. Une contradiction est déclarée "
            "par les règles ou n'existe pas : le moteur n'en devine aucune."
        ),
    )


class ReasoningRequest(BaseModel):
    """Entrée du Reasoning Engine (`REASONING_ENGINE.md` §5)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    requete_id: UUID
    station_id: UUID | None = None
    contexte: StationContexte
    regles: list[RegleInference] = Field(
        default_factory=list,
        description=(
            "Règles applicables (extension v1). Une liste vide est légitime : "
            "elle produit un résultat sans conclusion, ce qui est honnête."
        ),
    )
    question: str = Field(min_length=1, max_length=500)
    profondeur_max: int = Field(
        ge=1,
        le=32,
        description=(
            "Profondeur maximale de la chaîne d'inférence. Bornée pour garantir "
            "la terminaison : une inférence non bornée ne peut pas être auditée."
        ),
    )


class EtapeInference(BaseModel):
    """Un pas de raisonnement, intégralement justifié (`§5`).

    Une étape sans prémisse n'est pas une déduction, c'est une affirmation.
    Une étape sans source de règle est une règle inventée.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    ordre: int = Field(ge=1)
    regle_appliquee: str = Field(min_length=1, max_length=500)
    source_regle: SourceReference
    regle_id: UUID | None = Field(
        default=None,
        description="KnowledgeObject portant la règle, lorsqu'elle en provient",
    )
    premisses: list[str] = Field(min_length=1)
    conclusion_locale: str = Field(min_length=1, max_length=500)
    evidence_level: EvidenceLevel = Field(
        description="Niveau de preuve de la règle appliquée à cette étape"
    )


class Conclusion(BaseModel):
    """Une conclusion inférée, explicable de bout en bout (`§5`, `§6`)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    conclusion_id: UUID
    enonce: str = Field(min_length=1, max_length=500)
    niveau_confiance: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Bornes issues du contrat §5. Valeur fournie par la règle, jamais "
            "calculée par le moteur — voir la docstring du module."
        ),
    )
    methode_confiance: MethodeConfiance
    evidence_level_plancher: EvidenceLevel = Field(
        description="Plus faible niveau de preuve de la chaîne, dérivé par ordre"
    )
    chaine_inference: list[EtapeInference] = Field(min_length=1)
    sources_utilisees: list[SourceReference] = Field(min_length=1)
    connaissances_utilisees: list[UUID] = Field(default_factory=list)
    moteurs_solicites: list[SourceMoteurContexte] = Field(default_factory=list)

    @model_validator(mode="after")
    def _chaine_contigue(self) -> "Conclusion":
        """La chaîne doit être 1..N sans trou ni doublon.

        Une chaîne trouée n'est pas une explication : elle laisse un pas
        non justifié entre deux affirmations.
        """
        ordres = [etape.ordre for etape in self.chaine_inference]
        attendu = list(range(1, len(ordres) + 1))
        if ordres != attendu:
            raise ValueError(f"chaîne d'inférence non contiguë : {ordres} au lieu de {attendu}")
        return self

    @model_validator(mode="after")
    def _sources_fermees(self) -> "Conclusion":
        """Toute source citée par une étape est déclarée, et réciproquement.

        Interdit deux dérives symétriques : une étape s'appuyant sur une
        source non déclarée, et une conclusion déclarant une source qui ne
        sert à rien — laquelle donnerait l'illusion d'un appui inexistant.
        """
        etapes = {_cle_source(etape.source_regle) for etape in self.chaine_inference}
        declarees = {_cle_source(source) for source in self.sources_utilisees}
        if orphelines := etapes - declarees:
            raise ValueError(
                f"sources citées par la chaîne mais non déclarées : {sorted(orphelines)}"
            )
        if inutilisees := declarees - etapes:
            raise ValueError(
                f"sources déclarées mais non utilisées par la chaîne : {sorted(inutilisees)}"
            )
        return self

    @model_validator(mode="after")
    def _plancher_coherent(self) -> "Conclusion":
        """Le plancher déclaré est bien le plus faible maillon de la chaîne."""
        attendu = niveau_plancher([etape.evidence_level for etape in self.chaine_inference])
        if self.evidence_level_plancher != attendu:
            raise ValueError(
                f"plancher incohérent : déclaré {self.evidence_level_plancher}, "
                f"calculé {attendu} depuis la chaîne"
            )
        return self


class ContradictionDetectee(BaseModel):
    """Deux conclusions incompatibles (`§5`, `§6`).

    Aucun champ de résolution n'existe, et c'est délibéré. `GSIE-CON-002` et
    `SCIENTIFIC_CONSTITUTION.md` S-3 interdisent de trancher un conflit
    automatiquement : il est présenté, jamais arbitré par la machine.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    conclusion_a: UUID
    conclusion_b: UUID
    description: str = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def _conclusions_distinctes(self) -> "ContradictionDetectee":
        if self.conclusion_a == self.conclusion_b:
            raise ValueError("une conclusion ne peut pas se contredire elle-même")
        return self


class InferenceResult(BaseModel):
    """Sortie du Reasoning Engine (`REASONING_ENGINE.md` §5).

    Peut ne contenir aucune conclusion : lorsqu'aucune règle applicable
    n'existe, l'absence de résultat est un résultat honnête. `GSIE-CON-002`
    interdit de combler le vide par une estimation non fondée.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    resultat_id: UUID
    requete_origine: UUID
    conclusions: list[Conclusion] = Field(default_factory=list)
    contradictions: list[ContradictionDetectee] = Field(default_factory=list)
    date_inference: datetime
    resultat_partiel: bool = Field(
        default=False,
        description=(
            "Vrai lorsque `profondeur_max` a été atteinte alors que des règles "
            "restaient applicables. Une troncation silencieuse violerait "
            "`GSIE-CON-004`, qui impose que les limites soient visibles."
        ),
    )
    regles_non_appliquees: list[str] = Field(
        default_factory=list,
        description=(
            "Identifiants des règles encore applicables à l'arrêt. Vide lorsque "
            "l'inférence est allée à son terme. Trié pour le déterminisme."
        ),
    )

    @model_validator(mode="after")
    def _partiel_coherent(self) -> "InferenceResult":
        """Un résultat partiel doit dire lesquelles des règles restaient.

        Annoncer une troncation sans nommer ce qui a été tronqué informe
        l'utilisateur qu'il lui manque quelque chose, sans lui dire quoi.
        """
        if self.resultat_partiel and not self.regles_non_appliquees:
            raise ValueError("résultat déclaré partiel sans indiquer les règles non appliquées")
        if self.regles_non_appliquees and not self.resultat_partiel:
            raise ValueError("règles non appliquées listées alors que le résultat se dit complet")
        if self.regles_non_appliquees != sorted(self.regles_non_appliquees):
            raise ValueError("regles_non_appliquees doit être trié (déterminisme)")
        return self

    @model_validator(mode="after")
    def _contradictions_referencent_des_conclusions(self) -> "InferenceResult":
        """Une contradiction ne peut désigner que des conclusions présentes."""
        connues = {conclusion.conclusion_id for conclusion in self.conclusions}
        for contradiction in self.contradictions:
            inconnues = {contradiction.conclusion_a, contradiction.conclusion_b} - connues
            if inconnues:
                raise ValueError(
                    f"contradiction référençant des conclusions absentes : {sorted(inconnues)}"
                )
        return self

    @model_validator(mode="after")
    def _conclusions_uniques(self) -> "InferenceResult":
        identifiants = [conclusion.conclusion_id for conclusion in self.conclusions]
        if len(identifiants) != len(set(identifiants)):
            raise ValueError("deux conclusions portent le même identifiant")
        return self


def _cle_source(source: SourceReference) -> str:
    """Clé d'identité d'une source, stable et lisible dans les erreurs."""
    return f"{source.type_source}|{source.auteur}|{source.reference}"
