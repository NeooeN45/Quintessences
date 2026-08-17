from pathlib import Path

from scripts.audit_engines import MOTEURS, auditer_moteurs


def test_les_quatorze_moteurs_respectent_le_contrat_structurel() -> None:
    racine = Path(__file__).parents[2]
    resultats = auditer_moteurs(racine)

    assert len(resultats) == 14
    assert tuple(resultat.moteur for resultat in resultats) == MOTEURS
    assert all(resultat.valide for resultat in resultats), resultats
