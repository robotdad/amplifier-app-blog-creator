# How I Built This: Blog Creator

**The story of migrating and unifying two scenario tools into a production Amplifier app**

---

## The Journey

### Starting Point

Two working scenario tools:
- `blog_writer`: Style-aware content generation with review cycles
- `article_illustrator`: AI-powered image generation and placement

Both solved real problems, both production-tested, but siloed and not reusable.

### The Vision

Create a unified workflow that:
1. Generates content matching your voice
2. Optionally illustrates that content
3. Follows amplifier-dev patterns (git sources, capability registry)
4. Contributes reusable modules to ecosystem

### The Metacognitive Recipe

**Content Phase**:
1. Understand author's style from samples
2. Generate content matching that style
3. Verify accuracy against source material
4. Verify consistency with style profile
5. Incorporate human feedback
6. Iterate until approved

**Illustration Phase**:
1. Analyze finalized content structure
2. Identify where images add value
3. Generate contextual prompts
4. Create images with best available API
5. Insert at optimal positions

**Key Insight**: Images require finalized content for context, so illustration must follow content approval.

---

## Architecture Decisions

### Decision 1: Unified App vs Separate Tools

**Chose**: Single app with optional illustration phase
**Why**:
- Workflow dependency (images need final content)
- State continuity (single session)
- Better UX (one command)
**Alternative**: Separate tools with state handoff - more complex, worse UX

### Decision 2: Extract 3 Modules

**Chose**: image-generation, style-extraction, markdown-utils as modules
**Why**:
- Clear domain boundaries
- Reusable by other apps
- Follows amplifier-dev patterns
**Alternative**: Monolithic app - misses reusability opportunity

### Decision 3: Git Sources

**Chose**: All dependencies via git sources
**Why**:
- Enables frictionless sharing
- Works anywhere
- Microsoft core, robotdad modules
**Alternative**: Path dependencies - breaks standalone installation

### Decision 4: Capability Registry

**Chose**: Modules register capabilities for cooperation
**Why**:
- Avoids duplicate configuration
- Enables module sharing
- Follows amplifier-dev patterns
**Alternative**: Independent module instances - duplicate work

### Decision 5: uvx as Primary Usage

**Chose**: `uvx` for quickstart, clone only for development
**Why**:
- Frictionless user experience (no install needed)
- Users don't need to manage git clones
- Auto-updates to latest version
- Developers still have full clone for modifications
**Alternative**: Clone-first - more friction for casual users

---

## Implementation Approach

### Phase 1: Agent Consultation

Consulted specialized agents:
- **zen-architect**: Validated architecture, suggested simplifications
- **api-contract-designer**: Designed clean module interfaces
- **integration-specialist**: Confirmed git source and capability patterns

### Phase 2: DDD Process

Followed Document-Driven Development:
1. Created comprehensive plan (ai_working/ddd/plan.md)
2. Updated ALL documentation first (this phase)
3. Documented as if already working
4. User approval before coding
5. Implementation follows specification exactly

### Phase 3: Module Extraction

Migrated code from scenarios/:
- image-generation: ~570 LOC from article_illustrator
- style-extraction: ~200 LOC from blog_writer
- markdown-utils: ~400 LOC consolidated from both

Total: ~1,170 LOC of production-tested utility code

### Phase 4: Unified App

Combined workflows from both tools (~2,600 LOC):
- Content phase: blog_writer logic
- Illustration phase: article_illustrator logic
- Unified CLI with `--illustrate` flag
- Single session spanning both phases

---

## Code Structure

```
src/amplifier_app_blog_creator/
├── core/                        # Pure business logic
│   ├── stages/                  # Independent stage functions
│   │   ├── style_extraction.py
│   │   ├── draft_generation.py
│   │   ├── review.py
│   │   └── revision.py
│   ├── workflow.py              # Stage orchestration
│   └── models.py                # Shared data models
├── cli/                         # CLI interface
│   ├── ui.py                    # Display logic
│   ├── input_handler.py         # User input
│   └── main.py                  # CLI entry point
├── web/                         # Web interface
│   ├── app.py                   # FastAPI application
│   ├── routes/                  # HTTP endpoints
│   │   ├── sessions.py          # Session + workflow management
│   │   ├── progress.py          # SSE progress streaming
│   │   └── content.py           # File preview, markdown rendering
│   ├── templates/               # Jinja2 templates
│   │   ├── base.html            # Base layout
│   │   ├── setup.html           # Stage 1: Input collection
│   │   ├── progress.html        # Stage 2: AI processing
│   │   ├── review.html          # Stage 3: Edit & review
│   │   └── complete.html        # Stage 4: Success
│   └── static/                  # Static assets
│       ├── css/                 # Design tokens, layout, components
│       └── js/                  # HTMX, CodeMirror, interactions
├── reviewers/                   # Review implementations
│   ├── source_reviewer.py       # Fact-checking
│   └── style_reviewer.py        # Voice consistency
├── session.py                   # State management (shared by CLI and web)
├── illustration_phase.py        # Image generation (unchanged)
├── utils/                       # Defensive utilities
└── vendored_toolkit/            # Progress, file ops, validation
```

---

## Architectural Evolution

### Phase 1: Stage-Based Refactoring

**The Need:**

Original implementation used monolithic pipeline:
- Single `run_pipeline()` function handled all stages
- Blocking I/O (`input()`) stopped execution for user feedback
- UI concerns mixed with business logic
- Hard to test individual stages
- Couldn't support alternative interfaces (web)

**The Solution:**

Refactored to clean separation of concerns:

**Core Logic** (`core/`):
- Independent stage functions with clear contracts
- No UI dependencies (print, input, etc.)
- Progress via optional callbacks
- Fully testable in isolation
- Async throughout

**CLI Adapter** (`cli/`):
- Thin layer over core workflow
- Handles all display and input
- Preserves user experience
- Easy to swap for web/API adapters

**Stage Contracts:**

Each stage is a pure async function:

```python
async def extract_style(
    writings_dir: Path,
    progress_callback: Callable[[str], None] | None = None
) -> StyleProfile:
    """Extract writing style from samples."""
    # Pure logic, no UI
    # Optional progress updates
    # Returns typed result

async def generate_draft(
    brain_dump: str,
    style_profile: StyleProfile,
    additional_instructions: str | None = None,
    progress_callback: Callable[[str], None] | None = None
) -> str:
    """Generate blog post from idea."""
    # Pure generation logic
    # No blocking, no print statements
    # Returns markdown string
```

**Workflow Orchestrator:**

Coordinates stages with session state:

```python
class BlogCreatorWorkflow:
    """Orchestrates blog creation stages."""

    async def run_style_extraction(self, writings_dir: Path) -> StyleProfile
    async def run_draft_generation(self, brain_dump: str) -> str
    async def run_review(self) -> ReviewResult
    async def run_revision(self, feedback: RevisionFeedback) -> str
```

**Benefits:**
- Stage-by-stage execution
- Clear progress visibility
- Resumable at any stage
- Ready for web/API interfaces
- Better testability

---

### Phase 2: Web Interface

**The Need:**

CLI is functional but limited:
- No live markdown preview while editing
- File-based feedback is clunky (edit file, save, continue)
- Hard to demo to stakeholders (console output not visually impressive)
- Real-time progress only via console output
- Barrier for non-CLI-comfortable users

**The Solution:**

Added web interface as parallel adapter to core logic:

**Web Adapter** (`web/`):
- FastAPI application with SSE support
- Jinja2 templates for server-side rendering
- HTMX for dynamic HTML updates without page reloads
- CodeMirror 6 for rich markdown editing
- Pure UI layer (NO business logic)

**Technology Choices:**

**FastAPI + HTMX** (chosen over React/Vue):
- Python-only stack (critical for uvx distribution)
- Simple mental model (server renders HTML)
- No build step required
- Progressive enhancement (works without JavaScript)
- SSE support built-in

**CodeMirror 6** (chosen for markdown editor):
- Professional syntax highlighting
- Keyboard shortcuts and vim mode
- Accessible (screen reader support)
- Custom theming (matches warm aesthetic)
- Vendored bundle (no npm required)

**Design System:**

Created comprehensive design specifications:
- **Aesthetic:** "Sophisticated warmth" - professional polish + approachability
- **Colors:** Warm neutrals with amber accents
- **Motion:** Deliberate elegance (150-700ms timing protocol)
- **Typography:** System font stack with 1.25 ratio scale
- **Shadows:** Multi-layer depth for dimensionality
- **Accessibility:** WCAG AA compliance throughout

**4-Stage User Journey:**

1. **Setup** - File path inputs with validation, preview capability
2. **Progress** - Real-time SSE streaming with subtle animations
3. **Review** - Rich editor with slide-out review drawer
4. **Complete** - Celebration animation and download

**Slide-Out Drawer Pattern:**

Review panel slides from right (future-proofs for chat):
- Full-width editor by default (maximum editing space)
- Toggle drawer with badge showing issue count
- Smooth 350ms spring animation
- Keyboard shortcut: Cmd/Ctrl + R
- Same pattern will host chat interface in Phase 3

**Benefits:**
- Rich editing experience (syntax highlighting, live preview)
- Visual progress during AI processing (no waiting in dark)
- Easier to demo (polished, professional appearance)
- Impresses executives while remaining approachable
- Foundation for chat-based feedback (Phase 3)

**Design Principles Applied:**

**Ruthless Simplicity:**
- Web layer is thin adapter (like CLI)
- Reuses all core/ logic (zero duplication)
- HTMX simpler than React (server-rendered HTML)
- No complex state management (server owns state)

**Modular Design:**
- web/ is independent "brick" alongside cli/
- Both consume same core/ "studs" (BlogCreatorWorkflow)
- Can develop/test/improve independently
- Adding web didn't require changing core/

---

## Module Composition

This app demonstrates how Amplifier modules compose:

```python
# Import reusable modules
from amplifier_module_style_extraction import StyleExtractor
from amplifier_module_image_generation import ImageGenerator
from amplifier_module_markdown_utils import extract_title, slugify

# Or use via capability registry
style_extractor = coordinator.get_capability("style_extraction.analyzer")
image_generator = coordinator.get_capability("image_generation.orchestrator")

# Compose into app workflow
profile = await style_extractor.extract_style(writings_dir)
draft = await generate_with_style(idea, profile)
illustrated = await add_illustrations(draft, image_generator)
```

---

## Key Patterns

### 1. Checkpoint Pattern

Save state after every expensive operation:

```python
# After style extraction
state.style_profile = profile
state.save()

# After draft generation
state.current_draft = draft
state.save()

# After each image
state.images.append(result)
state.save()
```

**Enables**: Interrupt and resume anytime without losing work

### 2. Capability Registry Usage

```python
# Try capability first (cooperation)
extractor = coordinator.get_capability("style_extraction.analyzer")

# Fall back to direct import (independence)
if not extractor:
    from amplifier_module_style_extraction import StyleExtractor
    extractor = StyleExtractor()
```

**Enables**: Modules share resources when present, work standalone otherwise

### 3. Path Expansion

```python
# ALWAYS expand ~ in paths from config
writings_dir = Path(config.get("writings_dir", "~/writings")).expanduser()
data_dir = Path(config.get("data_dir", "~/.data")).expanduser()
```

**Prevents**: File not found errors with tilde paths

---

## Cost Estimates

**Content Phase** (using Claude):
- Style extraction: ~$0.01
- Draft generation: ~$0.05
- Reviews: ~$0.02 each
- **Total content**: ~$0.10-$0.15 per post

**Illustration Phase** (optional):
- Content analysis: ~$0.01
- Prompt generation: ~$0.01 per image
- Image generation: ~$0.04 per image (GPT-Image-1)
- **Total for 5 images**: ~$0.20-$0.25

**Complete illustrated post**: ~$0.35-$0.40 total

---

## Development

### Setup

```bash
cd amplifier-app-blog-creator
uv sync --dev
```

### Run Tests

```bash
uv run pytest
```

### Type Checking

```bash
uv run pyright
```

---

## Learn More

- [HOW_I_BUILT_THIS.md](./HOW_I_BUILT_THIS.md) - Complete creation story and decisions
- [MIGRATION_NOTES.md](./MIGRATION_NOTES.md) - Lessons from scenarios/ migration
- [Module READMEs](../) - Documentation for each module
- [Amplifier Documentation](https://github.com/microsoft/amplifier-dev/blob/main/docs/)

---

## Contributing

See the main [Amplifier contributing guide](https://github.com/microsoft/amplifier-dev/blob/main/CONTRIBUTING.md).

---

## License

MIT License - See [LICENSE](https://github.com/robotdad/amplifier-dev/blob/main/LICENSE) file.
