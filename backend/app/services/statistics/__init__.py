"""StatMind AI Statistics Engine & Method Registry"""
from backend.app.services.statistics.registry import MethodRegistry
from backend.app.services.statistics.descriptive import DescriptiveStatisticsMethod
from backend.app.services.statistics.ttest import IndependentSamplesTTestMethod
from backend.app.services.statistics.correlation import PearsonCorrelationMethod
from backend.app.services.statistics.chi_square import ChiSquareTestMethod
from backend.app.services.statistics.regression import SimpleLinearRegressionMethod
from backend.app.services.statistics.anova import OneWayAnovaMethod
from backend.app.services.statistics.mann_whitney import MannWhitneyUMethod
from backend.app.services.statistics.kruskal import KruskalWallisMethod
from backend.app.services.statistics.multiple_regression import MultipleLinearRegressionMethod
from backend.app.services.statistics.logistic_regression import LogisticRegressionMethod
from backend.app.services.statistics.ancova import ANCOVAMethod


def bootstrap_registry() -> None:
    """Register all Phase 0 and Phase 2 statistical methods into the MethodRegistry."""
    MethodRegistry.register(DescriptiveStatisticsMethod())
    MethodRegistry.register(IndependentSamplesTTestMethod())
    MethodRegistry.register(PearsonCorrelationMethod())
    MethodRegistry.register(ChiSquareTestMethod())
    MethodRegistry.register(SimpleLinearRegressionMethod())
    MethodRegistry.register(OneWayAnovaMethod())
    MethodRegistry.register(MannWhitneyUMethod())
    MethodRegistry.register(KruskalWallisMethod())
    MethodRegistry.register(MultipleLinearRegressionMethod())
    MethodRegistry.register(LogisticRegressionMethod())
    MethodRegistry.register(ANCOVAMethod())


# Automatically bootstrap on import
bootstrap_registry()

__all__ = [
    "MethodRegistry",
    "bootstrap_registry",
    "DescriptiveStatisticsMethod",
    "IndependentSamplesTTestMethod",
    "PearsonCorrelationMethod",
    "ChiSquareTestMethod",
    "SimpleLinearRegressionMethod",
    "OneWayAnovaMethod",
    "MannWhitneyUMethod",
    "KruskalWallisMethod",
    "MultipleLinearRegressionMethod",
    "LogisticRegressionMethod",
    "ANCOVAMethod",
]
