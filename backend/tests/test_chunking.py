from app.services.ingestion import chunk_text


def test_document_is_split_into_multiple_chunks():
    text = " ".join(f"w{i}" for i in range(1200))
    chunks = chunk_text(text, chunk_size=500, chunk_overlap=100)
    assert len(chunks) == 3
    assert all(len(c.split()) <= 500 for c in chunks)


def test_overlap_words_are_shared_between_consecutive_chunks():
    text = " ".join(f"w{i}" for i in range(1000))
    chunks = chunk_text(text, chunk_size=500, chunk_overlap=100)
    tail = chunks[0].split()[-100:]
    head = chunks[1].split()[:100]
    assert tail == head


def test_empty_document_yields_no_chunks():
    assert chunk_text("", chunk_size=500, chunk_overlap=100) == []
    assert chunk_text("   \n\t  ", chunk_size=500, chunk_overlap=100) == []


def test_short_document_is_a_single_chunk():
    chunks = chunk_text("only a few words here", chunk_size=500, chunk_overlap=100)
    assert chunks == ["only a few words here"]
