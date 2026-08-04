"""Load and chunk a local content corpus.

The corpus is a directory of Markdown/text files, each treated as one "page"
of your site. Pages are split into smaller passages (chunks) so retrieval can
point at the specific paragraph that supports an answer, mirroring how a real
answer engine cites a passage rather than a whole document.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Extensions treated as content pages.
_CONTENT_GLOBS = ("*.md", "*.markdown", "*.txt")

# A chunk is grown paragraph-by-paragraph until it reaches this many characters,
# keeping passages large enough to be meaningful but small enough to cite.
_TARGET_CHUNK_CHARS = 500


@dataclass(frozen=True)
class Document:
    """A single content page loaded from disk."""

    source: str  # filename, e.g. "cold-starts.md" — used as the citation label
    path: Path
    title: str
    text: str


@dataclass(frozen=True)
class Chunk:
    """A retrievable passage belonging to a :class:`Document`."""

    source: str  # the owning page's filename
    title: str  # the owning page's human-readable title
    text: str
    chunk_index: int  # position of this chunk within its page


def _derive_title(text: str, fallback: str) -> str:
    """Return the first Markdown H1 (``# ...``) as the page title, else *fallback*."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


def load_corpus(content_dir: str | Path) -> list[Document]:
    """Load every content file under *content_dir* into :class:`Document` objects.

    Args:
        content_dir: Directory containing Markdown/text pages.

    Returns:
        Documents sorted by filename for deterministic ordering.

    Raises:
        FileNotFoundError: If *content_dir* does not exist or contains no pages.
    """
    root = Path(content_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"Content directory not found: {root}")

    paths: list[Path] = []
    for pattern in _CONTENT_GLOBS:
        paths.extend(root.glob(pattern))

    documents: list[Document] = []
    for path in sorted(set(paths), key=lambda p: p.name):
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        title = _derive_title(text, fallback=path.stem.replace("-", " ").title())
        documents.append(
            Document(source=path.name, path=path, title=title, text=text)
        )

    if not documents:
        raise FileNotFoundError(
            f"No Markdown/text pages found in {root} "
            f"(looked for {', '.join(_CONTENT_GLOBS)})"
        )
    return documents


def _split_paragraphs(text: str) -> list[str]:
    """Split page text into non-empty paragraphs, dropping Markdown headings."""
    paragraphs: list[str] = []
    for block in re.split(r"\n\s*\n", text):
        # Strip leading heading markers so passage text reads as prose.
        cleaned = re.sub(r"^#{1,6}\s+", "", block.strip()).strip()
        if cleaned:
            paragraphs.append(cleaned)
    return paragraphs


def chunk_documents(
    documents: list[Document], target_chars: int = _TARGET_CHUNK_CHARS
) -> list[Chunk]:
    """Split each document into passage-sized chunks.

    Paragraphs are greedily concatenated until a chunk reaches *target_chars*,
    which keeps related sentences together while bounding chunk size.

    Args:
        documents: Pages produced by :func:`load_corpus`.
        target_chars: Soft upper bound on chunk length in characters.

    Returns:
        A flat list of :class:`Chunk` objects across all documents.
    """
    chunks: list[Chunk] = []
    for doc in documents:
        buffer = ""
        index = 0
        for paragraph in _split_paragraphs(doc.text):
            buffer = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
            if len(buffer) >= target_chars:
                chunks.append(
                    Chunk(source=doc.source, title=doc.title, text=buffer, chunk_index=index)
                )
                index += 1
                buffer = ""
        if buffer:
            chunks.append(
                Chunk(source=doc.source, title=doc.title, text=buffer, chunk_index=index)
            )
    return chunks
