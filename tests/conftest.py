"""Shared fixtures: a small, controlled corpus written to a temp directory.

Using a purpose-built corpus (rather than the shipped ``content/`` pages) keeps
the retrieval assertions stable and independent of any later edits to the
sample content.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# Two topically-distinct pages so retrieval has a clear right answer per query.
_PAGES = {
    "provisioned-concurrency.md": (
        "# Reducing cold starts with provisioned concurrency\n\n"
        "Provisioned concurrency keeps a configured number of execution "
        "environments initialized and ready to respond immediately, which "
        "removes the cold start penalty for latency sensitive endpoints. You pay "
        "for the reserved capacity whether or not it is used."
    ),
    "package-size.md": (
        "# How deployment package size affects cold starts\n\n"
        "A larger deployment package takes longer for the platform to download "
        "and unpack into a new environment. Removing unused dependencies and "
        "excluding test files shrinks the package and speeds up initialization."
    ),
    "gardening.md": (
        "# Composting basics for a home garden\n\n"
        "Compost turns kitchen scraps and yard trimmings into rich soil for "
        "vegetables and flowers. Turn the pile regularly and keep it moist."
    ),
}


@pytest.fixture
def corpus_dir(tmp_path: Path) -> Path:
    """Write the fixture pages to a temp directory and return its path."""
    for name, text in _PAGES.items():
        (tmp_path / name).write_text(text, encoding="utf-8")
    return tmp_path
