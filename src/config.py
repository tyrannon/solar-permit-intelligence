"""Configuration constants for the solar permit intelligence pipeline."""

from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_LABELED_DIR = DATA_DIR / "labeled"

# Output directory
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Confidence thresholds
MIN_CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence to accept an extraction
REVIEW_CONFIDENCE_THRESHOLD = 0.85  # Below this, flag for review

# System size validation ranges (kW)
MIN_RESIDENTIAL_SYSTEM_SIZE = 2.0
MAX_RESIDENTIAL_SYSTEM_SIZE = 20.0

# Module wattage assumptions for validation (kW per module)
MIN_MODULE_WATTAGE = 0.3
MAX_MODULE_WATTAGE = 0.45

# Service panel validation
MIN_SERVICE_PANEL_RATING = 100  # Amps

# File naming patterns
RAW_PDF_PATTERN = "permit_*.pdf"
PROCESSED_JSON_PATTERN = "permit_*_processed.json"
EXTRACTED_JSON_PATTERN = "permit_*_extracted.json"
TRUTH_JSON_PATTERN = "permit_*_truth.json"

# Logging
LOG_FILE = OUTPUTS_DIR / "pipeline.log"
ERROR_LOG_FILE = OUTPUTS_DIR / "error_log.txt"
