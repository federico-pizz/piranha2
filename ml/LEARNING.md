# ML - Learning Guide

This folder contains the recommendation system using TensorFlow/Keras.

## 🔧 Key Concepts

### Recommendation Systems Overview

Two main approaches:

1. **Collaborative Filtering** - "Users who liked X also liked Y"
   - Uses user-item interaction matrix
   - Works well with lots of data
   
2. **Content-Based Filtering** - "Items similar to X"
   - Uses item features (title, description)
   - Works for new items (no cold-start)

Our model uses **both** (hybrid approach).

### Embeddings

Embeddings convert high-dimensional data to dense vectors:

```python
# Instead of one-hot (10000 dimensions)
user_onehot = [0, 0, 1, 0, ..., 0]  # Very sparse

# Use embeddings (64 dimensions)
user_embedding = [0.12, -0.45, 0.78, ...]  # Dense and learnable
```

TensorFlow embeddings:
```python
embedding_layer = tf.keras.layers.Embedding(
    input_dim=10000,    # Vocabulary size
    output_dim=64       # Embedding dimension
)
```

### The Model Architecture

```
           User ID            Item ID         Text Embedding
              │                  │                  │
              ▼                  ▼                  ▼
        ┌──────────┐      ┌──────────┐      ┌──────────┐
        │Embedding │      │Embedding │      │  Dense   │
        │  Layer   │      │  Layer   │      │  Layers  │
        └────┬─────┘      └────┬─────┘      └────┬─────┘
             │                 │                  │
             └────────┬────────┴──────────────────┘
                      │
                      ▼
                ┌───────────┐
                │  Fusion   │
                │  Layers   │
                └─────┬─────┘
                      │
                      ▼
                ┌───────────┐
                │  Score    │
                │  [0, 1]   │
                └───────────┘
```

### Text Embeddings (Sentence Transformers)

Convert text to vectors that capture meaning:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# Similar texts → similar vectors
vec1 = model.encode("iPhone 13 nuovo")
vec2 = model.encode("Apple iPhone 13 come nuovo")
# cosine_similarity(vec1, vec2) ≈ 0.9
```

We use multilingual models for Italian text.

## 📁 File Structure

```
ml/
├── model.py   # TensorFlow model definition
├── embed.py   # Text embedding utilities
├── train.py   # Training script
└── model/     # Saved models (git-ignored)
```

## 🔄 Training Pipeline

1. **Data Preparation** - User interactions (views, likes)
2. **Embedding Generation** - Text → vectors
3. **Model Training** - Learn user preferences
4. **Evaluation** - AUC, accuracy metrics
5. **Export** - Save for inference

```bash
# Train with synthetic data
python train.py --epochs 10 --batch-size 256

# Train with custom parameters
python train.py --num-users 5000 --num-items 50000
```

## 💡 Key TensorFlow Concepts

### Custom Model (Subclassing)

```python
class MyModel(tf.keras.Model):
    def __init__(self):
        super().__init__()
        self.dense = tf.keras.layers.Dense(64)
    
    def call(self, inputs, training=False):
        return self.dense(inputs)
```

### Training Loop

```python
model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy']
)

model.fit(
    train_dataset,
    validation_data=val_dataset,
    epochs=10
)
```

### Callbacks

```python
callbacks = [
    tf.keras.callbacks.EarlyStopping(patience=3),
    tf.keras.callbacks.ModelCheckpoint('best.keras'),
    tf.keras.callbacks.TensorBoard(log_dir='logs/')
]
```

## 🧪 Quick Test

```python
# Test embeddings
from embed import get_embedder

embedder = get_embedder()
vec = embedder.embed_text("Fiat Panda usata Milano")
print(f"Embedding shape: {vec.shape}")  # (384,)
```

## 📊 Metrics to Watch

- **AUC** (Area Under Curve) - Classification quality
- **Precision@K** - Top-K recommendation accuracy
- **Recall@K** - Coverage of relevant items

## 📚 Resources

- [TensorFlow Recommenders](https://www.tensorflow.org/recommenders)
- [Sentence Transformers](https://www.sbert.net/)
- [Keras Documentation](https://keras.io/)
- [Deep Learning for Recommender Systems](https://dl.acm.org/doi/10.1145/3240323.3240372)
