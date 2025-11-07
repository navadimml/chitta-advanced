"""
Embedding Service for Semantic Similarity

Uses sentence-transformers to create embeddings for semantic matching.
Much more robust than string matching - handles variations, synonyms, paraphrasing.
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
from numpy.linalg import norm

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for creating and comparing semantic embeddings

    Uses a small, fast multilingual model that works well for Hebrew and English.
    """

    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Initialize embedding service

        Args:
            model_name: HuggingFace model name (default: multilingual model that works for Hebrew)
        """
        logger.info(f"Loading embedding model: {model_name}")
        try:
            self.model = SentenceTransformer(model_name)
            logger.info("✓ Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def embed(self, text: str) -> np.ndarray:
        """
        Create embedding for a single text

        Args:
            text: Text to embed

        Returns:
            Embedding vector as numpy array
        """
        return self.model.encode(text, convert_to_numpy=True)

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Create embeddings for multiple texts efficiently

        Args:
            texts: List of texts to embed

        Returns:
            Matrix of embeddings (one row per text)
        """
        return self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

    def cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score between 0 and 1 (1 = identical meaning)
        """
        return float(np.dot(embedding1, embedding2) / (norm(embedding1) * norm(embedding2)))

    def find_most_similar(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: np.ndarray,
        threshold: float = 0.5
    ) -> Optional[Tuple[int, float]]:
        """
        Find the most similar embedding from candidates

        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: Matrix of candidate embeddings
            threshold: Minimum similarity score to consider a match

        Returns:
            Tuple of (index, similarity_score) or None if no match above threshold
        """
        # Calculate similarities with all candidates
        similarities = np.dot(candidate_embeddings, query_embedding) / (
            norm(candidate_embeddings, axis=1) * norm(query_embedding)
        )

        # Find best match
        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])

        if best_score >= threshold:
            return (best_idx, best_score)

        return None


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create singleton embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
