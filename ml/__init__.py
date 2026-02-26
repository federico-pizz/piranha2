"""
Piranha ML Package

Contains the recommendation model, text embeddings, and training utilities.
"""
from .model import PiranhaRecommender, create_recommender
from .embed import TextEmbedder, get_embedder

__all__ = ["PiranhaRecommender", "create_recommender", "TextEmbedder", "get_embedder"]
