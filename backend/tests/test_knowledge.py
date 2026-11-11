"""Tests for knowledge module."""
import pytest

from app.knowledge.chunker import SemanticChunker


class TestSemanticChunker:
    """Tests for SemanticChunker."""
    
    def test_chunk_simple_text(self):
        """Chunk simple text."""
        chunker = SemanticChunker(chunk_size=20, chunk_overlap=5)
        text = "This is a test sentence. Another sentence here. And one more."
        
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) >= 1
        assert all(chunk.text for chunk in chunks)
    
    def test_chunk_empty_text(self):
        """Handle empty text."""
        chunker = SemanticChunker()
        chunks = chunker.chunk_text("")
        
        assert chunks == []
    
    def test_chunk_whitespace_only(self):
        """Handle whitespace-only text."""
        chunker = SemanticChunker()
        chunks = chunker.chunk_text("   \n\n   ")
        
        assert chunks == []
    
    def test_chunk_paragraphs(self):
        """Chunk multiple paragraphs."""
        chunker = SemanticChunker(chunk_size=50, chunk_overlap=10)
        text = """First paragraph with some content here.

Second paragraph with different content.

Third paragraph to make it longer."""
        
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.index >= 0
            assert chunk.word_count > 0
    
    def test_chunk_indices_sequential(self):
        """Chunk indices are sequential."""
        chunker = SemanticChunker(chunk_size=10, chunk_overlap=2)
        text = "One. Two. Three. Four. Five. Six. Seven. Eight. Nine. Ten."
        
        chunks = chunker.chunk_text(text)
        
        for i, chunk in enumerate(chunks):
            assert chunk.index == i
    
    def test_large_text_chunking(self):
        """Handle larger text."""
        chunker = SemanticChunker(chunk_size=100, chunk_overlap=20)
        text = " ".join(["This is sentence number {}.".format(i) for i in range(100)])
        
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.word_count <= 150


class TestEmbeddingService:
    """Tests for EmbeddingService.
    
    These tests require sentence-transformers to be installed.
    """
    
    @pytest.fixture
    def embedding_service(self):
        """Create embedding service instance."""
        from app.knowledge.embeddings import EmbeddingService
        return EmbeddingService()
    
    def test_embed_single_text(self, embedding_service):
        """Embed a single text."""
        embedding = embedding_service.embed_text("Test sentence for embedding.")
        
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
    
    def test_embed_multiple_texts(self, embedding_service):
        """Embed multiple texts."""
        texts = [
            "First text to embed.",
            "Second text to embed.",
            "Third text to embed.",
        ]
        
        embeddings = embedding_service.embed_texts(texts)
        
        assert len(embeddings) == 3
        for emb in embeddings:
            assert len(emb) == 384
    
    def test_embed_empty_list(self, embedding_service):
        """Handle empty list."""
        embeddings = embedding_service.embed_texts([])
        
        assert embeddings == []
    
    def test_embed_query(self, embedding_service):
        """Embed a search query."""
        embedding = embedding_service.embed_query("What is cholesterol?")
        
        assert len(embedding) == 384
    
    def test_embeddings_normalized(self, embedding_service):
        """Embeddings should be normalized."""
        import math
        
        embedding = embedding_service.embed_text("Test normalization.")
        
        magnitude = math.sqrt(sum(x*x for x in embedding))
        assert abs(magnitude - 1.0) < 0.01
