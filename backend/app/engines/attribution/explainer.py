"""Explainer: turn per-agent evidence into a 1-2 sentence human-readable narrative.

Output is consumed directly by the Frontend's SourceRadar / AgentEvidencePanel
and the Demo story-mode step 2.
"""

from __future__ import annotations

from typing import Dict, List


SOURCE_LABELS = {
    "traffic": "traffic emissions",
    "construction": "construction dust & diesel",
    "industrial": "industrial emissions",
    "biomass_burning": "biomass / waste burning",
    "stubble_burning": "stubble burning",
    "urban_form": "dense urban form",
    "mixed": "mixed sources",
}


def build_explanation(
    top_source: str,
    source_breakdown: Dict[str, float],
    per_agent_scores: Dict[str, float],
    agent_notes: Dict[str, List[str]],
    ward_name: str,
    current_aqi: float,
) -> str:
    """Render a concise explanation."""
    pct = source_breakdown.get(top_source, 0.0) * 100.0
    label = SOURCE_LABELS.get(top_source, top_source.replace("_", " "))

    # Pick the most explanatory agent note (the one with strongest score).
    top_agent = max(per_agent_scores.items(), key=lambda kv: kv[1])[0] if per_agent_scores else ""
    top_note = ""
    if top_agent and agent_notes.get(top_agent):
        top_note = agent_notes[top_agent][0]

    parts: List[str] = [
        f"AQI in {ward_name} is {int(current_aqi)}; "
        f"top driver is {label} (~{int(round(pct))}%)."
    ]
    if top_note:
        parts.append(top_note)
    return " ".join(parts)
