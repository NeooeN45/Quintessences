"""Vocabulaire contrôlé des grandeurs mesurables — CON-005, DEC-000038.

Une grandeur n'entre au vocabulaire que si une source fait autorité pour la
définir. Ces tests verrouillent la source citée : la modifier doit être un acte
délibéré, pas une dérive.
"""

from __future__ import annotations

from gsie_api.engines.evidence.schemas import SourceType
from gsie_api.seeds.variables_mesurables_data import (
    noms_de_faits_par_code,
    source_reserve_utile_inrae,
    variables_mesurables,
)


class TestSourceFaitAutorite:
    """Aucune grandeur sans source citée — sinon elle est citable sans être vérifiable."""

    def test_chaque_variable_cite_sa_source(self) -> None:
        for variable in variables_mesurables():
            assert variable.source.reference, f"{variable.code} : référence vide"
            assert variable.source.auteur, f"{variable.code} : auteur absent"

    def test_la_source_de_la_reserve_utile_est_figee(self) -> None:
        """Changer de source change le sens de la grandeur — acte délibéré.

        Le DOI est ce qui rend la définition vérifiable après coup : sans lui,
        « réserve utile » redevient un mot dont chacun a sa version.
        """
        source = source_reserve_utile_inrae()

        # La référence entière est verrouillée, pas seulement le DOI : c'est
        # elle qui sera citée dans une conclusion. Un titre altéré ferait
        # citer un document qui n'est pas celui consulté.
        assert source.reference == (
            "Réservoir utile des sols de la France métropolitaine, version 2.0, "
            "INRAE, doi:10.15454/9IRARJ"
        )
        assert source.type_source is SourceType.referentiel_officiel
        assert source.version_source == "2.0"

    def test_le_niveau_institutionnel_est_declare(self) -> None:
        """Un référentiel officiel plafonne à B, jamais A sans convergence."""
        assert source_reserve_utile_inrae().type_source is SourceType.referentiel_officiel


class TestVocabulaireExploitable:
    def test_les_codes_sont_uniques(self) -> None:
        codes = [variable.code for variable in variables_mesurables()]

        assert len(codes) == len(set(codes))

    def test_chaque_variable_porte_une_unite(self) -> None:
        """Comparer deux grandeurs sans unité est une faute silencieuse."""
        for variable in variables_mesurables():
            assert variable.unite, f"{variable.code} : unité absente"

    def test_la_reserve_utile_est_au_vocabulaire(self) -> None:
        """Variable du périmètre pilote acté par DEC-000038."""
        assert noms_de_faits_par_code()["reserve_utile_mm"] == "pedologie_reserve_utile_mm"

    def test_la_definition_distingue_le_plafond_de_l_accessible(self) -> None:
        """La confusion des deux produirait une sous-détection de contrainte.

        Sommer sans distinguer surestime l'eau disponible, donc le diagnostic
        conclurait « pas de contrainte » là où elle existe — l'erreur la plus
        coûteuse, parce qu'elle est silencieuse.
        """
        reserve = next(v for v in variables_mesurables() if v.code == "reserve_utile_mm")

        assert "accessible" in reserve.definition
        assert "dérivée" in reserve.definition


class TestFamillesDisjointes:
    """Seules les grandeurs quantitatives peuvent produire une condition."""

    def test_aucune_variable_qualitative_n_est_admise(self) -> None:
        """Rameau 2008 donne des préférences, pas des seuils — non dérivables."""
        qualitatives = {
            "tolerance_secheresse",
            "exigence_lumiere",
            "preference_edaphique",
            "tolerance_engorgement_racinaire",
        }

        assert set(noms_de_faits_par_code()).isdisjoint(qualitatives)
