"""Blog Creator - Main entry point."""

import sys

from .cli.main import main as cli_main


def main():
    """Entry point dispatches to CLI."""
    return cli_main()


if __name__ == "__main__":
    sys.exit(main())
