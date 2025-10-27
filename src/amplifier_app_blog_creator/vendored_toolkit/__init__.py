"""
Vendored Toolkit Utilities

Temporarily vendored from amplifier-app-cli/toolkit until toolkit
is properly packaged and distributed.

Source: microsoft/amplifier-dev/amplifier-app-cli/toolkit/utilities/
Date: 2025-10-26

These files are UNMODIFIED copies for easy refactoring when toolkit
becomes available as a proper package.
"""

# File operations with cloud-sync retry logic
from .file_ops import append_jsonl
from .file_ops import discover_files
from .file_ops import read_json
from .file_ops import safe_read_text
from .file_ops import safe_write_text
from .file_ops import validate_path_exists
from .file_ops import write_json

# Progress reporting
from .progress import ProgressReporter
from .progress import SimpleSpinner
from .progress import log_stage
from .validation import validate_file_extension

# Validation utilities
from .validation import validate_input_path
from .validation import validate_json_structure
from .validation import validate_minimum_files
from .validation import validate_not_empty
from .validation import validate_output_path
from .validation import validate_pattern
from .validation import validate_range

__all__ = [
    # File ops
    "write_json",
    "read_json",
    "safe_write_text",
    "safe_read_text",
    "discover_files",
    "validate_path_exists",
    "append_jsonl",
    # Progress
    "ProgressReporter",
    "SimpleSpinner",
    "log_stage",
    # Validation
    "validate_input_path",
    "validate_output_path",
    "validate_minimum_files",
    "validate_pattern",
    "validate_file_extension",
    "validate_json_structure",
    "validate_range",
    "validate_not_empty",
]
