# Web Interface Module

**Web adapter for blog creator - polished browser-based interface with rich markdown editing**

---

## Overview

The web module provides a browser-based interface for blog creation using FastAPI, HTMX, and server-side rendering. It's a pure UI adapter layer that consumes the same `core/` business logic as the CLI.

**Technology Stack:**
- **FastAPI** - Async web framework
- **HTMX** - Dynamic HTML without page reloads
- **Jinja2** - Server-side templating
- **CodeMirror 6** - Rich markdown editor
- **Server-Sent Events (SSE)** - Real-time progress streaming

**Design Philosophy:**
- Thin adapter (no business logic)
- Reuses `core/` stage functions
- Python-only stack (uvx compatible)
- Progressive enhancement (works without JavaScript)

---

## Architecture

### Module Structure

```
web/
├── app.py                   # FastAPI application + startup
├── main.py                  # Web mode entry point
├── routes/
│   ├── sessions.py          # Session CRUD + workflow endpoints
│   ├── progress.py          # SSE progress streaming
│   └── content.py           # File operations (preview, render)
├── templates/
│   ├── base.html            # Base layout with header/footer
│   ├── components/          # Reusable template fragments
│   │   ├── header.html
│   │   ├── footer.html
│   │   └── stage-indicator.html
│   ├── setup.html           # Stage 1: Input collection
│   ├── progress.html        # Stage 2: AI processing
│   ├── review.html          # Stage 3: Editor + review
│   └── complete.html        # Stage 4: Success
└── static/
    ├── css/
    │   ├── tokens.css       # Design tokens (colors, shadows, motion)
    │   ├── layout.css       # Grid system, page layouts
    │   └── components.css   # Component-specific styles
    └── js/
        ├── htmx.min.js      # HTMX library (vendored)
        ├── codemirror.bundle.js  # CodeMirror editor (vendored)
        └── app.js           # Custom interactions
```

---

## API Endpoints

### Session Management

```python
POST   /sessions
# Create new session
# Body: {"idea_path": str, "writings_dir": str, "additional_instructions": str?}
# Returns: {"session_id": str, "redirect": "/sessions/{id}/setup"}

GET    /sessions/{id}
# Get session state
# Returns: SessionState as JSON

DELETE /sessions/{id}
# Delete session
# Returns: 204 No Content
```

### Workflow Stages

```python
POST   /sessions/{id}/validate-path
# Validate file or directory path
# Body: {"path": str, "type": "file|directory"}
# Returns: {"valid": bool, "word_count": int?, "file_count": int?, "error": str?}

GET    /sessions/{id}/preview-file
# Get file content preview
# Query: ?path=/path/to/file.md
# Returns: {"content": str, "word_count": int, "truncated": bool}

POST   /sessions/{id}/start-workflow
# Begin Stages 1-3 (extraction, generation, review)
# Runs in background, client polls /progress
# Returns: {"status": "started"}

GET    /sessions/{id}/review
# Get review data for current draft
# Returns: {"draft": str, "source_issues": list, "style_issues": list, "iteration": int}

PUT    /sessions/{id}/draft
# Update draft content (auto-save from editor)
# Body: {"content": str}
# Returns: {"saved": true}

POST   /sessions/{id}/approve
# Finalize and save approved draft
# Returns: {"download_path": str}

POST   /sessions/{id}/regenerate
# Re-run review and revision with current draft
# Returns: {"status": "started"}
```

### Progress Streaming

```python
GET    /sessions/{id}/progress
# SSE stream of real-time progress
# Content-Type: text/event-stream
# Events:
data: {
    "stage": "style_extraction",
    "progress": 60,
    "message": "Analyzing writing samples...",
    "subtasks": [{"name": str, "status": str}],
    "time_estimate": str
}
```

### Content Operations

```python
POST   /render-markdown
# Render markdown to HTML for preview
# Body: {"content": str}
# Returns: {"html": str}
```

---

## Templates

### Base Layout (base.html)

Provides consistent structure for all pages:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Blog Creator{% endblock %}</title>
    <link rel="stylesheet" href="/static/css/tokens.css">
    <link rel="stylesheet" href="/static/css/layout.css">
    <link rel="stylesheet" href="/static/css/components.css">
</head>
<body>
    <div class="app-layout">
        {% include "components/header.html" %}

        <main class="main-content">
            {% block content %}{% endblock %}
        </main>

        {% include "components/footer.html" %}
    </div>

    <script src="/static/js/htmx.min.js"></script>
    <script src="/static/js/app.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

### Stage Templates

Each stage extends base.html and implements specific workflow step:

- **setup.html** - File path inputs, validation, preview
- **progress.html** - Real-time SSE progress, stage cards
- **review.html** - CodeMirror editor, review drawer
- **complete.html** - Success animation, download

---

## Design System

### Color Tokens (Warm Confidence)

```css
:root {
    /* Surfaces */
    --color-bg-primary: hsl(30, 15%, 97%);
    --color-bg-secondary: hsl(30, 20%, 99%);
    --color-bg-tertiary: hsl(30, 10%, 95%);

    /* Accent */
    --color-accent-primary: #D4943B;
    --color-accent-hover: hsl(35, 65%, 50%);

    /* Text */
    --color-text-primary: hsl(30, 10%, 20%);
    --color-text-secondary: hsl(30, 8%, 45%);
    --color-text-tertiary: hsl(30, 6%, 60%);

    /* Semantic */
    --color-success: hsl(140, 50%, 45%);
    --color-warning: hsl(35, 80%, 55%);
    --color-error: hsl(5, 70%, 55%);
}
```

### Motion Tokens

```css
:root {
    /* Durations */
    --duration-instant: 150ms;
    --duration-quick: 250ms;
    --duration-standard: 350ms;
    --duration-deliberate: 500ms;
    --duration-celebration: 700ms;

    /* Easing */
    --easing-spring: cubic-bezier(0.34, 1.35, 0.64, 1);
    --easing-standard: cubic-bezier(0.4, 0, 0.2, 1);
}
```

### Shadow Tokens

```css
:root {
    --shadow-button: 0 1px 2px hsl(30deg 10% 20% / 0.08),
                     0 2px 8px hsl(30deg 10% 20% / 0.06),
                     0 4px 16px hsl(30deg 10% 20% / 0.04);

    --shadow-card: 0 2px 4px hsl(30deg 10% 20% / 0.06),
                   0 4px 12px hsl(30deg 10% 20% / 0.04),
                   0 8px 24px hsl(30deg 10% 20% / 0.03);

    --shadow-modal: 0 4px 8px hsl(30deg 10% 20% / 0.08),
                    0 8px 24px hsl(30deg 10% 20% / 0.06),
                    0 16px 48px hsl(30deg 10% 20% / 0.04);
}
```

See `.design/AESTHETIC-GUIDE.md` for complete design system documentation.

---

## Key Components

### PathInput

File/directory path input with validation:
- Text input (type or paste)
- Browse button (native file picker)
- Drag-and-drop zone
- Real-time validation via HTMX
- Visual feedback (✓ valid, ⚠ invalid)

### FilePreview

Collapsible preview of file content:
- Shows metadata (word count, file count)
- Truncates long content with "View Full" expansion
- Read-only for MVP

### ProgressStage

Individual stage progress card:
- Status icon (✓ completed, ⟳ active, ○ pending)
- Progress bar with shimmer effect
- Subtask list with real-time updates
- Time estimates

### MarkdownEditor

Rich editing with CodeMirror 6:
- Syntax highlighting
- Line numbers
- Preview toggle (source ↔ rendered HTML)
- Auto-save via HTMX
- Keyboard shortcuts

### ReviewDrawer

Slide-out panel from right:
- Shows source accuracy and style issues
- Contextual links to editor
- Action buttons (Approve, Regenerate)
- Keyboard shortcut: Cmd/Ctrl + R
- Future home for chat interface

### SuccessState

Celebration on completion:
- Animated checkmark (spring entrance)
- Stats counter (count-up animation)
- Download button
- Start new post action

---

## Implementation Patterns

### Workflow Adapter

Wraps `BlogCreatorWorkflow` for web context:

```python
class WebWorkflowAdapter:
    """Adapts BlogCreatorWorkflow for web with SSE progress."""

    def __init__(self, session_id: str):
        self.session = SessionManager(Path(f".data/blog_creator/{session_id}"))
        self.progress_queue = asyncio.Queue()
        self.workflow = BlogCreatorWorkflow(
            self.session,
            progress_callback=self._progress_callback
        )

    def _progress_callback(self, message: str):
        """Capture progress for SSE streaming."""
        self.progress_queue.put_nowait({
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    async def stream_progress(self):
        """SSE generator for progress updates."""
        while True:
            try:
                update = await asyncio.wait_for(
                    self.progress_queue.get(),
                    timeout=30.0
                )
                yield f"data: {json.dumps(update)}\n\n"
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
```

### SSE Progress Client

JavaScript client for real-time updates:

```javascript
const eventSource = new EventSource(`/sessions/${sessionId}/progress`);

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);

    // Update progress bar
    document.querySelector('.progress-bar').style.width = data.progress + '%';

    // Update message
    document.querySelector('.stage-message').textContent = data.message;

    // Update subtasks via HTMX
    if (data.subtasks) {
        htmx.ajax('GET', `/components/subtasks?data=${JSON.stringify(data.subtasks)}`, {
            target: '.subtask-list',
            swap: 'innerHTML'
        });
    }
};
```

### Browser Auto-Open

Cross-platform browser launch on startup:

```python
import webbrowser
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Open browser
    port = 8000
    webbrowser.open(f"http://localhost:{port}")
    yield
    # Shutdown: cleanup

app = FastAPI(lifespan=lifespan)
```

---

## Accessibility

### WCAG AA Compliance

**Color Contrast:**
- Text: ≥4.5:1 (normal), ≥3:1 (large)
- UI components: ≥3:1
- All tokens validated

**Touch Targets:**
- Minimum 44×44px (Apple HIG)
- Minimum 48×48px (Android Material)

**Keyboard Navigation:**
- Tab order follows visual hierarchy
- Focus indicators (2px amber outline)
- Skip links: "Skip to main content"
- Drawer toggle: Cmd/Ctrl + R

**Screen Readers:**
- Semantic HTML (`<header>`, `<main>`, `<nav>`)
- ARIA labels where needed
- Progress announcements (`aria-live="polite"`)

**Reduced Motion:**
```css
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
```

---

## Development

### Running Web Mode

```bash
cd amplifier-app-blog-creator

# Start web server
uv run blog-creator --mode web

# Custom port
uv run blog-creator --mode web --port 3000

# Don't auto-open browser
uv run blog-creator --mode web --no-browser
```

### Testing

```bash
# Run web-specific tests
uv run pytest tests/web/

# Test workflow adapter
uv run pytest tests/web/test_workflow_adapter.py

# Test routes
uv run pytest tests/web/test_routes.py
```

### Static Asset Management

**Vendored Libraries:**
- HTMX (~14KB) - Copy from CDN or official release
- CodeMirror 6 bundle (~200KB) - Build once, vendor

**Why vendor:**
- No CDN dependencies (works offline)
- No npm build step needed
- Version control for reproducibility
- Single Python stack maintained

---

## Design System

Complete design specifications in `.design/AESTHETIC-GUIDE.md`:

**Aesthetic:** "Sophisticated Warmth"
- Professional polish for executives
- Warm approachability for first-timers
- Streamlined efficiency for power users

**Key Elements:**
- Warm neutral colors (beige/taupe undertones)
- Amber accents (#D4943B)
- Multi-layer shadows (3-4 layers)
- Soft corners (10px standard)
- Deliberate motion (150-700ms timing)
- System typography (1.25 ratio scale)

**Component Specifications:**

See `ai_working/blog_web_interface/COMPONENT_SPECS.md` for detailed specs including:
- HTML structure
- CSS styling with design tokens
- JavaScript interactions
- Accessibility requirements
- Animation details

---

## User Journey

### Stage 1: Setup

**User provides:**
- Idea file path (type, browse, or drag-drop)
- Writing samples directory path
- Optional: Additional instructions

**Features:**
- Real-time path validation
- File content preview (collapsible)
- Writing samples list with metadata
- Smart defaults and helper text

### Stage 2: Progress

**System shows:**
- Overall progress (0-100%)
- Individual stage progress cards
- Real-time status messages
- Time estimates and actual durations
- Smooth transitions between stages

**Updates via SSE:**
- Progress bars fill smoothly
- Subtask lists update in real-time
- Stage completion animations
- No page reloads

### Stage 3: Review

**User interacts with:**
- Rich markdown editor (CodeMirror)
- Syntax highlighting and line numbers
- Live preview toggle
- Auto-save functionality
- Review drawer (slide-out from right)

**Review panel shows:**
- Source accuracy issues
- Style consistency feedback
- Iteration counter
- Action buttons

**Actions:**
- Approve (finalize draft)
- Edit & Re-generate (manual changes)
- Provide Feedback (iterate with AI)

### Stage 4: Complete

**System celebrates:**
- Animated checkmark (500ms spring)
- Stats count up (iterations, time)
- Download button
- Start new post option

---

## Browser Compatibility

**Supported Browsers:**
- Chrome/Edge 90+ (Chromium)
- Firefox 88+
- Safari 14+

**Required Features:**
- CSS Grid and Flexbox
- CSS Custom Properties (variables)
- Server-Sent Events (SSE)
- ES6 JavaScript

**Progressive Enhancement:**
- Core functionality works without JavaScript
- Enhanced experience with JavaScript enabled
- Graceful degradation for older browsers

---

## Future Enhancements (Post-MVP)

**Phase 3: Chat Feedback**
- Chat interface in same drawer as review panel
- Natural language feedback on drafts
- Quick actions ("Make shorter", "Add example")
- Conversation history

**Phase 4: Advanced Features**
- Session history and management UI
- Multiple draft comparison
- Collaborative editing (multi-user)
- Export to multiple formats

**Not Planned (Simplicity):**
- User accounts/authentication (local-only tool)
- Cloud storage (file-based sessions)
- Mobile optimization (desktop/laptop focus)
- Complex editor features (keep it focused)

---

## Philosophy Alignment

### Ruthless Simplicity

**What we built:**
- Thin adapter layer (no business logic)
- Server-rendered HTML (HTMX over React)
- File-based sessions (no database)
- Vendored assets (no complex build)

**What we avoided:**
- Frontend framework overhead
- Complex state management
- Database dependencies
- Microservices architecture
- Over-engineered abstractions

### Modular Design

**Bricks:**
- `web/` is self-contained adapter module
- Independent of `cli/` (both work)
- Consumes `core/` via stable interfaces

**Studs:**
- `BlogCreatorWorkflow` API unchanged
- `SessionState` model unchanged
- Progress callback signature unchanged

**Regeneratable:**
- Can rebuild web/ from route specs
- Can rebuild templates from wireframes
- Core interface remains stable

---

## Learn More

**Design Documentation:**
- `.design/AESTHETIC-GUIDE.md` - Complete visual system
- `ai_working/blog_web_interface/DESIGN_VISION.md` - Design philosophy
- `ai_working/blog_web_interface/COMPONENT_SPECS.md` - Detailed component specs

**Core Logic:**
- `core/README.md` - Business logic documentation (if exists)
- `core/stages/` - Individual stage implementations

**Related:**
- `cli/README.md` - CLI adapter patterns (if exists)
- `../../README.md` - Main project documentation
