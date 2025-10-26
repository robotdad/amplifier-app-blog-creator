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
from .file_ops import (
    write_json,
    read_json,
    safe_write_text,
    safe_read_text,
    discover_files,
    validate_path_exists,
    append_jsonl,
)

# Progress reporting
from .progress import (
    ProgressReporter,
    SimpleSpinner,
    log_stage,
)

# Validation utilities
from .validation import (
    validate_input_path,
    validate_output_path,
    validate_minimum_files,
    validate_pattern,
    validate_file_extension,
    validate_json_structure,
    validate_range,
    validate_not_empty,
)

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
