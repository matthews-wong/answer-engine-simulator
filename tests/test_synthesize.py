"""The offline extractive fallback returns an answer that cites the right page.

All tests force ``use_claude=False`` so no network or SDK is involved.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from answersim.corpus import chunk_documents, load_corpus
from answersim.retrieve import Retriever
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


def test_no_passages_yields_no_citations() -> None:
    answer = synthesize("anything at all", [], use_claude=False)

    assert answer.mode == "extractive"
    assert answer.cited_sources == []
    assert "No content" in answer.text
