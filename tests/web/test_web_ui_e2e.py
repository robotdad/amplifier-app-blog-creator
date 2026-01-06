"""
Playwright E2E tests for Blog Creator web UI.

Tests the complete user workflow from configuration through blog post creation.
"""
import os
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="session")
def base_url():
    """Base URL for the web application."""
    return os.getenv("TEST_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def test_api_key():
    """Test Anthropic API key."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set - skipping E2E tests")
    return api_key


@pytest.fixture(scope="session")
def test_fixtures_dir():
    """Path to test fixtures directory."""
    from pathlib import Path
    return str(Path(__file__).parent.parent.parent.parent / "amplifier-bundle-blog-creator" / "test-fixtures")


class TestConfiguration:
    """Test API key configuration flow."""
    
    def test_configuration_page_loads(self, page: Page, base_url):
        """Configuration page should load and show API key form."""
        page.goto(f"{base_url}/configure")
        
        # Should show configuration form
        expect(page.get_by_role("heading", name="Configuration")).to_be_visible()
        
        # Should have API key input
        api_key_input = page.get_by_label("Anthropic API Key")
        expect(api_key_input).to_be_visible()
        
        # Should have submit button
        expect(page.get_by_role("button", name="Continue")).to_be_visible()
    
    def test_valid_api_key_saves(self, page: Page, base_url, test_api_key):
        """Valid API key should save and redirect to new session."""
        page.goto(f"{base_url}/configure")
        
        # Fill in API key
        page.get_by_label("Anthropic API Key").fill(test_api_key)
        
        # Submit form
        page.get_by_role("button", name="Continue").click()
        
        # Should redirect to new session
        page.wait_for_url("**/sessions/new")
        expect(page).to_have_url(f"{base_url}/sessions/new")


class TestSetup:
    """Test blog post setup form."""
    
    def test_setup_page_loads(self, page: Page, base_url, test_api_key):
        """Setup page should show input form for idea and samples."""
        # Configure first
        page.goto(f"{base_url}/configure")
        page.get_by_label("Anthropic API Key").fill(test_api_key)
        page.get_by_role("button", name="Continue").click()
        
        # Should show setup form
        expect(page.get_by_role("heading", name="Create Blog Post")).to_be_visible()
        
        # Should have idea file input
        expect(page.get_by_label("Idea File")).to_be_visible()
        
        # Should have writings directory input
        expect(page.get_by_label("Writing Samples Directory")).to_be_visible()
        
        # Should have optional instructions
        expect(page.get_by_label("Additional Instructions")).to_be_visible()
    
    def test_path_validation(self, page: Page, base_url, test_api_key, test_fixtures_dir):
        """Path inputs should validate in real-time."""
        # Setup
        page.goto(f"{base_url}/configure")
        page.get_by_label("Anthropic API Key").fill(test_api_key)
        page.get_by_role("button", name="Continue").click()
        
        # Fill in valid paths
        idea_path = f"{test_fixtures_dir}/idea-notes.md"
        samples_dir = f"{test_fixtures_dir}/writing-samples"
        
        page.get_by_label("Idea File").fill(idea_path)
        page.get_by_label("Writing Samples Directory").fill(samples_dir)
        
        # Should show validation success indicators (wait for HTMX)
        page.wait_for_timeout(1000)  # Allow HTMX validation
        
        # Start button should be enabled
        start_button = page.get_by_role("button", name="Start Creating")
        expect(start_button).to_be_enabled()


class TestWorkflowProgress:
    """Test blog creation workflow with recipe execution."""
    
    def test_workflow_starts_and_shows_progress(self, page: Page, base_url, test_api_key, test_fixtures_dir):
        """Workflow should start and show real-time progress via SSE."""
        # Setup session
        page.goto(f"{base_url}/configure")
        page.get_by_label("Anthropic API Key").fill(test_api_key)
        page.get_by_role("button", name="Continue").click()
        
        # Fill in test data
        idea_path = f"{test_fixtures_dir}/idea-notes.md"
        samples_dir = f"{test_fixtures_dir}/writing-samples"
        
        page.get_by_label("Idea File").fill(idea_path)
        page.get_by_label("Writing Samples Directory").fill(samples_dir)
        page.get_by_label("Additional Instructions").fill("Keep under 800 words for testing")
        
        # Start workflow
        page.get_by_role("button", name="Start Creating").click()
        
        # Should redirect to progress page
        page.wait_for_url("**/progress", timeout=5000)
        
        # Should show progress page elements
        expect(page.get_by_role("heading", name="Creating Your Blog Post")).to_be_visible()
        
        # Should show stage cards
        expect(page.locator('[data-stage="0"]')).to_be_visible()  # Style Extraction
        expect(page.locator('[data-stage="1"]')).to_be_visible()  # Draft Generation
        expect(page.locator('[data-stage="2"]')).to_be_visible()  # Review
        expect(page.locator('[data-stage="3"]')).to_be_visible()  # Revision
    
    def test_workflow_completes_and_redirects(self, page: Page, base_url, test_api_key, test_fixtures_dir):
        """Workflow should complete all stages and redirect to review."""
        # Setup and start (same as above)
        page.goto(f"{base_url}/configure")
        page.get_by_label("Anthropic API Key").fill(test_api_key)
        page.get_by_role("button", name="Continue").click()
        
        idea_path = f"{test_fixtures_dir}/idea-notes.md"
        samples_dir = f"{test_fixtures_dir}/writing-samples"
        
        page.get_by_label("Idea File").fill(idea_path)
        page.get_by_label("Writing Samples Directory").fill(samples_dir)
        page.get_by_role("button", name="Start Creating").click()
        
        # Wait for workflow completion (may take 3-5 minutes)
        # SSE sends 'complete' event which triggers redirect
        page.wait_for_url("**/review", timeout=600000)  # 10 minute timeout
        
        # Should show review page
        expect(page.get_by_role("heading", name="Review Your Draft")).to_be_visible()
        
        # Should show markdown editor
        expect(page.locator(".CodeMirror")).to_be_visible()
        
        # Should have approve button
        expect(page.get_by_role("button", name="Approve")).to_be_visible()


class TestReviewPage:
    """Test draft review and editing functionality."""
    
    @pytest.fixture
    def review_page(self, page: Page, base_url, test_api_key, test_fixtures_dir):
        """Navigate to review page with completed workflow."""
        # Setup and complete workflow
        page.goto(f"{base_url}/configure")
        page.get_by_label("Anthropic API Key").fill(test_api_key)
        page.get_by_role("button", name="Continue").click()
        
        idea_path = f"{test_fixtures_dir}/idea-notes.md"
        samples_dir = f"{test_fixtures_dir}/writing-samples"
        
        page.get_by_label("Idea File").fill(idea_path)
        page.get_by_label("Writing Samples Directory").fill(samples_dir)
        page.get_by_role("button", name="Start Creating").click()
        
        # Wait for completion
        page.wait_for_url("**/review", timeout=600000)
        return page
    
    def test_markdown_editor_visible(self, review_page: Page):
        """Review page should show CodeMirror editor."""
        expect(review_page.locator(".CodeMirror")).to_be_visible()
        
        # Should have content
        editor_content = review_page.locator(".CodeMirror-line")
        expect(editor_content.first).to_be_visible()
    
    def test_preview_toggle(self, review_page: Page):
        """Should be able to toggle between edit and preview modes."""
        # Find toggle button
        preview_toggle = review_page.get_by_role("button", name="Preview")
        expect(preview_toggle).to_be_visible()
        
        # Click to show preview
        preview_toggle.click()
        
        # Preview should be visible, editor hidden
        expect(review_page.locator(".markdown-preview")).to_be_visible()
    
    def test_review_drawer(self, review_page: Page):
        """Should show review feedback in drawer."""
        # Open review drawer
        review_button = review_page.get_by_role("button", name="View Review")
        if review_button.is_visible():
            review_button.click()
            
            # Drawer should open
            expect(review_page.locator('[data-drawer="review"]')).to_be_visible()
    
    def test_approve_workflow(self, review_page: Page):
        """Approve button should finalize and redirect to complete page."""
        # Click approve
        review_page.get_by_role("button", name="Approve").click()
        
        # Should redirect to complete page
        review_page.wait_for_url("**/complete", timeout=10000)
        
        # Should show success message
        expect(review_page.get_by_text("Blog Post Created")).to_be_visible()


class TestCompletePage:
    """Test completion page functionality."""
    
    @pytest.fixture
    def complete_page(self, page: Page, base_url, test_api_key, test_fixtures_dir):
        """Navigate to complete page via full workflow."""
        # Setup, workflow, and approve
        page.goto(f"{base_url}/configure")
        page.get_by_label("Anthropic API Key").fill(test_api_key)
        page.get_by_role("button", name="Continue").click()
        
        idea_path = f"{test_fixtures_dir}/idea-notes.md"
        samples_dir = f"{test_fixtures_dir}/writing-samples"
        
        page.get_by_label("Idea File").fill(idea_path)
        page.get_by_label("Writing Samples Directory").fill(samples_dir)
        page.get_by_role("button", name="Start Creating").click()
        
        page.wait_for_url("**/review", timeout=600000)
        page.get_by_role("button", name="Approve").click()
        page.wait_for_url("**/complete", timeout=10000)
        
        return page
    
    def test_download_markdown_available(self, complete_page: Page):
        """Should show download button for markdown file."""
        download_button = complete_page.get_by_role("button", name="Download Markdown")
        expect(download_button).to_be_visible()
    
    def test_session_stats_visible(self, complete_page: Page):
        """Should show session statistics."""
        # Should display iteration count
        expect(complete_page.get_by_text("Iterations")).to_be_visible()
        
        # Should display word count
        expect(complete_page.get_by_text("Words")).to_be_visible()


# Smoke Test - Quick validation without full workflow
class TestSmoke:
    """Quick smoke tests that don't require full workflow execution."""
    
    def test_home_page_redirects(self, page: Page, base_url):
        """Home page should redirect to configure or new session."""
        page.goto(base_url)
        
        # Should redirect to either configure or sessions/new
        page.wait_for_load_state("networkidle")
        assert "/configure" in page.url or "/sessions/new" in page.url
    
    def test_static_assets_load(self, page: Page, base_url):
        """CSS files should load successfully."""
        response = page.goto(f"{base_url}/static/css/tokens.css")
        assert response.status == 200
        
        response = page.goto(f"{base_url}/static/css/layout.css")
        assert response.status == 200
        
        response = page.goto(f"{base_url}/static/css/components.css")
        assert response.status == 200
