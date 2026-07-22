"""Tests unitaires — Climate Engine (SYNOP Météo-France).

Les appels réseau sont mockés (monkeypatch de SynopClient) avec des
lignes CSV réelles capturées manuellement le 2026-07-17 (station
07510 Bordeaux-Mérignac, 00h et 03h UTC du 2026-01-01) — pas de
donnée inventée.
"""

import gzip
from datetime import datetime

import httpx
import pytest

from gsie_api.engines.climate.dpclim_client import DPClimClient
from gsie_api.engines.climate.engine import ClimateEngine, ClimateEngineError
from gsie_api.engines.climate.meteofrance_client import MeteoFranceClient
from gsie_api.engines.climate.paquet_observation_client import PaquetObservationClient
from gsie_api.engines.climate.schemas import ClimateQuery, ClimatologieQuotidienneQuery
from gsie_api.engines.climate.synop_client import SynopClient, SynopClientError
from gsie_api.engines.climate.vigilance_client import VigilanceClient

# Réponse réelle capturée le 2026-07-18 (API Package Observations,
# /public/DPPaquetObs/v2/paquet/horaire?id-departement=33&format=csv),
# 2 premières lignes (station 33042001 BELIN-BELIET).
_PAQUET_OBSERVATION_CSV = (
    "lat;lon;geo_id_insee;reference_time;insert_time;validity_time;t;td;tx;tn;u;ux;un;dd;ff;"
    "dxy;fxy;ddraf;raf;rr1;t_10;t_20;t_50;t_100;vv;etat_sol;sss;n;insolh;ray_glo01;pres;pmer\n"
    "44.4935;-0.7905;33042001;2026-07-18T09:10:06Z;2026-07-18T09:02:57Z;2026-07-18T09:00:00Z;"
    "299.15;;299.15;296.95;;;;;;;;;;0.0;;;;;;;;;;;;\n"
    "44.4935;-0.7905;33042001;2026-07-18T08:10:06Z;2026-07-18T08:02:03Z;2026-07-18T08:00:00Z;"
    "296.85;;296.95;295.25;;;;;;;;;;0.0;;;;;;;;;;;;\n"
)

# Réponse réelle capturée le 2026-07-18T04:00:13Z (API Vigilance,
# /public/DPVigilance/v1/cartevigilance/encours), réduite à 2 échéances
# (J, J1) x 2 domaines (3010, 3410) — structure intacte, données réelles.
_VIGILANCE_JSON = {
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

# Réponse réelle capturée le 2026-07-18 (API DPClim, station 33042001
# BELIN-BELIET, produit quotidien juin 2026) — en-tête complet (133
# colonnes, jeu variable selon la station) + 2 lignes de données réelles.
_DPCLIM_CSV = (
    "POSTE;DATE;RR;QRR;DRR;QDRR;TN;QTN;HTN;QHTN;TX;QTX;HTX;QHTX;TM;QTM;TMNX;QTMNX;TNSOL;QTNSOL;TN50;QTN50;DG;QDG;TAMPLI;QTAMPLI;TNTXM;QTNTXM;PMERM;QPMERM;PMERMIN;QPMERMIN;FFM;QFFM;FXI;QFXI;DXI;QDXI;HXI;QHXI;FXY;QFXY;DXY;QDXY;HXY;QHXY;FF2M;QFF2M;FXI2;QFXI2;DXI2;QDXI2;HXI2;QHXI2;FXI3S;QFXI3S;DXI3S;QDXI3S;HXI3S;QHXI3S;UN;QUN;HUN;QHUN;UX;QUX;HUX;QHUX;DHUMI40;QDHUMI40;DHUMI80;QDHUMI80;TSVM;QTSVM;DHUMEC;QDHUMEC;UM;QUM;INST;QINST;GLOT;QGLOT;DIFT;QDIFT;DIRT;QDIRT;SIGMA;QSIGMA;INFRART;QINFRART;UV_INDICEX;QUV_INDICEX;NB300;QNB300;BA300;QBA300;NEIG;QNEIG;BROU;QBROU;ORAG;QORAG;GRESIL;QGRESIL;GRELE;QGRELE;ROSEE;QROSEE;VERGLAS;QVERGLAS;SOLNEIGE;QSOLNEIGE;GELEE;QGELEE;FUMEE;QFUMEE;BRUME;QBRUME;ECLAIR;QECLAIR;ETPMON;QETPMON;ETPGRILLE;QETPGRILLE;UV;QUV;TMERMAX;QTMERMAX;TMERMIN;QTMERMIN;HNEIGEF;QHNEIGEF;NEIGETOTX;QNEIGETOTX;NEIGETOT06;QNEIGETOT06\n"
    "33042001;20260601;0,0;1;;;12,4;1;254;9;25,2;1;1402;9;19,6;1;18,80;1;;;;;0;9;12,8;1;18,8;1;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;3,6;9;;;;;;;;;;;;\n"
    "33042001;20260602;3,8;1;;;15,8;1;2325;9;22,5;1;1211;9;18,0;1;19,15;1;;;;;0;9;6,7;1;19,2;1;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;4,0;9;;;;;;;;;;;;\n"
)

# Réponse réelle capturée le 2026-07-18 (API Météo des forêts,
# /public/DPMeteoForets/v1/carte/encours), 3 premières lignes du CSV.
_DANGER_FEUX_CSV = (
    "reference_time;dep_code;niveau_j1;niveau_j2;dep_nom\n"
    "2026-07-17T14:50:06Z;01;1;1;Ain\n"
    "2026-07-17T14:50:06Z;02;1;1;Aisne\n"
    "2026-07-17T14:50:06Z;03;1;2;Allier\n"
)

_HEADER = (
    "lat;lon;geo_id_wmo;geo_id_wigos;name;reference_time;insert_time;validity_time;pmer;tend;"
    "cod_tend;dd;ff;t;td;u;vv;ww;w1;w2;n;nbas;hbas;cl;cm;ch;pres;niv_bar;geop;tend24;tn12;tn24;"
    "tx12;tx24;tminsol;sw;tw;raf10;rafper;per;etat_sol;ht_neige;ssfrai;perssfrai;rr1;rr3;rr6;"
    "rr12;rr24;phenspe1;phenspe2;phenspe3;phenspe4;nnuage1;ctype1;hnuage1;nnuage2;ctype2;"
    "hnuage2;nnuage3;ctype3;hnuage3;nnuage4;ctype4;hnuage4"
)
# Ligne réelle 00h UTC (2026-01-01) — station 07510 Bordeaux-Mérignac.
_ROW_00H = (
    "44.830667;-0.691333;07510;0-20000-0-07510;BORDEAUX-MERIGNAC;2026-01-01T00:10:06Z;"
    "2026-01-01T00:02:31Z;2026-01-01T00:00:00Z;102150;-110;8;130;2.9;270.45;270.15;98;150;49;;;"
    "101;9;30;;;;101530;;;-310;;;;;269.05;;;4.4;4.4;-10;;0.0;;;0.0;0.0;0.0;0.0;0.2;;;;;0;0;;;;;;;;;;"
)
# Ligne réelle 03h UTC (2026-01-01) — la plus récente des deux, doit être retenue.
_ROW_03H = (
    "44.830667;-0.691333;07510;0-20000-0-07510;BORDEAUX-MERIGNAC;2026-01-01T03:10:05Z;"
    "2026-01-01T03:04:16Z;2026-01-01T03:00:00Z;102000;-140;7;150;2.7;270.95;270.65;98;180;49;;;"
    "101;9;30;;;;101390;;;-400;;;;;269.05;;;4.8;5.0;-10;0;0.0;;;0.0;0.0;0.0;0.0;0.2;;;;;0;0;;;;;;;;;;"
)


def _make_gzipped_csv(rows: list[str]) -> bytes:
    csv_text = "\n".join([_HEADER, *rows])
    return gzip.compress(csv_text.encode("utf-8"))


def _patch_transport(monkeypatch: pytest.MonkeyPatch, status_code: int, content: bytes) -> None:
    """Force tout httpx.AsyncClient créé pendant le test à répondre via ce transport mocké."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, content=content, request=request)

    transport = httpx.MockTransport(handler)
    original_init = httpx.AsyncClient.__init__

    def _patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", _patched_init)


@pytest.fixture
def engine(monkeypatch: pytest.MonkeyPatch) -> ClimateEngine:
    gz_bytes = _make_gzipped_csv([_ROW_00H, _ROW_03H])
    _patch_transport(monkeypatch, 200, gz_bytes)
    return ClimateEngine(synop_client=SynopClient())


async def test_query_returns_most_recent_observation(engine: ClimateEngine):
    """Entre deux observations réelles, la plus récente (03h, pas 00h) doit être retenue."""
    result = await engine.query(ClimateQuery(station_id="07510"))

    assert result is not None
    assert result.date_observation.hour == 3
    assert result.nom_station == "BORDEAUX-MERIGNAC"


async def test_query_converts_temperature_kelvin_to_celsius(engine: ClimateEngine):
    """t=270.95K (ligne 03h) doit être converti en 270.95 - 273.15 = -2.2°C exactement."""
    result = await engine.query(ClimateQuery(station_id="07510"))

    assert result.temperature_c == pytest.approx(270.95 - 273.15)


async def test_query_converts_pressure_pa_to_hpa(engine: ClimateEngine):
    """pmer=102000 Pa doit être converti en 1020.0 hPa exactement."""
    result = await engine.query(ClimateQuery(station_id="07510"))

    assert result.pression_hpa == pytest.approx(1020.0)


async def test_query_preserves_humidity_wind_precipitation_as_is(engine: ClimateEngine):
    """u, dd, ff, rr1 sont déjà dans l'unité cible — pas de conversion à appliquer."""
    result = await engine.query(ClimateQuery(station_id="07510"))

    assert result.humidite_pct == 98.0
    assert result.vent_direction_deg == 150.0
    assert result.vent_vitesse_ms == 2.7
    assert result.precipitations_1h_mm == 0.0


async def test_query_returns_none_for_unknown_station(engine: ClimateEngine):
    """Une station absente des données doit retourner None — jamais une observation inventée."""
    result = await engine.query(ClimateQuery(station_id="99999"))

    assert result is None


async def test_query_raises_on_network_failure(monkeypatch: pytest.MonkeyPatch):
    """Une panne réseau doit lever ClimateEngineError, jamais une observation par défaut."""
    _patch_transport(monkeypatch, 503, b"")
    engine = ClimateEngine()

    with pytest.raises(ClimateEngineError):
        await engine.query(ClimateQuery(station_id="07510"))


async def test_synop_client_raises_on_gzip_decode_failure(monkeypatch: pytest.MonkeyPatch):
    """Une réponse non-gzip doit lever SynopClientError, pas planter silencieusement."""
    _patch_transport(monkeypatch, 200, b"not gzip data")
    client = SynopClient()

    with pytest.raises(SynopClientError):
        await client.get_latest_observation("07510")


def test_return_engine_version():
    """version() doit retourner une chaîne non vide."""
    assert len(ClimateEngine.version()) > 0


async def test_get_danger_feux_parses_real_csv_response(monkeypatch: pytest.MonkeyPatch):
    """Parse la réponse CSV réelle de l'API Météo des forêts (3 départements)."""
    monkeypatch.setattr(
        "gsie_api.engines.climate.meteofrance_client.get_settings",
        lambda: type("S", (), {"meteofrance_api_key": "fake-key-for-test"})(),
    )
    _patch_transport(monkeypatch, 200, _DANGER_FEUX_CSV.encode("utf-8"))
    engine = ClimateEngine(meteofrance_client=MeteoFranceClient())

    resultats = await engine.get_danger_feux()

    assert len(resultats) == 3
    assert resultats[0].dep_code == "01"
    assert resultats[0].dep_nom == "Ain"
    assert resultats[2].niveau_j1 == 1
    assert resultats[2].niveau_j2 == 2


async def test_get_danger_feux_raises_without_api_key(monkeypatch: pytest.MonkeyPatch):
    """Sans clé configurée, doit lever ClimateEngineError — jamais un niveau par défaut."""
    monkeypatch.setattr(
        "gsie_api.engines.climate.meteofrance_client.get_settings",
        lambda: type("S", (), {"meteofrance_api_key": None})(),
    )
    engine = ClimateEngine(meteofrance_client=MeteoFranceClient())

    with pytest.raises(ClimateEngineError):
        await engine.get_danger_feux()


async def test_get_danger_feux_raises_on_network_failure(monkeypatch: pytest.MonkeyPatch):
    """Une panne réseau doit lever ClimateEngineError, jamais un niveau par défaut."""
    monkeypatch.setattr(
        "gsie_api.engines.climate.meteofrance_client.get_settings",
        lambda: type("S", (), {"meteofrance_api_key": "fake-key-for-test"})(),
    )
    _patch_transport(monkeypatch, 503, b"")
    engine = ClimateEngine(meteofrance_client=MeteoFranceClient())

    with pytest.raises(ClimateEngineError):
        await engine.get_danger_feux()


def _patch_dpclim_transport(
    monkeypatch: pytest.MonkeyPatch, fichier_statuses: list[int], fichier_body: bytes
) -> None:
    """Mock dispatchant selon le chemin appelé.

    Commande (202) puis fichier (statuts en séquence).
    """
    calls = {"fichier": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/commande-station/quotidienne"):
            return httpx.Response(
                202,
                json={"elaboreProduitAvecDemandeResponse": {"return": "2026024266715"}},
                request=request,
            )
        if path.endswith("/commande/fichier"):
            idx = min(calls["fichier"], len(fichier_statuses) - 1)
            status_code = fichier_statuses[idx]
            calls["fichier"] += 1
            body = fichier_body if status_code == 201 else b""
            return httpx.Response(status_code, content=body, request=request)
        raise AssertionError(f"URL non mockée : {request.url}")

    transport = httpx.MockTransport(handler)
    original_init = httpx.AsyncClient.__init__

    def _patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", _patched_init)
    monkeypatch.setattr(
        "gsie_api.engines.climate.dpclim_client.get_settings",
        lambda: type("S", (), {"meteofrance_api_key": "fake-key-for-test"})(),
    )


async def test_get_climatologie_quotidienne_parses_real_csv_with_variable_columns(
    monkeypatch: pytest.MonkeyPatch,
):
    """Parse une réponse DPClim réelle (jeu de colonnes propre à cette station) sans rien perdre."""
    _patch_dpclim_transport(monkeypatch, [201], _DPCLIM_CSV.encode("utf-8"))
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
    # Toutes les colonnes brutes sont conservées, y compris celles propres à cette station.
    assert premiere.valeurs_brutes["NEIGETOTX"] is None
    assert premiere.valeurs_brutes["QTN"] == "1"
    assert len(premiere.valeurs_brutes) == 136


async def test_get_climatologie_quotidienne_polls_until_ready(monkeypatch: pytest.MonkeyPatch):
    """Deux 404 (commande pas encore prête) puis un 201 doivent aboutir sans erreur."""
    _patch_dpclim_transport(monkeypatch, [404, 404, 201], _DPCLIM_CSV.encode("utf-8"))
    engine = ClimateEngine(dpclim_client=DPClimClient(poll_interval_s=0.0))

    resultats = await engine.get_climatologie_quotidienne(
        ClimatologieQuotidienneQuery(
            id_station="33042001",
            date_deb_periode=datetime(2026, 6, 1),
            date_fin_periode=datetime(2026, 6, 10),
        )
    )

    assert len(resultats) == 2


async def test_get_climatologie_quotidienne_raises_after_max_poll_attempts(
    monkeypatch: pytest.MonkeyPatch,
):
    """Une commande jamais prête doit lever ClimateEngineError, pas boucler indéfiniment."""
    _patch_dpclim_transport(monkeypatch, [404, 404, 404], b"")
    engine = ClimateEngine(dpclim_client=DPClimClient(poll_interval_s=0.0, max_poll_attempts=3))

    with pytest.raises(ClimateEngineError):
        await engine.get_climatologie_quotidienne(
            ClimatologieQuotidienneQuery(
                id_station="33042001",
                date_deb_periode=datetime(2026, 6, 1),
                date_fin_periode=datetime(2026, 6, 10),
            )
        )


async def test_get_climatologie_quotidienne_raises_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
):
    """Sans clé configurée, doit lever ClimateEngineError avant tout appel réseau."""
    monkeypatch.setattr(
        "gsie_api.engines.climate.dpclim_client.get_settings",
        lambda: type("S", (), {"meteofrance_api_key": None})(),
    )
    engine = ClimateEngine(dpclim_client=DPClimClient())

    with pytest.raises(ClimateEngineError):
        await engine.get_climatologie_quotidienne(
            ClimatologieQuotidienneQuery(
                id_station="33042001",
                date_deb_periode=datetime(2026, 6, 1),
                date_fin_periode=datetime(2026, 6, 10),
            )
        )


def _patch_vigilance_transport(
    monkeypatch: pytest.MonkeyPatch, status_code: int, json_body: dict
) -> None:
    monkeypatch.setattr(
        "gsie_api.engines.climate.vigilance_client.get_settings",
        lambda: type("S", (), {"meteofrance_api_key": "fake-key-for-test"})(),
    )
    _patch_transport(
        monkeypatch,
        status_code,
        __import__("json").dumps(json_body).encode("utf-8") if json_body else b"",
    )


async def test_get_vigilance_parses_real_response(monkeypatch: pytest.MonkeyPatch):
    """Parse la réponse Vigilance réelle (2 échéances, 2 domaines chacune)."""
    _patch_vigilance_transport(monkeypatch, 200, _VIGILANCE_JSON)
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


async def test_get_vigilance_raises_without_api_key(monkeypatch: pytest.MonkeyPatch):
    """Sans clé configurée, doit lever ClimateEngineError — jamais un niveau par défaut."""
    monkeypatch.setattr(
        "gsie_api.engines.climate.vigilance_client.get_settings",
        lambda: type("S", (), {"meteofrance_api_key": None})(),
    )
    engine = ClimateEngine(vigilance_client=VigilanceClient())

    with pytest.raises(ClimateEngineError):
        await engine.get_vigilance()


async def test_get_vigilance_raises_on_network_failure(monkeypatch: pytest.MonkeyPatch):
    """Une panne réseau doit lever ClimateEngineError, jamais une carte par défaut."""
    _patch_vigilance_transport(monkeypatch, 503, {})
    engine = ClimateEngine(vigilance_client=VigilanceClient())

    with pytest.raises(ClimateEngineError):
        await engine.get_vigilance()


def _patch_paquet_observation_transport(
    monkeypatch: pytest.MonkeyPatch, status_code: int, content: bytes
) -> None:
    monkeypatch.setattr(
        "gsie_api.engines.climate.paquet_observation_client.get_settings",
        lambda: type("S", (), {"meteofrance_api_key": "fake-key-for-test"})(),
    )
    _patch_transport(monkeypatch, status_code, content)


async def test_get_observations_horaires_parses_real_csv(monkeypatch: pytest.MonkeyPatch):
    """Parse la réponse CSV réelle du Package Observations et convertit Kelvin -> Celsius."""
    _patch_paquet_observation_transport(monkeypatch, 200, _PAQUET_OBSERVATION_CSV.encode("utf-8"))
    engine = ClimateEngine(paquet_observation_client=PaquetObservationClient())

    resultats = await engine.get_observations_horaires("33")

    assert len(resultats) == 2
    assert resultats[0].geo_id_insee == "33042001"
    assert resultats[0].temperature_c == pytest.approx(299.15 - 273.15)
    assert resultats[0].precipitations_1h_mm == 0.0
    assert resultats[0].pression_hpa is None
    assert resultats[0].humidite_pct is None


async def test_get_observations_horaires_raises_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
):
    """Sans clé configurée, doit lever ClimateEngineError — jamais une observation par défaut."""
    monkeypatch.setattr(
        "gsie_api.engines.climate.paquet_observation_client.get_settings",
        lambda: type("S", (), {"meteofrance_api_key": None})(),
    )
    engine = ClimateEngine(paquet_observation_client=PaquetObservationClient())

    with pytest.raises(ClimateEngineError):
        await engine.get_observations_horaires("33")


async def test_get_observations_horaires_raises_on_network_failure(
    monkeypatch: pytest.MonkeyPatch,
):
    """Une panne réseau doit lever ClimateEngineError, jamais une observation par défaut."""
    _patch_paquet_observation_transport(monkeypatch, 503, b"")
    engine = ClimateEngine(paquet_observation_client=PaquetObservationClient())

    with pytest.raises(ClimateEngineError):
        await engine.get_observations_horaires("33")
