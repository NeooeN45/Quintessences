"""Data Registry GSIE.

Le paquet reste volontairement sans réexport : chaque consommateur importe le
module de contrat dont il dépend. Cette règle empêche qu'un import léger comme
``gsie_api.data.lifecycle`` charge les adapters, le resolver, la base ou le
service de ressources et recrée un cycle d'import.
"""
