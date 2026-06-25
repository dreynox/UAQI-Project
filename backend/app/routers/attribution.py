"""Attribution router: source attribution for wards."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.attribution import Attribution
from app.models.ward import Ward
from app.utils.envelope import ok

router = APIRouter()


@router.get("/wards/{ward_id}/attribution")
def ward_attribution(ward_id: int, db: Session = Depends(get_db)):
    """Top source attribution with confidence and per-agent evidence."""
    w = db.query(Ward).filter(Ward.id == ward_id).first()
    if not w:
        raise HTTPException(status_code=404, detail=f"Ward {ward_id} not found")
    attr = (
        db.query(Attribution)
        .filter(Attribution.ward_id == ward_id)
        .order_by(Attribution.computed_at.desc())
        .first()
    )
    if not attr:
        return ok(None, warnings=[f"No attribution computed yet for ward {ward_id}"], city=w.city_id)
    import json
    return ok({
        "ward_id": w.id,
        "ward_name": w.name,
        "top_source": attr.top_source,
        "confidence": round(attr.confidence, 3),
        "source_breakdown": json.loads(attr.source_breakdown_json),
        "agent_evidence": json.loads(attr.agent_evidence_json),
        "explanation": attr.explanation,
        "computed_at": attr.computed_at.isoformat(),
    }, city=w.city_id)