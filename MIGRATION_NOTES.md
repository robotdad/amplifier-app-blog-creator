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

## Stage-Based Refactoring (2025-01-26)

### From Monolithic to Modular

**Previous Architecture**:
- Single `run_pipeline()` function
- Blocking `input()` for user feedback
- Print statements throughout logic
- Hard to test stages independently

**New Architecture**:
- `core/` - Pure stage functions (no UI, no blocking I/O)
- `cli/` - CLI adapter (display + input handling)
- `workflow.py` - Stage orchestrator
- Progress via optional callbacks

**Benefits**:
- Each stage independently testable
- No blocking in core logic
- Ready for web interface
- Better separation of concerns
- Clearer progress visibility

**What Didn't Change**:
- Session management (`session.py`)
- Review implementations (`reviewers/`)
- Defensive utilities (`utils/`)
- Vendored toolkit
- Illustration phase

**Philosophy Applied**:
- Ruthless simplicity: minimal abstractions, clear contracts
- Modular design: stages are "bricks", interfaces are "studs"
- Each stage regeneratable from signature

---

## Web Interface Addition (2025-10-26)

### From CLI-Only to Dual-Interface

**Web layer added as parallel adapter:**

**New Module** (`web/`):
- FastAPI application with async/SSE support
- Jinja2 templates for 4 workflow stages
- HTMX for dynamic updates (no page reloads)
- CodeMirror 6 for rich markdown editing
- Design system: "Sophisticated warmth" aesthetic

**Technology Stack:**
- FastAPI + Uvicorn (async web serving)
- HTMX (dynamic HTML)
- Jinja2 (server-side templates)
- CodeMirror 6 (rich editor)
- Server-Sent Events (real-time progress)

**Why Python-Only:**
- Critical for uvx distribution
- No Node.js build step required
- Single stack to maintain
- Simpler deployment

**Benefits**:
- Rich editing experience (syntax highlighting, live preview)
- Real-time visual progress during AI processing
- Professional aesthetic impresses executives
- Easier to demo to stakeholders
- File preview before processing
- Foundation for chat feedback (Phase 3)

**What Didn't Change**:
- All of `core/` (zero changes to business logic)
- All of `cli/` (CLI mode unaffected)
- Session management (works for both modes)
- Dependencies on style/image/markdown modules

**Mode Selection:**
```bash
blog-creator --mode cli    # Traditional CLI (default)
blog-creator --mode web    # Opens browser with web UI
```

**Philosophy Applied**:
- Ruthless simplicity: web is thin adapter (like CLI), reuses all core/
- Modular design: web/ is independent brick, consumes same studs as cli/
- No changes to existing working code (cli/, core/)
- Browser auto-open via Python stdlib (webbrowser module)

---

## Quick Reference

**Quick Start (uvx - primary)**:
```bash
uvx --from git+https://github.com/robotdad/amplifier-app-blog-creator blog-creator \
  --idea notes.md \
  --writings-dir ~/posts/
```

**Development Install**: `cd amplifier-app-blog-creator && uv sync --dev`
**Resume**: Add `--resume` flag
**Illustrate**: Add `--illustrate --style "minimalist diagrams"`

---

**Migration Date**: 2025-10-22
**Status**: Documentation complete
**Next**: Code implementation following DDD process
