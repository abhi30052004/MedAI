"""Pydantic schemas for AI analysis and extracted items."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID


# ── Extracted Items ──────────────────────────────────────────────

class ExtractedItemResponse(BaseModel):
    id: int
    org_id: UUID
    case_id: int
    document_id: int
    category: str
    value: str
    details: Optional[Dict[str, Any]] = None
    source_page: Optional[int] = None
    source_snippet: Optional[str] = None
    confidence: Optional[float] = None
    ai_generated: bool
    review_status: str
    original_value: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ExtractedItemReview(BaseModel):
    """PATCH body for reviewing an extracted item."""
    action: str  # confirm | edit | reject
    value: Optional[str] = None  # new value for 'edit'


# ── Case Summary ────────────────────────────────────────────────

class CaseSummaryResponse(BaseModel):
    id: int
    case_id: int
    version: int
    summary_json: Dict[str, Any]
    model_used: str
    provider: str
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Analysis Status ─────────────────────────────────────────────

class AnalysisStatusResponse(BaseModel):
    status: str  # not_started | processing | completed
    latest_summary: Optional[CaseSummaryResponse] = None
    extracted_items_count: int = 0
    pending_review_count: int = 0
