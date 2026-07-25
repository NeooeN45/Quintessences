"""Diagnostic Engine — assemblage et refus, jamais jugement.

Responsabilité (`DIAGNOSTIC_ENGINE.md` §1) :
- Synthétiser les conclusions du Reasoning Engine et les qualifications
  déclarées en un `Diagnostic` cohérent : contraintes, atouts, risques,
  contradictions, incertitudes.
- Ne jamais juger : le rôle d'une conclusion (contrainte, atout, risque),
  son domaine et l'état global sont DÉCLARÉS par l'appelant. Les déduire du
  texte français d'un énoncé serait de l'invention (`GSIE-CON-002`).
- Ne jamais trancher une contradiction (`SCIENTIFIC_CONSTITUTION` S-3) :
  les contradictions sont présentées au forestier, jamais arbitrées.
- Ne produire ni recommandation ni prescription (garantie §6,
  `GSIE-CON-001`).

Déterminisme : à requête et horloge identiques, deux exécutions produisent
un `Diagnostic` identique. `date_diagnostic` est une entrée du moteur et non
une lecture d'horloge interne — sans quoi le moteur ne serait pas testable.
Les qualifications sont traitées dans un ordre total explicite (tri par
`conclusion_id`). Aucun parcours de `set` dans un chemin qui produit de la
sortie. L'identifiant stable est dérivé du contenu par `uuid5` (namespace
fixe), jamais par `uuid4`.

Sur `confiance` : le moteur n'invente aucune table de conversion. Il
sélectionne le minimum des `niveau_confiance` des conclusions — une valeur
qui existe déjà, pas un nombre nouveau (`ADR-007`). Un diagnostic n'est pas
plus assuré que sa conclusion la moins assurée.
"""

from datetime import datetime
from uuid import UUID, uuid5

from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.logging import get_logger
from gsie_api.engines.diagnostic.schemas import (
    ContradictionDeclaree,
    ContradictionDomaines,
    Diagnostic,
    DiagnosticRequest,
    DomaineElement,
    DomaineRisque,
    ElementDiagnostic,
    QualificationConclusion,
    RisqueDiagnostic,
    RoleDiagnostic,
    domaine_commun,
)
from gsie_api.engines.reasoning.schemas import Conclusion, StationContexte, niveau_plancher

logger = get_logger("gsie_api.diagnostic.engine")

# Namespace fixe pour la dérivation déterministe d'identifiants par uuid5.
# Distinct du namespace du Reasoning Engine : un diagnostic_id ne doit pas
# pouvoir collisionner avec un conclusion_id, même si les contenus dérivés
# se chevauchent.
_NAMESPACE_DETERMINISME = UUID("00000000-0000-4000-8000-000000000011")

# Blocs de StationContexte examinés pour les incertitudes factuelles.
# Ordre figé pour le déterminisme de la sortie.
_BLOCS_CONTEXTE: tuple[tuple[str, str], ...] = (
    ("geographie", "géographique"),
    ("climat", "climatique"),
    ("pedologie", "pédologique"),
    ("botanique", "botanique"),
    ("peuplement", "de peuplement"),
)


class DiagnosticEngineError(Exception):
    """Erreur de base du Diagnostic Engine.

    Levée lorsqu'une conclusion est malformée, qu'une contradiction est
    inconstructible (domaines identiques ou non comparables), ou qu'aucun
    élément n'a pu être produit. Jamais levée pour un contexte partiel —
    c'est une incertitude, pas une panne (`CODE_QUALITY_STANDARD` §3.5).
    """


class DiagnosticEngine:
    """Moteur d'assemblage de diagnostics stationnels.

    Une instance est créée par requête HTTP avec la session DB de la
    requête (même schéma que `ReasoningEngine`). En v1, aucune persistance
    n'est effectuée — le moteur est pur et sans effet de bord sur la base.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def version() -> str:
        """Version du moteur."""
        return "0.1.0"

    async def diagnostiquer(
        self,
        request: DiagnosticRequest,
        date_diagnostic: datetime,
    ) -> Diagnostic:
        """Produit un diagnostic en assemblant les conclusions qualifiées.

        Args:
            request: La requête contenant les conclusions, leurs
                qualifications (rôle + domaine), l'état global déclaré et
                les contradictions déclarées.
            date_diagnostic: Horloge passée par l'appelant — jamais lue
                en interne. Garantit le déterminisme et la testabilité.

        Returns:
            Un `Diagnostic` à l'état `brouillon` — un moteur ne produit
            jamais de diagnostic validé (`GSIE-CON-001`).

        Raises:
            DiagnosticEngineError: Si une chaîne d'inférence est vide,
                si une contradiction est inconstructible (domaines
                identiques ou non comparables entre un risque et une
                contrainte), ou si zéro élément a été produit.
        """
        # 1. Indexer les conclusions par conclusion_id.
        # La bijection conclusions/qualifications est garantie par le
        # validateur de DiagnosticRequest : on lui fait confiance.
        conclusions_par_id: dict[UUID, Conclusion] = {
            conclusion.conclusion_id: conclusion for conclusion in request.conclusions
        }

        # 2. Traiter les qualifications dans l'ordre trié par conclusion_id.
        qualifications_triees = sorted(request.qualifications, key=lambda q: q.conclusion_id)

        contraintes: list[ElementDiagnostic] = []
        atouts: list[ElementDiagnostic] = []
        risques: list[RisqueDiagnostic] = []

        for qualification in qualifications_triees:
            conclusion = conclusions_par_id[qualification.conclusion_id]
            element = _construire_element(conclusion, qualification)
            if isinstance(element, RisqueDiagnostic):
                risques.append(element)
            elif isinstance(element, ElementDiagnostic):
                if qualification.role is RoleDiagnostic.contrainte:
                    contraintes.append(element)
                else:
                    atouts.append(element)

        # Condition d'erreur : zéro élément produit.
        if not contraintes and not atouts and not risques:
            raise DiagnosticEngineError(
                "aucun élément produit : le diagnostic ne peut pas être vide "
                "(ni contrainte, ni atout, ni risque)"
            )

        # 3. Plancher du diagnostic : niveau_plancher sur TOUS les éléments.
        niveaux = [e.evidence_level for e in contraintes]
        niveaux += [a.evidence_level for a in atouts]
        niveaux += [r.evidence_level for r in risques]
        plancher_diagnostic = niveau_plancher(niveaux)

        # 4. Confiance : minimum des niveau_confiance des conclusions.
        # Sélection d'une valeur existante, pas fabrication d'un nombre
        # nouveau (ADR-007). Un diagnostic n'est pas plus assuré que sa
        # conclusion la moins assurée.
        confiance = min(c.niveau_confiance for c in request.conclusions)

        # 5. Traduire les ContradictionDeclaree en ContradictionDomaines.
        contradictions = _traduire_contradictions(request.contradictions, request.qualifications)

        # 6. Incertitudes : un constat factuel par bloc de contexte absent.
        incertitudes = _incertitudes_contexte(request.contexte)

        # 7. diagnostic_id : uuid5 dérivé de requete_id et conclusions_source triés.
        conclusions_source_triees = sorted(c.conclusion_id for c in request.conclusions)
        # Séparateur explicite plutôt que la représentation Python d'une liste :
        # `repr()` est un détail d'implémentation de CPython, et le faire entrer
        # dans la dérivation d'un identifiant persistant reviendrait à faire
        # dépendre la citabilité d'un diagnostic d'un choix de la bibliothèque
        # standard. Une évolution de `UUID.__repr__` changerait silencieusement
        # tous les identifiants déjà émis.
        cle_derivation = "|".join(
            [str(request.requete_id), *(str(c) for c in conclusions_source_triees)]
        )
        diagnostic_id = uuid5(_NAMESPACE_DETERMINISME, cle_derivation)

        # 9. Construire le Diagnostic. statut_validation reste à brouillon
        # (valeur par défaut) — un moteur ne produit pas de diagnostic
        # validé (GSIE-CON-001). Ne pas le renseigner explicitement.
        return Diagnostic(
            diagnostic_id=diagnostic_id,
            requete_origine=request.requete_id,
            station_id=request.station_id,
            type_diagnostic=request.type_diagnostic,
            etat_global=request.etat_global.etat,
            contraintes=contraintes,
            atouts=atouts,
            risques=risques,
            contradictions=contradictions,
            confiance=confiance,
            evidence_level_plancher=plancher_diagnostic,
            incertitudes=incertitudes,
            conclusions_source=conclusions_source_triees,
            date_diagnostic=date_diagnostic,
        )


# --- Fonctions pures (testables isolément, sans session) --------------------


def _construire_element(
    conclusion: Conclusion, qualification: QualificationConclusion
) -> ElementDiagnostic | RisqueDiagnostic:
    """Construit un ElementDiagnostic ou RisqueDiagnostic selon le rôle.

    La source est celle de la DERNIÈRE étape de la chaîne d'inférence :
    l'affirmation portée par l'élément est celle produite par la règle
    terminale. Prendre une autre source attribuerait l'assertion à un
    travail qui ne l'a pas produite.

    Le niveau de preuve est `conclusion.evidence_level_plancher` : un
    élément ne peut pas être mieux établi que le plus faible maillon qui
    le soutient. Jamais l'evidence_level de la dernière étape seule.

    La description est `conclusion.enonce`, repris tel quel et jamais
    reformulé — reformuler serait interpréter, et interpréter est interdit.
    """
    # Vérification défensive : une chaîne vide ne devrait pas arriver (le
    # contrat Reasoning l'interdit via min_length=1), mais ne pas supposer.
    if not conclusion.chaine_inference:
        raise DiagnosticEngineError(
            f"chaîne d'inférence vide sur la conclusion {conclusion.conclusion_id} "
            f"— le contrat Reasoning l'interdit, mais elle est arrivée"
        )

    source = conclusion.chaine_inference[-1].source_regle
    evidence = conclusion.evidence_level_plancher
    description = conclusion.enonce

    if qualification.role is RoleDiagnostic.risque:
        # domaine_risque, probabilite et horizon sont garantis non-None par
        # le validateur _champs_coherents_avec_le_role. Les assertions de
        # typage ci-dessous le confirment à mypy.
        assert qualification.domaine_risque is not None  # noqa: S101
        assert qualification.probabilite is not None  # noqa: S101
        assert qualification.horizon is not None  # noqa: S101
        return RisqueDiagnostic(
            description=description,
            probabilite=qualification.probabilite,
            horizon=qualification.horizon,
            domaine=qualification.domaine_risque,
            evidence_level=evidence,
            source=source,
        )

    # Pour contrainte et atout : domaine_element est garanti non-None.
    assert qualification.domaine_element is not None  # noqa: S101
    return ElementDiagnostic(
        description=description,
        domaine=qualification.domaine_element,
        evidence_level=evidence,
        source=source,
    )


def _domaine_qualification(
    qualification: QualificationConclusion,
) -> DomaineElement | DomaineRisque:
    """Retourne le domaine d'une qualification, quel que soit son type.

    Pour une contrainte ou un atout : `domaine_element` (DomaineElement).
    Pour un risque : `domaine_risque` (DomaineRisque).

    Les deux types sont distincts (§5) mais projetables sur l'échelle
    commune `Domaine` via `domaine_commun()` — c'est cette projection qui
    permet à une contradiction d'opposer un atout et un risque.
    """
    if qualification.role is RoleDiagnostic.risque:
        assert qualification.domaine_risque is not None  # noqa: S101
        return qualification.domaine_risque
    assert qualification.domaine_element is not None  # noqa: S101
    return qualification.domaine_element


def _traduire_contradictions(
    contradictions_declarees: list[ContradictionDeclaree],
    qualifications: list[QualificationConclusion],
) -> list[ContradictionDomaines]:
    """Traduit les contradictions déclarées en ContradictionDomaines.

    Pour chaque contradiction, on retrouve les domaines des deux conclusions
    via leurs qualifications, on les projette sur l'échelle commune `Domaine`
    via `domaine_commun()`, et on construit `ContradictionDomaines`. Les
    trois cas — élément/élément, risque/risque, mixte — suivent un seul
    chemin : la projection est totale.

    Une contradiction intra-domaine (deux conclusions projetant sur le même
    `Domaine`) est légitime : c'est le cas normal des conflits
    bibliographiques au sein d'une même discipline (SCIENTIFIC_CONSTITUTION
    S-3). `domaine_a` et `domaine_b` peuvent donc être égaux.

    Les contradictions sont triées par (conclusion_a, conclusion_b) pour le
    déterminisme de la sortie.
    """
    qualifications_par_id: dict[UUID, QualificationConclusion] = {
        q.conclusion_id: q for q in qualifications
    }

    resultats: list[ContradictionDomaines] = []
    for contradiction in sorted(
        contradictions_declarees,
        key=lambda c: (c.conclusion_a, c.conclusion_b),
    ):
        qualif_a = qualifications_par_id[contradiction.conclusion_a]
        qualif_b = qualifications_par_id[contradiction.conclusion_b]
        resultats.append(
            ContradictionDomaines(
                description=contradiction.description,
                domaine_a=domaine_commun(_domaine_qualification(qualif_a)),
                domaine_b=domaine_commun(_domaine_qualification(qualif_b)),
            )
        )

    return resultats


def _incertitudes_contexte(contexte: StationContexte) -> list[str]:
    """Constate factuellement les blocs de contexte absents.

    Pour chaque bloc absent (geographie, climat, pedologie, botanique,
    peuplement), formule : « aucune donnée <bloc> pour cette station ».
    C'est factuel et vérifiable, donc autorisé — ce n'est pas une
    incertitude « métier » inventée.

    Aucune autre incertitude n'est produite. La liste est triée par ordre
    des blocs dans `_BLOCS_CONTEXTE` (déjà ordonné), donc déterministe.
    """
    incertitudes: list[str] = []
    for nom_champ, libelle in _BLOCS_CONTEXTE:
        bloc = getattr(contexte, nom_champ)
        if bloc is None:
            incertitudes.append(f"aucune donnée {libelle} pour cette station")
    return incertitudes
