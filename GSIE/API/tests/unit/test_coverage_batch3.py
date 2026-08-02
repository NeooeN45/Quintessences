"""Tests unitaires — couverture des derniers gaps résiduels (batch 3).

Couvre des comportements résiduels dans 17 modules : gardes défensives,
branches d'erreur peu communes et points d'entrée exécutés en
``__main__``.
"""

from __future__ import annotations

import ast
import importlib
import runpy
import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import (
    AsyncMock,
    MagicMock,
    Mock,
    patch,
)
from uuid import uuid4

import pytest

# ===========================================================================
# 1. core/config.py — cache des valeurs déchiffrées et fallback racine API
# ===========================================================================


class TestConfigDecryptedEnvCacheLookup:
    """get_field_value : retour direct quand la clé préfixée est dans le cache."""

    def should_return_cached_value_when_exact_prefixed_key_matches(self) -> None:
        from gsie_api.core.config import Settings, _DecryptedEnvSource

        # La clé doit être exactement f"{prefix}{field_name}" = "GSIE_app_name"
        with patch("gsie_api.core.config._decrypted_env_cache", {"GSIE_app_name": "test_val"}):
            source = _DecryptedEnvSource(Settings)
            val, key, complex_val = source.get_field_value(None, "app_name")
            assert val == "test_val"
            assert key == "GSIE_app_name"
            assert complex_val is False


class TestConfigApiRootFallback:
    """Fallback _API_ROOT quand pyproject.toml n'est pas trouvé à la racine."""

    def should_use_fallback_root_when_pyproject_missing(self) -> None:
        import gsie_api.core.config as config_module

        # Au lieu d'utiliser importlib.reload (qui corrompt numpy en --cov
        # sur Windows), on exécute uniquement le bloc source calculant
        # _API_ROOT avec exec. On padde avec des lignes vides pour que les
        # numéros de ligne correspondent au fichier source — coverage
        # trace alors correctement l'exécution dans config.py.
        source_path = Path(config_module.__file__)
        source_lines = source_path.read_text(encoding="utf-8").splitlines()

        # Bloc de calcul de _API_ROOT (1-indexé 351-355 = indices 350-354)
        # Inclut l'assignation principale + le if/else fallback
        relevant_code = "\n".join(source_lines[350:355])
        # Padder avec des lignes vides pour aligner les numéros de ligne
        padded_code = "\n" * 350 + relevant_code
        code_obj = compile(padded_code, str(source_path), "exec")

        namespace: dict = {"__file__": str(source_path), "Path": Path}
        with patch.object(Path, "exists", return_value=False):
            exec(code_obj, namespace)

        # Le fallback assigne _API_ROOT au parent direct du fichier
        assert namespace["_API_ROOT"] == Path(source_path).resolve().parent


# ===========================================================================
# 2. engines/autecology_adapter.py — profil sans valeur exploitable
# ===========================================================================


class TestAutecologyAdapterProfileWithoutValue:
    """profile_to_rule : erreur quand value_text et value_numeric sont tous deux None."""

    def should_raise_when_profile_has_no_value(self) -> None:
        from gsie_api.engines.autecology_adapter import (
            AutecologyAdapterError,
            profile_to_rule,
        )
        from gsie_api.engines.evidence.schemas import (
            EvidenceLevel,
            SourceReference,
            SourceType,
        )

        # AutecologyProfileCreate valide qu'au moins value_text ou value_numeric
        # est non-None au niveau Pydantic. Pour tester la garde défensive de
        # l'adaptateur, on construit un mock qui contourne cette
        # validation — la garde protège précisément contre un objet mal formé
        # qui aurait échappé à la validation Pydantic.
        profile = MagicMock()
        profile.species_gbif_taxon_key = 2882431  # Fagus sylvatica (connu)
        profile.variable = "preference_edaphique"
        profile.value_text = None
        # value_numeric doit être un objet dont str() retourne "" (falsy)
        # pour que `value_text or str(value_numeric)` soit falsy et déclenche
        # la garde défensive.
        profile.value_numeric = MagicMock()
        profile.value_numeric.__str__ = Mock(return_value="")
        profile.evidence_level = EvidenceLevel.C
        profile.source = SourceReference(
            type_source=SourceType.referentiel_officiel,
            auteur="Test",
            date_publication="2026",
            reference="test",
        )
        with pytest.raises(AutecologyAdapterError, match="profil sans valeur"):
            profile_to_rule(profile)


# ===========================================================================
# 3. engines/botanical/indigenat_loader.py — lignes avec nom scientifique vide
# ===========================================================================


class TestIndigenatLoaderEmptyNomScientifique:
    """Une ligne avec Nom_scientifique vide est ignorée (skip)."""

    def should_skip_rows_with_empty_nom_scientifique(self, tmp_path: Path) -> None:
        from gsie_api.engines.botanical.indigenat_loader import IndigenatLoader

        # Créer un TSV avec une ligne valide et une ligne avec nom vide
        tab_content = (
            '"Nom_scientifique"\t"CD_NOM_TaxRefv18.0"\n'
            '"Abies alba Mill., 1768"\t"79319"\n'
            '""\t"999"\n'
        )
        tab_file = tmp_path / "test_indigenat.tab"
        tab_file.write_text(tab_content, encoding="utf-8-sig")

        loader = IndigenatLoader(dataset_path=tab_file)
        # find déclenche _ensure_loaded qui parcourt les lignes
        # La ligne avec nom vide doit être skippée
        row = loader.find(cd_nom=79319, nom_scientifique=None)
        assert row is not None
        assert row["Nom_scientifique"] == "Abies alba Mill., 1768"
        # La ligne avec nom vide ne doit pas être dans by_cd_nom
        assert loader.find(cd_nom=999, nom_scientifique=None) is None


# ===========================================================================
# 4. engines/climate/arome_grib_decoder.py — variable t2m absente
# ===========================================================================


class TestAromeGribDecoderMissingT2m:
    """Variable t2m absente du dataset décodé → AromeGribDecodeError."""

    def should_raise_when_t2m_absent_from_decoded_dataset(self) -> None:
        from gsie_api.engines.climate.arome_grib_decoder import (
            AromeGribDecodeError,
            extract_nearest_temperature_celsius,
        )

        # Mock cfgrib.open_datasets pour retourner un dataset sans t2m
        fake_dataset = MagicMock()
        fake_dataset.__contains__ = Mock(return_value=False)  # "t2m" not in dataset

        with patch("gsie_api.engines.climate.arome_grib_decoder.cfgrib") as mock_cfgrib:
            mock_cfgrib.open_datasets = Mock(return_value=[fake_dataset])
            with pytest.raises(AromeGribDecodeError, match="t2m absente"):
                extract_nearest_temperature_celsius(b"fake_grib", 44.0, -0.5)


# ===========================================================================
# 5. engines/climate/synop_client.py — double vérification du cache sous verrou
# ===========================================================================


class TestSynopClientCacheDoubleCheckedLocking:
    """Re-vérification du cache sous le verrou : un autre appelant a rempli le cache."""

    async def should_return_cached_value_on_second_check_under_lock(self) -> None:
        import asyncio

        from gsie_api.engines.climate.synop_client import (
            SynopClient,
            _CachedFile,
        )

        client = SynopClient()
        year = 2025
        csv_text = "lat;lon;geo_id_wmo;validity_time;t;td;u;pmer;dd;ff;rr1"

        # Pour atteindre la re-vérification sous le verrou, le premier check
        # du cache doit échouer (cache vide), puis le cache doit être rempli
        # avant la re-vérification sous le verrou.
        # On mock _get_lock pour qu'il remplisse le cache comme effet de bord.
        def _fill_cache_and_return_lock(year_arg: int) -> asyncio.Lock:
            client._cache[year_arg] = _CachedFile(year_arg, csv_text)
            return asyncio.Lock()

        with patch.object(client, "_get_lock", side_effect=_fill_cache_and_return_lock):
            result = await client._fetch_year(year)
        assert result == csv_text


# ===========================================================================
# 6. engines/correlation/engine.py — coefficient NaN par variance nulle
# ===========================================================================


class TestCorrelationEngineNanCoefficient:
    """Coefficient NaN (variance nulle) → CorrelationEngineError."""

    async def should_raise_when_coefficient_is_nan(self) -> None:
        from gsie_api.engines.correlation.engine import (
            CorrelationEngine,
            CorrelationEngineError,
        )
        from gsie_api.engines.correlation.schemas import (
            CorrelationComputeRequest,
            DomaineCorrelation,
            ParametreCorrelation,
            SourceMoteur,
        )
        from gsie_api.engines.evidence.schemas import (
            EvidenceLevel,
            SourceReference,
            SourceType,
        )
        from gsie_api.infrastructure.models.enums import CorrelationMethod

        # Une série constante (variance nulle) produit un coefficient NaN
        request = CorrelationComputeRequest(
            requete_id=uuid4(),
            domaine=DomaineCorrelation.stationnel,
            variable_a=ParametreCorrelation(
                source_moteur=SourceMoteur.terrain,
                variable="altitude",
                valeurs=[100.0, 100.0, 100.0, 100.0, 100.0],
            ),
            variable_b=ParametreCorrelation(
                source_moteur=SourceMoteur.terrain,
                variable="pH",
                valeurs=[5.0, 6.0, 5.5, 6.5, 5.0],
            ),
            methode=CorrelationMethod.pearson,
            source=SourceReference(
                type_source=SourceType.peer_reviewed,
                auteur="Test",
                reference="test",
            ),
            evidence_level=EvidenceLevel.B,
        )

        engine = CorrelationEngine(session=Mock())
        with pytest.raises(CorrelationEngineError, match="variance nulle"):
            await engine.compute(request)


# ===========================================================================
# 7. engines/evidence/wrapper.py — import réussi du module Rust
# ===========================================================================


class TestEvidenceWrapperRustModuleAvailable:
    """Import réussi du module Rust → _RUST_AVAILABLE = True + log info."""

    def should_set_rust_available_when_module_importable(self) -> None:
        import gsie_api.engines.evidence.wrapper as wrapper_module

        # Créer un faux module gsie_evidence dans sys.modules
        fake_rust = MagicMock()
        fake_rust.EvidenceEngine.version.return_value = "0.1.0"

        mock_logger = MagicMock()
        with (
            patch.dict(sys.modules, {"gsie_evidence": fake_rust}),
            patch("gsie_api.core.logging.get_logger", return_value=mock_logger),
        ):
            importlib.reload(wrapper_module)
            assert wrapper_module._RUST_AVAILABLE is True
            # Le logger.info doit avoir été appelé avec "evidence_engine_rust_loaded"
            info_calls = [c for c in mock_logger.info.call_args_list if "rust_loaded" in str(c)]
            assert len(info_calls) >= 1

        # Restaurer l'état normal (sans Rust)
        sys.modules.pop("gsie_evidence", None)
        importlib.reload(wrapper_module)
        assert wrapper_module._RUST_AVAILABLE is False


# ===========================================================================
# 8. engines/knowledge/regles.py — valeur vide après strip
# ===========================================================================


class TestReglesNombreLisibleEmptyValue:
    """_nombre_lisible : retourne None pour une valeur vide après strip."""

    def should_return_none_for_empty_string(self) -> None:
        from gsie_api.engines.knowledge.regles import _nombre_lisible

        assert _nombre_lisible("") is None

    def should_return_none_for_whitespace_only_string(self) -> None:
        from gsie_api.engines.knowledge.regles import _nombre_lisible

        assert _nombre_lisible("   ") is None


# ===========================================================================
# 9. engines/learning/router.py — chemin succès de learning_process
# ===========================================================================


class TestLearningRouterProcessSuccess:
    """learning_process : retour normal (200) quand process retourne un LearningOutput."""

    async def should_return_output_when_process_succeeds(self) -> None:
        from starlette.requests import Request
        from starlette.responses import Response

        from gsie_api.engines.learning.router import learning_process
        from gsie_api.engines.learning.schemas import (
            LearningOutput,
            LearningOutputType,
            LearningStatut,
        )

        fake_output = LearningOutput(
            output_id=uuid4(),
            type=LearningOutputType.proposition_revision,
            description="Test proposition",
            justification=["chaîne d'apprentissage"],
            confidence=0.8,
            date_output=datetime.now(UTC),
            statut=LearningStatut.propose,
        )

        signal = MagicMock()
        signal.type = MagicMock()
        signal.contenu = {}

        # Construire une vraie Request et Response Starlette pour slowapi
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/learning/process",
            "headers": [],
            "query_string": b"",
            "client": ("127.0.0.1", 12345),
        }
        real_request = Request(scope)
        real_response = Response()

        with (
            patch("gsie_api.engines.learning.router.LearningEngine") as mock_engine_cls,
            patch("gsie_api.engines.learning.router._limiter") as mock_limiter,
        ):
            mock_engine = mock_engine_cls.return_value
            mock_engine.process = AsyncMock(return_value=fake_output)

            # Contourner le décorateur rate limiter en mockant la limite
            mock_limiter.limit = MagicMock(return_value=lambda func: func)

            mock_session = AsyncMock()

            result = await learning_process(
                request_body=signal,
                request=real_request,
                response=real_response,
                session=mock_session,
                _user=MagicMock(),
            )
            assert result is fake_output


# ===========================================================================
# 10. engines/reasoning/engine.py — opérateur booléen interdit et variable
#     non tracée
# ===========================================================================


class TestReasoningEngineUnauthorizedBoolOp:
    """BoolOp avec un opérateur non autorisé → ValueError."""

    def should_raise_for_unauthorized_bool_op(self) -> None:
        from gsie_api.engines.reasoning.engine import _evaluer_noeud

        # Construire un AST BoolOp avec un opérateur non autorisé (ast.Add)
        node = ast.BoolOp(
            op=ast.Add(),  # Non autorisé — seul And et Or le sont
            values=[ast.Constant(True), ast.Constant(False)],
        )
        ast.fix_missing_locations(node)
        with pytest.raises(ValueError, match="connecteur logique interdit"):
            _evaluer_noeud(node, {})


class TestReasoningEngineUntracedConditionVariable:
    """Variable dans la condition sans provenance traçable → branche défensive."""

    async def should_include_untraced_variable_in_premisses(self) -> None:
        import gsie_api.engines.reasoning.engine as engine_module
        from gsie_api.engines.evidence.schemas import (
            EvidenceLevel,
            SourceReference,
            SourceType,
        )
        from gsie_api.engines.reasoning.engine import ReasoningEngine
        from gsie_api.engines.reasoning.schemas import (
            BlocContexte,
            ReasoningRequest,
            RegleInference,
            SourceMoteurContexte,
            StationContexte,
        )

        # Workaround : engine.py importe SourceReference et EvidenceLevel
        # sous TYPE_CHECKING uniquement.
        engine_module.SourceReference = SourceReference  # type: ignore[attr-defined]
        engine_module.EvidenceLevel = EvidenceLevel  # type: ignore[attr-defined]
        RegleInference.model_rebuild()

        source = SourceReference(
            type_source=SourceType.peer_reviewed,
            auteur="Test",
            reference="test",
        )

        bloc = BlocContexte(
            source_moteur=SourceMoteurContexte.pedology,
            source=source,
            evidence_level=EvidenceLevel.B,
            valeurs={"pH": 5.0},
        )
        contexte = StationContexte(pedologie=bloc)

        # La règle référence "pedologie_pH" qui est dans le contexte (donc
        # dans faits_bruts) ET "custom_var" qui ne sera injecté que dans faits
        # (pas dans faits_bruts ni dans provenance_faits_derives).
        # Le contexte aplatit les variables avec le préfixe du bloc :
        # pedologie_pH pour le bloc pedologie.
        regle = RegleInference(
            identifiant="R_TEST",
            condition="pedologie_pH >= 4.0 and custom_var == 1",
            enonce_conclusion="Test conclusion",
            source=source,
            evidence_level=EvidenceLevel.B,
            niveau_confiance=0.8,
        )

        request = ReasoningRequest(
            requete_id=uuid4(),
            contexte=contexte,
            regles=[regle],
            question="Test",
            profondeur_max=3,
        )

        engine = ReasoningEngine(session=Mock())

        # Patch _evaluer_condition pour injecter custom_var dans faits
        # avant l'évaluation, simulant un fait sans provenance traçable.
        # On retourne True directement sans évaluer la condition réelle
        # (qui échouerait car custom_var n'est pas un fait de contexte).
        def _patched_evaluer(condition: str, faits: dict) -> bool:
            faits["custom_var"] = 1
            return True

        with patch.object(engine_module, "_evaluer_condition", side_effect=_patched_evaluer):
            result = await engine.infer(request, date_inference=datetime(2026, 1, 1, tzinfo=UTC))

        # La conclusion doit être produite (la règle a été appliquée)
        assert len(result.conclusions) >= 1
        # Vérifier que la prémisse contient custom_var sans source ni règle
        conclusion = result.conclusions[0]
        all_premisses = " ".join(" ".join(etape.premisses) for etape in conclusion.chaine_inference)
        assert "custom_var" in all_premisses


# ===========================================================================
# 11. engines/simulation_backend.py — propagation d'erreur de croissance
# ===========================================================================


class TestSimulationBackendCircumferenceProjectionError:
    """CalibratedGrowthBackend : GrowthModelError sur project_circumference."""

    def should_raise_simulation_error_when_circumference_projection_fails(self) -> None:
        from gsie_api.engines.growth_models import GrowthModelError
        from gsie_api.engines.simulation_backend import (
            CalibratedGrowthBackend,
            SimulationBackendError,
        )

        backend = CalibratedGrowthBackend()

        with (
            patch(
                "gsie_api.engines.simulation_backend.project_circumference",
                side_effect=GrowthModelError("espèce non calibrée pour la circonférence"),
            ),
            pytest.raises(SimulationBackendError, match="espèce non calibrée"),
        ):
            backend.simulate_growth(
                species="Unknown species",
                initial_state={"circumference": 150.0},
                horizon_years=10,
            )


# ===========================================================================
# 12. engines/validation/engine.py — persistance ignorée sans session
# ===========================================================================


class TestValidationEngineNoSessionPersist:
    """_persist_result : garde-fou quand session est None (appel direct)."""

    async def should_return_early_when_session_is_none_in_persist_result(self) -> None:
        from gsie_api.engines.validation.engine import ValidationEngine
        from gsie_api.engines.validation.schemas import (
            CauseBlocage,
            ControleResultat,
            ResultatControle,
            TypeCauseBlocage,
            TypeSortie,
            ValidationRequest,
            ValidationResult,
            ValidationStatut,
        )

        engine = ValidationEngine(session=None)
        request = ValidationRequest(
            requete_id=uuid4(),
            type_sortie=TypeSortie.diagnostic,
            contenu={"evidence_level": "B", "justification": "test"},
        )
        result = ValidationResult(
            validation_id=uuid4(),
            requete_origine=request.requete_id,
            statut=ValidationStatut.bloque,
            controles=[
                ControleResultat(
                    nom_controle="test",
                    resultat=ResultatControle.non_conforme,
                    details="test",
                )
            ],
            causes_blocage=[
                CauseBlocage(
                    type_cause=TypeCauseBlocage.sans_niveau_preuve,
                    element_concerne=request.requete_id,
                    description="test cause",
                )
            ],
            date_validation=datetime.now(UTC),
        )

        # _persist_result doit retourner immédiatement sans lever d'erreur
        # car session is None
        await engine._persist_result(request, result)


# ===========================================================================
# 13. metrics/db_quality.py — plafonnement des séries de progression
# ===========================================================================


class TestDbQualityProgressSeriesCapping:
    """Plafonnement des séries de progression quand > _MAX_SERIES_PAR_METRIQUE."""

    async def should_cap_ingestion_progress_when_over_max_series(self) -> None:
        from contextlib import asynccontextmanager

        from gsie_api.metrics import db_quality

        # Créer plus de progressions que _MAX_SERIES_PAR_METRIQUE (50)
        mock_progress = MagicMock()
        mock_progress.pipeline = "pipeline_{i}"
        mock_progress.status = "status_{i}"
        mock_progress.last_offset = 100

        progressions = []
        for i in range(60):
            p = MagicMock()
            p.pipeline = f"pipeline_{i}"
            p.status = f"status_{i}"
            p.last_offset = i
            progressions.append(p)

        mock_session = AsyncMock()
        mock_session.scalar = AsyncMock(side_effect=[10, 5, 3, 2, 1])

        mock_result_aliases = MagicMock()
        mock_result_aliases.__iter__ = MagicMock(return_value=iter([("GBIF", 5)]))
        mock_result_completeness = MagicMock()
        mock_result_completeness.fetchone.return_value = (10, 5, 3, 2, 1)
        mock_result_lang = MagicMock()
        mock_result_lang.__iter__ = MagicMock(return_value=iter([("fr", 5)]))
        mock_result_quality = MagicMock()
        mock_result_quality.__iter__ = MagicMock(return_value=iter([("good", 3)]))
        mock_result_progress = MagicMock()
        mock_result_progress.scalars = MagicMock(return_value=iter(progressions))

        mock_session.execute = AsyncMock(
            side_effect=[
                mock_result_aliases,
                mock_result_completeness,
                mock_result_lang,
                mock_result_quality,
                mock_result_progress,
            ]
        )

        @asynccontextmanager
        async def _fake_factory():
            yield mock_session

        with (
            patch.object(db_quality, "async_session_factory", _fake_factory),
            patch.object(db_quality.logger, "warning") as mock_warning,
        ):
            await db_quality._collect_metrics()
            # Le warning de plafonnement doit avoir été émis
            warning_calls = [c for c in mock_warning.call_args_list if "cardinalite" in str(c)]
            assert len(warning_calls) >= 1


# ===========================================================================
# 14. outbox_worker.py — exécution en tant que point d'entrée __main__
# ===========================================================================


class TestOutboxWorkerMainEntryPoint:
    """if __name__ == "__main__": main() — exécution du point d'entrée."""

    def should_execute_main_when_run_as_main(self) -> None:
        # runpy.run_module re-exécute le module, ce qui re-crée les métriques
        # Prometheus (déjà enregistrées). On mock le registry pour éviter
        # l'erreur de duplication.

        # Mock run_worker pour éviter la connexion DB
        with (
            patch("gsie_api.outbox_worker.run_worker", new_callable=AsyncMock),
            patch("gsie_api.outbox_worker.asyncio.run") as mock_asyncio_run,
            patch("prometheus_client.Counter"),
            patch("prometheus_client.Gauge"),
            patch("prometheus_client.Histogram"),
        ):
            runpy.run_module("gsie_api.outbox_worker", run_name="__main__")
            # asyncio.run doit avoir été appelé (par main())
            mock_asyncio_run.assert_called_once()
            # Ferme la coroutine créée par run_worker() que le mock d'asyncio.run
            # n'a pas consommée — évite RuntimeWarning "coroutine never awaited".
            mock_asyncio_run.call_args.args[0].close()


# ===========================================================================
# 15. resources/validators.py — nombre de champs excessif
# ===========================================================================


class TestValidatorsTooManyFields:
    """validate_resource_payload : trop de champs → erreur."""

    def should_report_error_when_too_many_fields(self) -> None:
        from gsie_api.resources.validators import MAX_FIELDS, validate_resource_payload

        # Créer un dict avec plus de MAX_FIELDS champs
        data = {f"field_{i}": i for i in range(MAX_FIELDS + 1)}
        errors = validate_resource_payload(data)
        assert any("Trop de champs" in e for e in errors)


# ===========================================================================
# 16. seeds/autecology_pilot_data.py — retour des profils construits
# ===========================================================================


class TestAutecologyPilotDataSeedReturnsProfiles:
    """seed_autecology_pilot : retourne les profils construits."""

    async def should_return_pilot_profiles_from_seed_function(self) -> None:
        from gsie_api.seeds.autecology_pilot_data import (
            build_autecology_pilot_profiles,
            seed_autecology_pilot,
        )

        result = await seed_autecology_pilot()
        expected = build_autecology_pilot_profiles()
        assert len(result) == len(expected)
        assert result == expected


# ===========================================================================
# 17. seeds/run_seeds.py — exécution en tant que point d'entrée __main__
# ===========================================================================


class TestRunSeedsMainEntryPoint:
    """if __name__ == "__main__": main() — exécution du point d'entrée."""

    def should_execute_main_when_run_as_main(self) -> None:
        # Mock run_seeds pour éviter le RuntimeError
        with (
            patch("gsie_api.seeds.run_seeds.run_seeds", new_callable=AsyncMock),
            patch("gsie_api.seeds.run_seeds.asyncio.run") as mock_asyncio_run,
            patch("sys.argv", ["run_seeds.py"]),
        ):
            runpy.run_module("gsie_api.seeds.run_seeds", run_name="__main__")
            # asyncio.run doit avoir été appelé (par main())
            mock_asyncio_run.assert_called_once()
            # Ferme la coroutine créée par run_seeds() que le mock d'asyncio.run
            # n'a pas consommée — évite RuntimeWarning "coroutine never awaited".
            mock_asyncio_run.call_args.args[0].close()
