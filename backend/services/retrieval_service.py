"""ChromaDB storage and search. Knows nothing about prompts or the AI model."""
from dataclasses import dataclass

from backend.services.chunking_service import Chunk


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    document_id: str
    filename: str
    page_number: int
    chunk_index: int
    score: float  # cosine similarity, higher is better


class RetrievalService:
    def __init__(self, client, collection_name: str = "document_chunks"):
        self._collection = client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, document_id: str, filename: str, chunks: list[Chunk],
                   embeddings: list[list[float]]) -> None:
        if not chunks:
            return
        self._collection.add(
            ids=[f"{document_id}:{c.index}" for c in chunks],
            documents=[c.text for c in chunks],
            embeddings=embeddings,
            metadatas=[
                {"document_id": document_id, "filename": filename,
                 "page_number": c.page_number, "chunk_index": c.index}
                for c in chunks
            ],
        )

    def search(self, query_embedding: list[float], document_ids: list[str] | None = None,
               top_k: int = 5) -> list[RetrievedChunk]:
        """document_ids=None searches everything; an empty list searches nothing."""
        if document_ids is not None and not document_ids:
            return []
        total = self._collection.count()
        if total == 0:
            return []
        where = None
        if document_ids is not None:
            where = ({"document_id": document_ids[0]} if len(document_ids) == 1
                     else {"document_id": {"$in": document_ids}})
        result = self._collection.query(
            query_embeddings=[query_embedding], n_results=min(top_k, total), where=where
        )
        hits = []
        for text, meta, dist in zip(result["documents"][0], result["metadatas"][0],
                                    result["distances"][0]):
            hits.append(RetrievedChunk(
                text=text, document_id=meta["document_id"], filename=meta["filename"],
                page_number=meta["page_number"], chunk_index=meta["chunk_index"],
                score=1.0 - dist,
            ))
        return hits

    def delete_document(self, document_id: str) -> None:
        self._collection.delete(where={"document_id": document_id})

    def count_for_document(self, document_id: str) -> int:
        return len(self._collection.get(where={"document_id": document_id}, include=[])["ids"])