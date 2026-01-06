# Web UI Tests

Playwright end-to-end tests for the Blog Creator web interface.

## Prerequisites

```bash
# Install dependencies
cd amplifier-app-blog-creator
uv sync --dev

# Install Playwright browsers
uv run playwright install chromium
```

## Running Tests

### Full Test Suite

```bash
# Set API key for E2E tests
export ANTHROPIC_API_KEY="your-key"

# Start web server in background
cd amplifier-app-blog-creator
uv run python -m amplifier_app_blog_creator.web.main --no-browser &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Run tests
uv run pytest tests/web/ -v

# Cleanup
kill $SERVER_PID
```

### Smoke Tests Only (Fast)

```bash
# Start server
uv run python -m amplifier_app_blog_creator.web.main --no-browser &
SERVER_PID=$!

# Run smoke tests (no API key needed)
uv run pytest tests/web/test_web_ui_e2e.py::TestSmoke -v

# Cleanup
kill $SERVER_PID
```

### Single Test

```bash
uv run pytest tests/web/test_web_ui_e2e.py::TestConfiguration::test_configuration_page_loads -v
```

### With Visual Debugging

```bash
# Run with headed browser (visible)
uv run pytest tests/web/ --headed

# Run with trace recording
uv run pytest tests/web/ --tracing on

# View trace
uv run playwright show-trace test-results/trace.zip
```

## Test Structure

- `test_web_ui_e2e.py` - End-to-end workflow tests
- `conftest.py` - Pytest fixtures and configuration

## Test Classes

### TestConfiguration
- Configuration page loads
- API key validation
- Redirect to new session

### TestSetup
- Setup form loads
- Path validation (HTMX)
- Form submission triggers workflow

### TestWorkflowProgress
- Progress page appears
- SSE streaming works
- Stage cards update
- Workflow completes and redirects

### TestReviewPage
- Markdown editor visible
- Preview toggle works
- Review feedback drawer
- Approve finalizes post

### TestCompletePage
- Download buttons available
- Session statistics shown

### TestSmoke (Quick)
- Home page redirects correctly
- Static assets load

## Known Limitations

1. **Full workflow tests take 3-5 minutes** - Recipe executes real LLM calls
2. **Requires ANTHROPIC_API_KEY** - E2E tests need real API access
3. **Server must be running** - Tests assume localhost:8000
4. **Timeouts** - Some tests have 10-minute timeouts for recipe completion

## Troubleshooting

**Tests hang waiting for progress:**
→ Check recipe execution is working: `amplifier tool invoke recipes operation=execute ...`

**Configuration page doesn't load:**
→ Verify server is running on port 8000

**Static assets 404:**
→ Check `web/static/` directory exists with CSS files

**API key validation fails:**
→ Verify ANTHROPIC_API_KEY is valid and has credits
