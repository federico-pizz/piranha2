"""
Text Embedding Utilities (TensorFlow-only)

Generates embeddings from product text using TensorFlow Hub's
Universal Sentence Encoder (USE). Supports multilingual text.
"""
from typing import List, Optional
import numpy as np
import os
import tensorflow as tf
import tensorflow_hub as hub


class TextEmbedder:
    """
    TensorFlow-based text embedder using Universal Sentence Encoder.
    
    Uses the multilingual USE model for Italian text support.
    Embeddings are cached in Redis for performance.
    """
    
    # Multilingual Universal Sentence Encoder
    MODEL_URL = "https://tfhub.dev/google/universal-sentence-encoder-multilingual/3"
    EMBEDDING_DIM = 512
    
    def __init__(self, use_cache: bool = True):
        """
        Initialize the embedder.
        
        Args:
            use_cache: Whether to cache embeddings in Redis
        """
        self.use_cache = use_cache
        self._model = None
        self._redis = None
    
    @property
    def model(self):
        """Lazy load the model (downloads on first use)."""
        if self._model is None:
            print("Loading Universal Sentence Encoder (multilingual)...")
            self._model = hub.load(self.MODEL_URL)
            print("Model loaded successfully!")
        return self._model
    
    @property
    def redis_client(self):
        """Lazy init Redis client."""
        if self._redis is None and self.use_cache:
            try:
                import redis
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
                self._redis = redis.from_url(redis_url)
            except Exception:
                self._redis = False  # Disable caching
        return self._redis if self._redis else None
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text (title + description)
        
        Returns:
            numpy array of shape (512,)
        """
        # Check cache first
        cache_key = f"emb:{hash(text) % (10**8)}"
        if self.redis_client:
            cached = self.redis_client.get(cache_key)
            if cached:
                return np.frombuffer(cached, dtype=np.float32)
        
        # Generate embedding
        embeddings = self.model([text])
        embedding = embeddings[0].numpy()
        
        # Cache for 24 hours
        if self.redis_client:
            self.redis_client.setex(
                cache_key,
                86400,
                embedding.astype(np.float32).tobytes()
            )
        
        return embedding
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            batch_size: Batch size for encoding (USE handles internally)
        
        Returns:
            numpy array of shape (len(texts), 512)
        """
        # USE handles batching efficiently
        embeddings = self.model(texts)
        return embeddings.numpy()
    
    def embed_product(self, title: str, description: Optional[str] = None) -> np.ndarray:
        """
        Generate embedding for a product.
        Combines title and description for richer representation.
        
        Args:
            title: Product title
            description: Optional product description
        
        Returns:
            numpy array of shape (512,)
        """
        if description:
            text = f"{title}. {description[:500]}"  # Truncate long descriptions
        else:
            text = title
        
        return self.embed_text(text)
    
    @property
    def embedding_dim(self) -> int:
        """Return the embedding dimension."""
        return self.EMBEDDING_DIM


# Singleton instance for the app
_embedder_instance: Optional[TextEmbedder] = None


def get_embedder() -> TextEmbedder:
    """Get or create the global embedder instance."""
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = TextEmbedder()
    return _embedder_instance


def precompute_embeddings(db_session, batch_size: int = 100):
    """
    Pre-compute embeddings for all products in the database.
    Store in Redis for fast access.
    """
    from backend.services.db import Product
    
    embedder = get_embedder()
    offset = 0
    
    while True:
        products = db_session.query(Product) \
            .order_by(Product.id) \
            .offset(offset) \
            .limit(batch_size) \
            .all()
        
        if not products:
            break
        
        texts = [
            f"{p.title}. {p.description[:500] if p.description else ''}"
            for p in products
        ]
        
        embeddings = embedder.embed_batch(texts)
        
        # Store embeddings in Redis
        for product, embedding in zip(products, embeddings):
            if embedder.redis_client:
                embedder.redis_client.setex(
                    f"product_emb:{product.id}",
                    86400 * 7,  # 1 week
                    embedding.astype(np.float32).tobytes()
                )
        
        offset += batch_size
        print(f"Embedded {offset} products...")
    
    print("Done!")
