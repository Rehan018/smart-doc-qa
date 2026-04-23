from typing import List


class Chunk:
    def __init__(self, text: str, chunk_index: int):
        self.text = text
        self.chunk_index = chunk_index


class ChunkingService:
    def __init__(self, chunk_size: int = 1200, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str) -> List[Chunk]:
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

        chunks = []
        current_chunk = ""
        chunk_index = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) <= self.chunk_size:
                current_chunk += " " + para
            else:
                chunks.append(
                    Chunk(
                        text=current_chunk.strip(),
                        chunk_index=chunk_index
                    )
                )
                chunk_index += 1

                # overlap logic
                overlap_text = current_chunk[-self.overlap:] if len(current_chunk) > self.overlap else current_chunk
                current_chunk = overlap_text + " " + para

        if current_chunk.strip():
            chunks.append(
                Chunk(
                    text=current_chunk.strip(),
                    chunk_index=chunk_index
                )
            )

        return chunks

class TetChunk:
    def __init__(self, text: str, chunk_index: int):
        self.text = text
        self.chunk_index = chunk_index