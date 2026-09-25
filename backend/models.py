from typing import Optional, List, Any
from pydantic import BaseModel, Field

class TenderRecord(BaseModel):
    id: Optional[int] = None
    tender_id: str
    reference_no: Optional[str] = None
    department: Optional[str] = None
    admin_type: Optional[str] = None
    authority: Optional[str] = None
    locality: Optional[str] = None
    zone: Optional[str] = None
    ward: Optional[str] = None
    title: Optional[str] = None
    work_description: Optional[str] = None
    tender_value: Optional[float] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    published_date: Optional[str] = None
    bid_opening_date: Optional[str] = None
    work_order_date: Optional[str] = None
    work_period_days: Optional[int] = None
    expected_completion_date: Optional[str] = None
    status: Optional[str] = None
    status_note: Optional[str] = None
    source_url: Optional[str] = None

class ExtractionRequest(BaseModel):
    raw_page_text: str
    structured_hints: Optional[dict] = Field(default_factory=dict)
    source_url: Optional[str] = None

class ExtractedTender(BaseModel):
    tender_id: Optional[str] = None
    reference_no: Optional[str] = None
    department: Optional[str] = None
    admin_type: Optional[str] = None
    authority: Optional[str] = None
    locality: Optional[str] = None
    zone: Optional[str] = None
    ward: Optional[str] = None
    title: Optional[str] = None
    work_description: Optional[str] = None
    tender_value: Optional[float] = None
    published_date: Optional[str] = None
    bid_opening_date: Optional[str] = None
    work_order_date: Optional[str] = None
    work_period_days: Optional[int] = None
    status: Optional[str] = None
    source_url: Optional[str] = None

class AnalysisRequest(BaseModel):
    tender: ExtractedTender

class EvidenceItem(BaseModel):
    id: Optional[int] = None
    tender_id: str
    title: Optional[str] = None
    authority: Optional[str] = None
    locality: Optional[str] = None
    published_date: Optional[str] = None
    similarity_score: Optional[float] = None
    time_difference_days: Optional[int] = None
    source_url: Optional[str] = None
    evidence_type: Optional[str] = "TENDER_RECORD"
    evidence_text: Optional[str] = None
    source_date: Optional[str] = None

class AnalysisResponse(BaseModel):
    current_tender: ExtractedTender
    is_urban_scope: bool
    scope_note: Optional[str] = None
    silence_flag: bool = False
    repetition_flag: bool = False
    status_code: str = "GREEN"  # "GREEN", "ORANGE", "RED", "ORANGE_RED"
    status_headline: str = "No accountability signal detected"
    similar_tender: Optional[TenderRecord] = None
    similarity_score: float = 0.0
    time_difference_days: Optional[int] = None
    portal_search_note: Optional[str] = "Official portal search requires user interaction."
    explanation: str
    evidence_list: List[EvidenceItem] = Field(default_factory=list)

class RTIDraftRequest(BaseModel):
    tender_id: str
    authority: Optional[str] = None
    title: Optional[str] = None
    reference_no: Optional[str] = None
    silence_flag: bool = False
    repetition_flag: bool = False
    similar_tender_id: Optional[str] = None
    similarity_score: Optional[float] = None

class RTIDraftResponse(BaseModel):
    tender_id: str
    subject: str
    recipient: str
    questions: List[str]
    full_draft_text: str
