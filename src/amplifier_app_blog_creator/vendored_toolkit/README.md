# Vendored Toolkit Utilities

**Source**: microsoft/amplifier-dev/amplifier-app-cli/toolkit/
**Date Vendored**: 2025-10-26
**Reason**: Toolkit is not packaged with amplifier-app-cli distribution

---

## What's Vendored

Copied from `amplifier-app-cli/toolkit/utilities/`:
- `file_ops.py` - Robust file I/O with cloud-sync retry logic
- `progress.py` - Progress reporting and stage logging
- `validation.py` - Input validation utilities

**Total**: ~500 LOC of utility code

---

## Why Vendored

The toolkit directory exists in the amplifier-app-cli source repo but is NOT included in the distribution package:

```toml
# amplifier-app-cli/pyproject.toml
packages = ["amplifier_app_cli"]  # toolkit is NOT listed
```

**Result**: When users install amplifier-app-cli via git source, they get `amplifier_app_cli` package but not `toolkit`.

**Our need**: We want the robust file I/O, progress reporting, and validation utilities.

**Solution**: Vendor the specific files we need until toolkit is properly packaged.

---

## Refactoring Later

**When toolkit is packaged with amplifier-app-cli**:

1. Remove this `vendored_toolkit/` directory
2. Update imports:
   ```python
   # Change from:
   from .vendored_toolkit.file_ops import write_json

   # To:
   from amplifier_app_cli.toolkit import write_json
   ```
3. Update pyproject.toml to use amplifier-app-cli dependency

**How to know when ready**: Check if `amplifier-app-cli` pyproject.toml includes toolkit in packages list.

---

## Files in This Directory

- `README.md` - This file (explains vendoring)
- `__init__.py` - Package marker, exports utilities
- `file_ops.py` - From toolkit/utilities/file_ops.py
- `progress.py` - From toolkit/utilities/progress.py
- `validation.py` - From toolkit/utilities/validation.py

**No modifications made** - copied as-is for easy diff checking when refactoring.

---

## Attribution

Original code: Microsoft MADE:Explorations Team
Source: https://github.com/microsoft/amplifier-dev/tree/main/amplifier-app-cli/toolkit
License: MIT (same as amplifier-app-cli)

Vendored temporarily until toolkit is properly packaged and distributed.
