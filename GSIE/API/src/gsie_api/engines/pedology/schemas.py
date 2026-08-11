"""Schémas Pydantic pour le Pedology Engine.

Conforme à PEDOLOGY_ENGINE.md §5 (contrat d'interface), avec un
périmètre v1 restreint aux propriétés de sol modélisées par SoilGrids
(ISRIC, aucune clé requise) pour un point donné : pH (H2O), argile,
sable, limon (0-5cm). Pas de `ProfilSol` (horizons détaillés) ni de
`ClassificationSol` (RPF/WRB) en v1 — ces données exigent le
Référentiel Pédologique Forestier (RFC-0013, sous accord ONF/INRAE non
encore formalisé), pas une valeur approximée (ADR-009).

Niveau de preuve (EVIDENCE_FRAMEWORK.md §4.2, cas Pédologie) : SoilGrids
est un produit peer-reviewed unique (Poggio et al., 2021, SOIL
journal) — plafond **B** (établi) en l'absence de convergence
multi-sources, jamais A.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference


class PedologyQuery(BaseModel):
    """Requête de propriétés de sol pour un point (SoilGrids ISRIC)."""

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID = Field(default_factory=uuid4)
    latitude: float = Field(ge=-90.0, le=90.0, description="WGS 84")
    longitude: float = Field(ge=-180.0, le=180.0, description="WGS 84")
    profondeur: str = Field(
        default="0-5cm",
        description="Tranche de profondeur SoilGrids (ex. 0-5cm, 5-15cm, 15-30cm)",
    )


# Ce qu'une unite autorise, et rien de plus.
#
# Chaque borne est **definitionnelle** : elle dit ce que l'unite signifie, non
# ce qui serait agronomiquement plausible. Une unite absente de cette table
# n'est pas contrainte — mieux vaut ne rien verifier que verifier au hasard.
_BORNES_PAR_UNITE: dict[str, tuple[float, float]] = {
    # Une part du tout ne depasse pas le tout.
    "%": (0.0, 100.0),
    # Echelle sur laquelle SoilGrids publie le pH de l'eau du sol.
    "pH": (0.0, 14.0),
    # Une teneur massique est positive ou nulle. Pas de borne haute : elle
    # dependrait du materiau et releverait du jugement.
    "g/kg": (0.0, float("inf")),
    # Une masse volumique apparente est strictement positive ; la borne haute
    # est celle de la matiere minerale la plus dense, laissee ouverte.
    "kg/dm³": (0.0, float("inf")),
}


class SolCaracteristique(BaseModel):
    """Une caractéristique de sol (PEDOLOGY_ENGINE.md §5)."""

    model_config = ConfigDict(extra="forbid")

    nom: str = Field(description="Ex. « ph », « argile_pct », « sable_pct »")
    valeur: float
    unite: str
    source: SourceReference
    evidence_level: EvidenceLevel = EvidenceLevel.B

    @model_validator(mode="after")
    def _valeur_dans_son_unite(self) -> "SolCaracteristique":
        """La valeur reste dans ce que son unité autorise.

        Seconde ligne de défense, indépendante du client qui produit la valeur.
        `soilgrids_client.py` retombait sur un facteur d'échelle de 1 quand
        SoilGrids omettait `unit_measure` : une couche `phh2o` de moyenne 52 —
        un pH de 5,2 mis à l'échelle par dix — ressortait à **pH 52**. Ce
        contrôle-ci l'aurait arrêté quel que soit le client fautif.

        Le contrôle porte sur l'**unité**, pas sur le nom : `nom` est libre
        (« ph », « argile_pct », « pH_eau »…), tandis que l'unité dit ce que le
        nombre peut valoir. Se fier au nom obligerait à énumérer ses variantes,
        et la garde manquerait la première orthographe imprévue.

        **Bornes définitionnelles uniquement.** Un pourcentage supérieur à cent
        n'est pas une teneur remarquable, c'est une part dépassant le tout. Le
        pH 0–14 est l'échelle sur laquelle SoilGrids publie, pas un seuil
        agronomique. Aucune borne n'est posée sur ce qui relèverait d'un
        jugement — dire qu'un sol est « trop acide » exigerait une source, et
        n'appartient pas à un schéma (`ADR-009`).
        """
        bornes = _BORNES_PAR_UNITE.get(self.unite)
        if bornes is None:
            return self
        minimum, maximum = bornes
        if not minimum <= self.valeur <= maximum:
            raise ValueError(
                f"« {self.nom} » vaut {self.valeur} {self.unite}, hors de "
                f"l'intervalle {minimum}–{maximum} que cette unité autorise"
            )
        return self


class PedologyData(BaseModel):
    """Résultat d'une requête pédologique (PEDOLOGY_ENGINE.md §5).

    v1 : sans profil de sol ni classification (voir docstring module).
    """

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID
    latitude: float
    longitude: float
    profondeur: str
    caracteristiques: list[SolCaracteristique] = Field(default_factory=list, max_length=20)
    source: SourceReference
    date_donnees: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PedologyIngestResult(BaseModel):
    """Résultat d'ingestion d'une caractéristique de sol dans le Knowledge Engine.

    Une caractéristique par résultat : chaque propriété SoilGrids (pH,
    argile, sable, limon) devient une connaissance atomique distincte,
    interrogeable indépendamment (`par_concept`, `par_domaine`) plutôt
    qu'un unique objet fourre-tout par point.
    """

    model_config = ConfigDict(extra="forbid")

    nom: str = Field(description="Caractéristique concernée, ex. « ph »")
    statut: str = Field(description="ingested | quarantined | refused (EvidenceKnowledgePipeline)")
    evidence_level: EvidenceLevel
    connaissance_id: UUID
    version: int | None = Field(
        default=None, description="Version dans le graphe si ingérée (None sinon)"
    )
    raison: str | None = Field(
        default=None, description="Motif si non ingérée (quarantaine ou refus)"
    )


class PedologyIngestResponse(BaseModel):
    """Résultat de `POST /pedology/query-and-ingest` — une entrée par caractéristique."""

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID
    latitude: float
    longitude: float
    profondeur: str
    resultats: list[PedologyIngestResult] = Field(default_factory=list, max_length=20)
