"""Tests unitaires — invariants de `diagnostic/schemas.py`.

Le Diagnostic Engine produit la première sortie du système qu'un forestier
lit directement et sur laquelle il engage sa responsabilité. Les garanties
du §6 de `DIAGNOSTIC_ENGINE.md` sont encodées dans le typage Pydantic. Ce
module démontre que chaque invariant rejette ce qu'il doit rejeter — et
accepte ce qui est légitime. Un invariant trop strict est un bug au même
titre qu'un invariant absent.

Couvre : `Diagnostic` (statut de validation, contenu non vide, plancher
cohérent, sources uniques, sérialisation invariante, absence de champs
d'action), `DiagnosticRequest`, `ElementDiagnostic`, `RisqueDiagnostic`,
`ContradictionDomaines`, `Probabilite`, `mention_statut`.

Références constitutionnelles : GSIE-CON-001 (le forestier décide),
GSIE-CON-002 (sourçage), GSIE-CON-004 (limites visibles),
SCIENTIFIC_CONSTITUTION S-3 (contradictions présentées, jamais arbitrées).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from gsie_api.engines.diagnostic.schemas import (
    ContradictionDomaines,
    Diagnostic,
    DiagnosticRequest,
    Domaine,
    DomaineElement,
    DomaineRisque,
    ElementDiagnostic,
    EtatGlobal,
    EtatGlobalDeclare,
    Probabilite,
    QualificationConclusion,
    RisqueDiagnostic,
    RoleDiagnostic,
    StatutValidation,
    TypeDiagnostic,
    ValidationHumaine,
    domaine_commun,
)
from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference, SourceType
from gsie_api.engines.reasoning.schemas import (
    BlocContexte,
    Conclusion,
    EtapeInference,
    MethodeConfiance,
    SourceMoteurContexte,
    StationContexte,
    niveau_plancher,
)

# ---------------------------------------------------------------------------
# Fabriques — objets valides réutilisables, paramétrables par argument.
# ---------------------------------------------------------------------------


def _source(
    *,
    auteur: str = "Rameau et al.",
    reference: str = "doi:10.0000/test",
    type_source: SourceType = SourceType.peer_reviewed,
) -> SourceReference:
    """Construit une `SourceReference` valide par défaut."""
    return SourceReference(
        type_source=type_source,
        auteur=auteur,
        reference=reference,
    )


def _etape(
    *,
    ordre: int = 1,
    evidence_level: EvidenceLevel = EvidenceLevel.B,
    source: SourceReference | None = None,
) -> EtapeInference:
    """Construit une `EtapeInference` valide par défaut."""
    return EtapeInference(
        ordre=ordre,
        regle_appliquee="Règle de test",
        source_regle=source or _source(),
        premisses=["fait observé"],
        conclusion_locale="conclusion locale",
        evidence_level=evidence_level,
    )


def _conclusion(
    *,
    conclusion_id: UUID | None = None,
    evidence_level: EvidenceLevel = EvidenceLevel.B,
    niveau_confiance: float = 0.8,
) -> Conclusion:
    """Construit une `Conclusion` valide minimale (pour `DiagnosticRequest`)."""
    etape = _etape(evidence_level=evidence_level)
    return Conclusion(
        conclusion_id=conclusion_id or uuid4(),
        enonce="Conclusion de test",
        niveau_confiance=niveau_confiance,
        methode_confiance=MethodeConfiance.fournie_par_regle,
        evidence_level_plancher=evidence_level,
        chaine_inference=[etape],
        sources_utilisees=[etape.source_regle],
    )


def _bloc_contexte(
    *,
    source_moteur: SourceMoteurContexte = SourceMoteurContexte.pedology,
    evidence_level: EvidenceLevel = EvidenceLevel.B,
) -> BlocContexte:
    """Construit un `BlocContexte` valide par défaut."""
    return BlocContexte(
        source_moteur=source_moteur,
        source=_source(),
        evidence_level=evidence_level,
        valeurs={"pH": 5.2},
    )


def _station_contexte() -> StationContexte:
    """Construit un `StationContexte` valide (un bloc pédologique)."""
    return StationContexte(pedologie=_bloc_contexte())


def _element(
    *,
    description: str = "Sol acide, pH 5,2",
    domaine: DomaineElement = DomaineElement.pedologique,
    evidence_level: EvidenceLevel = EvidenceLevel.B,
    source: SourceReference | None = None,
) -> ElementDiagnostic:
    """Construit un `ElementDiagnostic` valide par défaut."""
    return ElementDiagnostic(
        description=description,
        domaine=domaine,
        evidence_level=evidence_level,
        source=source or _source(),
    )


def _risque(
    *,
    description: str = "Risque de dépérissement lié au déficit hydrique",
    probabilite: Probabilite = Probabilite.eleve,
    horizon: str = "10 ans",
    domaine: DomaineRisque = DomaineRisque.climatique,
    evidence_level: EvidenceLevel = EvidenceLevel.B,
    source: SourceReference | None = None,
) -> RisqueDiagnostic:
    """Construit un `RisqueDiagnostic` valide par défaut."""
    return RisqueDiagnostic(
        description=description,
        probabilite=probabilite,
        horizon=horizon,
        domaine=domaine,
        evidence_level=evidence_level,
        source=source or _source(),
    )


def _validation_humaine(
    *,
    validateur: str = "Dr. Camille Dubois",
    date_validation: datetime = datetime(2026, 7, 25, 12, 0, 0, tzinfo=UTC),
) -> ValidationHumaine:
    """Construit une `ValidationHumaine` valide par défaut."""
    return ValidationHumaine(
        validateur=validateur,
        date_validation=date_validation,
    )


def _diagnostic(
    *,
    statut_validation: StatutValidation = StatutValidation.brouillon,
    validation: ValidationHumaine | None = None,
    contraintes: list[ElementDiagnostic] | None = None,
    atouts: list[ElementDiagnostic] | None = None,
    risques: list[RisqueDiagnostic] | None = None,
    evidence_level_plancher: EvidenceLevel | None = None,
    conclusions_source: list[UUID] | None = None,
    confiance: float = 0.75,
    etat_global: EtatGlobal = EtatGlobal.sain,
    type_diagnostic: TypeDiagnostic = TypeDiagnostic.stationnel,
) -> Diagnostic:
    """Construit un `Diagnostic` valide par défaut.

    Le `evidence_level_plancher` est dérivé correctement via `niveau_plancher`
    à partir des éléments réellement présents — sauf si l'appelant le fournit
    explicitement (pour les tests qui visent à falsifier la cohérence).
    """
    contraintes = contraintes if contraintes is not None else []
    atouts = atouts if atouts is not None else [_element()]
    risques = risques if risques is not None else []
    conclusions_source = conclusions_source if conclusions_source is not None else [uuid4()]

    if evidence_level_plancher is None:
        niveaux = [e.evidence_level for e in contraintes]
        niveaux += [a.evidence_level for a in atouts]
        niveaux += [r.evidence_level for r in risques]
        # Si la liste est vide (test de contenu vide), on passe un plancher
        # explicite pour éviter que niveau_plancher lève avant Pydantic.
        # Le validateur _contenu_non_vide rejettera de toute façon.
        evidence_level_plancher = niveau_plancher(niveaux) if niveaux else EvidenceLevel.F

    return Diagnostic(
        diagnostic_id=uuid4(),
        requete_origine=uuid4(),
        station_id=uuid4(),
        type_diagnostic=type_diagnostic,
        etat_global=etat_global,
        contraintes=contraintes,
        atouts=atouts,
        risques=risques,
        confiance=confiance,
        evidence_level_plancher=evidence_level_plancher,
        conclusions_source=conclusions_source,
        date_diagnostic=datetime(2026, 7, 25, 12, 0, 0, tzinfo=UTC),
        statut_validation=statut_validation,
        validation=validation,
    )


def _qualification(
    *,
    conclusion_id: UUID | None = None,
    role: RoleDiagnostic = RoleDiagnostic.contrainte,
    domaine_element: DomaineElement | None = DomaineElement.pedologique,
    domaine_risque: DomaineRisque | None = None,
    probabilite: Probabilite | None = None,
    horizon: str | None = None,
) -> QualificationConclusion:
    """Construit une `QualificationConclusion` valide par défaut (contrainte)."""
    if role is RoleDiagnostic.risque:
        return QualificationConclusion(
            conclusion_id=conclusion_id or uuid4(),
            role=role,
            domaine_element=None,
            domaine_risque=domaine_risque or DomaineRisque.climatique,
            probabilite=probabilite or Probabilite.eleve,
            horizon=horizon or "10 ans",
        )
    return QualificationConclusion(
        conclusion_id=conclusion_id or uuid4(),
        role=role,
        domaine_element=domaine_element,
        domaine_risque=None,
        probabilite=None,
        horizon=None,
    )


def _etat_global() -> EtatGlobalDeclare:
    """Construit un `EtatGlobalDeclare` valide par défaut."""
    return EtatGlobalDeclare(
        etat=EtatGlobal.vigueur_reduite,
        justification="Vigueur réduite constatée sur le peuplement",
        source=_source(),
        evidence_level=EvidenceLevel.B,
    )


def _diagnostic_request(
    *,
    conclusions: list[Conclusion] | None = None,
    qualifications: list[QualificationConclusion] | None = None,
    etat_global: EtatGlobalDeclare | None = None,
    contexte: StationContexte | None = None,
) -> DiagnosticRequest:
    """Construit une `DiagnosticRequest` valide par défaut.

    Si `qualifications` n'est pas fourni, en génère une par conclusion
    (bijection exigée par le validateur). Si `conclusions` n'est pas
    fourni, en génère une seule avec sa qualification correspondante.
    """
    if conclusions is None:
        conclusions = [_conclusion()]

    if qualifications is None:
        qualifications = [_qualification(conclusion_id=c.conclusion_id) for c in conclusions]

    return DiagnosticRequest(
        requete_id=uuid4(),
        station_id=uuid4(),
        conclusions=conclusions,
        qualifications=qualifications,
        etat_global=etat_global or _etat_global(),
        contexte=contexte or _station_contexte(),
        type_diagnostic=TypeDiagnostic.stationnel,
    )


# ---------------------------------------------------------------------------
# Diagnostic._validation_coherente — le cœur du module
# ---------------------------------------------------------------------------


class TestValidationCoherente:
    """Le statut de validation et la trace humaine sont indissociables."""

    def test_brouillon_sans_validation_accepte(self) -> None:
        """Un diagnostic brouillon sans validation humaine est légitime.

        Rend impossible : un moteur qui produit un brouillon se voit refuser
        la construction parce qu'il n'a pas de validateur — ce serait exiger
        une validation pour produire un non-validé.
        """
        diagnostic = _diagnostic(statut_validation=StatutValidation.brouillon)
        assert diagnostic.statut_validation is StatutValidation.brouillon
        assert diagnostic.validation is None

    def test_brouillon_avec_validation_rejete(self) -> None:
        """Un diagnostic brouillon portant une validation humaine est incohérent.

        Rend impossible : un diagnostic présenté comme non relu tout en
        portant la trace d'une relecture — un état contradictoire qui masque
        le vrai statut.
        """
        with pytest.raises(ValidationError, match="brouillon ne peut pas porter"):
            _diagnostic(
                statut_validation=StatutValidation.brouillon,
                validation=_validation_humaine(),
            )

    def test_valide_sans_validation_rejete(self) -> None:
        """Un diagnostic validé sans trace de validation est un auto-validation.

        Rend impossible : une machine qui se déclare validée sans inscrire
        d'identité humaine — le mensonge que GSIE-CON-001 interdit.
        """
        with pytest.raises(ValidationError, match="sans trace de validation"):
            _diagnostic(
                statut_validation=StatutValidation.valide,
                validation=None,
            )

    def test_valide_avec_validation_complete_accepte(self) -> None:
        """Un diagnostic validé avec une trace humaine nommée est légitime.

        Rend impossible : le rejet d'un diagnostic validé par une personne
        nommée et datée — ce serait refuser la seule voie d'acceptation
        légitime.
        """
        validation = _validation_humaine(validateur="Dr. Martin")
        diagnostic = _diagnostic(
            statut_validation=StatutValidation.valide,
            validation=validation,
        )
        assert diagnostic.statut_validation is StatutValidation.valide
        assert diagnostic.validation.validateur == "Dr. Martin"

    def test_refuse_sans_validation_rejete(self) -> None:
        """Un diagnostic refusé sans trace de relecture est incohérent.

        Rend impossible : un refus anonyme — un diagnostic marqué REFUSÉ
        sans qu'on sache qui a refusé ni quand, ce qui prive le refus de
        sa valeur d'information (AI_CONSTITUTION IA-5).
        """
        with pytest.raises(ValidationError, match="sans trace de validation"):
            _diagnostic(
                statut_validation=StatutValidation.refuse,
                validation=None,
            )

    def test_statut_par_defaut_est_brouillon(self) -> None:
        """Un diagnostic construit sans préciser le statut naît brouillon.

        Rend impossible : un diagnostic qui apparaîtrait dans le système
        sans statut explicite et serait indistinguable d'un diagnostic
        établi.
        """
        diagnostic = Diagnostic(
            diagnostic_id=uuid4(),
            requete_origine=uuid4(),
            station_id=uuid4(),
            type_diagnostic=TypeDiagnostic.stationnel,
            etat_global=EtatGlobal.sain,
            atouts=[_element()],
            confiance=0.75,
            evidence_level_plancher=EvidenceLevel.B,
            conclusions_source=[uuid4()],
            date_diagnostic=datetime(2026, 7, 25, 12, 0, 0, tzinfo=UTC),
        )
        assert diagnostic.statut_validation is StatutValidation.brouillon


# ---------------------------------------------------------------------------
# Diagnostic._contenu_non_vide
# ---------------------------------------------------------------------------


class TestContenuNonVide:
    """Un diagnostic vide donne l'apparence d'une analyse là où il n'y en a pas."""

    def test_aucun_element_rejete(self) -> None:
        """Un diagnostic sans contrainte, atout ni risque est rejeté.

        Rend impossible : la production d'un objet vide présenté comme une
        analyse — un non-résultat déguisé en résultat.
        """
        with pytest.raises(ValidationError, match="diagnostic vide"):
            _diagnostic(contraintes=[], atouts=[], risques=[])

    def test_un_seul_atout_accepte(self) -> None:
        """Un diagnostic avec un seul atout, rien d'autre, est légitime.

        Rend impossible : le rejet d'un diagnostic minimal mais honnête —
        une station peut n'avoir qu'un atout à signaler.
        """
        diagnostic = _diagnostic(contraintes=[], atouts=[_element()], risques=[])
        assert len(diagnostic.atouts) == 1
        assert len(diagnostic.contraintes) == 0
        assert len(diagnostic.risques) == 0

    def test_un_seul_risque_accepte(self) -> None:
        """Un diagnostic avec un seul risque, rien d'autre, est légitime.

        Rend impossible : le rejet d'un diagnostic signalant un seul risque —
        un risque isolé mérite d'être produit.
        """
        diagnostic = _diagnostic(contraintes=[], atouts=[], risques=[_risque()])
        assert len(diagnostic.risques) == 1
        assert len(diagnostic.atouts) == 0


# ---------------------------------------------------------------------------
# Diagnostic._plancher_coherent
# ---------------------------------------------------------------------------


class TestPlancherCoherent:
    """Le plancher déclaré est le plus faible maillon réellement présent."""

    def test_elements_b_et_d_plancher_d_accepte(self) -> None:
        """Éléments en B et D, plancher D : accepté (D est le plus faible).

        Rend impossible : le rejet d'un plancher correctement calculé —
        D est bien le plus faible parmi B et D.
        """
        diagnostic = _diagnostic(
            contraintes=[_element(evidence_level=EvidenceLevel.B)],
            atouts=[_element(evidence_level=EvidenceLevel.D)],
            risques=[],
            evidence_level_plancher=EvidenceLevel.D,
        )
        assert diagnostic.evidence_level_plancher is EvidenceLevel.D

    def test_elements_b_et_d_plancher_b_rejete(self) -> None:
        """Éléments en B et D, plancher B : rejeté (B n'est pas le plus faible).

        Rend impossible : la déclaration d'un plancher plus favorable que la
        réalité — surévaluer le niveau de preuve d'un diagnostic.
        """
        with pytest.raises(ValidationError, match="plancher incohérent"):
            _diagnostic(
                contraintes=[_element(evidence_level=EvidenceLevel.B)],
                atouts=[_element(evidence_level=EvidenceLevel.D)],
                risques=[],
                evidence_level_plancher=EvidenceLevel.B,
            )

    def test_plancher_tient_compte_des_risques(self) -> None:
        """Le plancher tient compte des risques autant que des contraintes et atouts.

        Rend impossible : un risque à faible niveau de preuve ignoré dans le
        calcul du plancher — un risque mal étayé doit abaisser le plancher
        global du diagnostic.
        """
        # Contraintes et atouts en B, un risque en D.
        # Le plancher doit être D (le risque abaisse le plancher).
        diagnostic = _diagnostic(
            contraintes=[_element(evidence_level=EvidenceLevel.B)],
            atouts=[_element(evidence_level=EvidenceLevel.B)],
            risques=[_risque(evidence_level=EvidenceLevel.D)],
        )
        assert diagnostic.evidence_level_plancher is EvidenceLevel.D

    def test_ordre_complet_a_b_c_d_e_f_verifie(self) -> None:
        """L'ordre A > B > C > D > E > F est respecté par le validateur.

        Rend impossible : un ordonnancement incorrect de l'échelle A–F qui
        laisserait passer un plancher incohérent sur l'échelle complète.
        """
        # Un élément par niveau : le plancher doit être F.
        elements = [
            _element(evidence_level=EvidenceLevel.A, description="Élément A"),
            _element(evidence_level=EvidenceLevel.B, description="Élément B"),
            _element(evidence_level=EvidenceLevel.C, description="Élément C"),
            _element(evidence_level=EvidenceLevel.D, description="Élément D"),
            _element(evidence_level=EvidenceLevel.E, description="Élément E"),
            _element(evidence_level=EvidenceLevel.F, description="Élément F"),
        ]
        diagnostic = _diagnostic(
            contraintes=elements,
            atouts=[],
            risques=[],
            evidence_level_plancher=EvidenceLevel.F,
        )
        assert diagnostic.evidence_level_plancher is EvidenceLevel.F

        # Inverse : déclarer A alors que F est présent doit échouer.
        with pytest.raises(ValidationError, match="plancher incohérent"):
            _diagnostic(
                contraintes=elements,
                atouts=[],
                risques=[],
                evidence_level_plancher=EvidenceLevel.A,
            )


# ---------------------------------------------------------------------------
# Diagnostic._sources_conclusions_uniques
# ---------------------------------------------------------------------------


class TestSourcesConclusionsUniques:
    """Les conclusions source ne doivent pas contenir de doublon."""

    def test_doublon_rejete(self) -> None:
        """conclusions_source avec un doublon : rejeté.

        Rend impossible : un diagnostic qui citerait deux fois la même
        conclusion d'origine — un gonflement artificiel de la base de preuve.
        """
        doublon = uuid4()
        with pytest.raises(ValidationError, match="doublon"):
            _diagnostic(conclusions_source=[doublon, doublon])

    def test_liste_vide_rejete(self) -> None:
        """conclusions_source vide : rejeté par min_length.

        Rend impossible : un diagnostic sans lien vers les conclusions qui
        le fondent — un diagnostic orphelin qui ne peut être contesté.
        """
        with pytest.raises(ValidationError, match="conclusions_source"):
            _diagnostic(conclusions_source=[])


# ---------------------------------------------------------------------------
# Sérialisation — la partie la plus délicate
# ---------------------------------------------------------------------------


class TestSerialisation:
    """Le statut de validation accompagne toute sérialisation."""

    def test_model_dump_contient_statut_validation(self) -> None:
        """model_dump() contient toujours la clé statut_validation.

        Rend impossible : un export dict qui perdrait le statut — le
        scénario que le model_serializer existe pour empêcher.
        """
        diagnostic = _diagnostic()
        donnees = diagnostic.model_dump()
        assert "statut_validation" in donnees
        assert donnees["statut_validation"] == StatutValidation.brouillon.value

    def test_model_dump_exclude_contient_quand_meme_statut(self) -> None:
        """model_dump(exclude={statut_validation}) le contient QUAND MÊME.

        Rend impossible : un appelant qui exclut explicitement le statut
        et obtient un export sans mention « non validé » — c'est la raison
        d'être du model_serializer en mode wrap : la garantie est portée
        par le sérialiseur, pas par la présence du champ.
        """
        diagnostic = _diagnostic()
        donnees = diagnostic.model_dump(exclude={"statut_validation"})
        assert "statut_validation" in donnees
        assert donnees["statut_validation"] == StatutValidation.brouillon.value

    def test_model_dump_json_relecture_redonne_diagnostic_equivalent(self) -> None:
        """model_dump_json() puis relecture redonne un Diagnostic équivalent.

        Rend impossible : une perte d'information au round-trip JSON —
        un diagnostic sérialisé puis relu doit être identique à l'original.
        """
        diagnostic = _diagnostic()
        json_str = diagnostic.model_dump_json()
        relu = Diagnostic.model_validate_json(json_str)
        assert relu == diagnostic

    def test_model_dump_mode_json_serialisable(self) -> None:
        """model_dump(mode="json") reste sérialisable en JSON sans erreur.

        Rend impossible : un dump en mode JSON qui produirait des types non
        sérialisables (UUID, datetime, enum) — le mode json doit tout
        convertir en primitives JSON.
        """
        diagnostic = _diagnostic()
        donnees = diagnostic.model_dump(mode="json")
        # json.dumps lève TypeError si un type n'est pas sérialisable.
        json.dumps(donnees)


# ---------------------------------------------------------------------------
# mention_statut()
# ---------------------------------------------------------------------------


class TestMentionStatut:
    """La mention lisible apposée sur toute présentation humaine."""

    def test_brouillon_contient_non_valide(self) -> None:
        """brouillon : la chaîne contient « NON VALIDÉ ».

        Rend impossible : un diagnostic brouillon présenté sans la mention
        « non validé » — le lecteur croirait à un diagnostic établi.
        """
        diagnostic = _diagnostic(statut_validation=StatutValidation.brouillon)
        mention = diagnostic.mention_statut()
        assert "NON VALIDÉ" in mention

    def test_refuse_contient_refuse(self) -> None:
        """refuse : la chaîne contient « REFUSÉ ».

        Rend impossible : un diagnostic refusé présenté sans la mention
        « refusé » — le refus serait invisible, et son intérêt (IA-5) perdu.
        """
        diagnostic = _diagnostic(
            statut_validation=StatutValidation.refuse,
            validation=_validation_humaine(),
        )
        mention = diagnostic.mention_statut()
        assert "REFUSÉ" in mention

    def test_valide_contient_nom_validateur(self) -> None:
        """valide : la chaîne contient le nom du validateur.

        Rend impossible : un diagnostic validé présenté sans nommer la
        personne qui a validé — la validation serait anonyme, donc non
        contestable.
        """
        validation = _validation_humaine(validateur="Dr. Camille Dubois")
        diagnostic = _diagnostic(
            statut_validation=StatutValidation.valide,
            validation=validation,
        )
        mention = diagnostic.mention_statut()
        assert "Dr. Camille Dubois" in mention


# ---------------------------------------------------------------------------
# Garantie §6 « un diagnostic n'est pas une décision » — introspection
# ---------------------------------------------------------------------------


class TestPasDeChampDecision:
    """Diagnostic ne comporte aucun champ d'action prescrite (garantie §6).

    Cette garantie est constitutionnelle (GSIE-CON-001), pas une convention
    de nommage. Une liste noire de noms proscrits serait toujours incomplète
    (guidance, directive, orientation, anglicismes…). On fige donc l'ensemble
    attendu : tout ajout fait échouer le test et force une décision explicite.
    La liste noire est conservée en second test pour un message d'erreur plus
    parlant — c'est la liste blanche qui garantit.
    """

    # Liste blanche : l'ensemble exact des champs attendus sur Diagnostic.
    # Tout champ nouveau doit passer par une relecture d'architecture.
    CHAMPS_ATTENDUS: frozenset[str] = frozenset(
        {
            "statut_validation",
            "validation",
            "diagnostic_id",
            "requete_origine",
            "station_id",
            "type_diagnostic",
            "etat_global",
            "contraintes",
            "atouts",
            "risques",
            "contradictions",
            "confiance",
            "evidence_level_plancher",
            "incertitudes",
            "conclusions_source",
            "date_diagnostic",
        }
    )

    # Champs dont la présence indiquerait que le moteur prescrit une action.
    # Liste non exhaustive — sert de message d'erreur explicite, pas de garde.
    CHAMPS_INTERDITS: frozenset[str] = frozenset(
        {
            "recommandation",
            "prescription",
            "action",
            "preconisation",
            "conseil",
            "intervention",
        }
    )

    def test_aucun_champ_ajoute_sans_revue(self) -> None:
        """Tout champ nouveau doit passer par une relecture d'architecture.

        Rend impossible : l'ajout silencieux d'un champ — de recommandation,
        de prescription, ou de tout autre nom auquel on n'avait pas pensé —
        au modèle Diagnostic. La garantie §6 ne peut pas reposer sur une
        liste de noms interdits : elle serait toujours incomplète. On fige
        l'ensemble attendu ; tout ajout fait échouer le test et force une
        décision explicite.
        """
        champs_present = set(Diagnostic.model_fields.keys())
        assert champs_present == self.CHAMPS_ATTENDUS, (
            f"Diagnostic comporte des champs inattendus : "
            f"ajouts={champs_present - self.CHAMPS_ATTENDUS}, "
            f"manquants={self.CHAMPS_ATTENDUS - champs_present}"
        )

    def test_aucun_champ_action_prescrite_nomme(self) -> None:
        """Aucun champ d'action prescrite par nom (message explicite).

        Rend impossible : un champ explicitement nommé « recommandation » ou
        « prescription » — le test donne un message d'erreur plus parlant que
        la liste blanche seule. Garde-fou secondaire, pas primaire.
        """
        champs_present = set(Diagnostic.model_fields.keys())
        champs_trouves = champs_present & self.CHAMPS_INTERDITS
        assert not champs_trouves, (
            f"Diagnostic comporte des champs d'action prescrite, "
            f"ce qui viole la garantie §6 et GSIE-CON-001 : {champs_trouves}"
        )


# ---------------------------------------------------------------------------
# ContradictionDomaines
# ---------------------------------------------------------------------------


class TestContradictionDomaines:
    """Deux éléments de domaines différents qui s'opposent, jamais arbitrés."""

    def test_domaines_egaux_accepte(self) -> None:
        """domaine_a == domaine_b : accepté.

        Rend impossible : l'invisibilité d'un conflit bibliographique au sein
        d'une même discipline — deux affirmations pédologiques opposées sont
        le cas normal des contradictions intra-domaine que
        SCIENTIFIC_CONSTITUTION S-3 demande de faire remonter. L'ancien
        contrat rejetait ce cas ; il est désormais légitime.
        """
        contradiction = ContradictionDomaines(
            description="Conflit bibliographique sur la fertilité du sol",
            domaine_a=Domaine.pedologique,
            domaine_b=Domaine.pedologique,
        )
        assert contradiction.domaine_a == contradiction.domaine_b
        assert contradiction.domaine_a is Domaine.pedologique

    def test_domaines_differents_accepte(self) -> None:
        """Deux domaines différents : accepté.

        Rend impossible : le rejet d'une contradiction légitime entre
        domaines — sol favorable et climat défavorable est une information
        que le forestier doit voir.
        """
        contradiction = ContradictionDomaines(
            description="Sol favorable, climat défavorable",
            domaine_a=Domaine.pedologique,
            domaine_b=Domaine.climatique,
        )
        assert contradiction.domaine_a is Domaine.pedologique
        assert contradiction.domaine_b is Domaine.climatique

    def test_domaine_element_et_risque_accepte(self) -> None:
        """Un atout (DomaineElement) projeté contre un risque (DomaineRisque).

        Rend impossible : l'invisibilité de la contradiction la plus
        fréquente — un atout pédologique contre un risque climatique.
        Avant le type Domaine unifié, ce cas était inexprimable. Le contrat
        §6 exige qu'il soit visible.
        """
        contradiction = ContradictionDomaines(
            description="Sol profond et fertile, mais déficit hydrique croissant",
            domaine_a=Domaine.pedologique,
            domaine_b=Domaine.climatique,
        )
        assert contradiction.domaine_a is Domaine.pedologique
        assert contradiction.domaine_b is Domaine.climatique

    # Liste blanche : l'ensemble exact des champs attendus sur
    # ContradictionDomaines. Tout ajout fait échouer le test et force une
    # relecture d'architecture. La machine ne tranche jamais entre domaines
    # (SCIENTIFIC_CONSTITUTION S-3) — un champ de résolution ne peut pas
    # apparaître sans qu'on le voie.
    CHAMPS_ATTENDUS_CONTRADICTION: frozenset[str] = frozenset(
        {"description", "domaine_a", "domaine_b"}
    )

    # Liste noire secondaire pour un message d'erreur plus parlant.
    CHAMPS_RESOLUTION: frozenset[str] = frozenset(
        {"resolution", "priorite", "gagnant", "poids", "arbitrage", "decision"}
    )

    def test_aucun_champ_ajoute_sans_revue(self) -> None:
        """Tout champ nouveau doit passer par une relecture d'architecture.

        Rend impossible : l'ajout silencieux d'un champ — de résolution,
        d'arbitrage, ou de tout autre nom auquel on n'avait pas pensé — au
        modèle ContradictionDomaines. La garantie S-3 ne peut pas reposer
        sur une liste de noms interdits : on fige l'ensemble attendu.
        """
        champs_present = set(ContradictionDomaines.model_fields.keys())
        assert champs_present == self.CHAMPS_ATTENDUS_CONTRADICTION, (
            f"ContradictionDomaines comporte des champs inattendus : "
            f"ajouts={champs_present - self.CHAMPS_ATTENDUS_CONTRADICTION}, "
            f"manquants={self.CHAMPS_ATTENDUS_CONTRADICTION - champs_present}"
        )

    def test_aucun_champ_resolution_nomme(self) -> None:
        """Aucun champ de résolution par nom (message explicite, S-3).

        Rend impossible : un champ explicitement nommé « resolution » ou
        « gagnant » — le test donne un message d'erreur plus parlant que la
        liste blanche seule. Garde-fou secondaire, pas primaire.
        """
        champs_present = set(ContradictionDomaines.model_fields.keys())
        champs_trouves = champs_present & self.CHAMPS_RESOLUTION
        assert not champs_trouves, (
            f"ContradictionDomaines comporte un champ de résolution, "
            f"ce qui viole S-3 : {champs_trouves}"
        )


# ---------------------------------------------------------------------------
# DiagnosticRequest
# ---------------------------------------------------------------------------


class TestDiagnosticRequest:
    """Entrée du Diagnostic Engine — au moins une conclusion et un contexte."""

    def test_conclusions_vides_rejete(self) -> None:
        """conclusions vide : rejeté.

        Rend impossible : un diagnostic sans conclusion à synthétiser —
        produire un diagnostic sans prémisse reviendrait à conclure à vide.
        """
        with pytest.raises(ValidationError, match="conclusions"):
            _diagnostic_request(conclusions=[])

    def test_une_seule_conclusion_accepte(self) -> None:
        """Une seule conclusion : accepté.

        Rend impossible : le rejet d'un diagnostic fondé sur une seule
        conclusion — un diagnostic minimal mais honnête est légitime.
        """
        requete = _diagnostic_request(conclusions=[_conclusion()])
        assert len(requete.conclusions) == 1

    def test_contexte_absent_rejete(self) -> None:
        """contexte absent : rejeté.

        Rend impossible : un diagnostic sans contexte stationnel — on ne
        synthétise pas sans connaître la station.
        """
        with pytest.raises(ValidationError, match="contexte"):
            DiagnosticRequest(
                requete_id=uuid4(),
                station_id=uuid4(),
                conclusions=[_conclusion()],
                qualifications=[_qualification()],
                etat_global=_etat_global(),
                contexte=None,  # type: ignore[arg-type]
                type_diagnostic=TypeDiagnostic.stationnel,
            )


# ---------------------------------------------------------------------------
# ElementDiagnostic et RisqueDiagnostic
# ---------------------------------------------------------------------------


class TestElementDiagnostic:
    """Une contrainte ou un atout sans source ni preuve n'existe pas."""

    def test_sans_source_rejete(self) -> None:
        """Sans source : rejeté (GSIE-CON-002).

        Rend impossible : un élément de diagnostic non sourcé — une
        affirmation sans origine, donc non contestable.
        """
        with pytest.raises(ValidationError, match="source"):
            ElementDiagnostic(
                description="Sol acide",
                domaine=DomaineElement.pedologique,
                evidence_level=EvidenceLevel.B,
                source=None,  # type: ignore[arg-type]
            )

    def test_sans_evidence_level_rejete(self) -> None:
        """Sans evidence_level : rejeté.

        Rend impossible : un élément sans niveau de preuve — le lecteur ne
        pourrait pas juger la fiabilité de l'information.
        """
        with pytest.raises(ValidationError, match="evidence_level"):
            ElementDiagnostic(
                description="Sol acide",
                domaine=DomaineElement.pedologique,
                evidence_level=None,  # type: ignore[arg-type]
                source=_source(),
            )

    def test_description_vide_rejete(self) -> None:
        """Description vide : rejeté.

        Rend impossible : un élément sans description — une contrainte ou
        un atout sans texte est une coquille vide.
        """
        with pytest.raises(ValidationError, match="description"):
            ElementDiagnostic(
                description="",
                domaine=DomaineElement.pedologique,
                evidence_level=EvidenceLevel.B,
                source=_source(),
            )


class TestRisqueDiagnostic:
    """Un risque sans source ni preuve n'existe pas."""

    def test_sans_source_rejete(self) -> None:
        """Sans source : rejeté (GSIE-CON-002).

        Rend impossible : un risque non sourcé — une alerte sans origine,
        donc non vérifiable.
        """
        with pytest.raises(ValidationError, match="source"):
            RisqueDiagnostic(
                description="Risque de dépérissement",
                probabilite=Probabilite.eleve,
                horizon="10 ans",
                domaine=DomaineRisque.climatique,
                evidence_level=EvidenceLevel.B,
                source=None,  # type: ignore[arg-type]
            )

    def test_sans_evidence_level_rejete(self) -> None:
        """Sans evidence_level : rejeté.

        Rend impossible : un risque sans niveau de preuve — le lecteur ne
        pourrait pas juger la fiabilité de l'alerte.
        """
        with pytest.raises(ValidationError, match="evidence_level"):
            RisqueDiagnostic(
                description="Risque de dépérissement",
                probabilite=Probabilite.eleve,
                horizon="10 ans",
                domaine=DomaineRisque.climatique,
                evidence_level=None,  # type: ignore[arg-type]
                source=_source(),
            )

    def test_description_vide_rejete(self) -> None:
        """Description vide : rejeté.

        Rend impossible : un risque sans description — une alerte sans
        texte est une coquille vide.
        """
        with pytest.raises(ValidationError, match="description"):
            RisqueDiagnostic(
                description="",
                probabilite=Probabilite.eleve,
                horizon="10 ans",
                domaine=DomaineRisque.climatique,
                evidence_level=EvidenceLevel.B,
                source=_source(),
            )


# ---------------------------------------------------------------------------
# ValidationHumaine — trace auditable de relecture
# ---------------------------------------------------------------------------


class TestValidationHumaine:
    """Une validation sans identité ni date fuseaute n'est pas auditable."""

    def test_validateur_vide_rejete(self) -> None:
        """validateur vide : rejeté.

        Rend impossible : une validation anonyme — on ne peut ni contester
        ni savoir qui a relu. GSIE-CON-005 exige une traçabilité nominative.
        """
        with pytest.raises(ValidationError, match="validateur"):
            ValidationHumaine(
                validateur="",
                date_validation=datetime(2026, 7, 25, 12, 0, 0, tzinfo=UTC),
            )

    def test_date_validation_naive_rejete(self) -> None:
        """date_validation sans fuseau horaire : rejeté.

        Rend impossible : un horodatage ambigu — un diagnostic relu à Chizé
        et contesté ailleurs, des années plus tard, ne permettrait pas
        d'établir l'antériorité de la relecture sur un événement de terrain.
        GSIE-CON-005 exige une traçabilité, pas une indication.
        """
        date_naive = datetime(2026, 7, 25, 12, 0, 0)  # tzinfo=None
        with pytest.raises(ValidationError, match="sans fuseau horaire"):
            ValidationHumaine(
                validateur="Dr. Camille Dubois",
                date_validation=date_naive,
            )

    def test_date_validation_avec_fuseau_accepte(self) -> None:
        """date_validation avec fuseau horaire : accepté.

        Rend impossible : le rejet d'une validation correctement datée —
        la seule forme légitime de trace.
        """
        validation = ValidationHumaine(
            validateur="Dr. Camille Dubois",
            date_validation=datetime(2026, 7, 25, 12, 0, 0, tzinfo=UTC),
        )
        assert validation.validateur == "Dr. Camille Dubois"
        assert validation.date_validation.tzinfo is not None


# ---------------------------------------------------------------------------
# Diagnostic.confiance — bornes du contrat §5 (0,0 à 1,0)
# ---------------------------------------------------------------------------


class TestBornesConfiance:
    """La confiance est bornée entre 0.0 et 1.0 inclus (contrat §5)."""

    def test_confiance_zero_accepte(self) -> None:
        """confiance = 0.0 : accepté (borne inférieure inclusive).

        Rend impossible : le rejet d'un diagnostic à confiance nulle —
        un diagnostic peut légitimement n'avoir aucune confiance.
        """
        diagnostic = _diagnostic(confiance=0.0)
        assert diagnostic.confiance == 0.0

    def test_confiance_un_accepte(self) -> None:
        """confiance = 1.0 : accepté (borne supérieure inclusive).

        Rend impossible : le rejet d'un diagnostic à confiance maximale —
        un diagnostic peut légitimement être pleinement confiant.
        """
        diagnostic = _diagnostic(confiance=1.0)
        assert diagnostic.confiance == 1.0

    def test_confiance_sous_borne_rejete(self) -> None:
        """confiance = -0.1 : rejeté (sous la borne inférieure).

        Rend impossible : une confiance négative — une valeur sans sens
        physique qui passerait inaperçue sans le validateur.
        """
        with pytest.raises(ValidationError, match="confiance"):
            _diagnostic(confiance=-0.1)

    def test_confiance_sur_borne_rejete(self) -> None:
        """confiance = 1.1 : rejeté (au-dessus de la borne supérieure).

        Rend impossible : une confiance supérieure à 1 — une valeur sans
        sens physique qui donnerait une fausse certitude.
        """
        with pytest.raises(ValidationError, match="confiance"):
            _diagnostic(confiance=1.1)


# ---------------------------------------------------------------------------
# Domaine — échelle commune pour les contradictions (union des domaines)
# ---------------------------------------------------------------------------


class TestDomaine:
    """Domaine est l'union de DomaineElement et DomaineRisque, pour §6.

    Ce type existe uniquement pour exprimer une contradiction entre un
    atout et un risque — le cas le plus fréquent et le plus utile au
    forestier. Une liste blanche fige l'ensemble attendu : tout ajout ou
    retrait force une relecture d'architecture.
    """

    # Liste blanche : l'ensemble exact des valeurs attendues sur Domaine.
    # Union de DomaineElement (5 valeurs) et DomaineRisque (3 valeurs),
    # soit 6 valeurs distinctes (sylvicole et climatique sont communs).
    VALEURS_ATTENDUES: frozenset[Domaine] = frozenset(
        {
            Domaine.pedologique,
            Domaine.climatique,
            Domaine.topographique,
            Domaine.botanique,
            Domaine.sylvicole,
            Domaine.sanitaire,
        }
    )

    def test_enum_fermee_liste_blanche(self) -> None:
        """Domaine contient exactement l'union des deux énumérations.

        Rend impossible : l'ajout silencieux d'un domaine (ou le retrait)
        — toute évolution de l'échelle commune doit passer par une
        relecture d'architecture, car elle change l'ensemble des
        contradictions exprimables.
        """
        valeurs_presentes = set(Domaine)
        assert valeurs_presentes == self.VALEURS_ATTENDUES, (
            f"Domaine comporte des valeurs inattendues : "
            f"ajouts={valeurs_presentes - self.VALEURS_ATTENDUES}, "
            f"manquantes={self.VALEURS_ATTENDUES - valeurs_presentes}"
        )

    def test_projection_element_totale(self) -> None:
        """domaine_commun() projette tout DomaineElement sur Domaine.

        Rend impossible : un DomaineElement sans équivalent commun — une
        contradiction impliquant ce domaine serait inexprimable.
        """
        for domaine_element in DomaineElement:
            domaine_commun(domaine_element)  # lève si non projetable

    def test_projection_risque_totale(self) -> None:
        """domaine_commun() projette tout DomaineRisque sur Domaine.

        Rend impossible : un DomaineRisque sans équivalent commun — une
        contradiction impliquant ce risque serait inexprimable.
        """
        for domaine_risque in DomaineRisque:
            domaine_commun(domaine_risque)  # lève si non projetable

    def test_projection_conserve_la_valeur(self) -> None:
        """La projection conserve la valeur de l'énumération d'origine.

        Rend impossible : une projection qui transformerait la valeur —
        un DomaineElement.climatique doit devenir Domaine.climatique,
        pas autre chose.
        """
        assert domaine_commun(DomaineElement.pedologique) is Domaine.pedologique
        assert domaine_commun(DomaineRisque.sanitaire) is Domaine.sanitaire
        assert domaine_commun(DomaineRisque.climatique) is Domaine.climatique


# ---------------------------------------------------------------------------
# Probabilite — enum fermée
# ---------------------------------------------------------------------------


class TestProbabilite:
    """Probabilite n'accepte que faible, modere, eleve, tres_eleve."""

    def test_valeurs_valides_acceptees(self) -> None:
        """Les quatre valeurs de l'enum sont acceptées.

        Rend impossible : le rejet d'une probabilité légitime — les quatre
        niveaux qualitatifs du contrat §5 doivent être constructibles.
        """
        valeurs_valides = (
            Probabilite.faible,
            Probabilite.modere,
            Probabilite.eleve,
            Probabilite.tres_eleve,
        )
        for valeur in valeurs_valides:
            risque = _risque(probabilite=valeur)
            assert risque.probabilite is valeur

    def test_valeur_invalide_rejetee(self) -> None:
        """Une valeur hors enum est rejetée.

        Rend impossible : une probabilité non prévue par le contrat — une
        fausse précision comme « 67 % » qui donnerait l'illusion d'un
        modèle quantitatif que le moteur ne possède pas (GSIE-CON-002).
        """
        with pytest.raises(ValueError):
            Probabilite("inexistant")
