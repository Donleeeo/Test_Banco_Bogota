from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


class QdrantStore:
    def __init__(self, host: str, port: int) -> None:
        self.client = QdrantClient(host=host, port=port)

    def ensure_collection(self, name: str, vector_size: int) -> None:
        exists = self.client.collection_exists(collection_name=name)
        if exists:
            return
        self.client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    def upsert(self, collection: str, points: list[PointStruct]) -> None:
        self.client.upsert(collection_name=collection, points=points)

    def search(self, collection: str, vector: list[float], limit: int = 5):
        return self.client.search(collection_name=collection, query_vector=vector, limit=limit)
