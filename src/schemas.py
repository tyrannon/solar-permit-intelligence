"""Data schemas using Pydantic models."""

from datetime import datetime
from typing import Dict, Optional, List
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class RuleStatus(str, Enum):
    """Status of a validation rule."""
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class RuleSeverity(str, Enum):
    """Severity level of a rule result."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ExtractedFields(BaseModel):
    """Structured fields extracted from a solar permit document."""

    project_address: Optional[str] = Field(None, description="Full street address of installation site")
    jurisdiction: Optional[str] = Field(None, description="City or county with permitting authority")
    contractor_name: Optional[str] = Field(None, description="Licensed solar contractor name")
    system_size_kw: Optional[float] = Field(None, description="Total DC system size in kilowatts")
    module_count: Optional[int] = Field(None, description="Total number of solar panels")
    module_model: Optional[str] = Field(None, description="Solar panel manufacturer and model")
    inverter_model: Optional[str] = Field(None, description="Inverter manufacturer and model")
    main_service_panel_rating: Optional[int] = Field(None, description="Main electrical panel amperage rating")
    battery_present: Optional[bool] = Field(None, description="Whether energy storage system is included")
    battery_model: Optional[str] = Field(None, description="Battery manufacturer and model, if present")

    @field_validator('system_size_kw')
    @classmethod
    def validate_system_size(cls, v):
        """Ensure system size is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError('system_size_kw must be positive')
        return v

    @field_validator('module_count', 'main_service_panel_rating')
    @classmethod
    def validate_positive_int(cls, v):
        """Ensure integer fields are positive if provided."""
        if v is not None and v <= 0:
            raise ValueError('Value must be positive')
        return v


class ConfidenceScores(BaseModel):
    """Confidence scores for each extracted field (0.0 to 1.0)."""

    project_address: Optional[float] = None
    jurisdiction: Optional[float] = None
    contractor_name: Optional[float] = None
    system_size_kw: Optional[float] = None
    module_count: Optional[float] = None
    module_model: Optional[float] = None
    inverter_model: Optional[float] = None
    main_service_panel_rating: Optional[float] = None
    battery_present: Optional[float] = None
    battery_model: Optional[float] = None


class RuleResult(BaseModel):
    """Result of applying a single validation rule."""

    rule_name: str = Field(..., description="Identifier for the rule")
    status: RuleStatus = Field(..., description="Pass, fail, or review required")
    message: str = Field(..., description="Human-readable explanation")
    severity: RuleSeverity = Field(..., description="Importance level")


class ProcessedDocument(BaseModel):
    """Complete processed document with all pipeline outputs."""

    document_id: str = Field(..., description="Unique identifier (typically filename)")
    extraction_timestamp: datetime = Field(default_factory=datetime.now, description="When extraction occurred")

    # Extracted data
    fields: ExtractedFields = Field(..., description="Extracted field values")
    confidence_scores: ConfidenceScores = Field(default_factory=ConfidenceScores, description="Confidence per field")

    # Validation results
    rule_results: List[RuleResult] = Field(default_factory=list, description="Results of all validation rules")

    # Metadata
    source_file: Optional[str] = Field(None, description="Path to original PDF")
    page_count: Optional[int] = Field(None, description="Number of pages in document")
    processing_notes: List[str] = Field(default_factory=list, description="Warnings or notes from processing")

    @property
    def passed_all_rules(self) -> bool:
        """Check if all rules passed."""
        return all(r.status == RuleStatus.PASS for r in self.rule_results)

    @property
    def has_failures(self) -> bool:
        """Check if any rules failed."""
        return any(r.status == RuleStatus.FAIL for r in self.rule_results)

    @property
    def needs_review(self) -> bool:
        """Check if any rules require review."""
        return any(r.status == RuleStatus.REVIEW_REQUIRED for r in self.rule_results)
