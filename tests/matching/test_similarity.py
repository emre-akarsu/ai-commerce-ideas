"""Pure-Python string similarity and the deterministic offline embedder."""

from __future__ import annotations

import math
import os
import subprocess
import sys
from pathlib import Path

import pytest

from components.matching.embedding import Embedder, HashingEmbedder, cosine
from components.matching.similarity import (
    jaro,
    jaro_winkler,
    levenshtein,
    levenshtein_similarity,
    token_set_ratio,
    trigram_cosine,
    trigrams,
)


def test_levenshtein_known_distances() -> None:
    assert levenshtein("kitten", "sitting") == 3
    assert levenshtein("", "abc") == 3
    assert levenshtein("abc", "") == 3
    assert levenshtein("same", "same") == 0
    assert levenshtein("12.5mm", "15mm") == 2


def test_levenshtein_similarity_is_normalised() -> None:
    assert levenshtein_similarity("abc", "abc") == 1.0
    assert levenshtein_similarity("", "") == 1.0
    assert levenshtein_similarity("abc", "xyz") == 0.0
    assert levenshtein_similarity("kitten", "sitting") == pytest.approx(1 - 3 / 7)


def test_jaro_and_jaro_winkler_reference_values() -> None:
    assert jaro("martha", "marhta") == pytest.approx(0.9444, abs=1e-4)
    assert jaro_winkler("martha", "marhta") == pytest.approx(0.9611, abs=1e-4)
    assert jaro_winkler("dixon", "dicksonx") == pytest.approx(0.8133, abs=1e-4)
    assert jaro_winkler("abc", "abc") == 1.0
    assert jaro_winkler("abc", "xyz") == 0.0
    assert jaro_winkler("", "") == 1.0
    assert jaro_winkler("a", "") == 0.0


def test_token_set_ratio_ignores_order_and_duplicates() -> None:
    a = "moisture resistant plasterboard 12.5mm"
    b = "12.5mm plasterboard moisture resistant moisture"
    assert token_set_ratio(a, b) == 1.0


def test_token_set_ratio_subset_scores_one_and_disjoint_scores_low() -> None:
    assert token_set_ratio("plasterboard 12.5mm", "synth mr plasterboard 12.5mm 2400x1200") == 1.0
    assert token_set_ratio("plasterboard", "copper pipe") < 0.5
    assert token_set_ratio("", "copper") == 0.0


def test_token_set_ratio_separates_a_one_token_difference() -> None:
    same = token_set_ratio("plasterboard 12.5mm tapered", "plasterboard 12.5mm tapered")
    near = token_set_ratio("plasterboard 12.5mm tapered", "plasterboard 15mm tapered")
    assert same == 1.0
    assert 0.5 < near < same


def test_trigrams_pad_and_count() -> None:
    assert trigrams("ab") == {"  a": 1, " ab": 1, "ab ": 1}
    # pg_trgm style: two leading spaces and one trailing space per word -> n + 1 trigrams
    assert sum(trigrams("plasterboard").values()) == len("plasterboard") + 1
    assert sum(trigrams("a bc").values()) == 2 + 3  # each word is padded on its own


def test_trigram_cosine_properties() -> None:
    assert trigram_cosine("plasterboard", "plasterboard") == pytest.approx(1.0)
    assert trigram_cosine("plasterboard", "") == 0.0
    assert trigram_cosine("aaa", "zzz") == 0.0
    a, b = "moisture resistant board", "moisture board"
    assert trigram_cosine(a, b) == pytest.approx(trigram_cosine(b, a))
    assert 0.0 < trigram_cosine(a, b) < 1.0


# --------------------------------------------------------------------------- embedder


def test_hashing_embedder_is_deterministic_and_unit_length() -> None:
    e1, e2 = HashingEmbedder(dim=64), HashingEmbedder(dim=64)
    v1, v2 = e1.embed("12.5mm moisture resistant plasterboard"), e2.embed(
        "12.5mm moisture resistant plasterboard"
    )
    assert v1 == v2
    assert len(v1) == 64 == e1.dim
    assert math.sqrt(sum(x * x for x in v1)) == pytest.approx(1.0)


def test_hashing_embedder_golden_vector_guards_the_hash_function() -> None:
    # Changing the hash, the feature set or the weights changes every stored score. If this
    # fails on purpose, regenerate the vector and re-check the eval.
    v = HashingEmbedder(dim=8).embed("plasterboard 12.5mm")
    assert list(v) == pytest.approx(
        [0.175882, -0.175882, 0.175882, -0.854282, 0.0, -0.351763, 0.150756, -0.175882], abs=1e-6
    )
    assert HashingEmbedder(dim=8).embed("") == tuple(0.0 for _ in range(8))


def test_hashing_embedder_is_identical_across_processes_and_hash_seeds() -> None:
    """The built-in hash() is salted per process; zlib.crc32 is not. Run the embedder in two
    fresh interpreters with different PYTHONHASHSEED values and compare with this process."""
    code = (
        "from components.matching.embedding import HashingEmbedder;"
        "print(repr(HashingEmbedder(dim=16).embed('plasterboard 12.5mm tapered 2400x1200')))"
    )
    packages = str(Path(__file__).resolve().parents[2] / "packages")
    outputs = []
    for seed in ("1", "424242"):
        env = {**os.environ, "PYTHONHASHSEED": seed, "PYTHONPATH": packages}
        done = subprocess.run(  # noqa: S603 - fixed interpreter and fixed code string
            [sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True
        )
        outputs.append(done.stdout.strip())
    here = repr(HashingEmbedder(dim=16).embed("plasterboard 12.5mm tapered 2400x1200"))
    assert outputs[0] == outputs[1] == here


def test_hashing_embedder_ranks_similar_text_higher() -> None:
    e = HashingEmbedder()
    q = e.embed("12.5mm moisture resistant plasterboard 2400x1200")
    close = e.embed("moisture resistant plasterboard tapered edge 12.5mm 2400x1200")
    far = e.embed("15mm copper compression elbow")
    assert cosine(q, close) > cosine(q, far) + 0.3
    assert 0.0 <= cosine(q, far) <= 1.0


def test_cosine_handles_zero_vectors() -> None:
    zero = (0.0, 0.0)
    assert cosine(zero, (1.0, 0.0)) == 0.0
    assert cosine((1.0, 0.0), (1.0, 0.0)) == pytest.approx(1.0)


def test_hashing_embedder_satisfies_the_embedder_protocol() -> None:
    assert isinstance(HashingEmbedder(), Embedder)
