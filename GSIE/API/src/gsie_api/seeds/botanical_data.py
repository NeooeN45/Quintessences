"""Données botaniques de référence pour les essences forestières françaises.

Source principale : Rameau et al. (2008), Flore forestière française,
tomes 1 (Plaines et collines) et 2 (Montagnes), Institut pour le
Développement Forestier (IDF).

Source secondaire : BDNFF (Base de Données Nomenclaturale de la Flore
de France), GBIF Backbone Taxonomy.

Classification familiale : classification classique (Cronquist/Takhtajan)
utilisée par Rameau et al. (2008). Acer est placé en Aceraceae, Tilia en
Tiliaceae, Corylus et Carpinus en Corylaceae, Aesculus en
Hippocastanaceae. Sapindaceae est inclus pour référence APG III.

Données structurées pour ingestion dans la base PostgreSQL GSIE.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Sources de référence
# ---------------------------------------------------------------------------

_SOURCE_RAMEAU: str = "Rameau et al. (2008), Flore forestière française, tome 1 & 2, IDF"
_SOURCE_BDNFF: str = "BDNFF (Base de Données Nomenclaturale de la Flore de France)"
_SOURCE_GBIF: str = "GBIF Backbone Taxonomy"

# ---------------------------------------------------------------------------
# Familles botaniques
# ---------------------------------------------------------------------------

FAMILLES: list[dict[str, str | None]] = [
    {
        "nom_scientifique": "Fagaceae",
        "nom_commun": "Famille du chêne, hêtre et châtaignier",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Pinaceae",
        "nom_commun": "Famille du pin, sapin, épicéa, mélèze et cèdre",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Salicaceae",
        "nom_commun": "Famille du saule et du peuplier",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Betulaceae",
        "nom_commun": "Famille du bouleau et de l'aulne",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Aceraceae",
        "nom_commun": "Famille de l'érable (classification classique)",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Oleaceae",
        "nom_commun": "Famille du frêne et de l'olivier",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Rosaceae",
        "nom_commun": "Famille du merisier, sorbier, aubépine et pommier",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Tiliaceae",
        "nom_commun": "Famille du tilleul (classification classique)",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Ulmaceae",
        "nom_commun": "Famille de l'orme",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Corylaceae",
        "nom_commun": "Famille du charme et du noisetier (classification classique)",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Taxaceae",
        "nom_commun": "Famille de l'if",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Cupressaceae",
        "nom_commun": "Famille du thuya, cyprès et genévrier",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Fabaceae",
        "nom_commun": "Famille du robinier et du genêt",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Juglandaceae",
        "nom_commun": "Famille du noyer",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Hippocastanaceae",
        "nom_commun": "Famille du marronnier (classification classique)",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Platanaceae",
        "nom_commun": "Famille du platane",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Euphorbiaceae",
        "nom_commun": "Famille du mercier et de l'euphorbe",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Berberidaceae",
        "nom_commun": "Famille de l'épine-vinette",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Caprifoliaceae",
        "nom_commun": "Famille du sureau et du chèvrefeuille",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Rhamnaceae",
        "nom_commun": "Famille du nerprun",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Anacardiaceae",
        "nom_commun": "Famille du sumac et du pistachier",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Sapindaceae",
        "nom_commun": "Famille de l'érable et du marronnier (classification APG)",
        "source_reference": _SOURCE_GBIF,
    },
    {
        "nom_scientifique": "Myrtaceae",
        "nom_commun": "Famille du myrte et de l'eucalyptus",
        "source_reference": _SOURCE_GBIF,
    },
    {
        "nom_scientifique": "Aquifoliaceae",
        "nom_commun": "Famille du houx",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Buxaceae",
        "nom_commun": "Famille du buis",
        "source_reference": _SOURCE_RAMEAU,
    },
]

# ---------------------------------------------------------------------------
# Genres botaniques
# ---------------------------------------------------------------------------

GENRES: list[dict[str, str | None]] = [
    # Fagaceae
    {
        "nom_scientifique": "Quercus",
        "famille_nom": "Fagaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Fagus",
        "famille_nom": "Fagaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Castanea",
        "famille_nom": "Fagaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    # Pinaceae
    {
        "nom_scientifique": "Pinus",
        "famille_nom": "Pinaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Picea",
        "famille_nom": "Pinaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Abies",
        "famille_nom": "Pinaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Larix",
        "famille_nom": "Pinaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Pseudotsuga",
        "famille_nom": "Pinaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Cedrus",
        "famille_nom": "Pinaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    # Salicaceae
    {
        "nom_scientifique": "Salix",
        "famille_nom": "Salicaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Populus",
        "famille_nom": "Salicaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    # Betulaceae
    {
        "nom_scientifique": "Betula",
        "famille_nom": "Betulaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Alnus",
        "famille_nom": "Betulaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    # Corylaceae
    {
        "nom_scientifique": "Carpinus",
        "famille_nom": "Corylaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Corylus",
        "famille_nom": "Corylaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    # Aceraceae / Sapindaceae
    {
        "nom_scientifique": "Acer",
        "famille_nom": "Aceraceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    # Oleaceae
    {
        "nom_scientifique": "Fraxinus",
        "famille_nom": "Oleaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    # Tiliaceae
    {
        "nom_scientifique": "Tilia",
        "famille_nom": "Tiliaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    # Ulmaceae
    {
        "nom_scientifique": "Ulmus",
        "famille_nom": "Ulmaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    # Rosaceae
    {
        "nom_scientifique": "Prunus",
        "famille_nom": "Rosaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Sorbus",
        "famille_nom": "Rosaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Crataegus",
        "famille_nom": "Rosaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Malus",
        "famille_nom": "Rosaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Pyrus",
        "famille_nom": "Rosaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    # Fabaceae
    {
        "nom_scientifique": "Robinia",
        "famille_nom": "Fabaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    # Juglandaceae
    {
        "nom_scientifique": "Juglans",
        "famille_nom": "Juglandaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    # Hippocastanaceae
    {
        "nom_scientifique": "Aesculus",
        "famille_nom": "Hippocastanaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    # Platanaceae
    {
        "nom_scientifique": "Platanus",
        "famille_nom": "Platanaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    # Taxaceae
    {
        "nom_scientifique": "Taxus",
        "famille_nom": "Taxaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    # Cupressaceae
    {
        "nom_scientifique": "Thuja",
        "famille_nom": "Cupressaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Cupressus",
        "famille_nom": "Cupressaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    # Aquifoliaceae
    {
        "nom_scientifique": "Ilex",
        "famille_nom": "Aquifoliaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    # Caprifoliaceae
    {
        "nom_scientifique": "Sambucus",
        "famille_nom": "Caprifoliaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    # Rhamnaceae
    {
        "nom_scientifique": "Rhamnus",
        "famille_nom": "Rhamnaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    # Buxaceae
    {
        "nom_scientifique": "Buxus",
        "famille_nom": "Buxaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    # Myrtaceae
    {
        "nom_scientifique": "Eucalyptus",
        "famille_nom": "Myrtaceae",
        "source_reference": _SOURCE_GBIF,
    },
    # Berberidaceae
    {
        "nom_scientifique": "Berberis",
        "famille_nom": "Berberidaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
    # Anacardiaceae
    {
        "nom_scientifique": "Rhus",
        "famille_nom": "Anacardiaceae",
        "source_reference": _SOURCE_RAMEAU,
    },
]

# ---------------------------------------------------------------------------
# Essences forestières
# ---------------------------------------------------------------------------

ESSENCES: list[dict[str, str | None]] = [
    # --- Feuillus principaux -------------------------------------------------
    {
        "nom_scientifique": "Quercus petraea",
        "nom_vernaculaire": "Chêne sessile",
        "genre_nom": "Quercus",
        "categorie_forestiere": "feuillu_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe tempérée, toute France métropolitaine sauf zone méditerranéenne sèche",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Quercus robur",
        "nom_vernaculaire": "Chêne pédonculé",
        "genre_nom": "Quercus",
        "categorie_forestiere": "feuillu_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe tempérée et océanique, toute France métropolitaine",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Quercus pubescens",
        "nom_vernaculaire": "Chêne pubescent",
        "genre_nom": "Quercus",
        "categorie_forestiere": "feuillu_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe méridionale, France méditerranéenne et pré-méditerranéenne",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Quercus rubra",
        "nom_vernaculaire": "Chêne rouge d'Amérique",
        "genre_nom": "Quercus",
        "categorie_forestiere": "feuillu_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Originaire d'Amérique du Nord, introduit et naturalisé en France",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Quercus cerris",
        "nom_vernaculaire": "Chêne chevelu",
        "genre_nom": "Quercus",
        "categorie_forestiere": "feuillu_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe méridionale et centrale, France méridionale et atlantique",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Quercus ilex",
        "nom_vernaculaire": "Chêne vert",
        "genre_nom": "Quercus",
        "categorie_forestiere": "feuillu_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Méditerranée, France méditerranéenne et atlantique sud",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Fagus sylvatica",
        "nom_vernaculaire": "Hêtre commun",
        "genre_nom": "Fagus",
        "categorie_forestiere": "feuillu_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe tempérée et océanique, toute France métropolitaine sauf extrême sud",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Castanea sativa",
        "nom_vernaculaire": "Châtaignier",
        "genre_nom": "Castanea",
        "categorie_forestiere": "feuillu_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe méridionale et atlantique, France occidentale et méridionale",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Fraxinus excelsior",
        "nom_vernaculaire": "Frêne commun",
        "genre_nom": "Fraxinus",
        "categorie_forestiere": "feuillu_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe tempérée, toute France métropolitaine",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Fraxinus angustifolia",
        "nom_vernaculaire": "Frêne à feuilles étroites",
        "genre_nom": "Fraxinus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe méridionale, France méditerranéenne et atlantique sud",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Prunus avium",
        "nom_vernaculaire": "Merisier",
        "genre_nom": "Prunus",
        "categorie_forestiere": "feuillu_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe tempérée, toute France métropolitaine",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Tilia cordata",
        "nom_vernaculaire": "Tilleul à petites feuilles",
        "genre_nom": "Tilia",
        "categorie_forestiere": "feuillu_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe tempérée, toute France métropolitaine",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Tilia platyphyllos",
        "nom_vernaculaire": "Tilleul à grandes feuilles",
        "genre_nom": "Tilia",
        "categorie_forestiere": "feuillu_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe centrale et méridionale, France septentrionale et montagnes",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Acer pseudoplatanus",
        "nom_vernaculaire": "Érable sycomore",
        "genre_nom": "Acer",
        "categorie_forestiere": "feuillu_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe montagnarde et tempérée, toute France métropolitaine",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Acer platanoides",
        "nom_vernaculaire": "Érable plane",
        "genre_nom": "Acer",
        "categorie_forestiere": "feuillu_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe centrale et tempérée, France septentrionale et montagnarde",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Acer campestre",
        "nom_vernaculaire": "Érable champêtre",
        "genre_nom": "Acer",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Microphanérophyte",
        "aire_repartition": "Europe tempérée et méridionale, toute France métropolitaine",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Acer opalus",
        "nom_vernaculaire": "Érable obier",
        "genre_nom": "Acer",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Microphanérophyte",
        "aire_repartition": "Europe méridionale et montagnarde, France méridionale et Alpes",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Ulmus minor",
        "nom_vernaculaire": "Orme champêtre",
        "genre_nom": "Ulmus",
        "categorie_forestiere": "feuillu_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe méridionale et tempérée, toute France métropolitaine",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Ulmus glabra",
        "nom_vernaculaire": "Orme de montagne",
        "genre_nom": "Ulmus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe tempérée et montagnarde, France septentrionale et montagnes",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Ulmus laevis",
        "nom_vernaculaire": "Orme lisse",
        "genre_nom": "Ulmus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe centrale et orientale, France septentrionale et vallées alluviales",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Juglans regia",
        "nom_vernaculaire": "Noyer commun",
        "genre_nom": "Juglans",
        "categorie_forestiere": "feuillu_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Originaire d'Asie, naturalisé en France, toute France métropolitaine",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Robinia pseudoacacia",
        "nom_vernaculaire": "Robinier faux-acacia",
        "genre_nom": "Robinia",
        "categorie_forestiere": "feuillu_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Originaire d'Amérique du Nord, naturalisé en France, particulièrement dans l'ouest et le sud",
        "source_reference": _SOURCE_RAMEAU,
    },
    # --- Conifères principaux ------------------------------------------------
    {
        "nom_scientifique": "Pinus sylvestris",
        "nom_vernaculaire": "Pin sylvestre",
        "genre_nom": "Pinus",
        "categorie_forestiere": "conifere_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Eurasie tempérée, toute France métropolitaine, surtout montagnes et sols acides",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Pinus pinaster",
        "nom_vernaculaire": "Pin maritime",
        "genre_nom": "Pinus",
        "categorie_forestiere": "conifere_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Méditerranée occidentale et atlantique sud, France atlantique et méditerranéenne",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Pinus nigra",
        "nom_vernaculaire": "Pin noir d'Autriche",
        "genre_nom": "Pinus",
        "categorie_forestiere": "conifere_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe méridionale montagnarde, France méridionale et introduit ailleurs",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Pinus nigra subsp. laricio",
        "nom_vernaculaire": "Pin laricio de Corse",
        "genre_nom": "Pinus",
        "categorie_forestiere": "conifere_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Corse, Calabre, introduit en France continentale notamment en Limousin et Auvergne",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Pinus uncinata",
        "nom_vernaculaire": "Pin à crochets",
        "genre_nom": "Pinus",
        "categorie_forestiere": "conifere_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Pyrennées et Alpes occidentales, France montagnarde du sud",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Pinus halepensis",
        "nom_vernaculaire": "Pin d'Alep",
        "genre_nom": "Pinus",
        "categorie_forestiere": "conifere_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Méditerranée, France méditerranéenne",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Pinus pinea",
        "nom_vernaculaire": "Pin parasol",
        "genre_nom": "Pinus",
        "categorie_forestiere": "conifere_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Méditerranée, France méditerranéenne et atlantique sud",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Picea abies",
        "nom_vernaculaire": "Épicéa commun",
        "genre_nom": "Picea",
        "categorie_forestiere": "conifere_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe montagnarde et boréale, France montagnarde (Alpes, Vosges, Massif central)",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Picea sitchensis",
        "nom_vernaculaire": "Épicéa de Sitka",
        "genre_nom": "Picea",
        "categorie_forestiere": "conifere_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Originaire d'Amérique du Nord, introduit en France surtout en Bretagne et Normandie",
        "source_reference": _SOURCE_GBIF,
    },
    {
        "nom_scientifique": "Abies alba",
        "nom_vernaculaire": "Sapin pecté",
        "genre_nom": "Abies",
        "categorie_forestiere": "conifere_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe montagnarde tempérée, France montagnarde (Vosges, Alpes, Pyrénées, Massif central)",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Abies grandis",
        "nom_vernaculaire": "Sapin de Vancouver",
        "genre_nom": "Abies",
        "categorie_forestiere": "conifere_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Originaire d'Amérique du Nord, introduit en France surtout dans le sud-ouest et le Massif central",
        "source_reference": _SOURCE_GBIF,
    },
    {
        "nom_scientifique": "Pseudotsuga menziesii",
        "nom_vernaculaire": "Douglas",
        "genre_nom": "Pseudotsuga",
        "categorie_forestiere": "conifere_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Originaire d'Amérique du Nord, introduit et largement planté en France",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Larix decidua",
        "nom_vernaculaire": "Mélèze d'Europe",
        "genre_nom": "Larix",
        "categorie_forestiere": "conifere_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Alpes et Carpates, France alpine et introduit dans le Massif central",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Larix kaempferi",
        "nom_vernaculaire": "Mélèze du Japon",
        "genre_nom": "Larix",
        "categorie_forestiere": "conifere_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Originaire du Japon, introduit en France surtout dans le Massif central et les Vosges",
        "source_reference": _SOURCE_GBIF,
    },
    {
        "nom_scientifique": "Larix x eurolepis",
        "nom_vernaculaire": "Mélèze hybride",
        "genre_nom": "Larix",
        "categorie_forestiere": "conifere_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Hybride L. decidua x L. kaempferi, planté en France dans le Massif central et les Vosges",
        "source_reference": _SOURCE_GBIF,
    },
    {
        "nom_scientifique": "Cedrus atlantica",
        "nom_vernaculaire": "Cèdre de l'Atlas",
        "genre_nom": "Cedrus",
        "categorie_forestiere": "conifere_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Originaire d'Afrique du Nord (Atlas), introduit en France méditerranéenne et atlantique sud",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Cedrus libani",
        "nom_vernaculaire": "Cèdre du Liban",
        "genre_nom": "Cedrus",
        "categorie_forestiere": "conifere_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Originaire du Liban et montagnes du Proche-Orient, introduit en France méditerranéenne",
        "source_reference": _SOURCE_GBIF,
    },
    # --- Feuillus d'accompagnement -------------------------------------------
    {
        "nom_scientifique": "Carpinus betulus",
        "nom_vernaculaire": "Charme commun",
        "genre_nom": "Carpinus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe tempérée, toute France métropolitaine sauf extrême sud",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Alnus glutinosa",
        "nom_vernaculaire": "Aulne glutineux",
        "genre_nom": "Alnus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe tempérée et océanique, toute France métropolitaine, bords de cours d'eau",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Alnus incana",
        "nom_vernaculaire": "Aulne blanc",
        "genre_nom": "Alnus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe montagnarde et centrale, France montagnarde (Alpes, Pyrénées)",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Alnus cordata",
        "nom_vernaculaire": "Aulne cordé",
        "genre_nom": "Alnus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Originaire d'Italie (Corse et Calabre), introduit en France méditerranéenne",
        "source_reference": _SOURCE_GBIF,
    },
    {
        "nom_scientifique": "Populus nigra",
        "nom_vernaculaire": "Peuplier noir",
        "genre_nom": "Populus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Eurasie tempérée, toute France métropolitaine, forêts alluviales",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Populus alba",
        "nom_vernaculaire": "Peuplier blanc",
        "genre_nom": "Populus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Eurasie tempérée et méridionale, France méditerranéenne et alluviale",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Salix alba",
        "nom_vernaculaire": "Saule blanc",
        "genre_nom": "Salix",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Eurasie tempérée, toute France métropolitaine, bords de cours d'eau",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Sorbus aucuparia",
        "nom_vernaculaire": "Sorbier des oiseleurs",
        "genre_nom": "Sorbus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Microphanérophyte",
        "aire_repartition": "Eurasie tempérée et boréale, France montagnarde et septentrionale",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Sorbus torminalis",
        "nom_vernaculaire": "Alisier torminal",
        "genre_nom": "Sorbus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Microphanérophyte",
        "aire_repartition": "Europe tempérée et méridionale, toute France métropolitaine, surtout chênaies",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Sorbus domestica",
        "nom_vernaculaire": "Cormier",
        "genre_nom": "Sorbus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Microphanérophyte",
        "aire_repartition": "Europe méridionale et tempérée, France méridionale et atlantique",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Sorbus aria",
        "nom_vernaculaire": "Alouchier",
        "genre_nom": "Sorbus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Microphanérophyte",
        "aire_repartition": "Europe tempérée et méridionale montagnarde, France montagnarde et méridionale",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Crataegus monogyna",
        "nom_vernaculaire": "Aubépine monogyne",
        "genre_nom": "Crataegus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Microphanérophyte",
        "aire_repartition": "Europe tempérée et méridionale, toute France métropolitaine, lisières et haies",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Prunus spinosa",
        "nom_vernaculaire": "Prunellier",
        "genre_nom": "Prunus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Nanophanérophyte",
        "aire_repartition": "Europe tempérée et méridionale, toute France métropolitaine, haies et lisières",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Corylus avellana",
        "nom_vernaculaire": "Noisetier",
        "genre_nom": "Corylus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Microphanérophyte",
        "aire_repartition": "Europe tempérée, toute France métropolitaine, sous-bois et lisières",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Ilex aquifolium",
        "nom_vernaculaire": "Houx",
        "genre_nom": "Ilex",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Microphanérophyte",
        "aire_repartition": "Europe tempérée et océanique, toute France métropolitaine, sous-bois",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Sambucus nigra",
        "nom_vernaculaire": "Sureau noir",
        "genre_nom": "Sambucus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Microphanérophyte",
        "aire_repartition": "Europe tempérée, toute France métropolitaine, lisières et clairières",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Rhamnus cathartica",
        "nom_vernaculaire": "Nerprun purgatif",
        "genre_nom": "Rhamnus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Microphanérophyte",
        "aire_repartition": "Europe tempérée et méridionale, France septentrionale et atlantique, haies et lisières",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Buxus sempervirens",
        "nom_vernaculaire": "Buis commun",
        "genre_nom": "Buxus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Nanophanérophyte",
        "aire_repartition": "Europe méridionale montagnarde, France méridionale et montagnarde, sous-bois",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Malus sylvestris",
        "nom_vernaculaire": "Pommier sauvage",
        "genre_nom": "Malus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Microphanérophyte",
        "aire_repartition": "Europe tempérée, toute France métropolitaine, lisières et haies",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Pyrus pyraster",
        "nom_vernaculaire": "Poirier sauvage",
        "genre_nom": "Pyrus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Microphanérophyte",
        "aire_repartition": "Europe tempérée et méridionale, France septentrionale et méridionale, lisières",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Aesculus hippocastanum",
        "nom_vernaculaire": "Marronnier d'Inde",
        "genre_nom": "Aesculus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Originaire des Balkans, introduit en France, parcs et alignements",
        "source_reference": _SOURCE_GBIF,
    },
    {
        "nom_scientifique": "Platanus x acerifolia",
        "nom_vernaculaire": "Platane commun",
        "genre_nom": "Platanus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Hybride P. orientalis x P. occidentalis, introduit en France, alignements et ripisylves",
        "source_reference": _SOURCE_GBIF,
    },
    # --- Conifères d'accompagnement ------------------------------------------
    {
        "nom_scientifique": "Taxus baccata",
        "nom_vernaculaire": "If commun",
        "genre_nom": "Taxus",
        "categorie_forestiere": "conifere_accompagnement",
        "type_biologique": "Microphanérophyte",
        "aire_repartition": "Europe tempérée et méridionale, France montagnarde et méridionale, sous-bois",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Thuja plicata",
        "nom_vernaculaire": "Thuya géant",
        "genre_nom": "Thuja",
        "categorie_forestiere": "conifere_accompagnement",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Originaire d'Amérique du Nord, introduit en France, surtout dans l'ouest et le Massif central",
        "source_reference": _SOURCE_GBIF,
    },
    # --- Espèces pionnières --------------------------------------------------
    {
        "nom_scientifique": "Betula pendula",
        "nom_vernaculaire": "Bouleau verruqueux",
        "genre_nom": "Betula",
        "categorie_forestiere": "pionniere",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Eurasie tempérée et boréale, toute France métropolitaine, sols acides et perturbés",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Betula pubescens",
        "nom_vernaculaire": "Bouleau pubescent",
        "genre_nom": "Betula",
        "categorie_forestiere": "pionniere",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Europe tempérée et boréale, France montagnarde et tourbières, sols hydromorphes acides",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Populus tremula",
        "nom_vernaculaire": "Tremble",
        "genre_nom": "Populus",
        "categorie_forestiere": "pionniere",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Eurasie tempérée et boréale, toute France métropolitaine, sols perturbés et lisières",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Salix caprea",
        "nom_vernaculaire": "Saule marsault",
        "genre_nom": "Salix",
        "categorie_forestiere": "pionniere",
        "type_biologique": "Microphanérophyte",
        "aire_repartition": "Eurasie tempérée, toute France métropolitaine, lisières et coupes forestières",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Salix viminalis",
        "nom_vernaculaire": "Saule des vanniers",
        "genre_nom": "Salix",
        "categorie_forestiere": "pionniere",
        "type_biologique": "Microphanérophyte",
        "aire_repartition": "Europe tempérée, France septentrionale et atlantique, bords de cours d'eau",
        "source_reference": _SOURCE_RAMEAU,
    },
    {
        "nom_scientifique": "Salix cinerea",
        "nom_vernaculaire": "Saule cendré",
        "genre_nom": "Salix",
        "categorie_forestiere": "pionniere",
        "type_biologique": "Microphanérophyte",
        "aire_repartition": "Europe tempérée, toute France métropolitaine, zones humides et marécages",
        "source_reference": _SOURCE_RAMEAU,
    },
    # --- Espèces introduites / exotiques -------------------------------------
    {
        "nom_scientifique": "Eucalyptus gunnii",
        "nom_vernaculaire": "Eucalyptus de Gunn",
        "genre_nom": "Eucalyptus",
        "categorie_forestiere": "feuillu_accompagnement",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Originaire de Tasmanie, introduit en France méditerranéenne et atlantique sud",
        "source_reference": _SOURCE_GBIF,
    },
    {
        "nom_scientifique": "Pinus radiata",
        "nom_vernaculaire": "Pin de Monterey",
        "genre_nom": "Pinus",
        "categorie_forestiere": "conifere_principal",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Originaire de Californie, introduit en France méditerranéenne et atlantique sud",
        "source_reference": _SOURCE_GBIF,
    },
    {
        "nom_scientifique": "Cupressus sempervirens",
        "nom_vernaculaire": "Cyprès toujours vert",
        "genre_nom": "Cupressus",
        "categorie_forestiere": "conifere_accompagnement",
        "type_biologique": "Phanérophyte",
        "aire_repartition": "Originaire de Méditerranée orientale, naturalisé en France méditerranéenne",
        "source_reference": _SOURCE_RAMEAU,
    },
]
