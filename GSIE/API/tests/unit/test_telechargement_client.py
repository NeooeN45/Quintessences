"""Tests unitaires — TelechargementClient (API de téléchargement Géoplateforme IGN).

Tests ciblent directement le client via respx, sans session DB.
Vérifient le parsing Atom XML et la gestion des 5 modes de panne.
"""

import httpx
import pytest
import respx
from httpx import Response

from gsie_api.engines.gis.telechargement_client import (
    _TELECHARGEMENT_BASE_URL,
    TelechargementClient,
    TelechargementClientError,
)

_CAPABILITIES_XML = """<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns:gpf_dl="https://data.geopf.fr/annexes/ressources/xsd/gpf_dl.xsd"
      xmlns="http://www.w3.org/2005/Atom"
      gpf_dl:page="1" gpf_dl:pagesize="2" gpf_dl:pagecount="56"
      gpf_dl:totalentries="112">
  <title>Géoplateforme API - Download</title>
  <entry>
    <title>ADMIN-EXPRESS-COG</title>
    <link href="https://data.geopf.fr/telechargement/resource/ADMIN-EXPRESS-COG"
          rel="alternate" type="application/atom+xml"/>
    <id>https://data.geopf.fr/telechargement/resource/ADMIN-EXPRESS-COG</id>
    <updated>2026-07-03T14:59:00+01:00</updated>
    <content>ADMIN EXPRESS COG — limites administratives</content>
    <gpf_dl:zone term="FRA" label="FRA France entière"/>
    <gpf_dl:format term="SHP" label="SHP (Shapefile)"/>
  </entry>
  <entry>
    <title>BDFORET</title>
    <link href="https://data.geopf.fr/telechargement/resource/BDFORET"
          rel="alternate" type="application/atom+xml"/>
    <id>https://data.geopf.fr/telechargement/resource/BDFORET</id>
    <updated>2026-01-15T14:59:00+01:00</updated>
    <content>BD Forêt v2 — couverture forestière</content>
    <gpf_dl:zone term="D033" label="D033 Gironde"/>
    <gpf_dl:format term="SHP" label="SHP (Shapefile)"/>
    <gpf_dl:format term="GPKG" label="GPKG (GeoPackage)"/>
  </entry>
</feed>"""

_RESOURCE_XML = """<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns:gpf_dl="https://data.geopf.fr/annexes/ressources/xsd/gpf_dl.xsd"
      xmlns="http://www.w3.org/2005/Atom"
      gpf_dl:page="1" gpf_dl:pagesize="2" gpf_dl:pagecount="27"
      gpf_dl:totalentries="54">
  <title>ADMIN EXPRESS COG</title>
  <entry>
    <title>ADMIN-EXPRESS-COG_3-1__SHP_WGS84G_FRA_2023-05-03</title>
    <link href="https://data.geopf.fr/telechargement/resource/ADMIN-EXPRESS-COG/ADMIN-EXPRESS-COG_3-1__SHP_WGS84G_FRA_2023-05-03"
          rel="alternate" type="application/atom+xml"/>
    <id>https://data.geopf.fr/telechargement/resource/ADMIN-EXPRESS-COG/ADMIN-EXPRESS-COG_3-1__SHP_WGS84G_FRA_2023-05-03</id>
    <updated>2023-09-14T14:59:00+01:00</updated>
    <content>ADMIN-EXPRESS-COG_3-1__SHP_WGS84G_FRA_2023-05-03</content>
    <gpf_dl:zone term="FRA" label="FRA France entière"/>
    <gpf_dl:format term="SHP" label="SHP (Shapefile)"/>
    <gpf_dl:editionDate>2023-05-03</gpf_dl:editionDate>
  </entry>
</feed>"""

_SUBRESOURCE_XML = """<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns:gpf_dl="https://data.geopf.fr/annexes/ressources/xsd/gpf_dl.xsd"
      xmlns="http://www.w3.org/2005/Atom"
      gpf_dl:page="1" gpf_dl:pagesize="5" gpf_dl:pagecount="1"
      gpf_dl:totalentries="1">
  <title>ADMIN-EXPRESS-COG_3-1__SHP_WGS84G_FRA_2023-05-03</title>
  <entry>
    <link href="https://data.geopf.fr/telechargement/download/ADMIN-EXPRESS-COG/ADMIN-EXPRESS-COG_3-1__SHP_WGS84G_FRA_2023-05-03/ADMIN-EXPRESS-COG_3-1__SHP_WGS84G_FRA_2023-05-03.7z"
          rel="alternate" type="application/x-7z-compressed"
          gpf_dl:length="50721560"/>
    <id>https://data.geopf.fr/telechargement/download/ADMIN-EXPRESS-COG/ADMIN-EXPRESS-COG_3-1__SHP_WGS84G_FRA_2023-05-03/ADMIN-EXPRESS-COG_3-1__SHP_WGS84G_FRA_2023-05-03.7z</id>
    <content>147a219d1998f990677ba1984085f7dc</content>
    <gpf_dl:mime_type>application/x-shapefile</gpf_dl:mime_type>
    <gpf_dl:mime_type>text/plain</gpf_dl:mime_type>
  </entry>
</feed>"""


class TestGetCapabilities:
    """get_capabilities() — liste des ressources IGN."""

    @respx.mock
    async def should_return_ressources_when_xml_well_formed(self) -> None:
        respx.get(f"{_TELECHARGEMENT_BASE_URL}/capabilities").mock(
            return_value=Response(200, text=_CAPABILITIES_XML)
        )
        client = TelechargementClient()

        ressources, page = await client.get_capabilities()

        assert page.total_entries == 112
        assert page.page == 1
        assert page.page_count == 56
        assert len(ressources) == 2
        assert ressources[0].nom == "ADMIN-EXPRESS-COG"
        assert "ADMIN EXPRESS COG" in ressources[0].description
        assert ressources[0].zones == ["FRA"]
        assert ressources[0].formats == ["SHP"]
        assert ressources[1].nom == "BDFORET"
        assert ressources[1].formats == ["SHP", "GPKG"]

    @respx.mock
    async def should_pass_filters_when_zone_and_format_given(self) -> None:
        route = respx.get(
            f"{_TELECHARGEMENT_BASE_URL}/capabilities",
            params={"page": "1", "limit": "50", "zone": "FRA", "format": "SHP"},
        ).mock(return_value=Response(200, text=_CAPABILITIES_XML))
        client = TelechargementClient()

        await client.get_capabilities(zone="FRA", format="SHP")

        assert route.called

    @respx.mock
    async def should_raise_when_xml_malformed(self) -> None:
        respx.get(f"{_TELECHARGEMENT_BASE_URL}/capabilities").mock(
            return_value=Response(200, text="<<< not XML >>>")
        )
        client = TelechargementClient()

        with pytest.raises(TelechargementClientError, match="parsing XML"):
            await client.get_capabilities()


class TestGetResource:
    """get_resource() — liste des dossiers d'une ressource."""

    @respx.mock
    async def should_return_dossiers_when_xml_well_formed(self) -> None:
        respx.get(f"{_TELECHARGEMENT_BASE_URL}/resource/ADMIN-EXPRESS-COG").mock(
            return_value=Response(200, text=_RESOURCE_XML)
        )
        client = TelechargementClient()

        dossiers, page = await client.get_resource("ADMIN-EXPRESS-COG")

        assert page.total_entries == 54
        assert len(dossiers) == 1
        assert dossiers[0].nom == "ADMIN-EXPRESS-COG_3-1__SHP_WGS84G_FRA_2023-05-03"
        assert dossiers[0].zone == "FRA"
        assert dossiers[0].format == "SHP"
        assert dossiers[0].date_edition == "2023-05-03"

    @respx.mock
    async def should_raise_when_xml_malformed(self) -> None:
        respx.get(f"{_TELECHARGEMENT_BASE_URL}/resource/BDFORET").mock(
            return_value=Response(200, text="<<< not XML >>>")
        )
        client = TelechargementClient()

        with pytest.raises(TelechargementClientError, match="parsing XML"):
            await client.get_resource("BDFORET")


class TestGetSubResource:
    """get_subresource() — liste des fichiers d'un dossier."""

    @respx.mock
    async def should_return_fichiers_when_xml_well_formed(self) -> None:
        respx.get(
            f"{_TELECHARGEMENT_BASE_URL}/resource/ADMIN-EXPRESS-COG/ADMIN-EXPRESS-COG_3-1__SHP_WGS84G_FRA_2023-05-03"
        ).mock(return_value=Response(200, text=_SUBRESOURCE_XML))
        client = TelechargementClient()

        fichiers, page = await client.get_subresource(
            "ADMIN-EXPRESS-COG", "ADMIN-EXPRESS-COG_3-1__SHP_WGS84G_FRA_2023-05-03"
        )

        assert page.total_entries == 1
        assert len(fichiers) == 1
        assert fichiers[0].taille_octets == 50721560
        assert fichiers[0].checksum_md5 == "147a219d1998f990677ba1984085f7dc"
        assert "application/x-shapefile" in fichiers[0].mime_types
        assert fichiers[0].url_download.endswith(".7z")


class TestDownloadFile:
    """download_file() — téléchargement binaire."""

    @respx.mock
    async def should_return_bytes_when_file_found(self) -> None:
        url = (
            f"{_TELECHARGEMENT_BASE_URL}/download/ADMIN-EXPRESS-COG"
            "/ADMIN-EXPRESS-COG_3-1__SHP_WGS84G_FRA_2023-05-03"
            "/ADMIN-EXPRESS-COG_3-1__SHP_WGS84G_FRA_2023-05-03.7z"
        )
        respx.get(url).mock(return_value=Response(200, content=b"\x37\x7a\xbc\xaf"))
        client = TelechargementClient()

        data = await client.download_file(
            "ADMIN-EXPRESS-COG",
            "ADMIN-EXPRESS-COG_3-1__SHP_WGS84G_FRA_2023-05-03",
            "ADMIN-EXPRESS-COG_3-1__SHP_WGS84G_FRA_2023-05-03.7z",
        )

        assert data == b"\x37\x7a\xbc\xaf"

    @respx.mock
    async def should_raise_when_http_404(self) -> None:
        url = f"{_TELECHARGEMENT_BASE_URL}/download/INEXISTANT" "/INEXISTANT/INEXISTANT.7z"
        respx.get(url).mock(return_value=Response(404))
        client = TelechargementClient()

        with pytest.raises(TelechargementClientError, match="Échec"):
            await client.download_file("INEXISTANT", "INEXISTANT", "INEXISTANT.7z")


class TestNetworkFailure:
    """Mode #1 — panne réseau."""

    @respx.mock
    async def should_raise_when_network_error(self) -> None:
        respx.get(f"{_TELECHARGEMENT_BASE_URL}/capabilities").mock(
            side_effect=httpx.ConnectError("connexion refusée")
        )
        client = TelechargementClient()

        with pytest.raises(TelechargementClientError, match="Échec"):
            await client.get_capabilities()
