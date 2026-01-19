"""
Text chunking logic for breaking pages into smaller pieces.
"""

import re
from typing import List


class Chunker:
    """Handles text chunking for RAG."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        Initialize chunker.

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        if not text:
            return []

        # Clean text
        text = self._clean_text(text)

        # If text is shorter than chunk size, return as single chunk
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # If we're not at the end, try to break at a sentence boundary
            if end < len(text):
                # Look for sentence endings within the last 20% of the chunk
                search_start = max(start, end - int(self.chunk_size * 0.2))
                sentence_end = self._find_sentence_end(text, search_start, end)

                if sentence_end > start:
                    end = sentence_end + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = end - self.chunk_overlap
            if start >= len(text):
                break

        return chunks

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text

    def _find_sentence_end(self, text: str, start: int, end: int) -> int:
        """Find the last sentence ending before end position."""
        # Look for sentence endings: . ! ? followed by space or newline
        pattern = r"[.!?][\s\n]"
        matches = list(re.finditer(pattern, text[start:end]))
        if matches:
            return start + matches[-1].start()
        return end
