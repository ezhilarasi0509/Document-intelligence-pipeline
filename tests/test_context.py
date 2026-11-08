from docintel.context import build_context, split_paragraphs


def test_short_docs_pass_through():
    assert build_context("short contract text", max_chars=100) == "short contract text"


def test_long_docs_keep_head_and_relevant_paragraphs():
    head = "THIS AGREEMENT between Acme Inc. and Beta LLC dated as of March 1, 2019.\n\n" + "x" * 3600
    filler = "\n\n".join(f"Boilerplate paragraph number {i} about nothing relevant." * 3 for i in range(200))
    key = "This Agreement shall be governed by the laws of the State of Delaware."
    text = head + "\n\n" + filler + "\n\n" + key + "\n\n" + filler
    ctx = build_context(text, max_chars=9000, head_chars=3500)
    assert len(ctx) <= 9000 + 100
    assert "Acme Inc." in ctx
    assert "State of Delaware" in ctx


def test_split_paragraphs_cuts_long_blocks():
    long = ". ".join(f"Sentence {i} is here" for i in range(400))
    parts = split_paragraphs(long, max_len=500)
    assert len(parts) > 3 and all(len(p) <= 520 for _, p in parts)
