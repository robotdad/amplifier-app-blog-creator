# amplifier-app-blog-creator

**Transform ideas into polished, illustrated blog posts matching your unique voice**

Stage-based blog creation workflow with independent, testable stages: style extraction, draft generation, automated review, and optional AI illustration.

---

## The Problem

You have ideas worth sharing, but:
- Writing takes hours of focused effort
- Generic AI writing doesn't capture your voice
- Finding relevant images is time-consuming
- Quality and consistency suffer under time pressure

---

## The Solution

Blog Creator uses a stage-based architecture with four independent stages:

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

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/robotdad/amplifier-app-blog-creator
cd amplifier-app-blog-creator

# Install dependencies
uv sync

# Run the app
uv run blog-creator --idea rough_notes.md --writings-dir ~/my_blog_posts/
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

## Usage Guide

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

## Command-Line Options

```bash
# Required
--idea PATH                  # Your rough notes/brain dump
--writings-dir PATH          # Directory with your writing samples

# Optional
--instructions TEXT          # Additional guidance (e.g., "remove company names")
--output PATH                # Custom output path (default: auto from title)
--with-images                # Enable illustration phase
--max-images N               # Maximum illustrations (default: 3)
--image-style TEXT           # Image style (e.g., "minimalist diagrams")
--resume                     # Resume from saved session
--reset                      # Discard saved state, start fresh
--max-iterations N           # Maximum refinement iterations (default: 10)
--verbose                    # Detailed logging
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
│   ├── session.py               # State management
│   ├── reviewers/               # Review implementations
│   ├── utils/                   # Defensive utilities
│   └── vendored_toolkit/        # Toolkit vendored from amplifier-app-cli
├── tests/                       # Test suite
│   ├── core/                    # Core logic tests
│   ├── cli/                     # CLI adapter tests
│   └── integration/             # End-to-end tests
├── README.md                    # This file
└── pyproject.toml               # Dependencies and config
```

---

## Learn More

- [HOW_I_BUILT_THIS.md](./HOW_I_BUILT_THIS.md) - Creation story and architectural decisions
- [MIGRATION_NOTES.md](./MIGRATION_NOTES.md) - Lessons learned and evolution
- [Amplifier Documentation](https://github.com/microsoft/amplifier-dev/blob/main/docs/)
