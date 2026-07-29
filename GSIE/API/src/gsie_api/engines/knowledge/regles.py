"""Dérivation d'une règle d'inférence depuis un fait sourcé (RFC-0028 §4.2).

`DEC-000038` a tranché : **la condition exécutable est dérivée, jamais
stockée**. Une chaîne persistée peut diverger du fait qu'elle traduit — on
corrigerait le seuil autécologique sans corriger la règle, et le moteur
appliquerait l'ancienne valeur *en citant la source révisée*. Défaillance
silencieuse produisant une conclusion fausse mais sourcée : le pire cas pour
ce projet.

La condition est donc construite à la lecture, à partir des
`assertion_qualifier` de l'assertion. Ce module ne fait que cela, sans toucher
à la base : il est donc vérifiable sans PostgreSQL.

Une règle incomplète n'est pas complétée par défaut. Elle est **refusée en
nommant ce qui manque** (`ADR-009`) : un seuil dont l'opérateur est absent
n'est pas « probablement inférieur à », il est inutilisable.
"""

from __future__ import annotations

from dataclasses import dataclass

# Opérateurs admis dans une condition dérivée. Volontairement restreint aux
# comparaisons : une règle dérivée d'un seuil ne fait que comparer. Les formes
# plus riches (conjonctions, conditions non numériques) restent portées par
# l'appelant via `ReasoningRequest.regles` — limite assumée par RFC-0028 §4.2.
_OPERATEURS_ADMIS: frozenset[str] = frozenset({"<", "<=", ">", ">=", "==", "!="})

# Clés attendues dans les `assertion_qualifier` d'un seuil.
_CLE_VARIABLE = "variable"
_CLE_OPERATEUR = "operateur"
_CLE_VALEUR = "valeur"
_CLE_ENONCE = "enonce_conclusion"
# Distinct du niveau de preuve : celui-ci qualifie la SOURCE, celui-la dit
# avec quelle force la regle s'applique. Le Diagnostic Engine pose la
# doctrine — « le moteur n'invente aucune table de conversion » (ADR-009) —
# donc la confiance est declaree, jamais deduite du niveau de preuve.
_CLE_CONFIANCE = "niveau_confiance"

_CLES_REQUISES: tuple[str, ...] = (
    _CLE_VARIABLE,
    _CLE_OPERATEUR,
    _CLE_VALEUR,
    _CLE_ENONCE,
    _CLE_CONFIANCE,
)

__all__ = ["DerivationImpossibleError", "condition_derivee", "deriver_regle"]


class DerivationImpossibleError(ValueError):
    """La règle ne peut pas être dérivée, et l'on refuse d'en inventer une.

    Transporte la liste complète de ce qui manque, pour que l'appelant puisse
    le dire à l'utilisateur plutôt que d'échouer sur le premier problème
    rencontré.
    """

    def __init__(self, assertion_id: str, manques: list[str]) -> None:
        self.assertion_id = assertion_id
        self.manques = list(manques)
        super().__init__(f"règle {assertion_id} non dérivable : {', '.join(manques)}")


@dataclass(frozen=True)
class RegleDerivee:
    """Résultat de la dérivation, avant habillage en `RegleInference`."""

    identifiant: str
    condition: str
    enonce_conclusion: str
    variable: str
    niveau_confiance: float


def _nombre_lisible(valeur: str) -> str | None:
    """Rend la valeur telle qu'elle sera écrite dans la condition, ou None.

    Une valeur non numérique n'est pas rejetée par principe — mais elle doit
    être citée, sans quoi la condition dérivée serait syntaxiquement fausse.
    """
    texte = valeur.strip()
    if not texte:
        return None
    try:
        float(texte)
    except ValueError:
        return None
    return texte


def _confiance_lisible(valeur: str) -> float | None:
    """Rend la confiance déclarée, ou None si elle n'est pas exploitable."""
    try:
        confiance = float(valeur.strip())
    except ValueError:
        return None
    return confiance if 0.0 <= confiance <= 1.0 else None


def condition_derivee(variable: str, operateur: str, valeur: str) -> str:
    """Construit la condition exécutable à partir des trois qualificateurs.

    Raises:
        ValueError: si l'opérateur n'est pas admis ou la valeur non numérique.
    """
    if operateur not in _OPERATEURS_ADMIS:
        raise ValueError(
            f"opérateur « {operateur} » non admis — attendus : {sorted(_OPERATEURS_ADMIS)}"
        )
    nombre = _nombre_lisible(valeur)
    if nombre is None:
        raise ValueError(
            f"valeur « {valeur} » non numérique : une condition dérivée compare des nombres"
        )
    return f"{variable} {operateur} {nombre}"


def deriver_regle(
    assertion_id: str,
    qualificateurs: dict[str, str],
    variables_connues: frozenset[str] | None = None,
) -> RegleDerivee:
    """Dérive une règle exécutable depuis les qualificateurs d'une assertion.

    Args:
        assertion_id: identifiant de l'assertion porteuse, cité dans les erreurs.
        qualificateurs: couples `key`/`value` d'`assertion_qualifier`.
        variables_connues: codes du vocabulaire contrôlé. Quand il est fourni,
            une variable hors vocabulaire est refusée.

            C'est ce qui empêche le flottement : sans référentiel commun, « RUM »,
            « réserve utile » et `reserve_utile_mm` désignent la même grandeur
            sans qu'aucun rapprochement soit possible, et une règle échoue
            silencieusement parce que son fait ne porte pas le même nom.

            `None` désactive le contrôle — réservé aux tests de la dérivation
            elle-même, jamais au chemin de production.

    Raises:
        DerivationImpossibleError: si un qualificateur requis manque, si la
            variable est hors vocabulaire, ou si la condition ne peut pas être
            construite. Aucune valeur par défaut n'est substituée.
    """
    manques = [cle for cle in _CLES_REQUISES if not (qualificateurs.get(cle) or "").strip()]
    if manques:
        raise DerivationImpossibleError(
            assertion_id, [f"qualificateur « {cle} » absent" for cle in manques]
        )

    variable = qualificateurs[_CLE_VARIABLE].strip()
    if variables_connues is not None and variable not in variables_connues:
        raise DerivationImpossibleError(
            assertion_id,
            [
                f"variable « {variable} » hors vocabulaire contrôlé : une grandeur "
                "doit porter un code unique, sinon deux écritures de la même "
                "notion ne se rejoignent jamais"
            ],
        )
    try:
        condition = condition_derivee(
            variable,
            qualificateurs[_CLE_OPERATEUR].strip(),
            qualificateurs[_CLE_VALEUR],
        )
    except ValueError as exc:
        raise DerivationImpossibleError(assertion_id, [str(exc)]) from exc

    confiance = _confiance_lisible(qualificateurs[_CLE_CONFIANCE])
    if confiance is None:
        raise DerivationImpossibleError(
            assertion_id,
            [
                f"niveau_confiance « {qualificateurs[_CLE_CONFIANCE]} » invalide : "
                "attendu un nombre entre 0 et 1"
            ],
        )

    return RegleDerivee(
        identifiant=assertion_id,
        condition=condition,
        enonce_conclusion=qualificateurs[_CLE_ENONCE].strip(),
        variable=variable,
        niveau_confiance=confiance,
    )
