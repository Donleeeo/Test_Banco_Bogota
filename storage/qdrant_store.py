from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


class QdrantStore:
    def __init__(self, host: str, port: int) -> None:
        self.client = QdrantClient(host=host, port=port)

    def ensure_collection(self, name: str, vector_size: int) -> None:
        # Si la coleccion ya existe no la recreo para no perder datos.
        exists = self.client.collection_exists(collection_name=name)
        if exists:
            return
        self.client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    def upsert(self, collection: str, points: list[PointStruct]) -> None:
        # Upsert permite actualizar si el id ya existe.
        self.client.upsert(collection_name=collection, points=points)

    def search(self, collection: str, vector: list[float], limit: int = 5):
        # Soporte simple para clientes nuevos y antiguos de Qdrant.
        if hasattr(self.client, "query_points"):
            response = self.client.query_points(collection_name=collection, query=vector, limit=limit)
            return response.points
        return self.client.search(collection_name=collection, query_vector=vector, limit=limit)
