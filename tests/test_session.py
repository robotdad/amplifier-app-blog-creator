"""Tests for session management module."""

import json
from pathlib import Path

from amplifier_app_blog_creator.session import SessionManager
from amplifier_app_blog_creator.session import SessionState
from amplifier_app_blog_creator.session import extract_title_from_markdown
from amplifier_app_blog_creator.session import slugify


class TestUtilityFunctions:
    """Test utility functions for session management."""

    def test_extract_title_from_markdown(self):
        """Test extracting H1 title from markdown."""
        content = """# My Blog Post Title

This is the content of the post.
"""
        assert extract_title_from_markdown(content) == "My Blog Post Title"

    def test_extract_title_no_title(self):
        """Test extraction with no title."""
        content = "Just some content without a title"
        assert extract_title_from_markdown(content) is None

    def test_extract_title_multiple_headings(self):
        """Test extraction with multiple headings (returns first H1)."""
        content = """# First Title

## Subheading

# Second Title
"""
        assert extract_title_from_markdown(content) == "First Title"

    def test_slugify_basic(self):
        """Test basic slugification."""
        assert slugify("Hello World") == "hello-world"
        assert slugify("My Blog Post") == "my-blog-post"

    def test_slugify_special_chars(self):
        """Test slugification with special characters."""
        assert slugify("Hello, World!") == "hello-world"
        assert slugify("Test @ #123") == "test-123"

    def test_slugify_multiple_spaces(self):
        """Test slugification with multiple spaces."""
        assert slugify("Hello   World") == "hello-world"
        assert slugify("Test___Post") == "test-post"

    def test_slugify_edge_cases(self):
        """Test slugification edge cases."""
        assert slugify("---test---") == "test"
        assert slugify("Test-Post") == "test-post"


class TestSessionState:
    """Test SessionState dataclass."""

    def test_session_state_creation(self):
        """Test creating a new session state."""
        state = SessionState(session_id="test123")
        assert state.session_id == "test123"
        assert state.stage == "initialized"
        assert state.iteration == 0
        assert state.max_iterations == 10
        assert state.current_draft == ""
        assert state.illustration_enabled is False

    def test_session_state_with_params(self):
        """Test creating session state with parameters."""
        state = SessionState(
            session_id="test123",
            idea_path="/path/to/idea.md",
            writings_dir="/path/to/writings",
            max_iterations=5,
        )
        assert state.session_id == "test123"
        assert state.idea_path == "/path/to/idea.md"
        assert state.writings_dir == "/path/to/writings"
        assert state.max_iterations == 5


class TestSessionManager:
    """Test SessionManager class."""

    def test_init_creates_directory(self, tmp_path):
        """Test that initialization creates session directory."""
        session_dir = tmp_path / "test_session"
        manager = SessionManager(session_dir=session_dir)

        assert manager.session_dir.exists()
        assert manager.state_file.exists()
        assert manager.state_file == session_dir / "state.json"

    def test_init_with_none_creates_default_dir(self, tmp_path, monkeypatch):
        """Test that None session_dir creates timestamped directory."""
        monkeypatch.chdir(tmp_path)
        manager = SessionManager(session_dir=None)

        assert manager.session_dir.exists()
        assert manager.session_dir.parent.name == "blog_creator"
        assert manager.session_dir.name.startswith("20")

    def test_save_and_load(self, tmp_path):
        """Test saving and loading state."""
        session_dir = tmp_path / "test_session"
        manager = SessionManager(session_dir=session_dir)

        manager.state.stage = "generating"
        manager.state.iteration = 3
        manager.state.current_draft = "Test draft content"
        manager.save()

        manager2 = SessionManager(session_dir=session_dir)
        assert manager2.state.stage == "generating"
        assert manager2.state.iteration == 3
        assert manager2.state.current_draft == "Test draft content"

    def test_update_stage(self, tmp_path):
        """Test updating workflow stage."""
        session_dir = tmp_path / "test_session"
        manager = SessionManager(session_dir=session_dir)

        manager.update_stage("style_extraction")
        assert manager.state.stage == "style_extraction"

        with open(manager.state_file) as f:
            data = json.load(f)
            assert data["stage"] == "style_extraction"

    def test_increment_iteration(self, tmp_path):
        """Test incrementing iteration counter."""
        session_dir = tmp_path / "test_session"
        manager = SessionManager(session_dir=session_dir)

        assert manager.state.iteration == 0
        result = manager.increment_iteration()
        assert result is True
        assert manager.state.iteration == 1

    def test_increment_iteration_exceeds_max(self, tmp_path):
        """Test incrementing iteration beyond max."""
        session_dir = tmp_path / "test_session"
        manager = SessionManager(session_dir=session_dir)
        manager.state.max_iterations = 3

        manager.increment_iteration()
        manager.increment_iteration()
        manager.increment_iteration()
        result = manager.increment_iteration()

        assert result is False
        assert manager.state.iteration == 4

    def test_set_style_profile(self, tmp_path):
        """Test saving style profile."""
        session_dir = tmp_path / "test_session"
        manager = SessionManager(session_dir=session_dir)

        profile = {"tone": "professional", "length": "medium"}
        manager.set_style_profile(profile)

        assert manager.state.style_profile == profile

        manager2 = SessionManager(session_dir=session_dir)
        assert manager2.state.style_profile == profile

    def test_update_draft(self, tmp_path):
        """Test updating draft content."""
        session_dir = tmp_path / "test_session"
        manager = SessionManager(session_dir=session_dir)
        manager.state.iteration = 2

        draft_content = "# Test Post\n\nThis is a test draft."
        manager.update_draft(draft_content)

        assert manager.state.current_draft == draft_content
        draft_file = session_dir / "draft_iter_2.md"
        assert draft_file.exists()
        assert draft_file.read_text() == draft_content

    def test_add_user_feedback(self, tmp_path):
        """Test adding user feedback."""
        session_dir = tmp_path / "test_session"
        manager = SessionManager(session_dir=session_dir)
        manager.state.iteration = 1

        feedback = {"type": "revision", "comment": "Add more examples"}
        manager.add_user_feedback(feedback)

        assert len(manager.state.user_feedback) == 1
        assert manager.state.user_feedback[0]["iteration"] == 1
        assert manager.state.user_feedback[0]["comment"] == "Add more examples"

    def test_mark_stage_complete(self, tmp_path):
        """Test marking illustration stages complete."""
        session_dir = tmp_path / "test_session"
        manager = SessionManager(session_dir=session_dir)

        manager.mark_stage_complete("analysis")
        assert manager.state.analysis_complete is True
        assert manager.state.prompts_complete is False

        manager.mark_stage_complete("prompts")
        assert manager.state.prompts_complete is True

    def test_is_complete(self, tmp_path):
        """Test checking workflow completion."""
        session_dir = tmp_path / "test_session"
        manager = SessionManager(session_dir=session_dir)

        assert manager.is_complete() is False

        manager.state.stage = "complete"
        assert manager.is_complete() is True

    def test_mark_complete(self, tmp_path):
        """Test marking workflow complete."""
        session_dir = tmp_path / "test_session"
        manager = SessionManager(session_dir=session_dir)

        manager.mark_complete()
        assert manager.state.stage == "complete"
        assert manager.is_complete() is True

    def test_add_error(self, tmp_path):
        """Test adding errors to session."""
        session_dir = tmp_path / "test_session"
        manager = SessionManager(session_dir=session_dir)

        manager.add_error("generation", "API timeout")

        assert len(manager.state.errors) == 1
        assert manager.state.errors[0]["stage"] == "generation"
        assert manager.state.errors[0]["error"] == "API timeout"

    def test_reset(self, tmp_path):
        """Test resetting session state."""
        session_dir = tmp_path / "test_session"
        manager = SessionManager(session_dir=session_dir)

        manager.state.stage = "generating"
        manager.state.iteration = 5
        manager.state.current_draft = "Draft content"

        manager.reset()

        assert manager.state.stage == "initialized"
        assert manager.state.iteration == 0
        assert manager.state.current_draft == ""

    def test_path_expansion(self, tmp_path, monkeypatch):
        """Test that paths are expanded with .expanduser()."""
        test_home = tmp_path / "fake_home"
        test_home.mkdir()
        monkeypatch.setenv("HOME", str(test_home))

        session_dir = Path("~/.data/test_session")
        manager = SessionManager(session_dir=session_dir)

        assert manager.session_dir.is_absolute()
        assert str(test_home) in str(manager.session_dir)

    def test_add_iteration_history(self, tmp_path):
        """Test adding iteration history entries."""
        session_dir = tmp_path / "test_session"
        manager = SessionManager(session_dir=session_dir)
        manager.state.iteration = 1

        entry = {"action": "draft_generated", "tokens": 1500}
        manager.add_iteration_history(entry)

        assert len(manager.state.iteration_history) == 1
        assert manager.state.iteration_history[0]["iteration"] == 1
        assert manager.state.iteration_history[0]["action"] == "draft_generated"
        assert "timestamp" in manager.state.iteration_history[0]
