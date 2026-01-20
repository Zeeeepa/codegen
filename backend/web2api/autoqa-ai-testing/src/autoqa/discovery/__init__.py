"""
Auto-discovery system for Web2API services.

Automatically detects authentication requirements, maps service features,
and builds executable operation definitions.
"""

from autoqa.discovery.auth_detector import AuthDetector
from autoqa.discovery.feature_mapper import FeatureMapper
from autoqa.discovery.operation_builder import OperationBuilder
from autoqa.discovery.orchestrator import DiscoveryOrchestrator

__all__ = [
    "AuthDetector",
    "FeatureMapper",
    "OperationBuilder",
    "DiscoveryOrchestrator",
]
