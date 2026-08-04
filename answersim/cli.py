"""Command-line entrypoint wiring the simulation pipeline together.

Flow: load corpus -> chunk -> TF-IDF retrieve -> synthesize -> report.

This is the single place the four library modules are composed, so the modules
themselves stay free of I/O and argument parsing.
"""

from __future__ import annotations

import sys

import click

from .corpus import chunk_documents, load_corpus
from .report import format_report
from .retrieve import Retriever
from .synthesize import synthesize

# Default content location, relative to the current working directory.
_DEFAULT_CONTENT_DIR = "content"


@click.command()
@click.argument("query")
@click.option(
    "--content",
    "content_dir",
    default=_DEFAULT_CONTENT_DIR,
    show_default=True,
    help="Directory of Markdown/text pages to treat as your site content.",
)
@click.option(
    "--k",
    "top_k",
    default=3,
    show_default=True,
    help="Number of passages to retrieve.",
)
@click.option(
    "--no-claude",
    is_flag=True,
    default=False,
    help="Force the offline extractive answer even if ANTHROPIC_API_KEY is set.",
)
def main(query: str, content_dir: str, top_k: int, no_claude: bool) -> None:
    """Simulate how an AI answer engine would answer QUERY from your content.

    Retrieves the most relevant passages from your local corpus, synthesizes an
    answer with inline citations (via Claude when available, otherwise an
    extractive fallback), and reports which of your pages were cited.
    """
    try:
        documents = load_corpus(content_dir)
    except FileNotFoundError as error:
        # Fail loudly at the boundary: a missing/empty corpus is a user error.
        raise click.ClickException(str(error)) from error

    chunks = chunk_documents(documents)
    retriever = Retriever(chunks)
    passages = retriever.top_k(query, k=top_k)

    # ``None`` auto-detects Claude; ``False`` forces the offline extractive path.
    use_claude = False if no_claude else None
    answer = synthesize(query, passages, use_claude=use_claude)

    click.echo(format_report(query, answer, passages))


if __name__ == "__main__":  # pragma: no cover - module executed as a script
    main(sys.argv[1:])
