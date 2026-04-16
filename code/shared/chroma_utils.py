"""ChromaDB utilities for RAG evaluation.

Shared module consolidating collection-building and retrieval logic
previously duplicated across fair_rag_evaluation.py, ragas_evaluation.py,
and latency_comparison.py.
"""

import chromadb


def build_chroma_collection(
    chroma_client: chromadb.Client,
    name: str,
    qa_pairs: list[dict],
    batch_size: int = 100,
) -> chromadb.Collection:
    """Build an ephemeral ChromaDB collection from QA pairs.

    Recreates the collection if it already exists (clean slate).
    Documents are formatted as "Q: {question}\nA: {answer}" and indexed
    with cosine similarity via HNSW.

    Args:
        chroma_client: Active ChromaDB client.
        name: Collection name (will be recreated if exists).
        qa_pairs: List of dicts with 'question' and 'answer' keys.
        batch_size: Number of documents per batch insert.

    Returns:
        Populated ChromaDB collection.
    """
    # Delete if exists for a clean slate
    try:
        chroma_client.delete_collection(name)
    except Exception:
        pass

    collection = chroma_client.create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )

    for i in range(0, len(qa_pairs), batch_size):
        batch = qa_pairs[i : i + batch_size]
        documents = [f"Q: {p['question']}\nA: {p['answer']}" for p in batch]
        ids = [str(p.get("id", f"{name}_{i + j}")) for j, p in enumerate(batch)]
        metadatas = [{"question": p["question"], "answer": p["answer"]} for p in batch]
        collection.add(documents=documents, ids=ids, metadatas=metadatas)

    return collection


def retrieve_contexts(
    collection: chromadb.Collection,
    query: str,
    n_results: int = 3,
) -> list[str]:
    """Retrieve top-k context chunks via semantic similarity.

    Args:
        collection: ChromaDB collection to query.
        query: The user question.
        n_results: Number of top results to return.

    Returns:
        List of retrieved document strings.
    """
    results = collection.query(query_texts=[query], n_results=n_results)
    if results["documents"] and results["documents"][0]:
        return list(results["documents"][0])
    return []
