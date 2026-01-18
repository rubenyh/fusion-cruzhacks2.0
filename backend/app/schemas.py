# schemas.py
from uagents import Model
from typing import Dict, Any, List, Optional

class DetectionInput(Model):
    detection_result: Dict[str, Any]
    request_id: str
    callback_url: str

class DeepSearchRequest(Model):
    detection_result: Dict[str, Any]
    request_id: str
    callback_url: str

class CleanedEvidence(Model):
    product_name_text: Optional[str] = None
    brand_text: Optional[str] = None
    additional_findings: List[str] = []
    recalls: List[Dict[str, Any]] = []
    lawsuits: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

class WriterRequest(Model):
    request_id: str
    callback_url: str
    product_name: str
    cleaned_evidence: CleanedEvidence
    aggregated_answers: List[str] = []
    all_sources: List[Dict[str, Any]] = []
    confidence: float = 0.0
