"""Web mode entry point."""

import logging
import threading
import time
import webbrowser

import uvicorn

logger = logging.getLogger(__name__)


def open_browser_delayed(url: str, delay: float = 1.5):
    """Open browser after server starts."""
    time.sleep(delay)
    try:
        webbrowser.open(url)
        logger.info(f"Opened browser to {url}")
    except Exception as e:
        logger.warning(f"Could not auto-open browser: {e}")
        print(f"\n🌐 Open your browser to: {url}\n")


def main():
    """Start blog creator web interface."""
    import sys

    no_browser = "--no-browser" in sys.argv

    port = 8000
    if "--port" in sys.argv:
        try:
            port_idx = sys.argv.index("--port")
            if port_idx + 1 < len(sys.argv):
                port = int(sys.argv[port_idx + 1])
        except (ValueError, IndexError):
            pass

    host = "localhost"
    if "--host" in sys.argv:
        try:
            host_idx = sys.argv.index("--host")
            if host_idx + 1 < len(sys.argv):
                host = sys.argv[host_idx + 1]
        except IndexError:
            pass

    url = f"http://{host}:{port}"

    if not no_browser:
        thread = threading.Thread(
            target=open_browser_delayed,
            args=(url,),
            daemon=True
        )
        thread.start()
    else:
        print(f"\n🌐 Server starting at: {url}\n")

    uvicorn.run(
        "amplifier_app_blog_creator.web.app:app",
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
