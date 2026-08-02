"""Tests d'intégration — Climate Engine (comportement avec PostgreSQL réel).

Le Climate Engine est stateless en v1 (observation ponctuelle, non
versionnée — voir docstring engine.py). Ces tests valident néanmoins
le comportement du moteur avec une session PostgreSQL réelle via
testcontainers : ils prouvent que l'engine s'exécute correctement dans
un contexte d'intégration (event loop, session DB, cycle de vie des
clients) plutôt qu'avec un stub de transport isolé.

Les appels réseau vers les 6 APIs Météo-France sont mockés via respx
avec des réponses réelles capturées manuellement (voir tests unitaires
`test_climate.py` pour la provenance exacte de chaque échantillon) —
pas de dépendance réseau, pas de donnée inventée (ADR-009).
"""

import gzip
from datetime import datetime
from typing import Any

import pytest
import respx
from httpx import Response
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.engines.climate.dpclim_client import DPClimClient
from gsie_api.engines.climate.engine import ClimateEngine, ClimateEngineError
from gsie_api.engines.climate.meteofrance_client import MeteoFranceClient
from gsie_api.engines.climate.paquet_observation_client import PaquetObservationClient
from gsie_api.engines.climate.schemas import (
    ClimateQuery,
    ClimatologieQuotidienneQuery,
)
from gsie_api.engines.climate.synop_client import SynopClient
from gsie_api.engines.climate.vigilance_client import VigilanceClient
from tests.conftest import requires_docker

pytestmark = requires_docker

# --- Constantes URL (vérifiées réelles, voir docstring de chaque client) ---

_SYNOP_URL_PATTERN = "https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/OBS/SYNOP/"

_DANGER_FEUX_URL = "https://public-api.meteofrance.fr/public/DPMeteoForets/v1/carte/encours"

_VIGILANCE_URL = "https://public-api.meteofrance.fr/public/DPVigilance/v1/cartevigilance/encours"

_PAQUET_OBS_URL = "https://public-api.meteofrance.fr/public/DPPaquetObs/v2/paquet/horaire"

_DPCLIM_COMMANDE_URL = (
    "https://public-api.meteofrance.fr/public/DPClim/v1/commande-station/quotidienne"
)

_DPCLIM_FICHIER_URL = "https://public-api.meteofrance.fr/public/DPClim/v1/commande/fichier"

# --- Réponses réelles capturées (voir tests/unit/test_climate.py) ---

_SYNOP_HEADER = (
    "lat;lon;geo_id_wmo;geo_id_wigos;name;reference_time;insert_time;validity_time;"
    "pmer;tend;cod_tend;dd;ff;t;td;u;vv;ww;w1;w2;n;nbas;hbas;cl;cm;ch;pres;niv_bar;"
    "geop;tend24;tn12;tn24;tx12;tx24;tminsol;sw;tw;raf10;rafper;per;etat_sol;ht_neige;"
    "ssfrai;perssfrai;rr1;rr3;rr6;rr12;rr24;phenspe1;phenspe2;phenspe3;phenspe4;"
    "nnuage1;ctype1;hnuage1;nnuage2;ctype2;hnuage2;nnuage3;ctype3;hnuage3;nnuage4;"
    "ctype4;hnuage4"
)

_SYNOP_ROW_00H = (
    "44.830667;-0.691333;07510;0-20000-0-07510;BORDEAUX-MERIGNAC;"
    "2026-01-01T00:10:06Z;2026-01-01T00:02:31Z;2026-01-01T00:00:00Z;102150;-110;8;"
    "130;2.9;270.45;270.15;98;150;49;;;101;9;30;;;;101530;;;-310;;;;;269.05;;;"
    "4.4;4.4;-10;;0.0;;;0.0;0.0;0.0;0.0;0.2;;;;;0;0;;;;;;;;;;"
)

_SYNOP_ROW_03H = (
    "44.830667;-0.691333;07510;0-20000-0-07510;BORDEAUX-MERIGNAC;"
    "2026-01-01T03:10:05Z;2026-01-01T03:04:16Z;2026-01-01T03:00:00Z;102000;-140;7;"
    "150;2.7;270.95;270.65;98;180;49;;;101;9;30;;;;101390;;;-400;;;;;269.05;;;"
    "4.8;5.0;-10;0;0.0;;;0.0;0.0;0.0;0.0;0.2;;;;;0;0;;;;;;;;;;"
)

_DANGER_FEUX_CSV = (
    "reference_time;dep_code;niveau_j1;niveau_j2;dep_nom\n"
    "2026-07-17T14:50:06Z;01;1;1;Ain\n"
    "2026-07-17T14:50:06Z;02;1;1;Aisne\n"
    "2026-07-17T14:50:06Z;03;1;2;Allier\n"
)

_VIGILANCE_JSON: dict[str, Any] = {
    "product": {
        "update_time": "2026-07-18T04:00:13Z",
        "periods": [
            {
                "echeance": "J",
                "timelaps": {
                    "domain_ids": [
                        {
                            "domain_id": "3010",
                            "max_color_id": 1,
                            "phenomenon_items": [
                                {"phenomenon_id": "9", "phenomenon_max_color_id": 1}
                            ],
                        },
                        {
                            "domain_id": "3410",
                            "max_color_id": 1,
                            "phenomenon_items": [
                                {"phenomenon_id": "9", "phenomenon_max_color_id": 1}
                            ],
                        },
                    ]
                },
            },
            {
                "echeance": "J1",
                "timelaps": {
                    "domain_ids": [
                        {
                            "domain_id": "3010",
                            "max_color_id": 1,
                            "phenomenon_items": [
                                {"phenomenon_id": "9", "phenomenon_max_color_id": 1}
                            ],
                        },
                        {
                            "domain_id": "3410",
                            "max_color_id": 1,
                            "phenomenon_items": [
                                {"phenomenon_id": "9", "phenomenon_max_color_id": 1}
                            ],
                        },
                    ]
                },
            },
        ],
    }
}

_PAQUET_OBS_CSV = (
    "lat;lon;geo_id_insee;reference_time;insert_time;validity_time;t;td;tx;tn;u;ux;"
    "un;dd;ff;dxy;fxy;ddraf;raf;rr1;t_10;t_20;t_50;t_100;vv;etat_sol;sss;n;insolh;"
    "ray_glo01;pres;pmer\n"
    "44.4935;-0.7905;33042001;2026-07-18T09:10:06Z;2026-07-18T09:02:57Z;"
    "2026-07-18T09:00:00Z;299.15;;299.15;296.95;;;;;;;;;;0.0;;;;;;;;;;;;\n"
    "44.4935;-0.7905;33042001;2026-07-18T08:10:06Z;2026-07-18T08:02:03Z;"
    "2026-07-18T08:00:00Z;296.85;;296.95;295.25;;;;;;;;;;0.0;;;;;;;;;;;;\n"
)

_DPCLIM_CSV = (
    "POSTE;DATE;RR;QRR;DRR;QDRR;TN;QTN;HTN;QHTN;TX;QTX;HTX;QHTX;TM;QTM;TMNX;QTMNX;TNSOL;QTNSOL;TN50;QTN50;DG;QDG;TAMPLI;QTAMPLI;TNTXM;QTNTXM;PMERM;QPMERM;PMERMIN;QPMERMIN;FFM;QFFM;FXI;QFXI;DXI;QDXI;HXI;QHXI;FXY;QFXY;DXY;QDXY;HXY;QHXY;FF2M;QFF2M;FXI2;QFXI2;DXI2;QDXI2;HXI2;QHXI2;FXI3S;QFXI3S;DXI3S;QDXI3S;HXI3S;QHXI3S;UN;QUN;HUN;QHUN;UX;QUX;HUX;QHUX;DHUMI40;QDHUMI40;DHUMI80;QDHUMI80;TSVM;QTSVM;DHUMEC;QDHUMEC;UM;QUM;INST;QINST;GLOT;QGLOT;DIFT;QDIFT;DIRT;QDIRT;SIGMA;QSIGMA;INFRART;QINFRART;UV_INDICEX;QUV_INDICEX;NB300;QNB300;BA300;QBA300;NEIG;QNEIG;BROU;QBROU;ORAG;QORAG;GRESIL;QGRESIL;GRELE;QGRELE;ROSEE;QROSEE;VERGLAS;QVERGLAS;SOLNEIGE;QSOLNEIGE;GELEE;QGELEE;FUMEE;QFUMEE;BRUME;QBRUME;ECLAIR;QECLAIR;ETPMON;QETPMON;ETPGRILLE;QETPGRILLE;UV;QUV;TMERMAX;QTMERMAX;TMERMIN;QTMERMIN;HNEIGEF;QHNEIGEF;NEIGETOTX;QNEIGETOTX;NEIGETOT06;QNEIGETOT06\n"
    "33042001;20260601;0,0;1;;;12,4;1;254;9;25,2;1;1402;9;19,6;1;18,80;1;;;;;0;9;12,8;1;18,8;1;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;3,6;9;;;;;;;;;;;;\n"
    "33042001;20260602;3,8;1;;;15,8;1;2325;9;22,5;1;1211;9;18,0;1;19,15;1;;;;;0;9;6,7;1;19,2;1;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;4,0;9;;;;;;;;;;;;\n"
)

_FAKE_API_KEY = "fake-key-for-integration-test"


# --- Helpers ---


def _make_synop_gzip(rows: list[str]) -> bytes:
    """Construit un CSV SYNOP gzippé à partir des lignes données."""
    csv_text = "\n".join([_SYNOP_HEADER, *rows])
    return gzip.compress(csv_text.encode("utf-8"))


def _mock_meteofrance_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mocke get_settings pour tous les clients Météo-France (clé requise)."""
    fake_settings = type("S", (), {"meteofrance_api_key": _FAKE_API_KEY})()
    for module_path in (
        "gsie_api.engines.climate.meteofrance_client.get_settings",
        "gsie_api.engines.climate.vigilance_client.get_settings",
        "gsie_api.engines.climate.paquet_observation_client.get_settings",
        "gsie_api.engines.climate.dpclim_client.get_settings",
    ):
        monkeypatch.setattr(module_path, lambda: fake_settings)


# --- Tests : query_synop (endpoint /climate/query) ---


@respx.mock
async def should_return_latest_observation_when_synop_api_responds(
    db_session: AsyncSession,
) -> None:
    """La dernière observation réelle (03h, pas 00h) doit inclure
    les conversions d'unités."""
    gz_bytes = _make_synop_gzip([_SYNOP_ROW_00H, _SYNOP_ROW_03H])
    respx.get(url__startswith=_SYNOP_URL_PATTERN).mock(return_value=Response(200, content=gz_bytes))

    engine = ClimateEngine(synop_client=SynopClient())
    result = await engine.query(ClimateQuery(station_id="07510"))

    assert result is not None
    assert result.date_observation.hour == 3
    assert result.nom_station == "BORDEAUX-MERIGNAC"
    assert result.temperature_c == pytest.approx(270.95 - 273.15)
    assert result.pression_hpa == pytest.approx(1020.0)
    assert result.humidite_pct == 98.0
    assert result.vent_direction_deg == 150.0
    assert result.vent_vitesse_ms == 2.7


@respx.mock
async def should_return_none_when_station_not_found_in_synop_data(
    db_session: AsyncSession,
) -> None:
    """Une station absente du SYNOP doit retourner None —
    jamais une observation inventée."""
    gz_bytes = _make_synop_gzip([_SYNOP_ROW_00H, _SYNOP_ROW_03H])
    respx.get(url__startswith=_SYNOP_URL_PATTERN).mock(return_value=Response(200, content=gz_bytes))

    engine = ClimateEngine(synop_client=SynopClient())
    result = await engine.query(ClimateQuery(station_id="99999"))

    assert result is None


@respx.mock
async def should_raise_engine_error_when_synop_api_fails(
    db_session: AsyncSession,
) -> None:
    """Une panne HTTP 503 de SYNOP doit lever ClimateEngineError,
    jamais une valeur par défaut."""
    respx.get(url__startswith=_SYNOP_URL_PATTERN).mock(return_value=Response(503))

    engine = ClimateEngine(synop_client=SynopClient())

    with pytest.raises(ClimateEngineError):
        await engine.query(ClimateQuery(station_id="07510"))


# --- Tests : danger_feux (endpoint /climate/danger-feux) ---


@respx.mock
async def should_return_departments_when_danger_feux_api_responds(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Le CSV réel de Météo des forêts doit être parsé en 3 départements
    avec niveaux corrects."""
    _mock_meteofrance_settings(monkeypatch)
    respx.get(_DANGER_FEUX_URL).mock(
        return_value=Response(200, content=_DANGER_FEUX_CSV.encode("utf-8"))
    )

    engine = ClimateEngine(meteofrance_client=MeteoFranceClient())
    resultats = await engine.get_danger_feux()

    assert len(resultats) == 3
    assert resultats[0].dep_code == "01"
    assert resultats[0].dep_nom == "Ain"
    assert resultats[2].niveau_j1 == 1
    assert resultats[2].niveau_j2 == 2


@respx.mock
async def should_raise_engine_error_when_danger_feux_api_fails(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Une panne HTTP 503 de l'API Météo des forêts doit lever ClimateEngineError."""
    _mock_meteofrance_settings(monkeypatch)
    respx.get(_DANGER_FEUX_URL).mock(return_value=Response(503))

    engine = ClimateEngine(meteofrance_client=MeteoFranceClient())

    with pytest.raises(ClimateEngineError):
        await engine.get_danger_feux()


# --- Tests : vigilance (endpoint /climate/vigilance) ---


@respx.mock
async def should_return_bulletins_when_vigilance_api_responds(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """La réponse JSON réelle de l'API Vigilance doit être parsée en 2 échéances (J, J1)."""
    _mock_meteofrance_settings(monkeypatch)
    respx.get(_VIGILANCE_URL).mock(return_value=Response(200, json=_VIGILANCE_JSON))

    engine = ClimateEngine(vigilance_client=VigilanceClient())
    bulletins = await engine.get_vigilance()

    assert len(bulletins) == 2
    assert bulletins[0].echeance == "J"
    assert bulletins[1].echeance == "J1"
    assert len(bulletins[0].domaines) == 2
    assert bulletins[0].domaines[0].domain_id == "3010"
    assert bulletins[0].domaines[0].max_color_id == 1
    assert bulletins[0].domaines[0].phenomenes[0].phenomenon_id == "9"
    assert bulletins[0].domaines[0].phenomenes[0].color_id == 1


@respx.mock
async def should_raise_engine_error_when_vigilance_api_fails(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Une panne HTTP 503 de l'API Vigilance doit lever ClimateEngineError."""
    _mock_meteofrance_settings(monkeypatch)
    respx.get(_VIGILANCE_URL).mock(return_value=Response(503))

    engine = ClimateEngine(vigilance_client=VigilanceClient())

    with pytest.raises(ClimateEngineError):
        await engine.get_vigilance()


# --- Tests : observations_horaires (endpoint /climate/observations-horaires) ---


@respx.mock
async def should_return_observations_when_paquet_obs_api_responds(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Le CSV réel du Package Observations doit être parsé avec conversion Kelvin -> Celsius."""
    _mock_meteofrance_settings(monkeypatch)
    respx.get(url__startswith=_PAQUET_OBS_URL).mock(
        return_value=Response(200, content=_PAQUET_OBS_CSV.encode("utf-8"))
    )

    engine = ClimateEngine(paquet_observation_client=PaquetObservationClient())
    resultats = await engine.get_observations_horaires("33")

    assert len(resultats) == 2
    assert resultats[0].geo_id_insee == "33042001"
    assert resultats[0].temperature_c == pytest.approx(299.15 - 273.15)
    assert resultats[0].precipitations_1h_mm == 0.0
    assert resultats[0].pression_hpa is None
    assert resultats[0].humidite_pct is None


# --- Tests : climatologie_quotidienne (endpoint /climate/climatologie-quotidienne) ---


@respx.mock
async def should_return_daily_observations_when_dpclim_api_responds(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Le flux DPClim (commande + polling + CSV) doit aboutir avec parsing des décimaux français."""
    _mock_meteofrance_settings(monkeypatch)

    respx.get(_DPCLIM_COMMANDE_URL).mock(
        return_value=Response(
            202,
            json={"elaboreProduitAvecDemandeResponse": {"return": "2026024266715"}},
        )
    )
    respx.get(_DPCLIM_FICHIER_URL).mock(
        return_value=Response(201, content=_DPCLIM_CSV.encode("utf-8"))
    )

    engine = ClimateEngine(dpclim_client=DPClimClient(poll_interval_s=0.0))
    resultats = await engine.get_climatologie_quotidienne(
        ClimatologieQuotidienneQuery(
            id_station="33042001",
            date_deb_periode=datetime(2026, 6, 1),
            date_fin_periode=datetime(2026, 6, 10),
        )
    )

    assert len(resultats) == 2
    premiere = resultats[0]
    assert premiere.id_station == "33042001"
    assert premiere.date.isoformat() == "2026-06-01"
    assert premiere.rr_mm == pytest.approx(0.0)
    assert premiere.tn_c == pytest.approx(12.4)
    assert premiere.tx_c == pytest.approx(25.2)
    assert premiere.tm_c == pytest.approx(19.6)


# --- Tests : list_stations_climatologie (endpoint /climate/climatologie-stations) ---


@respx.mock
async def should_return_stations_when_dpclim_list_stations_responds(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """La liste des stations DPClim d'un département doit être retournée telle quelle."""
    _mock_meteofrance_settings(monkeypatch)

    stations_payload: list[dict[str, Any]] = [
        {"id_station": "33042001", "nom": "BELIN-BELIET", "poste_ouvert": True},
        {"id_station": "33005001", "nom": "BORDEAUX-MERIGNAC", "poste_ouvert": True},
    ]
    respx.get(
        url__startswith=("https://public-api.meteofrance.fr/public/DPClim/v1/liste-stations")
    ).mock(return_value=Response(200, json=stations_payload))

    engine = ClimateEngine(dpclim_client=DPClimClient(poll_interval_s=0.0))
    stations = await engine.list_stations_climatologie("33")

    assert len(stations) == 2
    assert stations[0]["id_station"] == "33042001"
    assert stations[1]["nom"] == "BORDEAUX-MERIGNAC"
