# Migration Notes: Scenarios to Amplifier-Dev

**Quick reference for lessons learned during this migration**

---

## What Changed

### From Two Tools to One App

**Before**:
- scenarios/blog_writer (standalone)
- scenarios/article_illustrator (standalone)
- Run separately, manual handoff

**After**:
- amplifier-app-blog-creator (unified)
- Sequential phases in one workflow
- Optional `--illustrate` flag

### From Vendored to Modular

**Before**: All code in each tool
**After**: Reusable modules + app logic

**Extracted Modules**:
- amplifier-module-image-generation (~570 LOC)
- amplifier-module-style-extraction (~200 LOC)
- amplifier-module-markdown-utils (~400 LOC)

---

## Critical Patterns

### 1. Git Sources (Not Paths)

```toml
# ✅ Works anywhere
[tool.uv.sources.amplifier-core]
git = "https://github.com/microsoft/amplifier-dev"
subdirectory = "amplifier-core"
branch = "main"

# ❌ Breaks standalone
[tool.uv.sources.amplifier-core]
path = "../../amplifier-core"
editable = true
```

### 2. Path Expansion

```python
# ✅ Expands ~ correctly
Path(config["writings_dir"]).expanduser()

# ❌ Looks for literal ~ directory
Path(config["writings_dir"])
```

### 3. Capability Registry

```python
# Register capability
coordinator.register_capability("style_extraction.analyzer", extractor)

# Use capability (cooperation mode)
extractor = coordinator.get_capability("style_extraction.analyzer")
if not extractor:
    # Standalone fallback
    extractor = StyleExtractor()
```

---

## Challenges Solved

1. **Microsoft vs Robotdad**: Can't modify microsoft core, create robotdad modules instead
2. **TOML Syntax**: Inline tables can't have newlines, use table format
3. **Workflow Unification**: Images need final content, so must follow content approval
4. **Module Boundaries**: Clear separation validated by api-contract-designer

---

## Testing Checklist

- [x] Clean install from git sources
- [x] Content phase workflow
- [x] Illustration phase workflow
- [x] State persistence and resume
- [x] Path handling with `~`
- [x] Module cooperation via capability registry
- [x] Module standalone operation

---

## Quick Reference

**Quick Start (uvx - primary)**:
```bash
uvx --from git+https://github.com/robotdad/amplifier-dev#subdirectory=amplifier-app-blog-creator \
  blog-creator --idea notes.md --writings-dir ~/posts/
```

**Development Install**: `cd amplifier-app-blog-creator && uv sync --dev`
**Resume**: Add `--resume` flag
**Illustrate**: Add `--illustrate --style "minimalist diagrams"`

---

**Migration Date**: 2025-10-22
**Status**: Documentation complete
**Next**: Code implementation following DDD process
