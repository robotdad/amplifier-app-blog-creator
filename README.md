# amplifier-app-blog-creator

**Transform ideas into polished, illustrated blog posts matching your unique voice**

Complete blog creation workflow: extract your writing style, generate content, review for accuracy, optionally add AI-generated illustrations.

---

## The Problem

You have ideas worth sharing, but:
- Writing takes hours of focused effort
- Generic AI writing doesn't capture your voice
- Finding relevant images is time-consuming
- Quality and consistency suffer under time pressure

---

## The Solution

Blog Creator is a two-phase AI pipeline:

**Phase 1: Content Creation**
1. Extract your writing style from samples
2. Generate draft matching your voice
3. Review for source accuracy
4. Review for style consistency
5. Incorporate your feedback
6. Iterate until approved

**Phase 2: Illustration (Optional)**
1. Analyze finalized content
2. Generate contextual image prompts
3. Create images with AI (DALL-E, Imagen, GPT-Image-1)
4. Insert at optimal positions

**Result**: A complete blog post that sounds like you and looks professional.

---

## Quick Start

**Current Status**: Development setup required (uvx support coming when amplifier package published).

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
  --illustrate \
  --style "minimalist technical diagrams"
```

---

## Future: uvx Support

Once the `amplifier` package is published, you'll be able to run directly with `uvx`:

```bash
# Coming soon:
uvx blog-creator --idea notes.md --writings-dir ~/posts/
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
uvx --from git+https://github.com/robotdad/amplifier-dev#subdirectory=amplifier-app-blog-creator \
  blog-creator \
  --idea rough_notes.md \
  --writings-dir ~/my_blog_posts/
```

Or with alias configured:
```bash
blog-creator --idea rough_notes.md --writings-dir ~/my_blog_posts/
```

**What happens**:
1. Analyzes your writing samples → extracts style profile
2. Generates initial draft → matches your voice
3. Reviews against source (your idea) → flags inaccuracies
4. Reviews against style (your samples) → flags inconsistencies
5. Presents draft for your review
6. Incorporates your feedback → iterates until approved
7. Saves final post to session directory

### Provide Feedback

The tool saves drafts to `.data/blog_creator/<session>/draft_iter_1.md`

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
--illustrate                 # Enable illustration phase
--style TEXT                 # Image style (e.g., "minimalist diagrams")
--image-apis LIST            # Comma-separated: gptimage,imagen,dalle
--max-images N               # Maximum illustrations (default: 5)
--cost-limit FLOAT           # Budget limit for images
--resume                     # Resume from saved session
--reset                      # Discard saved state, start fresh
--max-iterations N           # Maximum refinement iterations (default: 10)
--verbose                    # Detailed logging
```

---

## How It Works

### Phase 1: Content Creation

```
Your Idea + Your Writings
         ↓
    [Extract Style] ────→ StyleProfile
         ↓
  [Generate Draft] ─────→ Initial blog post
         ↓
   [Review Sources] ─────→ Flag inaccuracies
         ↓
   [Review Style] ───────→ Flag inconsistencies
         ↓
   [Your Feedback] ──────→ Inline comments
         ↓
   [Revise] ─────────────→ Iterate until approved
         ↓
    Final Content
```

### Phase 2: Illustration (Optional)

```
Finalized Content
         ↓
[Content Analysis] ───────→ Identify illustration opportunities
         ↓
[Prompt Generation] ──────→ Contextual image prompts
         ↓
[Image Generation] ───────→ Multi-API (DALL-E, Imagen, GPT-Image-1)
         ↓
[Markdown Update] ────────→ Insert at optimal positions
         ↓
Illustrated Blog Post
```

### State Management

The app checkpoints after every expensive operation:
- Style extraction complete
- Draft generation
- Each review iteration
- Image generation

Can interrupt anytime and resume with `--resume`.

---

## Session Data

Working files saved to `.data/blog_creator/<timestamp>/`:
- `state.json` - Session state for resume
- `draft_iter_N.md` - Each iteration's draft
- `<slug>.md` - Final approved post
- `images/` - Generated illustrations (if enabled)

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

---

## Learn More

- [HOW_I_BUILT_THIS.md](./HOW_I_BUILT_THIS.md) - Creation story
- [MIGRATION_NOTES.md](./MIGRATION_NOTES.md) - Lessons from scenarios/
- [Amplifier Documentation](https://github.com/microsoft/amplifier-dev/blob/main/docs/)
