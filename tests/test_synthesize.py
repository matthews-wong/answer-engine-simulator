"""The offline extractive fallback returns an answer that cites the right page.

All tests force ``use_claude=False`` so no network or SDK is involved.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from answersim.corpus import Chunk, chunk_documents, load_corpus
from answersim.retrieve import RetrievedPassage, Retriever
from answersim.synthesize import synthesize


@pytest.fixture
def retriever(corpus_dir: Path) -> Retriever:
    documents = load_corpus(corpus_dir)
    return Retriever(chunk_documents(documents))


def test_fallback_answer_cites_the_retrieved_page(retriever: Retriever) -> None:
    query = "how does provisioned concurrency reduce cold starts"
    passages = retriever.top_k(query, k=3)

    answer = synthesize(query, passages, use_claude=False)

    assert answer.mode == "extractive"
    assert "provisioned-concurrency.md" in answer.cited_sources
    # The first cited page is citation [1] and appears as an inline marker.
    assert answer.cited_sources[0] == passages[0].chunk.source
    assert "[1]" in answer.text


def test_fallback_extracts_query_relevant_sentence(retriever: Retriever) -> None:
    query = "how does provisioned concurrency reduce cold starts"
    passages = retriever.top_k(query, k=3)

    answer = synthesize(query, passages, use_claude=False)

    # The chosen sentence should mention the concept the query asked about.
    assert "provisioned concurrency" in answer.text.lower()


def test_one_citation_per_page(retriever: Retriever) -> None:
    query = "cold start latency"
    passages = retriever.top_k(query, k=3)

    answer = synthesize(query, passages, use_claude=False)

    # Citations map to distinct pages, matching how an engine attributes claims.
    assert len(answer.cited_sources) == len(set(answer.cited_sources))


def test_inline_markers_map_to_cited_sources_by_position() -> None:
    # A page can contribute several chunks to the top-k. The inline ``[n]``
    # marker must index cited_sources by position (n -> cited_sources[n-1]), and
    # each page must be numbered once. This pins the citation numbering against
    # an off-by-one when a later passage repeats an already-seen page.
    passages = [
        RetrievedPassage(
            Chunk(source="a.md", title="A", text="Alpha concurrency detail.", chunk_index=0),
            score=0.9,
        ),
        RetrievedPassage(
            Chunk(source="b.md", title="B", text="Beta package detail.", chunk_index=0),
            score=0.6,
        ),
        RetrievedPassage(
            Chunk(source="a.md", title="A", text="Alpha second chunk.", chunk_index=1),
            score=0.3,
        ),
    ]

    answer = synthesize("alpha beta detail", passages, use_claude=False)

    # First-seen page order: a.md is [1], b.md is [2]; the repeat of a.md adds no
    # new citation.
    assert answer.cited_sources == ["a.md", "b.md"]
    for marker in re.findall(r"\[(\d+)\]", answer.text):
        number = int(marker)
        assert answer.cited_sources[number - 1] in {"a.md", "b.md"}
    assert "[1]" in answer.text and "[2]" in answer.text and "[3]" not in answer.text


def test_no_passages_yields_no_citations() -> None:
    answer = synthesize("anything at all", [], use_claude=False)

    assert answer.mode == "extractive"
    assert answer.cited_sources == []
    assert "No content" in answer.text
