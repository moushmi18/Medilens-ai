"""LlamaIndex integration for document processing and vector store.

Uses LlamaIndex for:
- Semantic node parsing/chunking
- Qdrant vector store integration
- Document ingestion pipeline
"""
from typing import Any, List
from uuid import uuid4

from llama_index.core import Document, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from app.core.logging import get_logger
from app.embeddings.qdrant_client import TRUSTED_KNOWLEDGE_COLLECTION

logger = get_logger(__name__)

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


def get_llama_embed_model():
    """Get LlamaIndex embedding model."""
    return HuggingFaceEmbedding(model_name=EMBEDDING_MODEL)


def get_qdrant_vector_store(
    client: QdrantClient,
    collection_name: str = TRUSTED_KNOWLEDGE_COLLECTION,
) -> QdrantVectorStore:
    """Get LlamaIndex Qdrant vector store wrapper."""
    return QdrantVectorStore(
        client=client,
        collection_name=collection_name,
    )


class LlamaIndexDocumentProcessor:
    """Document processor using LlamaIndex for parsing and chunking."""
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        self.node_parser = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        
        self.embed_model = get_llama_embed_model()
        Settings.embed_model = self.embed_model
    
    def parse_document(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> List[TextNode]:
        """Parse a document into nodes using LlamaIndex.
        
        Args:
            text: Document text
            metadata: Optional metadata to attach to nodes
            
        Returns:
            List of TextNode objects
        """
        doc = Document(
            text=text,
            metadata=metadata or {},
        )
        
        nodes = self.node_parser.get_nodes_from_documents([doc])
        
        for node in nodes:
            if metadata:
                node.metadata.update(metadata)
        
        logger.debug(
            "document_parsed_with_llamaindex",
            node_count=len(nodes),
            chunk_size=self.chunk_size,
        )
        
        return nodes
    
    def nodes_to_qdrant_points(
        self,
        nodes: List[TextNode],
        source_id: str,
    ) -> List[dict]:
        """Convert LlamaIndex nodes to Qdrant point format.
        
        Args:
            nodes: List of TextNode objects
            source_id: Source document ID
            
        Returns:
            List of dicts ready for Qdrant upsert
        """
        points = []
        
        for i, node in enumerate(nodes):
            embedding = self.embed_model.get_text_embedding(node.text)
            
            point = {
                "id": str(uuid4()),
                "vector": embedding,
                "payload": {
                    "source_id": source_id,
                    "chunk_index": i,
                    "chunk_text": node.text,
                    "node_id": node.node_id,
                    **node.metadata,
                },
            }
            points.append(point)
        
        return points
    
    def ingest_to_qdrant(
        self,
        client: QdrantClient,
        collection_name: str,
        text: str,
        source_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Full ingestion pipeline using LlamaIndex.
        
        Args:
            client: Qdrant client
            collection_name: Target collection
            text: Document text
            source_id: Source document ID
            metadata: Optional metadata
            
        Returns:
            Number of points ingested
        """
        nodes = self.parse_document(text, metadata)
        
        if not nodes:
            logger.warning("no_nodes_generated", source_id=source_id)
            return 0
        
        from qdrant_client.models import PointStruct
        
        points = []
        for i, node in enumerate(nodes):
            embedding = self.embed_model.get_text_embedding(node.text)
            
            points.append(PointStruct(
                id=str(uuid4()),
                vector=embedding,
                payload={
                    "source_id": source_id,
                    "chunk_index": i,
                    "chunk_text": node.text,
                    "node_id": node.node_id,
                    **(metadata or {}),
                    **node.metadata,
                },
            ))
        
        client.upsert(
            collection_name=collection_name,
            points=points,
        )
        
        logger.info(
            "llamaindex_ingestion_complete",
            source_id=source_id,
            points_count=len(points),
        )
        
        return len(points)
