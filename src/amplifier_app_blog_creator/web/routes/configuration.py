"""Configuration routes for API key setup."""

import logging
import os
from pathlib import Path
from typing import Annotated

import anthropic
from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

router = APIRouter()

template_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(template_dir))


def get_api_key(request: Request) -> str | None:
    """Get API key from environment or session."""
    env_key = os.getenv("ANTHROPIC_API_KEY")
    if env_key:
        return env_key
    return request.session.get("ANTHROPIC_API_KEY")


def is_configured(request: Request) -> bool:
    """Check if ANTHROPIC_API_KEY is configured."""
    return get_api_key(request) is not None


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root redirect - check configuration status."""
    if is_configured(request):
        return RedirectResponse(url="/sessions/new", status_code=302)
    return RedirectResponse(url="/configure", status_code=302)


@router.get("/configure", response_class=HTMLResponse)
async def configure_page(request: Request):
    """Show configuration page if not configured."""
    if is_configured(request):
        return RedirectResponse(url="/sessions/new", status_code=302)

    return templates.TemplateResponse("configuration.html", {"request": request, "show_stage_indicator": False})


@router.post("/configure", response_class=HTMLResponse)
async def validate_api_key(request: Request, api_key: Annotated[str, Form()]):
    """Validate API key and store in session."""
    api_key = api_key.strip()

    if not api_key:
        return """
            <div id="config-feedback" class="feedback feedback-error">
                Please enter an API key
            </div>
        """

    if not api_key.startswith("sk-ant-"):
        return """
            <div id="config-feedback" class="feedback feedback-error">
                Invalid API key format. Keys should start with 'sk-ant-'
            </div>
        """

    try:
        client = anthropic.Anthropic(api_key=api_key)
        client.messages.create(
            model="claude-3-5-sonnet-20241022", max_tokens=10, messages=[{"role": "user", "content": "test"}]
        )

        request.session["ANTHROPIC_API_KEY"] = api_key
        logger.info("API key validated and stored in session")

        return """
            <div id="config-feedback" class="feedback feedback-success">
                <p>API key validated successfully!</p>
                <p>Redirecting to workflow...</p>
                <script>
                    setTimeout(() => {
                        window.location.href = '/sessions/new';
                    }, 1000);
                </script>
            </div>
        """

    except anthropic.AuthenticationError:
        logger.warning("Invalid API key attempted")
        return """
            <div id="config-feedback" class="feedback feedback-error">
                Invalid API key. Please check your key and try again.
            </div>
        """
    except anthropic.APIError as e:
        logger.error(f"Anthropic API error during validation: {e}")
        return f"""
            <div id="config-feedback" class="feedback feedback-error">
                API error: {str(e)}. Please try again.
            </div>
        """
    except Exception as e:
        logger.error(f"Unexpected error during API key validation: {e}")
        return """
            <div id="config-feedback" class="feedback feedback-error">
                Unexpected error. Please try again.
            </div>
        """
