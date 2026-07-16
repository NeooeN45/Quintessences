"""Données écosystémiques de référence pour la France métropolitaine.

Trois jeux de données :
1. HABITATS_NATURA2000 — habitats forestiers et associés (codes EUR28 / Natura 2000)
2. STATIONS_FORESTIERES — types de stations forestières françaises (INRAE/ONF)
3. GROUPES_ECOLOGIQUES — groupes écologiques bio-indicateurs (ECOPHYTO / Dupouey et al.)

Sources principales :
- EUR28 : European Union Interpretation Manual (Commission européenne, 2013)
- Cahiers d'habitats : MNHN (1997-2002), « Habitats forestiers de la France métropolitaine »
- Catalogues des types de stations : INRAE / ONF (par région forestière)
- ECOPHYTO : base de bio-indication floristique (INRAE), Dupouey et al. (2011)

Ces données alimentent les tables ``ecosystem_habitats``, ``ecosystem_stations``
et ``ecosystem_groupes_ecologiques`` via ``gsie_api.seeds.run_seeds``.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 1. Habitats Natura 2000 / EUR28
# ---------------------------------------------------------------------------

HABITATS_NATURA2000: list[dict[str, str | None]] = [
    {
        "code_eur28": "41.2",
        "nom_habitat": "Chênaies-charmaies à Stellaire",
        "description": (
            "Forêts de plaine à dominance de Quercus robur et Carpinus betulus, "
            "développées sur sols mésotrophes à eutrophes, frais à humides. "
            "Sous-étage riche en Stellaria holostea, Anemone nemorosa, Primula elatior. "
            "Typiques des vallées et bas de versants en Europe tempérée."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "41.3",
        "nom_habitat": "Chênaies-frênaies à Primevère",
        "description": (
            "Forêts de plaine et collines à Quercus robur et Fraxinus excelsior, "
            "sur sols carbonatés ou marnes, neutres à légèrement basiques. "
            "Strate herbacée à Primula elatior, Mercurialis perennis, Corydalis solida. "
            "Sols bruns calcaires ou rendzines."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "41.5",
        "nom_habitat": "Chênaies acidiphiles",
        "description": (
            "Forêts à Quercus petraea et Quercus robur sur sols acides, "
            "pauvres en nutriments (pH < 5). Strate arbustive à Sorbus aucuparia, "
            "Ilex aquifolium. Strate herbacée à Deschampsia flexuosa, "
            "Vaccinium myrtillus, Pteridium aquilinum, Calluna vulgaris."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": None,
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "41.7",
        "nom_habitat": "Chênaies thermophiles et xérophiles",
        "description": (
            "Forêts à Quercus pubescens sur sols calcaires secs du sud de la France. "
            "Strate arbustive riche : Buxus sempervirens, Cornus sanguinea, "
            "Viburnum lantana. Strate herbacée à Sesleria caerulea, "
            "Teucrium chamaedrys, Carex flacca."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "41.8",
        "nom_habitat": "Hêtraies acidiphiles",
        "description": (
            "Forêts à Fagus sylvatica sur sols acides (pH 4-5), "
            "podzoliques ou bruns acides. Strate herbacée pauvre : "
            "Deschampsia flexuosa, Vaccinium myrtillus, Luzula luzuloides, "
            "Melampyrum pratense. Présentes en étage montagnard."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "41.9",
        "nom_habitat": "Hêtraies neutrophiles",
        "description": (
            "Forêts à Fagus sylvatica sur sols neutres à légèrement acides, "
            "bruns forestiers bien drainés. Strate herbacée diversifiée : "
            "Anemone nemorosa, Mercurialis perennis, Allium ursinum, "
            "Asperula odorata (= Galium odoratum), Lamium galeobdolon."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "41.11",
        "nom_habitat": "Hêtraies montagnardes à Aspérule",
        "description": (
            "Hêtraies de l'étage montagnard (800-1400 m) à Fagus sylvatica, "
            "sur sols bruns neutrophiles à mésotrophes. Strate herbacée à "
            "Galium odoratum (Asperula odorata), Dentaria pentaphyllos, "
            "Cardamine bulbifera, Actaea spicata."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "41.12",
        "nom_habitat": "Hêtraies submontagnardes à Millet",
        "description": (
            "Hêtraies de l'étage submontagnard (500-900 m) à Fagus sylvatica, "
            "sur sols acides à légèrement acides. Strate herbacée à "
            "Milium effusum, Luzula pilosa, Oxalis acetosella, "
            "Prenanthes purpurea. Transition avec les chênaies-hêtraies."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": None,
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "42.1",
        "nom_habitat": "Pinèdes subméditerranéennes de pins noirs",
        "description": (
            "Forêts à Pinus nigra subsp. salzmannii des étages supraméditerranéens, "
            "sur sols calcaires secs et rocailleux. Strate arbustive à "
            "Buxus sempervirens, Juniperus communis, Amelanchier ovalis. "
            "Présentes dans les Cévennes, Pyrénées orientales, Alpes du Sud."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "42.2",
        "nom_habitat": "Pinèdes pyrénéennes de pins sylvestres",
        "description": (
            "Forêts à Pinus sylvestris des étages montagnards à subalpins "
            "des Pyrénées, sur sols acides ou calcaires. Strate arbustive à "
            "Rhododendron ferrugineum (étage subalpin), Juniperus communis, "
            "Vaccinium myrtillus. Strate herbacée à Deschampsia flexuosa."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "42.3",
        "nom_habitat": "Pinèdes (sub)méditerranéennes de pins mésogéens",
        "description": (
            "Forêts à Pinus pinaster et Pinus halepensis du pourtour méditerranéen, "
            "sur sols acides (pin maritime) ou calcaires (pin d'Alep). "
            "Strate arbustive à Erica arborea, Arbutus unedo, Cistus monspeliensis. "
            "Sols secs, soumis au feu."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "42.4",
        "nom_habitat": "Pinèdes alpino-carpatiques de pins sylvestres",
        "description": (
            "Forêts à Pinus sylvestris de l'étage subalpin des Alpes internes, "
            "sur sols acides à podsoliques, climat continental. Strate arbustive à "
            "Vaccinium myrtillus, Vaccinium vitis-idaea, Juniperus communis. "
            "Strate herbacée à Deschampsia flexuosa, Melampyrum pratense."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "42.A",
        "nom_habitat": "Sapinières-pessières montagnardes",
        "description": (
            "Forêts à Abies alba et Picea abies de l'étage montagnard "
            "(800-1500 m), sur sols acides à neutres, climat humide. "
            "Strate herbacée à Oxalis acetosella, Luzula luzuloides, "
            "Vaccinium myrtillus, Homogyne alpina. Typiques des Vosges, Jura, Alpes."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "42.B",
        "nom_habitat": "Pessières subalpines",
        "description": (
            "Forêts à Picea abies de l'étage subalpin (1500-2000 m), "
            "climat continental froid et enneigé. Strate arbustive à "
            "Rhododendron ferrugineum, Sorbus aucuparia. Strate herbacée à "
            "Vaccinium myrtillus, Vaccinium vitis-idaea, Deschampsia flexuosa, "
            "Homogyne alpina."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "43.0",
        "nom_habitat": "Forêts de mélèzes et cèdres",
        "description": (
            "Forêts à Larix decidua de l'étage subalpin des Alpes internes, "
            "sur sols acides à neutres, climat continental. Strate herbacée à "
            "Vaccinium myrtillus, Rhododendron ferrugineum, Calamagrostis villosa. "
            "Mélèzes pionniers en altitude, souvent en mosaïque avec les pessières."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "44.1",
        "nom_habitat": "Forêts de saules riveraines",
        "description": (
            "Forêts pionnières à Salix alba, Salix fragilis, Salix viminalis "
            "des berges et grèves alluviales, sur sols inondables périodiquement. "
            "Strate herbacée à Phalaris arundinacea, Urtica dioica, "
            "Impatiens glandulifera. Habitats dynamiques liés aux crues."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "44.3",
        "nom_habitat": "Forêts de frênes et d'aulnes",
        "description": (
            "Forêts alluviales à Alnus glutinosa et Fraxinus excelsior "
            "des fonds de vallées et bordures de cours d'eau, sur sols "
            "hydromorphes engorgés. Strate herbacée à Carex remota, "
            "Circaea lutetiana, Filipendula ulmaria, Cirsium oleraceum."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "44.9",
        "nom_habitat": "Forêts de chênes et d'ormes riveraines",
        "description": (
            "Forêts mixtes alluviales à Quercus robur, Ulmus minor, "
            "Fraxinus excelsior des grandes vallées européennes, sur sols "
            "alluviaux profonds et frais. Strate herbacée à Allium ursinum, "
            "Circaea lutetiana, Stachys sylvatica, Carex sylvatica."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "9120",
        "nom_habitat": "Hêtraies atlantiques acidiphiles",
        "description": (
            "Hêtraies de l'Europe atlantique à Fagus sylvatica sur sols acides, "
            "climat océanique humide. Strate herbacée à Deschampsia flexuosa, "
            "Vaccinium myrtillus, Lonicera periclymenum, Ilex aquifolium. "
            "Habitat Natura 2000 (code 9120), présent en Normandie, Bretagne, Pays de la Loire."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "9130",
        "nom_habitat": "Hêtraies de l'Asperulo-Fagetum",
        "description": (
            "Hêtraies neutrophiles à Fagus sylvatica sur sols mésotrophes, "
            "du collinéen au montagnard. Strate herbacée à Galium odoratum, "
            "Anemone nemorosa, Mercurialis perennis, Melica uniflora. "
            "Habitat Natura 2000 (code 9130), largement réparti en France."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "9150",
        "nom_habitat": "Hêtraies calcicoles médio-européennes",
        "description": (
            "Hêtraies à Fagus sylvatica sur sols calcaires (rendzines, sols bruns "
            "calcaires), pH > 6. Strate herbacée à Sesleria caerulea, "
            "Carex digitata, Cephalanthera damasonium, Neottia nidus-avis. "
            "Habitat Natura 2000 (code 9150), présent en Jura, Alpes calcaires, Causse."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "9160",
        "nom_habitat": "Chênaies-frênaies à Stellaire",
        "description": (
            "Forêts à Quercus robur et Fraxinus excelsior sur sols hydromorphes "
            "argileux, frais à humides. Strate herbacée à Stellaria holostea, "
            "Circaea lutetiana, Carex sylvatica, Primula elatior. "
            "Habitat Natura 2000 (code 9160), présent en Île-de-France, Centre, Bourgogne."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "9190",
        "nom_habitat": "Vieilles chênaies acidiphiles",
        "description": (
            "Vieilles chênaies à Quercus robur sur sols acides, pauvres et humides, "
            "souvent en mosaïque avec des landes à Calluna. Strate arbustive à "
            "Betula pendula, Sorbus aucuparia. Strate herbacée à Deschampsia flexuosa, "
            "Molinia caerulea, Calluna vulgaris, Erica cinerea. "
            "Habitat Natura 2000 (code 9190)."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "91E0",
        "nom_habitat": "Forêts alluviales à Alnus et Fraxinus",
        "description": (
            "Forêts alluviales résiduelles à Alnus glutinosa et Fraxinus excelsior, "
            "bordant les cours d'eau et occupant les fonds de vallées. "
            "Strate herbacée à Carex remota, Circaea lutetiana, Filipendula ulmaria, "
            "Equisetum telmateia. Habitat Natura 2000 prioritaire (code 91E0*)."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "prioritaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "91F0",
        "nom_habitat": "Forêts mixtes à Quercus robur, Ulmus, Fraxinus",
        "description": (
            "Forêts mixtes de grandes vallées à Quercus robur, Ulmus laevis, "
            "Ulmus minor, Fraxinus excelsior, sur sols alluviaux profonds et fertiles. "
            "Strate herbacée à Allium ursinum, Stachys sylvatica, Carex sylvatica, "
            "Circaea lutetiana. Habitat Natura 2000 (code 91F0)."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "9230",
        "nom_habitat": "Chênaies galicio-portugaises à Quercus robur",
        "description": (
            "Chênaies atlantiques à Quercus robur du sud-ouest de la France, "
            "climat océanique hyperatlantique. Strate arbustive à Arbutus unedo, "
            "Erica arborea, Viburnum tinus. Strate herbacée à Pteridium aquilinum, "
            "Dactylis glomerata. Habitat Natura 2000 (code 9230), Landes, Pays Basque."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "9410",
        "nom_habitat": "Forêts acidiphiles à Picea des étages montagnard à alpin",
        "description": (
            "Pessières à Picea abies des étages montagnard à subalpin, "
            "sur sols acides à podsoliques, climat continental. Strate arbustive à "
            "Vaccinium myrtillus, Vaccinium vitis-idaea. Strate herbacée à "
            "Deschampsia flexuosa, Luzula luzuloides, Homogyne alpina. "
            "Habitat Natura 2000 (code 9410)."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "9430",
        "nom_habitat": "Forêts subalpines et montagnardes à Acer et Rumex",
        "description": (
            "Forêts de l'étage subalpin à Acer pseudoplatanus, Sorbus aucuparia, "
            "Ulmus glabra, sur éboulis et pentes fraîches des Alpes. "
            "Strate herbacée à Rumex arifolius (= Rumex alpestris), "
            "Adenostyles alliariae, Cicerbita alpina, Senecio cacaliaster. "
            "Habitat Natura 2000 (code 9430)."
        ),
        "categorie": "Forêts",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "4030",
        "nom_habitat": "Landes sèches européennes",
        "description": (
            "Landes à Calluna vulgaris et Erica cinerea sur sols acides et secs, "
            "dynamique de déforestation et pâturage. Strate arbustive à "
            "Ulex europaeus, Cytisus scoparius, Genista pilosa. "
            "Habitat Natura 2000 (code 4030), largement réparti en France."
        ),
        "categorie": "Landes",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "6210",
        "nom_habitat": "Pelouses sèches semi-naturelles et faciès d'embuissonnement",
        "description": (
            "Pelouses calcicoles à Bromus erectus et Brachypodium pinnatum, "
            "sur sols calcaires superficiels. Strate herbacée riche : "
            "Sesleria caerulea, Globularia bisnagarica, Anacamptis pyramidalis. "
            "Habitat Natura 2000 (code 6210), prioritaire sur substrat calcaire."
        ),
        "categorie": "Pelouses",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "7110",
        "nom_habitat": "Tourbières hautes actives",
        "description": (
            "Tourbières ombrotrophes à Sphagnum spp., climat océanique humide. "
            "Strate herbacée à Erica tetralix, Andromeda polifolia, "
            "Vaccinium oxycoccos, Drosera rotundifolia. Habitat Natura 2000 "
            "prioritaire (code 7110*), présent en Bretagne, Massif Central, Vosges."
        ),
        "categorie": "Tourbières",
        "interet_patrimonial": "prioritaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "6510",
        "nom_habitat": "Prairies maigres de fauche de basse altitude",
        "description": (
            "Prairies de fauche à Arrhenatherum elatius et Trisetum flavescens, "
            "sur sols mésotrophes, fauchées annuellement. Strate herbacée riche : "
            "Centaurea jacea, Leucanthemum vulgare, Trifolium pratense, "
            "Ranunculus acris. Habitat Natura 2000 (code 6510)."
        ),
        "categorie": "Prairies",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
    {
        "code_eur28": "4090",
        "nom_habitat": "Landes oroméditerranéennes endémiques à genêts épineux",
        "description": (
            "Landes à Genista lobelii et Echinospartum horridum des étages "
            "montagnard à subalpin des montagnes méditerranéennes. "
            "Habitat Natura 2000 (code 4090), présent dans les Pyrénées et Cévennes."
        ),
        "categorie": "Landes",
        "interet_patrimonial": "communautaire",
        "source_reference": "EUR28 / Cahiers d'habitats (MNHN, 1997-2002)",
    },
]


# ---------------------------------------------------------------------------
# 2. Stations forestières
# ---------------------------------------------------------------------------

STATIONS_FORESTIERES: list[dict[str, object]] = [
    {
        "code_station": "ST-LIM-01",
        "nom_station": "Chênaie acidiphile limousine",
        "description": (
            "Station sur sols acides (pH 4-5), bruns acides à podzoliques, "
            "sur granite ou gneiss. Végétation indicatrice : Deschampsia flexuosa, "
            "Vaccinium myrtillus, Calluna vulgaris, Pteridium aquilinum. "
            "Fertilité faible à modérée, drainage libre."
        ),
        "region_forestiere": "Limousin",
        "departements": ["23", "87", "19"],
        "altitude_min": 200,
        "altitude_max": 600,
        "ph_typique": {"min": 4.0, "max": 5.0, "mediane": 4.5},
        "rum_typique": {"min": 2.0, "max": 6.0, "mediane": 4.0},
        "essences_adaptees": [
            "Quercus petraea",
            "Quercus robur",
            "Castanea sativa",
            "Pinus pinaster",
        ],
        "essences_potentielles": ["Betula pendula", "Sorbus aucuparia", "Pinus sylvestris"],
        "source_reference": "Catalogue des types de stations — Limousin (INRAE/ONF, 1995)",
    },
    {
        "code_station": "ST-LIM-02",
        "nom_station": "Hêtraie-chênaie neutrophile limousine",
        "description": (
            "Station sur sols bruns neutres à mésotrophes, bas de versants "
            "et fonds de vallons. Végétation indicatrice : Anemone nemorosa, "
            "Mercurialis perennis, Lamium galeobdolon, Oxalis acetosella. "
            "Fertilité modérée à bonne, drainage libre à modéré."
        ),
        "region_forestiere": "Limousin",
        "departements": ["23", "87", "19"],
        "altitude_min": 250,
        "altitude_max": 700,
        "ph_typique": {"min": 5.5, "max": 6.5, "mediane": 6.0},
        "rum_typique": {"min": 4.0, "max": 10.0, "mediane": 7.0},
        "essences_adaptees": [
            "Fagus sylvatica",
            "Quercus petraea",
            "Fraxinus excelsior",
            "Carpinus betulus",
        ],
        "essences_potentielles": ["Tilia cordata", "Acer pseudoplatanus", "Prunus avium"],
        "source_reference": "Catalogue des types de stations — Limousin (INRAE/ONF, 1995)",
    },
    {
        "code_station": "ST-PYR-01",
        "nom_station": "Hêtraie pyrénéenne montagnarde",
        "description": (
            "Station de l'étage montagnard des Pyrénées, sur sols acides à neutres, "
            "climat montagnard humide. Végétation indicatrice : Luzula sylvatica, "
            "Oxalis acetosella, Vaccinium myrtillus, Prenanthes purpurea. "
            "Fertilité modérée, drainage libre, enneigement hivernal marqué."
        ),
        "region_forestiere": "Pyrénées",
        "departements": ["64", "65", "31", "09", "66"],
        "altitude_min": 800,
        "altitude_max": 1600,
        "ph_typique": {"min": 4.5, "max": 6.0, "mediane": 5.2},
        "rum_typique": {"min": 3.0, "max": 8.0, "mediane": 5.5},
        "essences_adaptees": ["Fagus sylvatica", "Abies alba", "Quercus petraea"],
        "essences_potentielles": ["Pinus sylvestris", "Sorbus aucuparia", "Acer pseudoplatanus"],
        "source_reference": "Catalogue des types de stations — Pyrénées (INRAE/ONF, 1997)",
    },
    {
        "code_station": "ST-PYR-02",
        "nom_station": "Sapinière-pessière subalpine pyrénéenne",
        "description": (
            "Station de l'étage subalpin des Pyrénées, sur sols acides, "
            "climat froid et humide. Végétation indicatrice : Rhododendron ferrugineum, "
            "Vaccinium myrtillus, Deschampsia flexuosa, Homogyne alpina. "
            "Fertilité faible, drainage libre, enneigement prolongé."
        ),
        "region_forestiere": "Pyrénées",
        "departements": ["64", "65", "31", "66"],
        "altitude_min": 1500,
        "altitude_max": 2200,
        "ph_typique": {"min": 4.0, "max": 5.5, "mediane": 4.8},
        "rum_typique": {"min": 2.0, "max": 6.0, "mediane": 4.0},
        "essences_adaptees": ["Abies alba", "Picea abies", "Pinus uncinata"],
        "essences_potentielles": ["Larix decidua", "Sorbus aucuparia"],
        "source_reference": "Catalogue des types de stations — Pyrénées (INRAE/ONF, 1997)",
    },
    {
        "code_station": "ST-VOS-01",
        "nom_station": "Sapinière vosgienne acidiphile",
        "description": (
            "Station de l'étage montagnard des Vosges, sur sols acides (pH 4-5), "
            "grès vosgien, climat océanique de montagne. Végétation indicatrice : "
            "Vaccinium myrtillus, Deschampsia flexuosa, Luzula luzuloides, "
            "Oxalis acetosella. Fertilité faible à modérée, drainage libre."
        ),
        "region_forestiere": "Vosges",
        "departements": ["67", "68", "88"],
        "altitude_min": 500,
        "altitude_max": 1100,
        "ph_typique": {"min": 4.0, "max": 5.0, "mediane": 4.5},
        "rum_typique": {"min": 2.0, "max": 6.0, "mediane": 4.0},
        "essences_adaptees": ["Abies alba", "Picea abies", "Fagus sylvatica"],
        "essences_potentielles": ["Quercus petraea", "Sorbus aucuparia", "Larix decidua"],
        "source_reference": "Catalogue des types de stations — Vosges (INRAE/ONF, 1993)",
    },
    {
        "code_station": "ST-VOS-02",
        "nom_station": "Érablaie de ravine vosgienne",
        "description": (
            "Station de fonds de vallon et ravines fraîches, sur éboulis grossiers, "
            "sols carbonatés locaux. Végétation indicatrice : Rumex arifolius, "
            "Adenostyles alliariae, Cicerbita alpina, Actaea spicata. "
            "Fertilité bonne, fraîcheur édaphique élevée."
        ),
        "region_forestiere": "Vosges",
        "departements": ["67", "68"],
        "altitude_min": 400,
        "altitude_max": 900,
        "ph_typique": {"min": 5.5, "max": 7.0, "mediane": 6.3},
        "rum_typique": {"min": 5.0, "max": 12.0, "mediane": 8.0},
        "essences_adaptees": [
            "Acer pseudoplatanus",
            "Fraxinus excelsior",
            "Ulmus glabra",
            "Tilia platyphyllos",
        ],
        "essences_potentielles": ["Fagus sylvatica", "Prunus avium", "Sorbus aucuparia"],
        "source_reference": "Catalogue des types de stations — Vosges (INRAE/ONF, 1993)",
    },
    {
        "code_station": "ST-MC-01",
        "nom_station": "Hêtraie-sapinière du Massif Central",
        "description": (
            "Station de l'étage montagnard du Massif Central, sur sols acides, "
            "climat montagnard à influence océanique. Végétation indicatrice : "
            "Vaccinium myrtillus, Deschampsia flexuosa, Luzula luzuloides, "
            "Oxalis acetosella. Fertilité modérée, drainage libre."
        ),
        "region_forestiere": "Massif Central",
        "departements": ["63", "15", "43", "48", "12"],
        "altitude_min": 700,
        "altitude_max": 1400,
        "ph_typique": {"min": 4.5, "max": 5.5, "mediane": 5.0},
        "rum_typique": {"min": 3.0, "max": 7.0, "mediane": 5.0},
        "essences_adaptees": ["Fagus sylvatica", "Abies alba", "Picea abies"],
        "essences_potentielles": ["Quercus petraea", "Sorbus aucuparia", "Larix decidua"],
        "source_reference": "Catalogue des types de stations — Massif Central (INRAE/ONF, 1996)",
    },
    {
        "code_station": "ST-MC-02",
        "nom_station": "Chênaie pubescente cévenole",
        "description": (
            "Station de l'étage supraméditerranéen des Cévennes, sur sols calcaires "
            "ou schisteux secs. Végétation indicatrice : Sesleria caerulea, "
            "Teucrium chamaedrys, Buxus sempervirens, Carex flacca. "
            "Fertilité faible, xérophile, drainage rapide."
        ),
        "region_forestiere": "Massif Central",
        "departements": ["48", "30", "12", "15"],
        "altitude_min": 300,
        "altitude_max": 900,
        "ph_typique": {"min": 6.0, "max": 7.5, "mediane": 6.8},
        "rum_typique": {"min": 1.0, "max": 4.0, "mediane": 2.5},
        "essences_adaptees": ["Quercus pubescens", "Pinus nigra", "Pinus sylvestris"],
        "essences_potentielles": ["Sorbus domestica", "Acer monspessulanum", "Cotinus coggygria"],
        "source_reference": "Catalogue des types de stations — Massif Central (INRAE/ONF, 1996)",
    },
    {
        "code_station": "ST-ALP-01",
        "nom_station": "Pessière subalpine alpine interne",
        "description": (
            "Station de l'étage subalpin des Alpes internes, sur sols acides, "
            "climat continental froid. Végétation indicatrice : Vaccinium myrtillus, "
            "Vaccinium vitis-idaea, Rhododendron ferrugineum, Homogyne alpina. "
            "Fertilité faible, enneigement prolongé, drainage libre."
        ),
        "region_forestiere": "Alpes",
        "departements": ["73", "74", "38", "05"],
        "altitude_min": 1500,
        "altitude_max": 2100,
        "ph_typique": {"min": 4.0, "max": 5.5, "mediane": 4.8},
        "rum_typique": {"min": 2.0, "max": 6.0, "mediane": 4.0},
        "essences_adaptees": ["Picea abies", "Larix decidua", "Pinus cembra"],
        "essences_potentielles": ["Sorbus aucuparia", "Pinus mugo"],
        "source_reference": "Catalogue des types de stations — Alpes (INRAE/ONF, 1998)",
    },
    {
        "code_station": "ST-ALP-02",
        "nom_station": "Hêtraie calcicole du Jura méridional",
        "description": (
            "Station de l'étage montagnard du Jura, sur rendzines et sols bruns "
            "calcaires, pH > 6. Végétation indicatrice : Sesleria caerulea, "
            "Carex digitata, Mercurialis perennis, Cephalanthera damasonium. "
            "Fertilité modérée, drainage libre à superficiel."
        ),
        "region_forestiere": "Jura",
        "departements": ["39", "25", "01"],
        "altitude_min": 600,
        "altitude_max": 1300,
        "ph_typique": {"min": 6.0, "max": 7.5, "mediane": 6.8},
        "rum_typique": {"min": 2.0, "max": 6.0, "mediane": 4.0},
        "essences_adaptees": ["Fagus sylvatica", "Abies alba", "Quercus petraea"],
        "essences_potentielles": ["Picea abies", "Acer pseudoplatanus", "Tilia platyphyllos"],
        "source_reference": "Catalogue des types de stations — Jura (INRAE/ONF, 1994)",
    },
    {
        "code_station": "ST-JUR-01",
        "nom_station": "Érablaie-tillaire de pentes jurassiennes",
        "description": (
            "Station de pentes fortes et éboulis du Jura, sur sols carbonatés "
            "squelettiques. Végétation indicatrice : Sesleria caerulea, "
            "Carex montana, Calamagrostis varia, Valeriana montana. "
            "Fertilité variable, xérophile, drainage très rapide."
        ),
        "region_forestiere": "Jura",
        "departements": ["39", "25"],
        "altitude_min": 500,
        "altitude_max": 1200,
        "ph_typique": {"min": 6.5, "max": 8.0, "mediane": 7.2},
        "rum_typique": {"min": 1.0, "max": 3.0, "mediane": 2.0},
        "essences_adaptees": [
            "Acer pseudoplatanus",
            "Tilia platyphyllos",
            "Fraxinus excelsior",
            "Ulmus glabra",
        ],
        "essences_potentielles": ["Fagus sylvatica", "Sorbus aria"],
        "source_reference": "Catalogue des types de stations — Jura (INRAE/ONF, 1994)",
    },
    {
        "code_station": "ST-BRE-01",
        "nom_station": "Chênaie atlantique acidiphile bretonne",
        "description": (
            "Station de plaine bretonne sur sols acides (pH 4-5), climat océanique "
            "hyperatlantique. Végétation indicatrice : Deschampsia flexuosa, "
            "Calluna vulgaris, Erica cinerea, Pteridium aquilinum, Lonicera periclymenum. "
            "Fertilité faible, drainage libre à modéré."
        ),
        "region_forestiere": "Bretagne",
        "departements": ["22", "29", "35", "56"],
        "altitude_min": 0,
        "altitude_max": 300,
        "ph_typique": {"min": 4.0, "max": 5.0, "mediane": 4.5},
        "rum_typique": {"min": 2.0, "max": 6.0, "mediane": 4.0},
        "essences_adaptees": [
            "Quercus robur",
            "Castanea sativa",
            "Pinus pinaster",
            "Betula pendula",
        ],
        "essences_potentielles": ["Fagus sylvatica", "Sorbus aucuparia", "Ilex aquifolium"],
        "source_reference": "Catalogue des types de stations — Bretagne (INRAE/ONF, 1992)",
    },
    {
        "code_station": "ST-LAN-01",
        "nom_station": "Pinède mésophile landaise",
        "description": (
            "Station du massif landais sur sols podzoliques acides (pH 4-5), "
            "nappe phréatique superficielle en hiver. Végétation indicatrice : "
            "Molinia caerulea, Erica cinerea, Calluna vulgaris, Ulex europaeus. "
            "Fertilité très faible, hydromorphie hivernale."
        ),
        "region_forestiere": "Landes",
        "departements": ["40", "33", "64"],
        "altitude_min": 0,
        "altitude_max": 100,
        "ph_typique": {"min": 4.0, "max": 5.0, "mediane": 4.5},
        "rum_typique": {"min": 1.0, "max": 5.0, "mediane": 3.0},
        "essences_adaptees": ["Pinus pinaster", "Quercus robur", "Betula pendula"],
        "essences_potentielles": ["Pinus radiata", "Eucalyptus gunnii"],
        "source_reference": "Catalogue des types de stations — Landes de Gascogne (INRAE/ONF, 1990)",
    },
    {
        "code_station": "ST-MED-01",
        "nom_station": "Chênaie verte méditerranéenne xérophile",
        "description": (
            "Station de l'étage mésoméditerranéen, sur sols calcaires secs, "
            "climat méditerranéen. Végétation indicatrice : Quercus ilex, "
            "Phillyrea latifolia, Pistacia terebinthus, Smilax aspera, "
            "Ruscus aculeatus. Fertilité faible, xérophile, drainage rapide."
        ),
        "region_forestiere": "Méditerranée",
        "departements": ["13", "83", "84", "06", "34", "30"],
        "altitude_min": 0,
        "altitude_max": 600,
        "ph_typique": {"min": 6.0, "max": 8.0, "mediane": 7.0},
        "rum_typique": {"min": 0.5, "max": 3.0, "mediane": 1.5},
        "essences_adaptees": [
            "Quercus ilex",
            "Quercus pubescens",
            "Pinus halepensis",
            "Pinus pinea",
        ],
        "essences_potentielles": ["Arbutus unedo", "Phillyrea angustifolia", "Juniperus oxycedrus"],
        "source_reference": "Catalogue des types de stations — Provence méditerranéenne (INRAE/ONF, 1999)",
    },
    {
        "code_station": "ST-MED-02",
        "nom_station": "Pinède de pin d'Alep sur calcaire sec",
        "description": (
            "Station de l'étage thermoméditerranéen, sur sols calcaires squelettiques, "
            "climat méditerranéen sec. Végétation indicatrice : Rosmarinus officinalis, "
            "Thymus vulgaris, Cistus albidus, Brachypodium retusum, Erica multiflora. "
            "Fertilité très faible, xérophile, sensibilité incendie élevée."
        ),
        "region_forestiere": "Méditerranée",
        "departements": ["13", "83", "84", "34", "11"],
        "altitude_min": 0,
        "altitude_max": 500,
        "ph_typique": {"min": 6.5, "max": 8.0, "mediane": 7.3},
        "rum_typique": {"min": 0.5, "max": 2.0, "mediane": 1.0},
        "essences_adaptees": ["Pinus halepensis", "Quercus coccifera", "Quercus ilex"],
        "essences_potentielles": ["Juniperus phoenicea", "Pistacia lentiscus"],
        "source_reference": "Catalogue des types de stations — Provence méditerranéenne (INRAE/ONF, 1999)",
    },
    {
        "code_station": "ST-IDF-01",
        "nom_station": "Chênaie-frênaie de plaine d'Île-de-France",
        "description": (
            "Station de plaine sur sols bruns lessivés à mésotrophes, "
            "limons profonds. Végétation indicatrice : Stellaria holostea, "
            "Anemone nemorosa, Carex sylvatica, Primula elatior, Circaea lutetiana. "
            "Fertilité modérée à bonne, drainage modéré."
        ),
        "region_forestiere": "Île-de-France",
        "departements": ["75", "77", "78", "91", "95", "94"],
        "altitude_min": 50,
        "altitude_max": 200,
        "ph_typique": {"min": 5.5, "max": 6.5, "mediane": 6.0},
        "rum_typique": {"min": 4.0, "max": 10.0, "mediane": 7.0},
        "essences_adaptees": [
            "Quercus robur",
            "Fraxinus excelsior",
            "Carpinus betulus",
            "Fagus sylvatica",
        ],
        "essences_potentielles": [
            "Tilia cordata",
            "Acer campestre",
            "Prunus avium",
            "Sorbus torminalis",
        ],
        "source_reference": "Catalogue des types de stations — Île-de-France (INRAE/ONF, 1991)",
    },
    {
        "code_station": "ST-IDF-02",
        "nom_station": "Aulnaie-frênaie riveraine d'Île-de-France",
        "description": (
            "Station alluviale de fonds de vallons et bordures de cours d'eau, "
            "sols hydromorphes engorgés. Végétation indicatrice : Carex remota, "
            "Circaea lutetiana, Filipendula ulmaria, Cirsium oleraceum, Urtica dioica. "
            "Fertilité bonne, hydromorphie permanente à saisonnière."
        ),
        "region_forestiere": "Île-de-France",
        "departements": ["77", "78", "91", "95"],
        "altitude_min": 40,
        "altitude_max": 180,
        "ph_typique": {"min": 6.0, "max": 7.5, "mediane": 6.8},
        "rum_typique": {"min": 6.0, "max": 15.0, "mediane": 10.0},
        "essences_adaptees": [
            "Alnus glutinosa",
            "Fraxinus excelsior",
            "Salix alba",
            "Populus nigra",
        ],
        "essences_potentielles": ["Quercus robur", "Ulmus minor", "Prunus padus"],
        "source_reference": "Catalogue des types de stations — Île-de-France (INRAE/ONF, 1991)",
    },
]


# ---------------------------------------------------------------------------
# 3. Groupes écologiques (bio-indicateurs)
# ---------------------------------------------------------------------------

GROUPES_ECOLOGIQUES: list[dict[str, object]] = [
    {
        "nom_groupe": "Groupe des acidiphiles",
        "description": (
            "Espèces indicatrices de sols acides (pH < 5), pauvres en bases "
            "et en nutriments. Présentes sur podzols, sols bruns acides, "
            "arenosols. Forte valeur bio-indicatrice pour le pH et la trophie."
        ),
        "indicateur": "pH",
        "valeurs_indicatrices": {
            "ph_min": 3.5,
            "ph_max": 5.0,
            "niveau": "acide",
            "fiabilite": "élevée",
        },
        "especes_caracteristiques": [
            "Calluna vulgaris",
            "Deschampsia flexuosa",
            "Vaccinium myrtillus",
            "Vaccinium vitis-idaea",
            "Erica cinerea",
            "Luzula luzuloides",
            "Pteridium aquilinum",
            "Melampyrum pratense",
        ],
        "source_reference": "ECOPHYTO (INRAE) — Dupouey et al. (2011)",
    },
    {
        "nom_groupe": "Groupe des neutrophiles",
        "description": (
            "Espèces indicatrices de sols neutres (pH 5.5-7), mésotrophes à "
            "eutrophes, bruns forestiers bien structurés. Indicatrices de "
            "fertilité modérée à bonne et de pH équilibré."
        ),
        "indicateur": "pH",
        "valeurs_indicatrices": {
            "ph_min": 5.5,
            "ph_max": 7.0,
            "niveau": "neutre",
            "fiabilite": "élevée",
        },
        "especes_caracteristiques": [
            "Mercurialis perennis",
            "Anemone nemorosa",
            "Lamium galeobdolon",
            "Allium ursinum",
            "Galium odoratum",
            "Carex sylvatica",
            "Stellaria holostea",
            "Primula elatior",
        ],
        "source_reference": "ECOPHYTO (INRAE) — Dupouey et al. (2011)",
    },
    {
        "nom_groupe": "Groupe des calcicoles",
        "description": (
            "Espèces indicatrices de sols calcaires (pH > 6.5), riches en "
            "carbonates, rendzines et sols bruns calcaires. Indicatrices "
            "d'alcalinité et de sécheresse édaphique fréquente."
        ),
        "indicateur": "pH",
        "valeurs_indicatrices": {
            "ph_min": 6.5,
            "ph_max": 8.0,
            "niveau": "basique",
            "fiabilite": "élevée",
        },
        "especes_caracteristiques": [
            "Sesleria caerulea",
            "Carex digitata",
            "Teucrium chamaedrys",
            "Buxus sempervirens",
            "Cephalanthera damasonium",
            "Carex flacca",
            "Globularia bisnagarica",
            "Helleborus foetidus",
        ],
        "source_reference": "ECOPHYTO (INRAE) — Dupouey et al. (2011)",
    },
    {
        "nom_groupe": "Groupe des hygrophytes",
        "description": (
            "Espèces indicatrices de sols humides à engorgés, hydromorphes, "
            "fonds de vallons et bordures de cours d'eau. Indicatrices "
            "d'excès d'eau permanent ou saisonnier."
        ),
        "indicateur": "humidité",
        "valeurs_indicatrices": {
            "rum_min": 6.0,
            "rum_max": 15.0,
            "niveau": "humide",
            "fiabilite": "élevée",
        },
        "especes_caracteristiques": [
            "Molinia caerulea",
            "Juncus effusus",
            "Carex remota",
            "Filipendula ulmaria",
            "Cirsium oleraceum",
            "Equisetum telmateia",
            "Caltha palustris",
            "Scirpus sylvaticus",
        ],
        "source_reference": "ECOPHYTO (INRAE) — Dupouey et al. (2011)",
    },
    {
        "nom_groupe": "Groupe des xérophiles",
        "description": (
            "Espèces indicatrices de sols secs, à faible réserve en eau, "
            "drainage rapide, sécheresse estivale marquée. Indicatrices "
            "de déficit hydrique édaphique."
        ),
        "indicateur": "humidité",
        "valeurs_indicatrices": {
            "rum_min": 0.5,
            "rum_max": 3.0,
            "niveau": "sec",
            "fiabilite": "élevée",
        },
        "especes_caracteristiques": [
            "Sesleria caerulea",
            "Teucrium chamaedrys",
            "Carex flacca",
            "Brachypodium retusum",
            "Rosmarinus officinalis",
            "Thymus vulgaris",
            "Erica multiflora",
            "Stipa capillata",
        ],
        "source_reference": "ECOPHYTO (INRAE) — Dupouey et al. (2011)",
    },
    {
        "nom_groupe": "Groupe des mésophiles",
        "description": (
            "Espèces indicatrices de sols à humidité moyenne, équilibrés, "
            "drainage libre sans excès. Indicatrices de conditions "
            "édaphiques modérées, ni trop sèches ni trop humides."
        ),
        "indicateur": "humidité",
        "valeurs_indicatrices": {
            "rum_min": 3.0,
            "rum_max": 6.0,
            "niveau": "moyen",
            "fiabilite": "modérée",
        },
        "especes_caracteristiques": [
            "Anemone nemorosa",
            "Oxalis acetosella",
            "Luzula pilosa",
            "Milium effusum",
            "Prenanthes purpurea",
            "Melica uniflora",
            "Festuca heterophylla",
            "Brachypodium sylvaticum",
        ],
        "source_reference": "ECOPHYTO (INRAE) — Dupouey et al. (2011)",
    },
    {
        "nom_groupe": "Groupe des nitratophiles",
        "description": (
            "Espèces indicatrices de sols riches en nitrates, eutrophes, "
            "souvent perturbés ou enrichis par apport organique. "
            "Indicatrices d'eutrophisation et de richesse trophique élevée."
        ),
        "indicateur": "trophie",
        "valeurs_indicatrices": {"niveau": "eutrophe", "nitrates": "élevé", "fiabilite": "élevée"},
        "especes_caracteristiques": [
            "Urtica dioica",
            "Galium aparine",
            "Sambucus nigra",
            "Geranium robertianum",
            "Alliaria petiolata",
            "Chelidonium majus",
            "Anthriscus sylvestris",
            "Lamium album",
        ],
        "source_reference": "ECOPHYTO (INRAE) — Dupouey et al. (2011)",
    },
    {
        "nom_groupe": "Groupe des oligotrophes",
        "description": (
            "Espèces indicatrices de sols pauvres en nutriments, "
            "oligotrophes, acides et peu fertiles. Indicatrices de "
            "déficit trophique et de faible fertilité."
        ),
        "indicateur": "trophie",
        "valeurs_indicatrices": {
            "niveau": "oligotrophe",
            "nitrates": "très faible",
            "fiabilite": "élevée",
        },
        "especes_caracteristiques": [
            "Calluna vulgaris",
            "Erica cinerea",
            "Deschampsia flexuosa",
            "Vaccinium myrtillus",
            "Nardus stricta",
            "Danthonia decumbens",
            "Galium saxatile",
            "Potentilla erecta",
        ],
        "source_reference": "ECOPHYTO (INRAE) — Dupouey et al. (2011)",
    },
    {
        "nom_groupe": "Groupe des mésotrophes",
        "description": (
            "Espèces indicatrices de sols à fertilité modérée, "
            "mésotrophes, ni pauvres ni riches. Indicatrices de "
            "conditions trophiques intermédiaires et équilibrées."
        ),
        "indicateur": "trophie",
        "valeurs_indicatrices": {
            "niveau": "mésotrophe",
            "nitrates": "modéré",
            "fiabilite": "modérée",
        },
        "especes_caracteristiques": [
            "Anemone nemorosa",
            "Mercurialis perennis",
            "Stellaria holostea",
            "Carex sylvatica",
            "Primula elatior",
            "Lamium galeobdolon",
            "Narcissus pseudonarcissus",
            "Polygonatum multiflorum",
        ],
        "source_reference": "ECOPHYTO (INRAE) — Dupouey et al. (2011)",
    },
    {
        "nom_groupe": "Groupe des espèces de climat continental",
        "description": (
            "Espèces indicatrices d'un climat continental, à forte amplitude "
            "thermique, hivers froids et étés chauds. Indicatrices de "
            "continentalité marquée (Alpes internes, Jura)."
        ),
        "indicateur": "climat",
        "valeurs_indicatrices": {
            "amplitude_thermique": "élevée",
            "continentalite": "forte",
            "fiabilite": "modérée",
        },
        "especes_caracteristiques": [
            "Larix decidua",
            "Pinus cembra",
            "Vaccinium vitis-idaea",
            "Rhododendron ferrugineum",
            "Homogyne alpina",
            "Calamagrostis villosa",
            "Loiseleuria procumbens",
            "Empetrum nigrum",
        ],
        "source_reference": "ECOPHYTO (INRAE) — Dupouey et al. (2011)",
    },
    {
        "nom_groupe": "Groupe des espèces de climat océanique",
        "description": (
            "Espèces indicatrices d'un climat océanique, à faible amplitude "
            "thermique, hivers doux et étés frais, humidité atmosphérique élevée. "
            "Indicatrices d'océanité marquée (Bretagne, Normandie, Pays Basque)."
        ),
        "indicateur": "climat",
        "valeurs_indicatrices": {
            "amplitude_thermique": "faible",
            "oceanite": "forte",
            "fiabilite": "modérée",
        },
        "especes_caracteristiques": [
            "Lonicera periclymenum",
            "Ilex aquifolium",
            "Arbutus unedo",
            "Erica arborea",
            "Daboecia cantabrica",
            "Ulex europaeus",
            "Sarothamnus scoparius",
            "Cyclamen hederifolium",
        ],
        "source_reference": "ECOPHYTO (INRAE) — Dupouey et al. (2011)",
    },
    {
        "nom_groupe": "Groupe des espèces de climat méditerranéen",
        "description": (
            "Espèces indicatrices d'un climat méditerranéen, à sécheresse "
            "estivale marquée et hivers doux. Indicatrices de thermie "
            "élevée et de xérothermie (Provence, Languedoc, Corse)."
        ),
        "indicateur": "climat",
        "valeurs_indicatrices": {"thermite": "élevée", "xerothmie": "forte", "fiabilite": "élevée"},
        "especes_caracteristiques": [
            "Quercus ilex",
            "Arbutus unedo",
            "Phillyrea latifolia",
            "Pistacia terebinthus",
            "Smilax aspera",
            "Ruscus aculeatus",
            "Cistus monspeliensis",
            "Erica multiflora",
        ],
        "source_reference": "ECOPHYTO (INRAE) — Dupouey et al. (2011)",
    },
    {
        "nom_groupe": "Groupe des sciaphiles",
        "description": (
            "Espèces indicatrices de faible luminosité, adaptées à l'ombre "
            "sous couvert forestier dense. Indicatrices d'ombrage élevé "
            "et de fermeture du couvert."
        ),
        "indicateur": "lumière",
        "valeurs_indicatrices": {
            "luminosite": "faible",
            "ombrage": "élevé",
            "fiabilite": "modérée",
        },
        "especes_caracteristiques": [
            "Oxalis acetosella",
            "Lamium galeobdolon",
            "Galium odoratum",
            "Mercurialis perennis",
            "Circaea lutetiana",
            "Carex sylvatica",
            "Asperula odorata",
            "Neottia nidus-avis",
        ],
        "source_reference": "ECOPHYTO (INRAE) — Dupouey et al. (2011)",
    },
    {
        "nom_groupe": "Groupe des héliophiles",
        "description": (
            "Espèces indicatrices de forte luminosité, adaptées au plein soleil, "
            "clairières, lisières et milieux ouverts. Indicatrices de luminosité "
            "élevée et d'ouverture du couvert."
        ),
        "indicateur": "lumière",
        "valeurs_indicatrices": {
            "luminosite": "élevée",
            "ombrage": "faible",
            "fiabilite": "modérée",
        },
        "especes_caracteristiques": [
            "Calluna vulgaris",
            "Erica cinerea",
            "Ulex europaeus",
            "Cytisus scoparius",
            "Pteridium aquilinum",
            "Brachypodium pinnatum",
            "Bromus erectus",
            "Trifolium pratense",
        ],
        "source_reference": "ECOPHYTO (INRAE) — Dupouey et al. (2011)",
    },
    {
        "nom_groupe": "Groupe des espèces de sols sableux",
        "description": (
            "Espèces indicatrices de sols à texture sableuse, filtrants, "
            "à faible réserve en eau et en nutriments. Indicatrices de "
            "texture grossière et de drainage rapide."
        ),
        "indicateur": "texture_sol",
        "valeurs_indicatrices": {
            "texture": "sableuse",
            "drainage": "rapide",
            "fiabilite": "modérée",
        },
        "especes_caracteristiques": [
            "Deschampsia flexuosa",
            "Calluna vulgaris",
            "Erica cinerea",
            "Corynephorus canescens",
            "Jasione montana",
            "Scleranthus annuus",
            "Teesdalia nudicaulis",
            "Spergula morisonii",
        ],
        "source_reference": "ECOPHYTO (INRAE) — Dupouey et al. (2011)",
    },
    {
        "nom_groupe": "Groupe des espèces de sols argileux",
        "description": (
            "Espèces indicatrices de sols à texture argileuse, lourds, "
            "à forte rétention en eau, hydromorphie fréquente. "
            "Indicatrices de texture fine et de drainage lent."
        ),
        "indicateur": "texture_sol",
        "valeurs_indicatrices": {
            "texture": "argileuse",
            "drainage": "lent",
            "fiabilite": "modérée",
        },
        "especes_caracteristiques": [
            "Molinia caerulea",
            "Juncus effusus",
            "Carex flacca",
            "Filipendula ulmaria",
            "Cirsium oleraceum",
            "Caltha palustris",
            "Ranunculus repens",
            "Glyceria fluitans",
        ],
        "source_reference": "ECOPHYTO (INRAE) — Dupouey et al. (2011)",
    },
    {
        "nom_groupe": "Groupe des espèces de sols limoneux",
        "description": (
            "Espèces indicatrices de sols à texture limoneuse, équilibrés, "
            "à bonne réserve en eau et nutriments. Indicatrices de texture "
            "moyenne et de drainage modéré, fertilité généralement bonne."
        ),
        "indicateur": "texture_sol",
        "valeurs_indicatrices": {
            "texture": "limoneuse",
            "drainage": "modéré",
            "fiabilite": "modérée",
        },
        "especes_caracteristiques": [
            "Anemone nemorosa",
            "Stellaria holostea",
            "Carex sylvatica",
            "Mercurialis perennis",
            "Lamium galeobdolon",
            "Narcissus pseudonarcissus",
            "Hyacinthoides non-scripta",
            "Polygonatum multiflorum",
        ],
        "source_reference": "ECOPHYTO (INRAE) — Dupouey et al. (2011)",
    },
]
