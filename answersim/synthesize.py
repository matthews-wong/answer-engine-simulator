"""Synthesize an answer with inline citations from retrieved passages.

Two paths, same output contract:

* **Claude path** — used when ``ANTHROPIC_API_KEY`` is set and the ``anthropic``
  SDK is installed. Claude writes a grounded answer with inline ``[n]`` markers.
* **Extractive fallback** — used otherwise (and on *any* Claude error). It picks
  the most query-relevant sentence from each top passage. This keeps the tool
  fully runnable offline, which is what the tests exercise.

Both return an :class:`Answer`, so callers never branch on which path ran.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from .retrieve import RetrievedPassage

# Model used only on the optional Claude path; see README "Enabling Claude synthesis".
_CLAUDE_MODEL = "claude-sonnet-5"


@dataclass(frozen=True)
class Answer:
    """A synthesized answer plus provenance.

    Attributes:
        text: The answer, with inline ``[n]`` citation markers.
        cited_sources: Page filenames actually referenced, ordered by citation
            number. ``cited_sources[0]`` is source ``[1]``.
        mode: ``"claude"`` or ``"extractive"`` — which synthesis path produced it.
    """

    text: str
    cited_sources: list[str]
    mode: str


def _order_sources(passages: list[RetrievedPassage]) -> list[str]:
    """Return unique page filenames in retrieval order (their citation numbering)."""
    ordered: list[str] = []
    for passage in passages:
        if passage.chunk.source not in ordered:
            ordered.append(passage.chunk.source)
    return ordered


def _split_sentences(text: str) -> list[str]:
    """Split a passage into sentences with a simple, dependency-free heuristic."""
    parts = re.split(r"(?<=[.!?])\s+", text.replace("\n", " ").strip())
    return [part.strip() for part in parts if part.strip()]


def _best_sentence(query: str, passage_text: str) -> str:
    """Pick the sentence in *passage_text* sharing the most words with *query*."""
    query_terms = {term for term in re.findall(r"\w+", query.lower()) if len(term) > 2}
    sentences = _split_sentences(passage_text)
    if not sentences:
        return passage_text.strip()

    def overlap(sentence: str) -> int:
        words = set(re.findall(r"\w+", sentence.lower()))
        return len(query_terms & words)

    best = max(sentences, key=overlap)
    # If nothing overlaps, fall back to the passage's opening sentence.
    return best if overlap(best) else sentences[0]


def _extractive_synthesize(query: str, passages: list[RetrievedPassage]) -> Answer:
    """Build an answer by extracting the top sentence from each cited page.

    One sentence is taken per *page* (not per chunk) so citations map cleanly to
    pages, matching how an answer engine attributes claims.
    """
    source_order = _order_sources(passages)
    citation_number = {source: i + 1 for i, source in enumerate(source_order)}

    seen_sources: set[str] = set()
    lines: list[str] = []
    cited: list[str] = []
    for passage in passages:
        source = passage.chunk.source
        if source in seen_sources:
            continue
        seen_sources.add(source)
        sentence = _best_sentence(query, passage.chunk.text)
        lines.append(f"{sentence} [{citation_number[source]}]")
        cited.append(source)

    if not lines:
        return Answer(
            text="No content in the corpus is relevant to this query.",
            cited_sources=[],
            mode="extractive",
        )
    return Answer(text=" ".join(lines), cited_sources=cited, mode="extractive")


def _build_claude_prompt(query: str, passages: list[RetrievedPassage]) -> str:
    """Render the numbered-passage prompt sent to Claude."""
    source_order = _order_sources(passages)
    citation_number = {source: i + 1 for i, source in enumerate(source_order)}

    blocks: list[str] = []
    for passage in passages:
        number = citation_number[passage.chunk.source]
        blocks.append(f"[{number}] ({passage.chunk.title})\n{passage.chunk.text}")
    passages_text = "\n\n".join(blocks)

    return (
        "You are simulating how an AI answer engine responds using only the "
        "passages below. Answer the question in 2-4 sentences using ONLY these "
        "passages. Add an inline citation marker like [1] or [2] after each claim, "
        "matching the numbered passage it came from. If the passages do not answer "
        "the question, say so plainly.\n\n"
        f"Question: {query}\n\n"
        f"Passages:\n{passages_text}\n\nAnswer:"
    )


def _cited_from_text(text: str, source_order: list[str]) -> list[str]:
    """Extract which page sources a ``[n]``-annotated answer actually referenced."""
    numbers = sorted({int(n) for n in re.findall(r"\[(\d+)\]", text)})
    cited: list[str] = []
    for number in numbers:
        if 1 <= number <= len(source_order):
            cited.append(source_order[number - 1])
    return cited


def _claude_synthesize(query: str, passages: list[RetrievedPassage]) -> Answer:
    """Synthesize via the Claude API. Raises on any SDK/transport error."""
    import anthropic  # imported lazily so the package works without the SDK

    client = anthropic.Anthropic()
    prompt = _build_claude_prompt(query, passages)
    response = client.messages.create(
        model=_CLAUDE_MODEL,
        max_tokens=1024,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()

    cited = _cited_from_text(text, _order_sources(passages))
    return Answer(text=text, cited_sources=cited, mode="claude")


def _claude_available() -> bool:
    """Return True if the Claude path can be attempted (key set and SDK present)."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


def synthesize(
    query: str,
    passages: list[RetrievedPassage],
    use_claude: bool | None = None,
) -> Answer:
    """Synthesize an answer with inline citations from retrieved *passages*.

    Args:
        query: The user question.
        passages: Ranked passages from :meth:`answersim.retrieve.Retriever.top_k`.
        use_claude: Force the synthesis path. ``None`` (default) auto-detects:
            use Claude when a key and the SDK are available, otherwise extract.
            ``False`` forces the offline extractive path (used by the tests).

    Returns:
        An :class:`Answer`. The Claude path degrades gracefully to the extractive
        path on any error, so this function never raises for synthesis failures.
    """
    if not passages:
        return Answer(
            text="No content in the corpus is relevant to this query.",
            cited_sources=[],
            mode="extractive",
        )

    should_use_claude = _claude_available() if use_claude is None else use_claude
    if should_use_claude:
        try:
            return _claude_synthesize(query, passages)
        except Exception:  # noqa: BLE001 — any failure must fall back cleanly
            pass
    return _extractive_synthesize(query, passages)
