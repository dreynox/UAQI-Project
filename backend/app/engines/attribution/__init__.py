"""Multi-modal source attribution engine.

Four cooperating agents (Spatial, Satellite, Traffic, Land Use) score a
ward's current air-quality problem. An orchestrator fuses them with
city-specific weights, an explainer renders human-readable text.

Each agent is a pure Python function with a documented input/output contract.
"""

from app.engines.attribution.orchestrator import (
    AttributionResult,
    compute_attribution,
    persist_attribution,
)

__all__ = ["compute_attribution", "persist_attribution", "AttributionResult"]
