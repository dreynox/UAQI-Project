"""Action library: catalog of enforcement actions and how to pick them.

Eight action types, each with:
- description: human-readable summary
- target_sources: which attribution buckets it counters
- max_expected_delta: ceiling AQI reduction (AQI points)
- estimated_cost_inr: rough cost band per incident
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ActionDef:
    code: str
    title: str
    description: str
    target_sources: tuple
    max_expected_delta: float  # negative = improvement (e.g. -25.0)
    estimated_cost_inr: int
    lead_time_hours: int


ACTION_TYPES: Dict[str, ActionDef] = {
    "inspection": ActionDef(
        code="inspection",
        title="Site inspection",
        description=(
            "Deploy inspector team to verify compliance, sample emissions, "
            "and issue notices."
        ),
        target_sources=("construction", "industrial", "waste_burning"),
        max_expected_delta=-12.0,
        estimated_cost_inr=8_000,
        lead_time_hours=4,
    ),
    "dust_control": ActionDef(
        code="dust_control",
        title="Dust-control enforcement",
        description=(
            "Mandatory water spraying, tarpaulin covering, and anti-dust "
            "nets at construction sites."
        ),
        target_sources=("construction", "urban_form"),
        max_expected_delta=-22.0,
        estimated_cost_inr=25_000,
        lead_time_hours=6,
    ),
    "traffic_diversion": ActionDef(
        code="traffic_diversion",
        title="Traffic diversion / restriction",
        description=(
            "Reroute heavy vehicles or restrict truck entry during peak hours."
        ),
        target_sources=("traffic",),
        max_expected_delta=-18.0,
        estimated_cost_inr=5_000,
        lead_time_hours=2,
    ),
    "waste_burning": ActionDef(
        code="waste_burning",
        title="Waste-burning crackdown",
        description=(
            "Anti-burning patrols in open-dump and landfill wards; "
            "deploy IEC vans."
        ),
        target_sources=("waste_burning", "biomass_burning"),
        max_expected_delta=-28.0,
        estimated_cost_inr=15_000,
        lead_time_hours=8,
    ),
    "industrial_audit": ActionDef(
        code="industrial_audit",
        title="Industrial emission audit",
        description=(
            "On-site audit of industrial stacks; continuous emissions "
            "monitoring system (CEMS) cross-check."
        ),
        target_sources=("industrial",),
        max_expected_delta=-30.0,
        estimated_cost_inr=45_000,
        lead_time_hours=24,
    ),
    "public_advisory": ActionDef(
        code="public_advisory",
        title="Public-health advisory",
        description=(
            "Issue multilingual SMS / IVR advisory to ward residents; "
            "school outdoor-activity suspension."
        ),
        target_sources=(),  # awareness, not direct reduction
        max_expected_delta=-4.0,
        estimated_cost_inr=2_000,
        lead_time_hours=1,
    ),
    "odd_even": ActionDef(
        code="odd_even",
        title="Odd-even vehicle scheme",
        description=(
            "Plate-based vehicle restriction during the action window."
        ),
        target_sources=("traffic",),
        max_expected_delta=-26.0,
        estimated_cost_inr=10_000,
        lead_time_hours=12,
    ),
    "construction_shutdown": ActionDef(
        code="construction_shutdown",
        title="Construction shutdown",
        description=(
            "Mandatory halt of all non-essential construction activity in "
            "the ward until AQI drops below threshold."
        ),
        target_sources=("construction",),
        max_expected_delta=-35.0,
        estimated_cost_inr=60_000,
        lead_time_hours=4,
    ),
}


# Map each attribution top_source → ordered list of actions.
ATTRIBUTION_TO_ACTIONS: Dict[str, List[str]] = {
    "traffic": ["odd_even", "traffic_diversion", "public_advisory"],
    "construction": ["construction_shutdown", "dust_control", "inspection"],
    "industrial": ["industrial_audit", "inspection", "public_advisory"],
    "stubble_burning": ["public_advisory", "waste_burning", "odd_even"],
    "biomass_burning": ["waste_burning", "public_advisory"],
    "waste_burning": ["waste_burning", "inspection", "public_advisory"],
    "urban_form": ["dust_control", "public_advisory"],
    "mixed": ["inspection", "public_advisory", "dust_control"],
}


def action_for_attribution(top_source: str) -> List[ActionDef]:
    """Return ranked action defs for the dominant attribution source."""
    codes = ATTRIBUTION_TO_ACTIONS.get(top_source, ["inspection", "public_advisory"])
    return [ACTION_TYPES[c] for c in codes]


def recommended_actions_for_ward(
    top_source: str,
    current_aqi: float,
) -> List[Dict]:
    """Render recommended actions as API-ready dicts."""
    actions = action_for_attribution(top_source)
    # If AQI is extreme, push shutdown-style actions to the front.
    out = []
    for a in actions:
        out.append({
            "action_code": a.code,
            "title": a.title,
            "description": a.description,
            "expected_aqi_delta": round(a.max_expected_delta, 1),
            "estimated_cost_inr": a.estimated_cost_inr,
            "lead_time_hours": a.lead_time_hours,
            "priority": "primary" if out == [] else "secondary",
        })
    if current_aqi > 350 and out:
        # Promote construction_shutdown / odd_even if available.
        for i, item in enumerate(out):
            if item["action_code"] in ("construction_shutdown", "odd_even"):
                out.insert(0, out.pop(i))
                out[0]["priority"] = "primary"
                break
    return out
