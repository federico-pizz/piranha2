"""
Piranha Recommendation Model

A simple TensorFlow/Keras hybrid recommender that combines:
1. Collaborative Filtering (user-item interactions)
2. Content-Based Filtering (product text embeddings)

Designed to be simple, efficient, and serve as a learning example.
"""
import tensorflow as tf
from tensorflow import keras
from typing import Tuple, Optional
import numpy as np


class PiranhaRecommender(keras.Model):
    """
    Hybrid Recommender Model
    
    Architecture:
    - User embedding (learned from interactions)
    - Item embedding (learned from interactions)
    - Content embedding from product text (pre-computed)
    - Fusion layer combining all signals
    
    The model outputs a relevance score [0, 1] for user-item pairs.
    """
    
    def __init__(
        self,
        num_users: int,
        num_items: int,
        embedding_dim: int = 64,
        content_embedding_dim: int = 512,  # From TensorFlow Hub USE
        hidden_units: Tuple[int, ...] = (128, 64),
        dropout_rate: float = 0.2,
        **kwargs
    ):
        super().__init__(**kwargs)
        
        self.num_users = num_users
        self.num_items = num_items
        self.embedding_dim = embedding_dim
        
        # User and Item embeddings (collaborative filtering)
        self.user_embedding = keras.layers.Embedding(
            input_dim=num_users,
            output_dim=embedding_dim,
            embeddings_regularizer=keras.regularizers.l2(1e-6),
            name="user_embedding"
        )
        
        self.item_embedding = keras.layers.Embedding(
            input_dim=num_items,
            output_dim=embedding_dim,
            embeddings_regularizer=keras.regularizers.l2(1e-6),
            name="item_embedding"
        )
        
        # Content feature processor
        self.content_processor = keras.Sequential([
            keras.layers.Dense(128, activation="relu"),
            keras.layers.Dropout(dropout_rate),
            keras.layers.Dense(embedding_dim, activation="relu"),
        ], name="content_processor")
        
        # Fusion layers - combine all signals
        fusion_layers = []
        for units in hidden_units:
            fusion_layers.extend([
                keras.layers.Dense(units, activation="relu"),
                keras.layers.BatchNormalization(),
                keras.layers.Dropout(dropout_rate),
            ])
        fusion_layers.append(keras.layers.Dense(1, activation="sigmoid"))
        
        self.fusion = keras.Sequential(fusion_layers, name="fusion")
    
    def call(self, inputs: dict, training: bool = False) -> tf.Tensor:
        """
        Forward pass.
        
        Args:
            inputs: dict with keys:
                - user_id: (batch_size,) int tensor
                - item_id: (batch_size,) int tensor
                - content_embedding: (batch_size, content_embedding_dim) float tensor
            training: whether in training mode
        
        Returns:
            scores: (batch_size, 1) relevance scores
        """
        user_id = inputs["user_id"]
        item_id = inputs["item_id"]
        content_emb = inputs.get("content_embedding")
        
        # Get embeddings
        user_vec = self.user_embedding(user_id)  # (batch, emb_dim)
        item_vec = self.item_embedding(item_id)  # (batch, emb_dim)
        
        # Element-wise product for collaborative signal
        collab_signal = user_vec * item_vec  # (batch, emb_dim)
        
        # Process content embedding if provided
        if content_emb is not None:
            content_vec = self.content_processor(content_emb, training=training)
            # Concatenate all signals
            combined = tf.concat([collab_signal, user_vec, item_vec, content_vec], axis=-1)
        else:
            combined = tf.concat([collab_signal, user_vec, item_vec], axis=-1)
        
        # Fusion to get final score
        score = self.fusion(combined, training=training)
        
        return score
    
    def get_config(self):
        """For model serialization."""
        return {
            "num_users": self.num_users,
            "num_items": self.num_items,
            "embedding_dim": self.embedding_dim,
        }


def create_recommender(
    num_users: int = 10000,
    num_items: int = 100000,
    embedding_dim: int = 64,
) -> PiranhaRecommender:
    """Factory function to create the recommender model."""
    model = PiranhaRecommender(
        num_users=num_users,
        num_items=num_items,
        embedding_dim=embedding_dim,
    )
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss=keras.losses.BinaryCrossentropy(),
        metrics=[
            keras.metrics.BinaryAccuracy(name="accuracy"),
            keras.metrics.AUC(name="auc"),
        ]
    )
    
    return model


class TwoTowerModel(keras.Model):
    """
    Alternative: Two-Tower Architecture
    
    Separate towers for users and items allow for:
    - Pre-computing item embeddings for fast inference
    - Approximate nearest neighbor search
    - Better scalability
    
    This is more scalable for production but slightly more complex.
    """
    
    def __init__(
        self,
        num_users: int,
        num_items: int,
        embedding_dim: int = 64,
        content_dim: int = 384,
        **kwargs
    ):
        super().__init__(**kwargs)
        
        # User tower
        self.user_embedding = keras.layers.Embedding(num_users, embedding_dim)
        self.user_tower = keras.Sequential([
            keras.layers.Dense(128, activation="relu"),
            keras.layers.Dense(embedding_dim),
            keras.layers.Lambda(lambda x: tf.nn.l2_normalize(x, axis=1))
        ], name="user_tower")
        
        # Item tower (includes content)
        self.item_embedding = keras.layers.Embedding(num_items, embedding_dim)
        self.item_tower = keras.Sequential([
            keras.layers.Dense(256, activation="relu"),
            keras.layers.Dense(embedding_dim),
            keras.layers.Lambda(lambda x: tf.nn.l2_normalize(x, axis=1))
        ], name="item_tower")
        
        # Temperature for softmax
        self.temperature = tf.Variable(0.05, trainable=True, name="temperature")
    
    def call(self, inputs: dict, training: bool = False) -> tf.Tensor:
        """Compute similarity between user and item embeddings."""
        user_id = inputs["user_id"]
        item_id = inputs["item_id"]
        content_emb = inputs.get("content_embedding")
        
        # User embedding
        user_vec = self.user_embedding(user_id)
        user_vec = self.user_tower(user_vec, training=training)
        
        # Item embedding (optionally with content)
        item_vec = self.item_embedding(item_id)
        if content_emb is not None:
            item_vec = tf.concat([item_vec, content_emb], axis=-1)
        item_vec = self.item_tower(item_vec, training=training)
        
        # Cosine similarity
        similarity = tf.reduce_sum(user_vec * item_vec, axis=-1, keepdims=True)
        score = tf.nn.sigmoid(similarity / self.temperature)
        
        return score
