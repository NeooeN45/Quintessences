"""Reasoning Engine — inférence explicable sur connaissances qualifiées.

Responsabilité (REASONING_ENGINE.md §1) :
- Appliquer des règles d'inférence explicites et auditées sur un contexte
  stationnel pour produire des conclusions expliquées et traçables.
- Ne jamais inventer de règle (`GSIE-CON-002`) : les règles sont fournies
  par l'appelant (Knowledge Engine en cible, dans la requête en v1).
- Ne jamais trancher une contradiction (`GSIE-CON-002`, S-3) : les
  contradictions sont signalées, jamais résolues.
- Ne produire ni diagnostic ni recommandation (séparation des
  responsabilités, §6).

Périmètre v1 (voir docstring schemas.py) : les règles d'inférence sont
fournies dans la requête par l'appelant, chacune avec sa
`SourceReference` et son `evidence_level`, sur le précédent assumé du
Correlation Engine. Le branchement direct sur le Knowledge Engine se fera
sans rupture de contrat.

Déterminisme : à contexte, règles et horloge identiques, deux exécutions
produisent un `InferenceResult` identique. `date_inference` est une entrée
du moteur et non une lecture d'horloge interne — sans quoi le moteur ne
serait pas testable. Les règles sont évaluées dans
un ordre total explicite (tri par identifiant avant chaque tour). Aucun
parcours de `set` dans un chemin qui produit de la sortie. Les
identifiants stables sont dérivés du contenu par `uuid5` (namespace
fixe), jamais par `uuid4`.

Évaluation des conditions : un évaluateur sûr basé sur le module `ast`
de la bibliothèque standard. Aucun appel à `eval` ou `exec`. Seuls les
nœuds `Name`, `Constant`, `Compare`, `BoolOp`, `UnaryOp` sont autorisés —
comparaisons et connecteurs logiques sur les variables du contexte. Toute
construction Python plus riche est rejetée comme règle mal formée.
"""

import ast
import operator as op_module
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid5

from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.logging import get_logger
from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference
from gsie_api.engines.reasoning.schemas import (
    BlocContexte,
    Conclusion,
    ContradictionDetectee,
    EtapeInference,
    InferenceResult,
    MethodeConfiance,
    ReasoningRequest,
    RegleInference,
    SourceMoteurContexte,
    StationContexte,
    niveau_plancher,
)


@dataclass(frozen=True, slots=True)
class _EtapeBrute:
    """Étape d'inférence avant attribution de son rang.

    `EtapeInference.ordre` dépend de la chaîne qui porte l'étape, pas de la
    règle qui l'a produite : la même étape occupe le rang 1 dans une
    conclusion et le rang 2 dans une autre. Séparer les deux évite de
    produire des chaînes non contiguës, que `Conclusion` rejette.
    """

    regle_appliquee: str
    source_regle: SourceReference
    # Niveaux de preuve des FAITS consommes par l'etape, distincts de celui de
    # la regle. Une conclusion ne peut pas etre mieux etablie que le plus
    # faible de ses maillons : un releve terrain isole (F) traverse par une
    # regle de catalogue (B) donne F, jamais B. Sans cela le moteur annonce
    # « etabli » sur une mesure unique non recoupee.
    niveaux_des_faits: tuple[EvidenceLevel, ...]
    premisses: list[str]
    conclusion_locale: str
    evidence_level: EvidenceLevel


logger = get_logger("gsie_api.reasoning.engine")

# Namespace fixe pour la dérivation déterministe d'identifiants par uuid5.
# Choisir un UUID constant garantit que deux moteurs produisant la même
# conclusion à partir de la même règle et des mêmes prémisses génèrent le
# même conclusion_id — exigence du déterminisme (§mission R2).
_NAMESPACE_DETERMINISME = UUID("00000000-0000-4000-8000-000000000010")


def conclusion_id_pour(requete_id: UUID, identifiant_regle: str) -> UUID:
    """Identifiant de la conclusion que produirait une règle donnée.

    Extrait du corps de `infer` pour qu'un appelant puisse rattacher une
    conclusion à la règle dont elle est issue **sans redériver la formule**.
    L'orchestration en a besoin : les qualifications de conclusions sont
    déclarées par l'appelant — le moteur « ne le sait pas et ne doit pas le
    deviner » — alors que les conclusions n'existent qu'après l'inférence.
    L'appelant déclare donc par règle, et cette fonction fait le lien.

    Recopier la dérivation ailleurs la ferait diverger au premier changement,
    et le rattachement échouerait en silence : aucune qualification ne
    correspondrait plus, sans que la formule paraisse fautive.
    """
    return uuid5(_NAMESPACE_DETERMINISME, f"{requete_id}|{identifiant_regle}")


class ReasoningEngineError(Exception):
    """Erreur de base du Reasoning Engine.

    Levée lorsqu'une règle est mal formée ou référence une variable
    absente du contexte. Jamais levée pour l'absence de conclusion —
    l'absence de résultat est un résultat honnête (`GSIE-CON-002`).
    """


# `RegleInference` vit désormais dans `schemas.py` : `ReasoningRequest` en
# dépend, et un contrat dont un type manque n'est pas un contrat.

# --- Évaluateur de conditions sûr -------------------------------------------

# Opérateurs de comparaison autorisés dans les conditions.
_COMPARE_OPS: dict[type[ast.cmpop], Any] = {
    ast.Eq: op_module.eq,
    ast.NotEq: op_module.ne,
    ast.Lt: op_module.lt,
    ast.LtE: op_module.le,
    ast.Gt: op_module.gt,
    ast.GtE: op_module.ge,
}

# Connecteurs logiques autorisés.
_BOOL_OPS: dict[type[ast.boolop], Any] = {
    ast.And: all,
    ast.Or: any,
}

# Opérateur unaire autorisé (négation logique).
_UNARY_OPS: dict[type[ast.unaryop], Any] = {
    ast.Not: op_module.not_,
}


def _evaluer_noeud(noeud: ast.AST, faits: dict[str, Any]) -> Any:
    """Évalue récursivement un nœud AST contre les faits courants.

    Seuls les nœuds `Name`, `Constant`, `Compare`, `BoolOp`, `UnaryOp`
    sont autorisés. Tout autre nœud lève `ValueError` — qui sera remonté
    comme `ReasoningEngineError` par l'appelant.
    """
    if isinstance(noeud, ast.Constant):
        return noeud.value
    if isinstance(noeud, ast.Name):
        if noeud.id not in faits:
            raise KeyError(noeud.id)
        return faits[noeud.id]
    if isinstance(noeud, ast.Compare):
        gauche = _evaluer_noeud(noeud.left, faits)
        for operation, droit_ast in zip(noeud.ops, noeud.comparators, strict=True):
            if type(operation) not in _COMPARE_OPS:
                raise ValueError(f"opérateur de comparaison interdit : {type(operation).__name__}")
            droit = _evaluer_noeud(droit_ast, faits)
            if not _COMPARE_OPS[type(operation)](gauche, droit):
                return False
            gauche = droit
        return True
    if isinstance(noeud, ast.BoolOp):
        if type(noeud.op) not in _BOOL_OPS:
            raise ValueError(f"connecteur logique interdit : {type(noeud.op).__name__}")
        valeurs = [_evaluer_noeud(v, faits) for v in noeud.values]
        return _BOOL_OPS[type(noeud.op)](valeurs)
    if isinstance(noeud, ast.UnaryOp):
        if type(noeud.op) not in _UNARY_OPS:
            raise ValueError(f"opérateur unaire interdit : {type(noeud.op).__name__}")
        return _UNARY_OPS[type(noeud.op)](_evaluer_noeud(noeud.operand, faits))
    raise ValueError(f"construction interdite dans une condition : {type(noeud).__name__}")


def _evaluer_condition(condition: str, faits: dict[str, Any]) -> bool:
    """Évalue une condition restreinte contre les faits.

    Lève `KeyError` si la condition référence une variable absente des
    faits. Lève `ValueError` si la condition contient une construction
    interdite. L'appelant convertit ces erreurs en `ReasoningEngineError`
    nommant la règle et la variable.
    """
    try:
        arbre = ast.parse(condition, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"condition non parsable : {exc.msg}") from exc
    return bool(_evaluer_noeud(arbre.body, faits))


# --- Aplatissement du StationContexte ---------------------------------------


def _aplatir_contexte(contexte: StationContexte) -> dict[str, tuple[Any, BlocContexte]]:
    """Aplati le contexte en {nom_variable: (valeur, bloc_provenance)}.

    ADR-009 : aucun fait sans provenance. Chaque variable provient d'un
    `BlocContexte` dont elle hérite la source et l'evidence_level.

    Les noms de variables sont préfixés par le nom du bloc pour éviter
    les collisions entre moteurs domaine (ex. ``pedologie_pH``,
    ``climat_precipitations_mm``). Le préfixe est dérivé du nom du champ
    dans `StationContexte`, pas du `source_moteur`, pour garantir la
    stabilité du nommage.
    """
    faits: dict[str, tuple[Any, BlocContexte]] = {}
    for nom_bloc, bloc in [
        ("geographie", contexte.geographie),
        ("climat", contexte.climat),
        ("pedologie", contexte.pedologie),
        ("botanique", contexte.botanique),
        ("peuplement", contexte.peuplement),
    ]:
        if bloc is None:
            continue
        for cle, valeur in bloc.valeurs.items():
            faits[f"{nom_bloc}_{cle}"] = (valeur, bloc)
    for correlation in contexte.correlations:
        for cle, valeur in correlation.valeurs.items():
            faits[f"correlation_{cle}"] = (valeur, correlation)
    return faits


# --- Moteur -----------------------------------------------------------------


class ReasoningEngine:
    """Moteur d'inférence par chaînage avant borné.

    Une instance est créée par requête HTTP avec la session DB de la
    requête (même schéma que `CorrelationEngine`). En v1, aucune
    persistance n'est effectuée — le moteur est pur et sans effet de
    bord sur la base.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def version() -> str:
        """Version du moteur."""
        return "0.1.0"

    async def _regles_du_territoire(self, territoire_id: UUID) -> list[RegleInference]:
        """Récupère les règles applicables au territoire depuis le Knowledge Engine.

        Les règles écartées sont journalisées, jamais tues : une règle rejetée
        parce qu'elle est mal formée doit pouvoir être corrigée, et le silence
        laisserait croire à une absence de connaissance.

        Un territoire inconnu n'est pas une erreur **ici**. `station_id` est
        facultatif dans `ReasoningRequest` et n'est pas contractuellement une
        `place` enregistrée : une station peut être décrite intégralement par le
        contexte de la requête, sans exister en base — c'est la même raison qui
        fait que `diagnostic.station_id` ne porte pas de clé étrangère. Faire
        remonter l'erreur refuserait une requête légitime dont le contexte
        suffit à raisonner.

        L'exigence reste entière là où elle a un sens : `regles_applicables`,
        interrogé directement, continue de lever. À cette question-là — « quelles
        règles s'appliquent ici ? » — répondre « aucune » pour un territoire
        introuvable serait une réponse fausse. Ici, l'appelant n'a pas posé cette
        question ; la récupération est un complément, et son échec est
        journalisé en avertissement plutôt que tu.
        """
        from gsie_api.engines.knowledge.engine import KnowledgeEngine, TerritoireInconnuError
        from gsie_api.seeds.variables_mesurables_data import noms_de_faits_par_code

        try:
            regles, ecartees = await KnowledgeEngine(self._session).regles_applicables(
                territoire_id,
                variables_connues=noms_de_faits_par_code(),
            )
        except TerritoireInconnuError:
            logger.warning(
                "regles_du_territoire_indisponibles",
                territoire_id=str(territoire_id),
                motif=(
                    "aucune `place` ne porte cet identifiant — le raisonnement "
                    "se poursuit sur les seules règles fournies dans la requête"
                ),
            )
            return []
        if ecartees:
            logger.info(
                "regles_ecartees",
                territoire_id=str(territoire_id),
                nombre=len(ecartees),
                motifs=ecartees,
            )
        return regles

    async def infer(
        self,
        request: ReasoningRequest,
        date_inference: datetime,
    ) -> InferenceResult:
        """Produit une inférence explicable par chaînage avant borné.

        Args:
            request: La requête contenant le contexte stationnel et la
                profondeur maximale de la chaîne.
            regles: Les règles d'inférence fournies par l'appelant
                (Knowledge Engine en cible). Chacune porte sa source et
                son niveau de preuve (ADR-009).

        Returns:
            Un `InferenceResult` contenant les conclusions inférées et
            les contradictions détectées. Peut être vide — l'absence de
            conclusion est un résultat honnête (`GSIE-CON-002`).

        Raises:
            ReasoningEngineError: Si une règle est mal formée (condition
                non parsable, construction interdite) ou référence une
                variable absente du contexte. L'erreur nomme la règle et
                la variable concernée.
        """
        # Les règles viennent de la requête, ou du Knowledge Engine à défaut
        # (RFC-0028 §4.3, DEC-000038). Le branchement était annoncé « sans
        # rupture de contrat » par GSIE-PROMPT-0017 : une requête qui porte ses
        # règles continue de fonctionner à l'identique, la récupération
        # s'ajoute et ne remplace pas.
        #
        # Sans elle, GeoSylva devrait embarquer la connaissance sylvicole, et
        # réviser un seuil imposerait de mettre à jour l'application sur chaque
        # téléphone — donc, en pratique, la connaissance ne serait jamais
        # révisée.
        regles = list(request.regles)
        if not regles and request.station_id is not None:
            regles = await self._regles_du_territoire(request.station_id)

        if not regles:
            return InferenceResult(
                resultat_id=uuid5(_NAMESPACE_DETERMINISME, f"{request.requete_id}|"),
                requete_origine=request.requete_id,
                conclusions=[],
                contradictions=[],
                date_inference=date_inference,
            )

        faits_bruts = _aplatir_contexte(request.contexte)
        faits: dict[str, Any] = {nom: valeur for nom, (valeur, _bloc) in faits_bruts.items()}

        # Étapes accumulées par conclusion (identifiant de règle → liste d'étapes).
        # Chaque règle appliquée produit une étape ; la conclusion locale
        # devient un fait pour le tour suivant.
        etapes_par_regle: dict[str, _EtapeBrute] = {}
        faits_du_tour_suivant: dict[str, Any] = {}
        regles_appliquees: set[str] = set()
        # Conclusions produites, indexées par identifiant de règle.
        conclusions_locales: dict[str, str] = {}
        # Provenance des faits dérivés (identifiant de règle qui les a produits).
        provenance_faits_derives: dict[str, str] = {}

        tour = 0
        profondeur_atteinte = False

        while tour < request.profondeur_max:
            tour += 1
            # Ordre total explicite : tri par identifiant de règle.
            regles_possibles = sorted(
                [r for r in regles if r.identifiant not in regles_appliquees],
                key=lambda r: r.identifiant,
            )
            if not regles_possibles:
                break

            regle_appliquee_ce_tour = False
            for regle in regles_possibles:
                # Évaluer la condition contre les faits courants (contexte + dérivés).
                try:
                    satisfaite = _evaluer_condition(regle.condition, faits)
                except KeyError as exc:
                    variable = str(exc).strip("'\"")
                    # Un fait dérivé encore absent signifie que la règle qui le
                    # produit n'a pas encore été appliquée : la condition n'est
                    # pas satisfaite à ce tour, ce n'est pas une erreur. C'est
                    # le mécanisme même du chaînage conditionnel.
                    if variable.startswith("conclusion_"):
                        continue
                    # En revanche, une variable de contexte absente est une
                    # règle inapplicable à cette station : erreur explicite,
                    # jamais un faux silencieux (`TECHNICAL_CONSTITUTION` T-7).
                    raise ReasoningEngineError(
                        f"règle « {regle.identifiant} » : variable « {variable} » "
                        f"absente du contexte"
                    ) from exc
                except ValueError as exc:
                    raise ReasoningEngineError(
                        f"règle « {regle.identifiant} » : condition mal formée — {exc}"
                    ) from exc

                if not satisfaite:
                    continue

                # Calculer les prémisses effectives : les variables de la
                # condition qui sont réellement présentes dans les faits.
                variables_condition = _extraire_variables(regle.condition)
                premisses_effectives: list[str] = []
                niveaux_des_faits: list[EvidenceLevel] = []
                for var in sorted(variables_condition):
                    if var in faits_bruts:
                        valeur, bloc = faits_bruts[var]
                        source_auteur = bloc.source.auteur
                        niveaux_des_faits.append(bloc.evidence_level)
                        premisses_effectives.append(f"{var} = {valeur} (source : {source_auteur})")
                    elif var in provenance_faits_derives:
                        regle_source = provenance_faits_derives[var]
                        premisses_effectives.append(
                            f"{var} = {faits[var]} (règle : {regle_source})"
                        )
                    else:
                        # Variable présente mais sans provenance traçable —
                        # ne devrait pas arriver car tous les faits ont une
                        # provenance (ADR-009). On l'inclut quand même pour
                        # ne pas perdre l'information.
                        premisses_effectives.append(f"{var} = {faits[var]}")

                # L'étape est mémorisée SANS son rang. `ordre` est une
                # propriété de la chaîne qui portera l'étape, pas de la règle :
                # une même étape peut occuper le rang 1 dans une conclusion et
                # le rang 2 dans une autre. Le rang est donc attribué à
                # l'assemblage, jamais ici.
                etapes_par_regle[regle.identifiant] = _EtapeBrute(
                    regle_appliquee=regle.enonce_conclusion,
                    source_regle=regle.source,
                    premisses=premisses_effectives,
                    conclusion_locale=regle.enonce_conclusion,
                    # Plancher de l'etape : sa regle ET les faits qu'elle
                    # consomme. Ne retenir que la regle annoncerait une etape
                    # mieux etablie que la mesure qui la fonde — un releve
                    # terrain isole (F) traverse par une regle de catalogue (B)
                    # ressortait en B. Surestimation silencieuse, exactement ce
                    # que ADR-009 previent.
                    evidence_level=niveau_plancher([regle.evidence_level, *niveaux_des_faits]),
                    niveaux_des_faits=tuple(niveaux_des_faits),
                )
                regles_appliquees.add(regle.identifiant)
                conclusions_locales[regle.identifiant] = regle.enonce_conclusion

                # Le fait dérivé n'est PAS visible immédiatement : il rejoint
                # les faits à la fin du tour. Sans cette temporisation, tout le
                # chaînage se produirait au premier tour et `profondeur_max`
                # n'aurait aucun effet — la borne d'audit serait décorative.
                nom_fait_derive = f"conclusion_{regle.identifiant}"
                faits_du_tour_suivant[nom_fait_derive] = True
                provenance_faits_derives[nom_fait_derive] = regle.identifiant

                regle_appliquee_ce_tour = True
                logger.debug("regle_appliquee", regle=regle.identifiant, tour=tour)

            # Publication différée des faits dérivés du tour.
            faits.update(faits_du_tour_suivant)
            faits_du_tour_suivant.clear()

            if not regle_appliquee_ce_tour:
                break
        else:
            profondeur_atteinte = True

        # Une règle qui n'a jamais pu être appliquée rend le résultat partiel,
        # quelle qu'en soit la raison : profondeur épuisée, ou point fixe
        # atteint alors que des règles restaient en attente d'un fait qui ne
        # viendra jamais — le cas d'un jeu de règles circulaire.
        #
        # Ne pas le signaler serait plus grave que de lever une erreur : le
        # système rendrait un résultat vide en le déclarant complet, et
        # l'auteur des règles n'apprendrait jamais que les siennes n'ont
        # jamais servi. C'est la troncation silencieuse que `GSIE-CON-004`
        # interdit.
        regles_restantes = [r for r in regles if r.identifiant not in regles_appliquees]
        resultat_partiel = bool(regles_restantes)
        if resultat_partiel:
            logger.info(
                "regles_non_appliquees",
                profondeur_max=request.profondeur_max,
                profondeur_atteinte=profondeur_atteinte,
                regles_restantes=len(regles_restantes),
            )

        # --- Assemblage des conclusions ---
        # Chaque règle appliquée produit une Conclusion. Les règles qui
        # forment une chaîne (la conclusion de l'une sert de prémisse à
        # l'autre) sont regroupées en une seule Conclusion dont la chaîne
        # d'inférence contient toutes les étapes impliquées.
        #
        # En v1, on adopte l'approche la plus simple et la plus traçable :
        # une Conclusion par règle appliquée, dont la chaîne d'inférence
        # contient l'étape de cette règle plus toutes les étapes des
        # règles dont elle dépend (transitivement, via les prémisses
        # dérivées). Cette approche garantit que chaque conclusion est
        # expliquée de bout en bout.
        conclusions: list[Conclusion] = []
        for identifiant in sorted(etapes_par_regle.keys()):
            etape = etapes_par_regle[identifiant]
            regle = next(r for r in regles if r.identifiant == identifiant)

            # Construire la chaîne d'inférence : l'étape courante plus
            # les étapes des règles dont elle dépend transitivement.
            dependances = _dependances_transitives(
                identifiant, provenance_faits_derives, regles, faits_bruts
            )
            # Les dépendances d'abord, la règle courante en dernier : c'est
            # l'ordre de lecture d'une démonstration. Le rang est attribué
            # ici, 1..N contigus, comme l'exige `Conclusion._chaine_contigue`.
            brutes = [etapes_par_regle[dep] for dep in sorted(dependances)]
            brutes.append(etape)
            chaine = [
                EtapeInference(
                    ordre=rang,
                    regle_appliquee=brute.regle_appliquee,
                    source_regle=brute.source_regle,
                    premisses=brute.premisses,
                    conclusion_locale=brute.conclusion_locale,
                    evidence_level=brute.evidence_level,
                )
                for rang, brute in enumerate(brutes, start=1)
            ]

            # Sources utilisées : exactement les sources des étapes de la
            # chaîne (le validateur _sources_fermees l'exige).
            sources_utilisees = _sources_de_chaine(chaine)

            # Moteurs sollicités : les source_moteur des blocs dont
            # proviennent les prémisses.
            moteurs_solicites = _moteurs_des_premisses(chaine, faits_bruts)

            # Identifiant de conclusion déterministe : uuid5 dérivé de
            # l'identifiant de la règle et de la requête. Deux exécutions
            # sur les mêmes entrées produisent le même conclusion_id.
            conclusion_id = conclusion_id_pour(request.requete_id, identifiant)

            conclusion = Conclusion(
                conclusion_id=conclusion_id,
                enonce=regle.enonce_conclusion,
                niveau_confiance=regle.niveau_confiance,
                methode_confiance=MethodeConfiance.fournie_par_regle,
                # Le plancher couvre les regles ET les faits consommes. Ne
                # retenir que les regles annoncerait une conclusion mieux
                # etablie que la mesure qui la fonde — surestimation
                # silencieuse, exactement ce que ADR-009 previent.
                evidence_level_plancher=niveau_plancher(
                    [e.evidence_level for e in chaine]
                    + [niveau for brute in brutes for niveau in brute.niveaux_des_faits]
                ),
                chaine_inference=chaine,
                sources_utilisees=sources_utilisees,
                moteurs_solicites=moteurs_solicites,
            )
            conclusions.append(conclusion)

        # --- Détection de contradictions ---
        contradictions = _detecter_contradictions(regles, conclusions)

        # `resultat_id` est dérivé du contenu : deux inférences identiques
        # portent le même identifiant. Ce n'est pas un défaut, c'est ce qui
        # rend le résultat citable et comparable d'une exécution à l'autre.
        resultat = InferenceResult(
            resultat_id=uuid5(
                _NAMESPACE_DETERMINISME,
                f"{request.requete_id}|" + "|".join(str(c.conclusion_id) for c in conclusions),
            ),
            requete_origine=request.requete_id,
            conclusions=conclusions,
            contradictions=contradictions,
            date_inference=date_inference,
            resultat_partiel=resultat_partiel,
            regles_non_appliquees=sorted(
                r.identifiant for r in regles if r.identifiant not in regles_appliquees
            )
            if resultat_partiel
            else [],
        )

        logger.info(
            "infERENCE_terminee",
            requete_id=str(request.requete_id),
            n_conclusions=len(conclusions),
            n_contradictions=len(contradictions),
            resultat_partiel=resultat_partiel,
        )
        return resultat


# --- Helpers : dépendances, sources, moteurs, contradictions ----------------


def _extraire_variables(condition: str) -> set[str]:
    """Extrait l'ensemble des noms de variables référencés dans la condition."""
    arbre = ast.parse(condition, mode="eval")
    return {n.id for n in ast.walk(arbre) if isinstance(n, ast.Name)}


def _sources_de_chaine(chaine: list[EtapeInference]) -> list[SourceReference]:
    """Retourne les sources uniques de la chaîne, dans un ordre stable.

    Le validateur `_sources_fermees` de `Conclusion` exige que les
    sources déclarées soient exactement celles citées par les étapes.
    On déduplique par clé source (type, auteur, référence) pour éviter
    les doublons, en préservant l'ordre d'apparition.
    """
    vues: set[str] = set()
    sources: list[SourceReference] = []
    for etape in chaine:
        cle = (
            f"{etape.source_regle.type_source}|{etape.source_regle.auteur}"
            f"|{etape.source_regle.reference}"
        )
        if cle not in vues:
            vues.add(cle)
            sources.append(etape.source_regle)
    return sources


def _moteurs_des_premisses(
    chaine: list[EtapeInference],
    faits_bruts: dict[str, tuple[Any, BlocContexte]],
) -> list[SourceMoteurContexte]:
    """Retourne les moteurs domaine dont proviennent les prémisses.

    En v1, on collecte les moteurs des blocs du contexte qui ont fourni
    les faits initiaux. Les faits dérivés (conclusions de règles
    antérieures) ne proviennent pas d'un moteur domaine. Tri par nom de
    moteur pour le déterminisme.
    """
    # Seuls comptent les faits réellement cités par les prémisses de la
    # chaîne. Déclarer un moteur qui n'a rien fourni serait une fausse
    # justification — le défaut que `GSIE-CON-004` cherche à empêcher.
    noms_cites = {
        nom
        for etape in chaine
        for premisse in etape.premisses
        for nom in (premisse.split(" = ", maxsplit=1)[0].strip(),)
    }
    moteurs: list[SourceMoteurContexte] = []
    vues: set[str] = set()
    for nom, (_valeur, bloc) in sorted(faits_bruts.items()):
        if nom not in noms_cites:
            continue
        if bloc.source_moteur.value not in vues:
            vues.add(bloc.source_moteur.value)
            moteurs.append(bloc.source_moteur)
    return moteurs


def _dependances_transitives(
    identifiant: str,
    provenance_faits_derives: dict[str, str],
    regles: list[RegleInference],
    faits_bruts: dict[str, tuple[Any, BlocContexte]],
) -> set[str]:
    """Retourne les identifiants de règles dont dépend transitivement la règle donnée.

    Une règle R dépend d'une règle R' si la condition de R référence un
    fait dérivé produit par R'. La dépendance est transitive : si R
    dépend de R' et R' dépend de R'', alors R dépend de R'' et R''.
    """
    # Construire la map : nom de fait dérivé → identifiant de règle productrice.
    fait_vers_regle = {nom: rid for nom, rid in provenance_faits_derives.items()}

    # Pour chaque règle, calculer les faits dérivés qu'elle référence.
    regle_par_id = {r.identifiant: r for r in regles}
    visites: set[str] = set()
    pile = [identifiant]
    dependances: set[str] = set()

    while pile:
        courant = pile.pop()
        if courant in visites:
            continue
        visites.add(courant)
        regle = regle_par_id.get(courant)
        if regle is None:
            continue
        variables = _extraire_variables(regle.condition)
        for var in variables:
            if var in fait_vers_regle:
                dep = fait_vers_regle[var]
                if dep != courant:
                    dependances.add(dep)
                    pile.append(dep)

    return dependances


def _detecter_contradictions(
    regles: list[RegleInference],
    conclusions: list[Conclusion],
) -> list[ContradictionDetectee]:
    """Détecte les contradictions déclarées entre règles.

    Une contradiction est déclarée lorsqu'une règle R porte
    ``contredit_regle_id = "R'"`` et que **both** R et R' ont produit
    une conclusion. Le moteur ne fait AUCUNE analyse sémantique — une
    contradiction non déclarée n'existe pas (`GSIE-CON-002`, `ADR-009`).

    Les deux conclusions restent présentes dans le résultat. Le moteur
    ne tranche jamais (`GSIE-CON-002`, S-3).
    """
    if not conclusions:
        return []

    # Map : énoncé de conclusion → conclusion_id. Permet de retrouver
    # l'UUID d'une conclusion à partir de l'énoncé de la règle qui l'a
    # produite. En v1, une règle = un énoncé = une conclusion.
    enonce_vers_conclusion: dict[str, UUID] = {
        conclusion.enonce: conclusion.conclusion_id for conclusion in conclusions
    }
    regle_par_id = {r.identifiant: r for r in regles}

    contradictions: list[ContradictionDetectee] = []
    vues: set[frozenset[str]] = set()
    for regle in regles:
        if regle.contredit_regle_id is None:
            continue
        cible = regle_par_id.get(regle.contredit_regle_id)
        if cible is None:
            continue
        # Les deux règles doivent avoir produit une conclusion.
        id_a = enonce_vers_conclusion.get(regle.enonce_conclusion)
        id_b = enonce_vers_conclusion.get(cible.enonce_conclusion)
        if id_a is None or id_b is None:
            continue
        # Éviter les doublons (A contredit B et B contredit A).
        paire = frozenset({regle.identifiant, regle.contredit_regle_id})
        if paire in vues:
            continue
        vues.add(paire)
        contradictions.append(
            ContradictionDetectee(
                conclusion_a=id_a,
                conclusion_b=id_b,
                description=(
                    f"La règle « {regle.identifiant} » déclare contredire "
                    f"la règle « {regle.contredit_regle_id} ». Les deux "
                    f"conclusions sont conservées ; le moteur ne tranche pas "
                    f"(GSIE-CON-002, SCIENTIFIC_CONSTITUTION S-3)."
                ),
            )
        )

    # Tri pour le déterminisme : par couple d'identifiants de conclusion.
    contradictions.sort(key=lambda c: (str(c.conclusion_a), str(c.conclusion_b)))
    return contradictions
