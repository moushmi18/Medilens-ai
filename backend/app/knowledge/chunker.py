"""Semantic chunking for knowledge base content.

Chunks text into semantically coherent pieces for embedding.
"""
import re
from dataclasses import dataclass
from typing import List

from app.core.logging import get_logger

logger = get_logger(__name__)

DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 64


@dataclass
class Chunk:
    """A text chunk with metadata."""
    text: str
    index: int
    start_char: int
    end_char: int
    
    @property
    def word_count(self) -> int:
        return len(self.text.split())


class SemanticChunker:
    """Chunks text into semantic units."""
    
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str) -> List[Chunk]:
        """Split text into semantic chunks.
        
        Strategy:
        1. Split by paragraph boundaries
        2. Combine small paragraphs
        3. Split large paragraphs by sentences
        4. Ensure overlap between chunks
        
        Args:
            text: Text to chunk
            
        Returns:
            List of Chunk objects
        """
        if not text or not text.strip():
            return []
        
        paragraphs = self._split_paragraphs(text)
        sentences = self._paragraphs_to_sentences(paragraphs)
        chunks = self._sentences_to_chunks(sentences)
        
        logger.debug(
            "text_chunked",
            input_chars=len(text),
            num_chunks=len(chunks),
        )
        
        return chunks
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _paragraphs_to_sentences(self, paragraphs: List[str]) -> List[str]:
        """Split paragraphs into sentences."""
        sentences = []
        for para in paragraphs:
            para_sentences = re.split(r'(?<=[.!?])\s+', para)
            for sent in para_sentences:
                sent = sent.strip()
                if sent:
                    sentences.append(sent)
        return sentences
    
    def _sentences_to_chunks(self, sentences: List[str]) -> List[Chunk]:
        """Combine sentences into chunks of target size."""
        if not sentences:
            return []
        
        chunks = []
        current_chunk = []
        current_size = 0
        current_start = 0
        char_pos = 0
        
        for sentence in sentences:
            sentence_size = len(sentence.split())
            
            if current_size + sentence_size > self.chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append(Chunk(
                    text=chunk_text,
                    index=len(chunks),
                    start_char=current_start,
                    end_char=current_start + len(chunk_text),
                ))
                
                overlap_words = self._get_overlap_words(current_chunk)
                current_chunk = overlap_words
                current_size = len(' '.join(overlap_words).split())
                current_start = char_pos - len(' '.join(overlap_words))
            
            current_chunk.append(sentence)
            current_size += sentence_size
            char_pos += len(sentence) + 1
        
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(Chunk(
                text=chunk_text,
                index=len(chunks),
                start_char=current_start,
                end_char=current_start + len(chunk_text),
            ))
        
        return chunks
    
    def _get_overlap_words(self, sentences: List[str]) -> List[str]:
        """Get overlap sentences from the end of current chunk."""
        if not sentences:
            return []
        
        all_words = ' '.join(sentences).split()
        if len(all_words) <= self.chunk_overlap:
            return sentences[-1:]
        
        overlap_text = ' '.join(all_words[-self.chunk_overlap:])
        last_sentence = sentences[-1]
        if len(last_sentence.split()) <= self.chunk_overlap:
            return [last_sentence]
        
        words_in_last = last_sentence.split()
        overlap_words = words_in_last[-self.chunk_overlap:]
        return [' '.join(overlap_words)]
