import hashlib
import struct


def generate_placeholder_embedding(text: str, dimensions: int) -> list[float]:
    """Deterministic pseudo-embedding, NOT a real one.

    It only proves the storage/retrieval pipeline (pgvector column, write,
    read) works end to end before a real provider is wired in a later step
    (OpenAI or sentence-transformers, see services/embeddings.py TODO there).
    Same text always produces the same vector; there is no semantic meaning
    encoded, so similarity search results at this stage are meaningless.
    """
    vector: list[float] = []
    counter = 0
    while len(vector) < dimensions:
        digest = hashlib.sha256(f"{text}:{counter}".encode("utf-8")).digest()
        for i in range(0, len(digest), 4):
            if len(vector) >= dimensions:
                break
            value = struct.unpack("I", digest[i:i + 4])[0]
            vector.append((value / 0xFFFFFFFF) * 2 - 1)  # normalize to [-1, 1]
        counter += 1
    return vector
