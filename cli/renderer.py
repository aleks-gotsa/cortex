"""Terminal markdown document rendering with navy blue theme."""

from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown
from rich.theme import Theme

from .cortex_cli import BLUE, DIM, LIGHT_BLUE, WHITE

_THEME = Theme(
    {
        "markdown.h1": f"bold {BLUE}",
        "markdown.h2": f"bold {BLUE}",
        "markdown.h3": f"bold {BLUE}",
        "markdown.h4": f"bold {BLUE}",
        "markdown.strong": f"bold {WHITE}",
        "markdown.emph": f"italic {WHITE}",
        "markdown.link": f"underline {LIGHT_BLUE}",
        "markdown.link_url": LIGHT_BLUE,
        "markdown.block_quote": DIM,
        "markdown.item.number": BLUE,
        "markdown.item.bullet": BLUE,
        "markdown.code": f"bold {WHITE} on #1a1a2e",
        "markdown.code_block": f"on #1a1a2e",
    }
)


def render_document(document: str, console: Console) -> None:
    """Render a markdown document to the terminal."""
    width = min(console.width - 4, 100)

    themed = Console(theme=_THEME, width=width, highlight=False)

    console.print()
    with themed.capture() as capture:
        themed.print(Markdown(document))
    console.print(capture.get(), highlight=False)
    console.print()
