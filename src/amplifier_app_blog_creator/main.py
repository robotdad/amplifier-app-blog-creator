"""Blog Creator - Main entry point."""

import sys

from .cli.main import main as cli_main


def main():
    """Entry point - dispatch to CLI or web based on --mode flag."""
    if "--mode" in sys.argv:
        mode_idx = sys.argv.index("--mode")
        if mode_idx + 1 < len(sys.argv):
            mode = sys.argv[mode_idx + 1]
            if mode == "web":
                from .web.main import main as web_main

                return web_main()

    return cli_main()


if __name__ == "__main__":
    sys.exit(main())
