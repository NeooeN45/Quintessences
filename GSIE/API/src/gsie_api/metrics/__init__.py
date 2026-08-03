"""Métriques Prometheus personnalisées GSIE."""

from gsie_api.metrics.db_quality import collect_db_metrics

__all__ = ["collect_db_metrics"]
