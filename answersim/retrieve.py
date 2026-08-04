"""TF-IDF retrieval over content chunks.

A real answer engine runs a large learned retriever; this project uses classic
TF-IDF with cosine similarity (scikit-learn) as a transparent, offline stand-in.
It is enough to demonstrate *which* of your passages an engine would likely draw
on to answer a query.
"""

from __future__ import annotations

from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .corpus import Chunk


@dataclass(frozen=True)
class RetrievedPassage:
    """A chunk paired with its cosine-similarity score for a query."""

    chunk: Chunk
    score: float


class Retriever:
    """A TF-IDF index over content chunks with top-k cosine retrieval."""

    def __init__(self, chunks: list[Chunk]) -> None:
        """Build the TF-IDF matrix over *chunks*.

        Args:
            chunks: Passages to index (from :func:`answersim.corpus.chunk_documents`).

        Raises:
            ValueError: If *chunks* is empty.
        """
        if not chunks:
            raise ValueError("Cannot build a retriever from an empty chunk list.")
        self._chunks = chunks
        # English stop words + sublinear tf dampening give stable ranking on
        # small corpora without any tuning.
        self._vectorizer = TfidfVectorizer(stop_words="english", sublinear_tf=True)
        self._matrix = self._vectorizer.fit_transform(c.text for c in chunks)

    def top_k(self, query: str, k: int = 3) -> list[RetrievedPassage]:
        """Return the *k* passages most similar to *query*, best first.

        Passages with zero similarity (no shared vocabulary) are dropped, so the
        result may contain fewer than *k* items — this signals that the corpus
        does not cover the query, which is itself a useful visibility signal.

        Args:
            query: The user question.
            k: Maximum number of passages to return.

        Returns:
            Ranked :class:`RetrievedPassage` objects.
        """
        query_vector = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self._matrix)[0]
        ranked = sorted(
            (
                RetrievedPassage(chunk=chunk, score=float(score))
                for chunk, score in zip(self._chunks, scores, strict=True)
            ),
            key=lambda passage: passage.score,
            reverse=True,
        )
        return [passage for passage in ranked[:k] if passage.score > 0.0]
