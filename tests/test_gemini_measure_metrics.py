"""SPEC-25 R2, R3, R4, R6, R8: metric functions, refusal rates, failure labels and the review sample.

Every number here was worked out by hand on a made-up ranking.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import measure_lib as ml  # noqa: E402

PREFIX = "a/"
EXPECT = ["a/x", "a/y"]
# a/z no, a/x yes, b/x wrong prefix, a/y yes, a/q no
RANKING = ["a/z", "a/x", "b/x", "a/y", "a/q"]
FLAGS = [False, True, False, True, False]


def test_is_right_needs_prefix_and_a_piece():
    assert ml.is_right("a/x/page", PREFIX, EXPECT)
    assert not ml.is_right("b/x", PREFIX, EXPECT)  # piece matches, prefix does not
    assert not ml.is_right("a/q", PREFIX, EXPECT)  # prefix matches, no piece


def test_flags_follow_the_ranking_and_are_padded_to_k():
    assert ml.flags_for(RANKING, PREFIX, EXPECT) == FLAGS
    assert ml.flags_for(["a/x"], PREFIX, EXPECT, k=5) == [True, False, False, False, False]
    assert ml.flags_for([], PREFIX, EXPECT, k=5) == [False] * 5


def test_hit_at_k():
    assert [ml.hit_at_k(FLAGS, k) for k in (1, 3, 5)] == [0, 1, 1]


def test_mrr_is_one_over_first_match_and_zero_when_none():
    assert ml.reciprocal_rank(FLAGS) == 0.5
    assert ml.reciprocal_rank([False] * 5) == 0.0
    assert ml.reciprocal_rank([True, False, False, False, False]) == 1.0


def test_ndcg_hand_computed_two_relevant_files():
    # DCG@3 = 1/log2(3); ideal@3 = 1 + 1/log2(3)
    assert ml.ndcg_at_k(FLAGS, 3, n_relevant=2) == pytest.approx(0.630930 / 1.630930, abs=1e-5)
    # DCG@5 = 1/log2(3) + 1/log2(5); ideal@5 = same ideal (only two relevant files exist)
    assert ml.ndcg_at_k(FLAGS, 5, n_relevant=2) == pytest.approx(1.061607 / 1.630930, abs=1e-5)
    assert ml.ndcg_at_k(FLAGS, 1, n_relevant=2) == 0.0


def test_ndcg_is_one_for_a_perfect_ranking_and_zero_with_no_relevant_file():
    assert ml.ndcg_at_k([True, True, False, False, False], 3, n_relevant=2) == pytest.approx(1.0)
    assert ml.ndcg_at_k([True, False, False, False, False], 5, n_relevant=1) == pytest.approx(1.0)
    assert ml.ndcg_at_k([False] * 5, 5, n_relevant=3) == 0.0
    assert ml.ndcg_at_k([True] * 5, 5, n_relevant=0) == 0.0


def test_ndcg_ideal_is_capped_at_k():
    # 10 relevant files exist, K = 3: ideal is three hits in a row
    ideal = 1 + 1 / math.log2(3) + 1 / math.log2(4)
    assert ml.ndcg_at_k([False, True, False, False, False], 3, n_relevant=10) == pytest.approx(
        (1 / math.log2(3)) / ideal
    )


def test_precision_at_k_counts_matches_over_k():
    assert ml.precision_at_k(FLAGS, 3) == pytest.approx(1 / 3)
    assert ml.precision_at_k(FLAGS, 5) == pytest.approx(2 / 5)
    assert ml.precision_at_k(FLAGS, 1) == 0.0


def test_dedupe_files_keeps_first_appearance():
    assert ml.dedupe_files(["a/x", "a/x", "a/y", "a/x", "b/z"]) == ["a/x", "a/y", "b/z"]
    assert ml.dedupe_files([]) == []


def _row(set_name, kind, flags, expect_n, n_rel):
    return {"set": set_name, "kind": kind, "flags": flags, "n_expect": expect_n, "n_relevant": n_rel}


def test_aggregate_overall_by_kind_and_by_set_with_p_at_k_only_for_multi_expect():
    rows = [
        _row("s1", "plain", [True, False, False, False, False], 1, 1),  # hit@1
        _row("s1", "error", [False, True, False, False, False], 1, 1),  # hit@3
        _row("s2", "plain", [False, False, False, False, False], 2, 2),  # miss
        _row("s2", "plain", FLAGS, 2, 2),  # multi-expect, hit@3
    ]
    out = ml.aggregate(rows)
    overall = out["overall"]
    assert overall["n"] == 4
    assert overall["hit@1"] == pytest.approx(1 / 4)
    assert overall["hit@3"] == pytest.approx(3 / 4)
    assert overall["hit@5"] == pytest.approx(3 / 4)
    assert overall["mrr"] == pytest.approx((1 + 0.5 + 0 + 0.5) / 4)
    # P@K averages only the two multi-expect questions: (0 + 1/3) / 2 at K=3
    assert overall["p@3"] == pytest.approx((0 + 1 / 3) / 2)
    assert out["by_kind"]["plain"]["n"] == 3
    assert out["by_kind"]["error"]["hit@3"] == 1.0
    assert out["by_set"]["s1"]["n"] == 2
    assert out["by_set"]["s2"]["hit@3"] == pytest.approx(1 / 2)
    assert out["by_set"]["s1"]["p@3"] is None  # no multi-expect question in s1


def test_aggregate_of_nothing_is_empty_not_a_crash():
    out = ml.aggregate([])
    assert out["overall"]["n"] == 0
    assert out["overall"]["hit@3"] is None


def test_refusal_rates():
    answerable = ["ok", "not_found", "ok", "ok", "not_found"]  # 2 of 5 wrongly refused
    out_of_scope = ["not_found", "not_found", "ok", "not_found"]  # 3 of 4 correctly refused
    r = ml.refusal_rates(answerable, out_of_scope)
    assert r["false_refusal"] == pytest.approx(2 / 5)
    assert r["correct_refusal"] == pytest.approx(3 / 4)
    assert r["answerable_n"] == 5 and r["out_of_scope_n"] == 4
    assert ml.refusal_rates([], [])["false_refusal"] is None


# --- R6: failure labels, one made-up case per label ---------------------------------------------------

LONG = (
    "the venv module creates isolated environments with their own interpreter and site packages "
    "so that each project keeps its own dependencies "
) * 3


def test_label_wording_when_fewer_than_half_the_terms_are_in_the_best_passage():
    terms = ["alpha", "beta", "gamma", "delta"]
    best = LONG + " alpha"  # 1 of 4 terms present
    assert ml.classify_miss(terms, best, ["a/q"], ["a/x"], ["a/x"], PREFIX) == "wording"


def test_label_wording_when_the_expected_file_has_no_passage_at_all():
    assert ml.classify_miss(["alpha"], "", ["a/q"], ["a/x"], ["a/x"], PREFIX) == "wording"


def test_exactly_half_the_terms_is_not_wording():
    terms = ["venv", "module", "zzz", "yyy"]  # 2 of 4 present = half, not fewer than half
    assert ml.classify_miss(terms, LONG, ["a/q"], ["a/x"], ["a/x"], PREFIX) != "wording"


def test_label_vague_chunk_short_passage():
    assert ml.classify_miss(["venv", "module"], "venv module", ["a/q"], ["a/x"], ["a/x"], PREFIX) == "vague chunk"


def test_label_vague_chunk_heading_only():
    heading_only = "\n".join(["# The venv module"] + ["## venv module"] * 20)
    assert len(heading_only) >= 200
    assert ml.classify_miss(["venv", "module"], heading_only, ["a/q"], ["a/x"], ["a/x"], PREFIX) == "vague chunk"


def test_a_heading_followed_by_body_text_is_not_heading_only():
    text = "# The venv module\n" + LONG
    assert ml.classify_miss(["venv", "module"], text, ["b/q"], ["a/x"], ["a/x"], PREFIX) == "other"


def test_label_vague_chunk_too_few_content_terms():
    text = "venv " * 80  # long, but one distinct content word
    assert ml.classify_miss(["venv"], text, ["a/q"], ["a/x"], ["a/x"], PREFIX) == "vague chunk"


def test_label_multi_page_first_result_is_a_sibling():
    # a/dir/one is a sibling of the expected a/dir/two (same directory)
    got = ml.classify_miss(["venv", "module"], LONG, ["a/dir/one", "a/q"], ["a/dir/two"], ["a/dir/two"], PREFIX)
    assert got == "multi-page"


def test_label_multi_page_another_expected_piece_matches_below_the_top_3():
    returned = ["a/q", "a/r", "a/s", "a/y", "a/t"]  # a/y (second piece) at rank 4
    got = ml.classify_miss(["venv", "module"], LONG, returned, ["a/x", "a/y"], ["a/x", "a/y"], PREFIX)
    assert got == "multi-page"


def test_label_other():
    assert ml.classify_miss(["venv", "module"], LONG, ["b/q", "c/r"], ["a/x"], ["a/x"], PREFIX) == "other"


def test_wording_wins_over_later_labels_fixed_order():
    # short passage AND sibling first: the first test in the order (wording) decides
    got = ml.classify_miss(["alpha", "beta"], "x", ["a/d/one"], ["a/d/two"], ["a/d/two"], PREFIX)
    assert got == "wording"


# --- R8: review sample ---------------------------------------------------------------------------------


def _fake_sets():
    sets = {}
    for name in ("s1", "s2", "s3"):
        qs = [
            {"q": f"{name} {kind} {i}", "kind": kind, "expect": [f"{name}/p{i}"]}
            for kind in ("plain", "error", "paraphrase", "pasted")
            for i in range(10)
        ]
        sets[name] = {"prefix": f"{name}/", "questions": qs, "out_of_scope": []}
    return sets


def test_review_sample_is_four_per_set_one_per_kind_and_fixed_by_seed():
    a = ml.review_sample(_fake_sets(), seed=25)
    b = ml.review_sample(_fake_sets(), seed=25)
    c = ml.review_sample(_fake_sets(), seed=26)
    assert a == b
    assert a != c
    assert len(a) == 12
    for name in ("s1", "s2", "s3"):
        kinds = [item["kind"] for item in a if item["set"] == name]
        assert kinds == ["plain", "error", "paraphrase", "pasted"]
