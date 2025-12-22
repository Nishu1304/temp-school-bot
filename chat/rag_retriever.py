# chat/rag_retriever.py
import os
import json
import math
import logging
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

from django.conf import settings
from .models import SchoolDocument

logger = logging.getLogger(__name__)

# Config - adjust if needed
INDEX_DIR = getattr(settings, "VECTOR_INDEX_DIR", "vector_index")
INDEX_PATH = os.path.join(INDEX_DIR, "index.faiss")
DOCMAP_PATH = os.path.join(INDEX_DIR, "doc_map.json")
EMBED_MODEL_NAME = getattr(settings, "EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
BATCH_SIZE = 64

# Module-level cache
_index = None
_doc_map = None
_embedder = None


def _ensure_dirs():
    os.makedirs(INDEX_DIR, exist_ok=True)


def _get_embedder():
    global _embedder
    if _embedder is None:
        logger.info("Loading embedding model: %s", EMBED_MODEL_NAME)
        _embedder = SentenceTransformer(EMBED_MODEL_NAME)
    return _embedder


def _save_doc_map(mapping: dict):
    with open(DOCMAP_PATH, "w", encoding="utf-8") as f:
        json.dump(mapping, f)


def _load_doc_map():
    global _doc_map
    if _doc_map is None:
        if os.path.exists(DOCMAP_PATH):
            with open(DOCMAP_PATH, "r", encoding="utf-8") as f:
                _doc_map = json.load(f)
        else:
            _doc_map = {}
    return _doc_map


def _save_index(index: faiss.Index):
    faiss.write_index(index, INDEX_PATH)


def _load_index():
    global _index
    if _index is None:
        if os.path.exists(INDEX_PATH):
            _index = faiss.read_index(INDEX_PATH)
        else:
            _index = None
    return _index


def index_documents(batch_size: int = BATCH_SIZE):
    """
    Build FAISS index from all SchoolDocument rows.
    Overwrites existing index files.
    """
    _ensure_dirs()
    embedder = _get_embedder()

    docs = list(SchoolDocument.objects.all())
    if not docs:
        logger.info("No SchoolDocument rows found. Nothing to index.")
        # remove any old files
        if os.path.exists(INDEX_PATH):
            os.remove(INDEX_PATH)
        if os.path.exists(DOCMAP_PATH):
            os.remove(DOCMAP_PATH)
        return {"indexed": 0}

    # Create embeddings in batches
    vectors = []
    mapping = {}
    total = len(docs)
    logger.info("Indexing %d documents in batches of %d", total, batch_size)

    for start in range(0, total, batch_size):
        batch = docs[start : start + batch_size]
        texts = [d.content if d.content else "" for d in batch]
        # encode -> numpy array
        embs = embedder.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        if embs.dtype != np.float32:
            embs = embs.astype("float32")
        for i, emb in enumerate(embs):
            idx = start + i
            vectors.append(emb)
            mapping[str(idx)] = batch[i].id

    vectors = np.stack(vectors).astype("float32")
    dim = vectors.shape[1]
    logger.info("Creating FAISS Index (dim=%d, n=%d)", dim, vectors.shape[0])
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)

    # save to disk
    _save_index(index)
    _save_doc_map(mapping)

    # reset caches
    global _index, _doc_map
    _index = index
    _doc_map = mapping

    logger.info("Indexing complete. Vectors indexed: %d", vectors.shape[0])
    return {"indexed": vectors.shape[0]}


def get_context(query: str, top_k: int = 3) -> List[SchoolDocument]:
    """
    Return top_k SchoolDocument objects most similar to query.
    If index doesn't exist, returns empty list.
    """
    if not query or not query.strip():
        return []

    _ensure_dirs()
    index = _load_index()
    mapping = _load_doc_map()

    if index is None or not mapping:
        logger.info("No FAISS index or doc map found.")
        return []

    embedder = _get_embedder()
    qvec = embedder.encode([query], convert_to_numpy=True)
    qvec = qvec.astype("float32")

    try:
        D, I = index.search(qvec, top_k)
    except Exception as e:
        logger.exception("FAISS search error: %s", e)
        return []

    results = []
    # I is shape (1, top_k)
    for idx in I[0]:
        if idx == -1:
            continue
        # mapping keys were saved as strings
        doc_id = mapping.get(str(int(idx))) or mapping.get(int(idx))
        if doc_id:
            try:
                doc = SchoolDocument.objects.get(id=doc_id)
                results.append(doc)
            except SchoolDocument.DoesNotExist:
                logger.warning("Mapped doc id %s not found in DB", doc_id)
    return results
