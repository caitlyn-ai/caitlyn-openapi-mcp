#!/usr/bin/env python3
"""Download sentence-transformers model to cache directory."""

import os
import sys

# Use the cache directory from environment or default
cache_dir = os.environ.get("SENTENCE_TRANSFORMERS_HOME", "./models")

print(f"Downloading model to: {cache_dir}")

try:
    from sentence_transformers import SentenceTransformer

    # Set cache directory
    os.environ["SENTENCE_TRANSFORMERS_HOME"] = cache_dir

    # Download the model
    model_name = "all-MiniLM-L6-v2"
    print(f"Downloading {model_name}...")
    model = SentenceTransformer(model_name)
    print(f"✓ Model downloaded successfully to {cache_dir}")
    print(f"  Model: {model_name}")
    print(f"  Max sequence length: {model.max_seq_length}")
except Exception as e:
    print(f"✗ Failed to download model: {e}", file=sys.stderr)
    sys.exit(1)
