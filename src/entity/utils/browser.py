from __future__ import annotations

"""Simple utility for launching a URL in the default web browser."""

from dataclasses import dataclass
from time import sleep
from webbrowser import open as open_browser


@dataclass
class BrowserLauncher:
    """Open a web browser after an optional delay."""

    url: str
    delay: float = 3.0

    def launch(self) -> None:
        """Launch the configured URL."""
        if self.delay:
            sleep(self.delay)
        open_browser(self.url)


def main() -> None:
    BrowserLauncher(url="http://localhost:3000").launch()


if __name__ == "__main__":
    main()
