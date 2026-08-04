"""Format the simulation result for the terminal.

The report shows the synthesized answer, which of your pages were "cited", and a
coverage note estimating how visible your content would be to an answer engine.
"""

from __future__ import annotations

from .retrieve import RetrievedPassage
from .synthesize import Answer


def _coverage_note(answer: Answer, passages: list[RetrievedPassage]) -> str:
    """Summarize retrieval strength and citation coverage in one line."""
    if not passages:
        return (
            "Coverage: none of your pages matched this query — an answer engine "
            "would be unlikely to cite you here."
        )
    top_score = passages[0].score
    distinct_pages = len({p.chunk.source for p in passages})
    return (
        f"Coverage: {len(answer.cited_sources)} of {distinct_pages} retrieved "
        f"page(s) were cited; top passage similarity {top_score:.2f}. "
        "Higher similarity and more cited pages suggest stronger AI-answer visibility."
    )


def format_report(
    query: str,
    answer: Answer,
    passages: list[RetrievedPassage],
) -> str:
    """Render a human-readable report for one simulated query.

    Args:
        query: The user question.
        answer: The synthesized :class:`Answer`.
        passages: The ranked passages used for synthesis.

    Returns:
        A multi-line string ready to print.
    """
    lines: list[str] = []
    lines.append(f"Query: {query}")
    lines.append(f"Synthesis mode: {answer.mode}")
    lines.append("")
    lines.append("Simulated answer:")
    lines.append(f"  {answer.text}")
    lines.append("")

    if answer.cited_sources:
        lines.append("Cited pages:")
        for number, source in enumerate(answer.cited_sources, start=1):
            lines.append(f"  [{number}] {source}")
    else:
        lines.append("Cited pages: none")
    lines.append("")

    lines.append("Retrieved passages (by TF-IDF similarity):")
    if passages:
        for passage in passages:
            lines.append(
                f"  {passage.score:.2f}  {passage.chunk.source} — {passage.chunk.title}"
            )
    else:
        lines.append("  (no matching passages)")
    lines.append("")

    lines.append(_coverage_note(answer, passages))
    return "\n".join(lines)
