"""
ASL Sign Language Recognition Model
Person 4 - Model Architecture

This model combines CNN and Transformer to recognize ASL signs from hand landmarks.
- CNN: Extracts local spatial patterns from landmarks
- Transformer: Captures temporal dependencies across frames

Input: (batch_size, num_frames, num_landmarks) -> (batch, 30, 63)
Output: (batch_size, num_classes) -> probability distribution over words
"""

import tensorflow as tf
from tensorflow.keras import layers, Model
import numpy as np


# =============================================================================
# POSITIONAL ENCODING (for Transformer)
# =============================================================================

class PositionalEncoding(layers.Layer):
    """
    Adds positional information to the input sequence.
    The Transformer doesn't know the order of frames without this.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def call(self, inputs):
        seq_length = tf.shape(inputs)[1]
        d_model = tf.shape(inputs)[2]
        
        # Create position indices
        positions = tf.range(seq_length, dtype=tf.float32)[:, tf.newaxis]
        dimensions = tf.range(d_model, dtype=tf.float32)[tf.newaxis, :]
        
        # Calculate angles
        angles = positions / tf.pow(10000.0, (2 * (dimensions // 2)) / tf.cast(d_model, tf.float32))
        
        # Apply sin to even indices, cos to odd indices
        sines = tf.sin(angles[:, 0::2])
        cosines = tf.cos(angles[:, 1::2])
        
        # Interleave sines and cosines
        pos_encoding = tf.concat([sines, cosines], axis=-1)
        pos_encoding = pos_encoding[:, :d_model]  # Ensure correct size
        
        return inputs + pos_encoding
    
    def get_config(self):
        return super().get_config()


# =============================================================================
# TRANSFORMER ENCODER BLOCK
# =============================================================================

class TransformerBlock(layers.Layer):
    """
    A single Transformer encoder block with:
    - Multi-Head Self-Attention
    - Feed-Forward Network
    - Residual connections and Layer Normalization
    """
    
    def __init__(self, embed_dim, num_heads, ff_dim, dropout_rate=0.1, **kwargs):
        super().__init__(**kwargs)
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.ff_dim = ff_dim
        self.dropout_rate = dropout_rate
        
        # Multi-Head Attention
        self.attention = layers.MultiHeadAttention(
            num_heads=num_heads,
            key_dim=embed_dim // num_heads
        )
        
        # Feed-Forward Network
        self.ffn = tf.keras.Sequential([
            layers.Dense(ff_dim, activation='relu'),
            layers.Dense(embed_dim)
        ])
        
        # Layer Normalization
        self.layernorm1 = layers.LayerNormalization(epsilon=1e-6)
        self.layernorm2 = layers.LayerNormalization(epsilon=1e-6)
        
        # Dropout
        self.dropout1 = layers.Dropout(dropout_rate)
        self.dropout2 = layers.Dropout(dropout_rate)
    
    def call(self, inputs, training=False):
        # Self-Attention with residual connection
        attention_output = self.attention(inputs, inputs)
        attention_output = self.dropout1(attention_output, training=training)
        x = self.layernorm1(inputs + attention_output)
        
        # Feed-Forward with residual connection
        ffn_output = self.ffn(x)
        ffn_output = self.dropout2(ffn_output, training=training)
        return self.layernorm2(x + ffn_output)
    
    def get_config(self):
        config = super().get_config()
        config.update({
            "embed_dim": self.embed_dim,
            "num_heads": self.num_heads,
            "ff_dim": self.ff_dim,
            "dropout_rate": self.dropout_rate
        })
        return config


# =============================================================================
# MAIN MODEL: CNN + TRANSFORMER
# =============================================================================

def build_asl_model(
    num_frames=30,
    num_landmarks=63,
    num_classes=100,
    cnn_filters=[64, 128],
    transformer_heads=4,
    transformer_dim=128,
    ff_dim=256,
    dropout_rate=0.3
):
    """
    Build the ASL Recognition Model combining CNN and Transformer.
    
    Args:
        num_frames: Number of frames per video (default: 30)
        num_landmarks: Number of landmark values per frame (default: 63 = 21 points × 3 coords)
        num_classes: Number of ASL words to classify (adjust based on your dataset)
        cnn_filters: List of filter sizes for CNN layers
        transformer_heads: Number of attention heads
        transformer_dim: Dimension of transformer embeddings
        ff_dim: Dimension of feed-forward network in transformer
        dropout_rate: Dropout rate for regularization
    
    Returns:
        Compiled Keras Model
    """
    
    # Input layer
    inputs = layers.Input(shape=(num_frames, num_landmarks), name='landmark_input')
    
    # =========================================================================
    # CNN BLOCK - Extract local patterns
    # =========================================================================
    x = inputs
    
    # First Conv1D layer
    x = layers.Conv1D(
        filters=cnn_filters[0],
        kernel_size=3,
        activation='relu',
        padding='same',
        name='conv1d_1'
    )(x)
    x = layers.BatchNormalization(name='bn_1')(x)
    
    # Second Conv1D layer
    x = layers.Conv1D(
        filters=cnn_filters[1],
        kernel_size=3,
        activation='relu',
        padding='same',
        name='conv1d_2'
    )(x)
    x = layers.BatchNormalization(name='bn_2')(x)
    
    # MaxPooling to reduce sequence length
    x = layers.MaxPooling1D(pool_size=2, name='maxpool')(x)
    
    # =========================================================================
    # PROJECTION - Match dimensions for Transformer
    # =========================================================================
    x = layers.Dense(transformer_dim, name='projection')(x)
    
    # =========================================================================
    # POSITIONAL ENCODING - Add position information
    # =========================================================================
    x = PositionalEncoding(name='positional_encoding')(x)
    x = layers.Dropout(dropout_rate, name='pos_dropout')(x)
    
    # =========================================================================
    # TRANSFORMER BLOCK - Capture temporal dependencies
    # =========================================================================
    x = TransformerBlock(
        embed_dim=transformer_dim,
        num_heads=transformer_heads,
        ff_dim=ff_dim,
        dropout_rate=dropout_rate,
        name='transformer_block'
    )(x)
    
    # Optional: Add more transformer blocks for deeper model
    # x = TransformerBlock(transformer_dim, transformer_heads, ff_dim, dropout_rate)(x)
    
    # =========================================================================
    # CLASSIFICATION HEAD - Make predictions
    # =========================================================================
    
    # Global Average Pooling - aggregate across time
    x = layers.GlobalAveragePooling1D(name='global_avg_pool')(x)
    
    # Dense layers
    x = layers.Dense(256, activation='relu', name='dense_1')(x)
    x = layers.Dropout(dropout_rate, name='dropout_1')(x)
    
    x = layers.Dense(128, activation='relu', name='dense_2')(x)
    x = layers.Dropout(dropout_rate, name='dropout_2')(x)
    
    # Output layer
    outputs = layers.Dense(num_classes, activation='softmax', name='output')(x)
    
    # Create model
    model = Model(inputs=inputs, outputs=outputs, name='ASL_CNN_Transformer')
    
    return model


# =============================================================================
# MODEL COMPILATION
# =============================================================================

def compile_model(model, learning_rate=0.001):
    """
    Compile the model with optimizer, loss, and metrics.
    
    Args:
        model: Keras model to compile
        learning_rate: Initial learning rate for Adam optimizer
    
    Returns:
        Compiled model
    """
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
        loss='categorical_crossentropy',
        metrics=[
            'accuracy',
            tf.keras.metrics.TopKCategoricalAccuracy(k=5, name='top5_accuracy')
        ]
    )
    return model


# =============================================================================
# TEST THE MODEL
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("ASL Sign Language Recognition Model")
    print("=" * 60)
    
    # Build model with default parameters
    model = build_asl_model(
        num_frames=30,        # 30 frames per video
        num_landmarks=63,     # 21 landmarks × 3 coordinates
        num_classes=100,      # Placeholder: adjust to your word count
        cnn_filters=[64, 128],
        transformer_heads=4,
        transformer_dim=128,
        ff_dim=256,
        dropout_rate=0.3
    )
    
    # Compile
    model = compile_model(model, learning_rate=0.001)
    
    # Print summary
    print("\nModel Summary:")
    print("-" * 60)
    model.summary()
    
    # Test with dummy data
    print("\n" + "-" * 60)
    print("Testing with dummy data...")
    print("-" * 60)
    
    # Create dummy input: (batch=2, frames=30, landmarks=63)
    dummy_input = np.random.randn(2, 30, 63).astype(np.float32)
    
    # Forward pass
    output = model.predict(dummy_input, verbose=0)
    
    print(f"Input shape:  {dummy_input.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Output sum (should be ~1.0 per sample): {output.sum(axis=1)}")
    
    print("\n" + "=" * 60)
    print("Model is ready! Adjust num_classes when you know the word count.")
    print("=" * 60)
    
    # Save model architecture to JSON (optional)
    # model_json = model.to_json()
    # with open("model_architecture.json", "w") as f:
    #     f.write(model_json)
    # print("Model architecture saved to model_architecture.json")
