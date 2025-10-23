---
profile:
  name: blog-creator
  version: "1.0.0"
  extends: base

session:
  orchestrator:
    module: loop-basic
  context:
    module: context-simple
    config:
      data_dir: ~/.amplifier-data/blog-creator
      writings_dir: ~/writings

tools:
  - module: tool-filesystem
  - module: tool-bash
  - module: style-extraction
    source: git+https://github.com/robotdad/amplifier-dev@main#subdirectory=amplifier-module-style-extraction
  - module: image-generation
    source: git+https://github.com/robotdad/amplifier-dev@main#subdirectory=amplifier-module-image-generation
  - module: markdown-utils
    source: git+https://github.com/robotdad/amplifier-dev@main#subdirectory=amplifier-module-markdown-utils

providers:
  - module: provider-anthropic
---

# Blog Creator Profile

Complete blog creation workflow with style-aware writing and optional AI illustration.

---

## What This Profile Enables

- **Style Extraction**: Analyze your writing samples to capture your unique voice
- **Content Generation**: Create blog posts matching your style
- **Source Review**: Verify accuracy against your source material
- **Style Review**: Ensure consistency with your writing patterns
- **Optional Illustration**: Add AI-generated images to finalized content
- **Multi-API Support**: DALL-E, Imagen, GPT-Image-1 for image generation

---

## Quick Start (No Installation)

```bash
# Run directly with uvx
uvx --from git+https://github.com/robotdad/amplifier-dev#subdirectory=amplifier-app-blog-creator \
  blog-creator \
  --idea your_notes.md \
  --writings-dir ~/your_posts/
```

**Requirements**:
- API keys for content generation (Claude) and images (OpenAI/Google)
- Set in environment: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`

## Profile-Based Usage (Optional)

If using with Amplifier CLI:

```bash
# Copy profile to your profiles directory
cp blog-creator.md ~/.amplifier/profiles/

# Modules auto-download from git when first used
amplifier run --profile blog-creator "Create blog post about X"
```

**Additional Requirements**:
- GitHub auth configured: `gh auth login`

---

## Quick Start

### Content Only

```bash
amplifier run --profile blog-creator \
  "Write blog post from idea.md using style from ~/my_posts/"
```

### With Illustrations

```bash
amplifier run --profile blog-creator \
  "Write and illustrate blog post from idea.md, style: minimalist diagrams"
```

---

## Configuration

### Data Directory

Working files saved to `~/.amplifier-data/blog-creator/`:
- Session state for resume
- Draft iterations
- Final blog posts
- Generated images

Override in profile config or via environment:
```bash
export BLOG_CREATOR_DATA_DIR=~/custom/path
```

### Writings Directory

Point to your existing blog posts for style extraction:
```yaml
session:
  context:
    config:
      writings_dir: ~/my_blog_posts
```

Or specify per-run in your prompt.

---

## API Keys

Set environment variables:

```bash
# Content generation (Claude)
export ANTHROPIC_API_KEY=your_key

# Image generation (optional)
export OPENAI_API_KEY=your_key       # For DALL-E, GPT-Image-1
export GOOGLE_API_KEY=your_key       # For Imagen
```

---

## Module Sources

All modules auto-download from git:

- **style-extraction**: Analyzes writing samples for voice/tone
- **image-generation**: Creates AI images with multiple providers
- **markdown-utils**: Processes markdown structure and content

These modules are shared with other apps that need the same capabilities.

---

## Example Workflows

### Basic Blog Post

```bash
amplifier run --profile blog-creator \
  "Create blog post from notes.md using my writing style from ~/posts/"
```

### Illustrated Technical Article

```bash
amplifier run --profile blog-creator \
  "Write illustrated article from architecture_notes.md.
   Use technical writing samples from ~/technical_posts/.
   Illustrations: minimalist black and white diagrams.
   Max 3 images, prefer Imagen for quality."
```

### Resume Interrupted Session

```bash
amplifier run --profile blog-creator --resume
```

---

## Cost Estimates

**Content Phase**:
- Style extraction: ~$0.01
- Draft + reviews: ~$0.10-$0.15

**Illustration Phase** (5 images):
- Analysis + prompts: ~$0.05
- Image generation: ~$0.15-$0.25

**Total**: ~$0.35-$0.40 for complete illustrated post

---

## Learn More

- [Blog Creator README](../README.md) - Complete app documentation
- [HOW_I_BUILT_THIS.md](../HOW_I_BUILT_THIS.md) - Creation story
- [Module Documentation](../../) - Individual module READMEs
