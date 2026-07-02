"""memory._chunk_document — paragraph merge, sentence split, boundary sizes."""

from backend.pipeline.memory import _chunk_document


def _words(n: int, word: str = "w") -> str:
    return " ".join([word] * n)


def test_small_paragraphs_merge_into_one_chunk():
    text = f"{_words(100)}\n\n{_words(100)}"
    chunks = _chunk_document(text, max_tokens=500)
    assert len(chunks) == 1
    assert chunks[0] == f"{_words(100)}\n\n{_words(100)}"


def test_budget_flush_starts_a_new_chunk():
    text = f"{_words(300)}\n\n{_words(300)}"
    chunks = _chunk_document(text, max_tokens=500)
    assert len(chunks) == 2
    assert [len(c.split()) for c in chunks] == [300, 300]


def test_merge_landing_exactly_on_budget_is_allowed():
    # The flush check is strictly `>`, so 250 + 250 == 500 stays together.
    text = f"{_words(250)}\n\n{_words(250)}"
    chunks = _chunk_document(text, max_tokens=500)
    assert len(chunks) == 1


def test_oversized_paragraph_splits_at_sentence_boundaries():
    sentence = _words(200) + "."
    para = " ".join([sentence] * 3)  # 600+ words, three sentences
    chunks = _chunk_document(para, max_tokens=500)
    assert len(chunks) == 2
    # Sentence-level chunks are joined with spaces, not paragraph breaks.
    assert "\n\n" not in chunks[0]
    assert all(len(c.split()) <= 500 + 201 for c in chunks)


def test_single_sentence_longer_than_budget_stays_whole():
    sentence = _words(700) + "."
    chunks = _chunk_document(sentence, max_tokens=500)
    assert len(chunks) == 1
    assert len(chunks[0].split()) == 700


def test_empty_and_whitespace_input():
    assert _chunk_document("") == []
    assert _chunk_document("\n\n  \n\n") == []
