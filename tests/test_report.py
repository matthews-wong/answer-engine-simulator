"""The report renders citations and a coverage note faithfully.

``report.py`` turns a synthesized answer plus its retrieved passages into the
terminal output. These tests pin the two things a user reads for a visibility
signal: which pages were cited, and the coverage summary line.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from answersim.corpus import chunk_documents, load_corpus
from answersim.report import format_report
from answersim.retrieve import Retriever
from answersim.synthesize import synthesize


@pytest.fixture
def retriever(corpus_dir: Path) -> Retriever:
    documents = load_corpus(corpus_dir)
    return Retriever(chunk_documents(documents))


def test_report_lists_cited_pages_in_citation_order(retriever: Retriever) -> None:
    query = "how does provisioned concurrency reduce cold starts"
    passages = retriever.top_k(query, k=3)
    answer = synthesize(query, passages, use_claude=False)

    report = format_report(query, answer, passages)

    # Each cited page is numbered to match its inline ``[n]`` marker, in order.
    assert "Cited pages:" in report
    for number, source in enumerate(answer.cited_sources, start=1):
        assert f"[{number}] {source}" in report


def test_coverage_note_counts_cited_of_retrieved(retriever: Retriever) -> None:
    query = "how does provisioned concurrency reduce cold starts"
    passages = retriever.top_k(query, k=3)
    answer = synthesize(query, passages, use_claude=False)

    report = format_report(query, answer, passages)

    distinct_pages = len({p.chunk.source for p in passages})
    # The extractive path cites one sentence per distinct retrieved page, so the
    # coverage line reports "<distinct> of <distinct>" — an off-by-one in either
    # count would break this.
    assert (
        f"Coverage: {len(answer.cited_sources)} of {distinct_pages} retrieved"
        in report
    )
    # Similarity is shown as a 0-1 ratio (not a percentage) with two decimals.
    assert f"top passage similarity {passages[0].score:.2f}" in report


def test_report_handles_no_matching_passages() -> None:
    query = "quantum entanglement in distant galaxies"
    answer = synthesize(query, [], use_claude=False)

    report = format_report(query, answer, [])

    assert "Cited pages: none" in report
    assert "(no matching passages)" in report
    assert "none of your pages matched this query" in report
