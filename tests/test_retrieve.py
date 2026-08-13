"""Retrieval picks the topically-correct page for a query."""

from __future__ import annotations

from pathlib import Path

import pytest

from answersim.corpus import chunk_documents, load_corpus
from answersim.retrieve import Retriever


@pytest.fixture
def retriever(corpus_dir: Path) -> Retriever:
    documents = load_corpus(corpus_dir)
    return Retriever(chunk_documents(documents))


def test_top_passage_matches_query_topic(retriever: Retriever) -> None:
    passages = retriever.top_k("how does provisioned concurrency reduce cold starts", k=3)

    assert passages, "expected at least one matching passage"
    assert passages[0].chunk.source == "provisioned-concurrency.md"
    # Scores are sorted best-first and are real cosine similarities.
    assert passages[0].score > 0.0
    assert passages == sorted(passages, key=lambda p: p.score, reverse=True)


def test_different_query_selects_different_page(retriever: Retriever) -> None:
    passages = retriever.top_k("does deployment package size affect cold starts", k=3)

    assert passages
    assert passages[0].chunk.source == "package-size.md"


def test_off_topic_query_drops_zero_similarity_passages(retriever: Retriever) -> None:
    # A query with no shared vocabulary should not match the cold-start pages.
    passages = retriever.top_k("quantum entanglement in distant galaxies", k=3)
    sources = {p.chunk.source for p in passages}

    assert "provisioned-concurrency.md" not in sources
    assert "package-size.md" not in sources


def test_ranking_is_deterministic(retriever: Retriever, corpus_dir: Path) -> None:
    # TF-IDF retrieval has no randomness, so a freshly built index must produce
    # byte-identical scores for the same query — the property the whole tool
    # relies on to be a stable visibility signal.
    documents = load_corpus(corpus_dir)
    other = Retriever(chunk_documents(documents))

    query = "how does provisioned concurrency reduce cold starts"
    first = [(p.chunk.source, p.score) for p in retriever.top_k(query, k=3)]
    second = [(p.chunk.source, p.score) for p in other.top_k(query, k=3)]

    assert first == second


def test_top_k_larger_than_corpus_returns_all_matches(retriever: Retriever) -> None:
    # Asking for more passages than exist must not raise or pad — it returns
    # every positive-similarity passage, capped by what the corpus contains.
    passages = retriever.top_k("cold starts", k=1000)

    assert all(p.score > 0.0 for p in passages)
    assert passages == sorted(passages, key=lambda p: p.score, reverse=True)


def test_empty_chunks_rejected() -> None:
    with pytest.raises(ValueError):
        Retriever([])
