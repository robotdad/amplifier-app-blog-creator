# amplifier-app-blog-creator

**Transform ideas into polished, illustrated blog posts matching your unique voice**

AI-powered blog creation with rich markdown editor, real-time progress, and style-aware generation. Run locally via uvx—no installation required.

---

## Quick Start (Recommended)

**Run directly with uvx:**

```bash
uvx --from git+https://github.com/robotdad/amplifier-app-blog-creator blog-creator --mode web
```

Your browser opens with a polished interface:
- Rich markdown editor with syntax highlighting
- Real-time AI progress visualization
- One-click approval or iterative refinement

**First time?** The app will prompt for your Anthropic API key (stored in session only, never saved).

---

## The Problem

You have ideas worth sharing, but:
- Writing takes hours of focused effort
- Generic AI writing doesn't capture your voice
- Finding relevant images is time-consuming
- Quality and consistency suffer under time pressure

---

## The Solution

Blog Creator uses AI to analyze your writing style and generate content that sounds like you:

**Stage 1: Style Extraction**
Analyzes your writing samples to extract your unique style profile.

**Stage 2: Draft Generation**
Generates initial blog post matching your voice and capturing your ideas.

**Stage 3: Review**
Automatically reviews draft for source accuracy and style consistency.

**Stage 4: Revision**
Incorporates feedback and refines the draft through iterative improvement.

**Stage 5: Illustration (Optional)**
Analyzes content and generates contextual AI illustrations.

**Result**: A complete blog post that sounds like you and looks professional.

---

## Web Interface (Recommended)

**Start the web interface:**

```bash
# Using uvx (no installation needed)
uvx --from git+https://github.com/robotdad/amplifier-app-blog-creator blog-creator --mode web

# Or if installed locally
blog-creator --mode web
```

Your browser opens automatically at http://localhost:8000

**Features:**
- 🎨 **Rich markdown editor** - Syntax highlighting, line numbers, live preview
- ⚡ **Real-time progress** - Watch AI work through each stage with time estimates
- 📄 **Content preview** - See your idea and writing samples before starting
- ✓ **Visual review** - Source accuracy and style feedback in slide-out panel
- 🎯 **One-click actions** - Approve immediately or iterate with AI
- 💎 **Professional polish** - Warm aesthetic designed to impress

**First-time setup:**
- App checks for ANTHROPIC_API_KEY environment variable
- If not found, friendly configuration screen appears
- Enter your API key (stored in session only, never saved to disk)
- Continue to main workflow

---

## Command-Line Interface

**For automation or scripting:**

```bash
# Using uvx
uvx --from git+https://github.com/robotdad/amplifier-app-blog-creator blog-creator \
  --idea rough_notes.md \
  --writings-dir ~/my_blog_posts/

# Or if installed locally
blog-creator --idea rough_notes.md --writings-dir ~/my_blog_posts/
```

CLI provides file-based feedback and console output for terminal-based workflows.

---

## Installation (For Development)

**Most users should use uvx** (no installation needed). Install locally only for development:

```bash
# Clone the repository
git clone https://github.com/robotdad/amplifier-app-blog-creator
cd amplifier-app-blog-creator

# Install dependencies
uv sync

# Run locally
uv run blog-creator --mode web
```

### Content Only

```bash
uv run blog-creator \
  --idea rough_notes.md \
  --writings-dir ~/my_blog_posts/
```

### Complete Illustrated Post

```bash
uv run blog-creator \
  --idea rough_notes.md \
  --writings-dir ~/my_blog_posts/ \
  --with-images \
  --max-images 3 \
  --image-style "minimalist technical diagrams"
```

---

## CLI Usage Guide

### Prepare Your Inputs

**1. Your Idea** (`rough_notes.md`):
```markdown
# Idea: Why Event-Driven Architecture Matters

Random thoughts:
- Decoupling is key
- Async communication patterns
- Example from my work with payment processing
- Resilience and scalability benefits
```

**2. Your Writings** (`~/my_blog_posts/`):
- 3-5 existing blog posts
- Same genre/audience
- Markdown format
- Represents your current voice

### Run the Tool

```bash
# Basic usage
blog-creator --idea rough_notes.md --writings-dir ~/my_blog_posts/

# With custom instructions
blog-creator \
  --idea notes.md \
  --writings-dir posts/ \
  --instructions "Keep under 1000 words, remove company names"

# Resume from saved session
blog-creator --resume

# Start fresh (discard saved state)
blog-creator --reset --idea notes.md --writings-dir posts/
```

**The workflow**:
1. Style extraction analyzes your writing samples
2. Draft generation creates initial post matching your voice
3. Automated review checks accuracy and style
4. Interactive feedback allows you to refine the draft
5. Revision incorporates your feedback
6. Process iterates until you approve
7. Final post saved to session directory

### Provide Feedback

The tool saves drafts to `.data/blog_creator/<session>/draft_iter_N.md`

**Option 1: Inline Comments**
```markdown
This paragraph explains X [but needs a concrete example here].

Great point [expand this with the pirate ship metaphor].
```

**Option 2: Approve**
Type `approve` when ready.

**Option 3: Skip**
Type `skip` to continue without changes.

---

## Web Interface Guide

### Getting Started

1. **Start the server:**
   ```bash
   blog-creator --mode web
   ```
   Your browser opens automatically to http://localhost:8000

2. **Provide your inputs:**
   - Idea file path (type, browse, or drag-and-drop)
   - Writing samples directory path
   - Optional: Additional instructions

3. **Watch the AI work:**
   - Real-time progress through extraction, generation, and review stages
   - Clear time estimates and completion status

4. **Review and refine:**
   - Rich markdown editor with syntax highlighting
   - Live preview toggle
   - Review panel shows accuracy and style feedback
   - Iterate until satisfied or approve immediately

5. **Download your post:**
   - Final markdown file ready to publish

### Web Interface Features

**Rich Editing:**
- CodeMirror editor with markdown syntax highlighting
- Line numbers and keyboard shortcuts
- Live preview toggle (source ↔ rendered)
- Auto-save while editing

**Visual Progress:**
- Real-time updates via Server-Sent Events
- Progress bars for each AI stage
- Time estimates and actual completion times
- Smooth animations without page reloads

**Smart Inputs:**
- File path validation as you type
- Native file picker integration
- Drag-and-drop support
- Preview your idea and samples before starting

**Professional Polish:**
- Warm, sophisticated aesthetic
- Smooth stage transitions
- Celebration animation on completion
- Accessible (WCAG AA compliant)

---

## Command-Line Options

```bash
# Mode selection
--mode [cli|web]             # Interface mode (default: cli)

# CLI Mode - Required
--idea PATH                  # Your rough notes/brain dump
--writings-dir PATH          # Directory with your writing samples

# CLI Mode - Optional
--instructions TEXT          # Additional guidance (e.g., "remove company names")
--output PATH                # Custom output path (default: auto from title)
--with-images                # Enable illustration phase
--max-images N               # Maximum illustrations (default: 3)
--image-style TEXT           # Image style (e.g., "minimalist diagrams")
--resume                     # Resume from saved session
--reset                      # Discard saved state, start fresh
--max-iterations N           # Maximum refinement iterations (default: 10)
--verbose                    # Detailed logging

# Web Mode - Optional
--no-browser                 # Don't auto-open browser
--port N                     # Server port (default: 8000)
--host TEXT                  # Server host (default: localhost)
```

---

## Architecture

Blog Creator uses a clean separation between core logic and UI concerns, enabling both CLI and future web interfaces.

### Core Module (`core/`)

**Pure business logic with no UI dependencies:**

- `stages/` - Independent, testable stage functions
  - `style_extraction.py` - Extract writing style from samples
  - `draft_generation.py` - Generate blog post from idea
  - `review.py` - Review draft for accuracy and style
  - `revision.py` - Revise draft based on feedback
- `workflow.py` - Orchestrates stages with session management
- `models.py` - Shared data models (StyleProfile, ReviewResult, etc.)

**Each stage**:
- Accepts clear inputs (paths, data models)
- Returns typed outputs (models, strings)
- Supports optional progress callbacks
- Testable in isolation
- No blocking I/O

### CLI Adapter (`cli/`)

**Command-line interface built on core:**

- `ui.py` - Display functions (stage transitions, progress, reviews)
- `input_handler.py` - User input handling (feedback, approvals)
- `main.py` - CLI entry point and workflow orchestration

### Web Adapter (`web/`)

**Web interface built on core:**

- `app.py` - FastAPI application with SSE support
- `routes/` - HTTP endpoints for sessions, workflow, and progress
- `templates/` - Jinja2 templates for each stage
- `static/` - CSS (design tokens, components) and JavaScript (HTMX, CodeMirror)

**Technology stack:**
- FastAPI + Uvicorn for async web serving
- HTMX for dynamic HTML without page reloads
- Jinja2 for server-side templating
- CodeMirror 6 for rich markdown editing
- Server-Sent Events (SSE) for real-time progress

### Supporting Modules

**Preserved from original design:**

- `session.py` - File-based session state management
- `reviewers/` - Source and style review implementations
- `utils/` - Defensive utilities (LLM parsing, retry patterns, etc.)
- `vendored_toolkit/` - File operations, progress reporting, validation

### Stage Flow

```
┌──────────────────────────────────────────────────────────┐
│ Stage 1: Style Extraction                                │
│   Input: writings_dir (Path)                             │
│   Output: StyleProfile                                   │
│   Duration: ~30s                                         │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ Stage 2: Draft Generation                                │
│   Input: brain_dump (str), StyleProfile                  │
│   Output: draft (str)                                    │
│   Duration: ~60s                                         │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ Stage 3: Review                                          │
│   Input: draft, brain_dump, StyleProfile                 │
│   Output: ReviewResult (source + style issues)           │
│   Duration: ~40s                                         │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ Stage 4: Revision                                        │
│   Input: draft, brain_dump, StyleProfile, feedback       │
│   Output: revised_draft (str)                            │
│   Duration: ~60s                                         │
│   ↻ Repeats until approved or max iterations            │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ Stage 5: Illustration (Optional)                         │
│   Input: final_draft                                     │
│   Output: illustrated_draft with embedded images         │
│   Duration: ~2-5 min depending on image count            │
└──────────────────────────────────────────────────────────┘
```

**Benefits**:
- Each stage independently testable
- Clear progress visibility
- Resumable at any stage
- No blocking in core logic
- Ready for alternative interfaces (web, API, etc.)

---

## Session Management

The tool maintains session state for resume capability:

```
.data/blog_creator/<timestamp>/
├── state.json              # Complete session state
├── draft_iter_1.md         # First iteration draft
├── draft_iter_2.md         # Second iteration draft
├── <slug>.md               # Final approved post
└── images/                 # Generated illustrations (if enabled)
    ├── diagram-1.png
    └── diagram-2.png
```

**State tracking:**
- Current stage (initialized, style_extracted, draft_written, etc.)
- Iteration count and history
- Style profile
- Review results
- User feedback history
- Draft versions

**Resume capability:**
- Interrupt anytime (Ctrl+C)
- Resume with `--resume` flag
- Picks up from last completed stage
- No work lost

---

## Dependencies

This app composes three Amplifier modules:

- **amplifier-module-style-extraction** - Analyzes writing samples
- **amplifier-module-image-generation** - Creates AI images
- **amplifier-module-markdown-utils** - Processes markdown

All dependencies install automatically via git sources.

---

## Development

```bash
cd amplifier-app-blog-creator
uv sync --dev
uv run pytest
```

### Running Tests

```bash
# All tests
uv run pytest

# Specific test
uv run pytest tests/core/stages/test_style_extraction.py

# With coverage
uv run pytest --cov=amplifier_app_blog_creator
```

### Project Structure

```
amplifier-app-blog-creator/
├── src/amplifier_app_blog_creator/
│   ├── core/                    # Pure business logic
│   │   ├── stages/              # Independent stage functions
│   │   ├── workflow.py          # Stage orchestration
│   │   └── models.py            # Data models
│   ├── cli/                     # CLI interface
│   │   ├── ui.py                # Display logic
│   │   ├── input_handler.py     # User input
│   │   └── main.py              # Entry point
│   ├── web/                     # Web interface
│   │   ├── app.py               # FastAPI application
│   │   ├── routes/              # HTTP endpoints
│   │   ├── templates/           # Jinja2 templates
│   │   └── static/              # CSS, JavaScript, assets
│   ├── session.py               # State management
│   ├── reviewers/               # Review implementations
│   ├── utils/                   # Defensive utilities
│   └── vendored_toolkit/        # Toolkit vendored from amplifier-app-cli
├── tests/                       # Test suite
│   ├── core/                    # Core logic tests
│   ├── cli/                     # CLI adapter tests
│   ├── web/                     # Web adapter tests
│   └── integration/             # End-to-end tests
├── README.md                    # This file
└── pyproject.toml               # Dependencies and config
```

---

## Learn More

- [HOW_I_BUILT_THIS.md](./HOW_I_BUILT_THIS.md) - Creation story and architectural decisions
- [MIGRATION_NOTES.md](./MIGRATION_NOTES.md) - Lessons learned and evolution
- [Amplifier Documentation](https://github.com/microsoft/amplifier-dev/blob/main/docs/)
