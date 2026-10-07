"""Text normalisation: cleaning, UK trade abbreviations, singularising, noise words."""

from __future__ import annotations

import pytest

from components.matching.text import TextNormaliser, clean_text, singularise

ABBREVIATIONS = {
    "p/board": "plasterboard",
    "pboard": "plasterboard",
    "te": "tapered edge",
    "se": "square edge",
    "mr": "moisture resistant",
    "t&g": "tongue and groove",
    "pse": "planed square edge",
    "par": "planed all round",
    "w/c": "wc",
}
NOISE = {"the", "and", "for", "please", "supply", "of", "with", "a"}


@pytest.fixture()
def norm() -> TextNormaliser:
    return TextNormaliser(ABBREVIATIONS, NOISE)


def test_clean_text_lowercases_and_folds_symbols() -> None:
    assert clean_text("  2400 × 1200 MM  ") == "2400 x 1200 mm"
    assert clean_text("7 m² of Board") == "7 m2 of board"
    assert clean_text("12.5mm​ board") == "12.5mm board"  # zero-width space removed
    assert clean_text("a\tb\nc") == "a b c"


def test_clean_text_neutralises_html_and_links() -> None:
    cleaned = clean_text("<b>board</b> see http://evil.example/x")
    assert "<" not in cleaned and "http" not in cleaned


def test_clean_text_turns_plumbing_fractions_into_words() -> None:
    assert "half inch" in clean_text('15mm x 1/2" x 300mm tap connector')
    assert "three quarter inch" in clean_text("3/4 inch valve")
    assert "1/2" not in clean_text("tap tail 1/2in")


@pytest.mark.parametrize(
    ("word", "expected"),
    [
        ("boards", "board"), ("valves", "valve"), ("tiles", "tile"), ("boxes", "box"),
        ("fittings", "fitting"), ("glass", "glass"), ("cls", "cls"), ("gas", "gas"),
        ("brass", "brass"), ("plus", "plus"), ("c16", "c16"), ("12.5mm", "12.5mm"),
        ("switches", "switch"), ("tees", "tee"), ("is", "is"),
    ],
)
def test_singularise(word: str, expected: str) -> None:
    assert singularise(word) == expected


def test_abbreviations_expand_to_words(norm: TextNormaliser) -> None:
    assert norm.tokens("P/Board") == ("plasterboard",)
    assert norm.tokens("MR p/boards TE") == ("moisture", "resistant", "plasterboard", "tapered",
                                              "edge")
    assert norm.tokens("T&G flooring") == ("tongue", "and", "groove", "flooring")
    assert norm.tokens("38x63 CLS PSE") == ("38x63", "cls", "planed", "square", "edge")
    assert norm.tokens("W/C pan") == ("wc", "pan")


def test_hyphens_and_possessives_split(norm: TextNormaliser) -> None:
    assert norm.tokens("click-clack waste") == ("click", "clack", "waste")
    assert norm.tokens("basin's tap") == ("basin", "tap")
    assert norm.tokens("push-fit") == ("push", "fit")


def test_punctuation_and_stray_multiplication_signs_drop(norm: TextNormaliser) -> None:
    assert norm.tokens("board, x tapered; (white)") == ("board", "tapered", "white")


def test_content_tokens_drop_noise_but_phrases_keep_everything(norm: TextNormaliser) -> None:
    text = "Please supply the MR board for a bathroom"
    assert norm.tokens(text)[:2] == ("please", "supply")
    assert norm.content_tokens(text) == ("moisture", "resistant", "board", "bathroom")


def test_phrase_normalisation_is_what_synonym_matching_uses(norm: TextNormaliser) -> None:
    assert norm.tokens("planed all round") == norm.tokens("PAR")


def test_a_single_letter_word_is_kept_so_s_trap_differs_from_trap(norm: TextNormaliser) -> None:
    assert norm.tokens("S trap") == ("s", "trap")
