from app.services.chunking_service import ChunkingService


def test_chunking_generates_chunks_with_overlap():
    text = "\n".join(
        [
            "Employees are entitled to casual leave.",
            "Sick leave is available for medical reasons.",
            "Maternity leave is available as per policy.",
            "Remote work may be approved by the manager.",
        ]
    )

    service = ChunkingService(chunk_size=80, overlap=20)
    chunks = service.chunk_text(text)

    assert len(chunks) > 1
    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1
    assert all(chunk.text for chunk in chunks)
