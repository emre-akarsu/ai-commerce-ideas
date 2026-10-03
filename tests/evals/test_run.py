import json
from pathlib import Path

from evals.metrics import critical_mismatch_upper_bound
from evals.run import FAIL, INSUFFICIENT_N, PASS, Result, decide_verdict

from components.core.domain import GoldenItem, Tier
from evals import run

GOLDEN = Path(run.__file__).parent / "golden" / "bearings_dev.jsonl"


def test_verdict_logic():
    assert decide_verdict(22, 0) == INSUFFICIENT_N
    assert decide_verdict(150, 0) == INSUFFICIENT_N  # the old minimum: its bound (2.5%) is above 2%
    assert decide_verdict(188, 0) == INSUFFICIENT_N
    assert decide_verdict(22, 1) == FAIL  # any false A/B fails regardless of n
    assert decide_verdict(189, 0) == PASS  # smallest sample whose zero-error bound is <= 2%
    assert decide_verdict(298, 0) == PASS
    assert decide_verdict(298, 3) == FAIL


def test_minimum_sample_is_the_smallest_one_that_can_pass():
    # a minimum below this would let a family reach FAIL by arithmetic alone, with zero errors
    assert critical_mismatch_upper_bound(0, run.MIN_AB_ITEMS) <= run.GATE_BOUND
    assert critical_mismatch_upper_bound(0, run.MIN_AB_ITEMS - 1) > run.GATE_BOUND
    assert run.MIN_AB_ITEMS == 189


def test_golden_dev_set_shape():
    items = run.load_golden(GOLDEN)
    assert len(items) >= 60
    assert all(i.split == "dev" and i.synthetic and i.rationale for i in items)
    assert {t for t in Tier} == {i.expected_tier for i in items}
    assert all(i.critical_mismatch == (i.expected_tier is Tier.D) for i in items)
    for token in ("2RS", "2Z", "C3", "6305"):
        assert any(token in i.candidate_mpn for i in items)


def test_runner_on_dev_set_is_insufficient_n_and_exits_zero(capsys):
    assert run.main([str(GOLDEN)]) == 0
    out = capsys.readouterr().out
    assert "SYNTHETIC SMOKE SET - proves the pipeline, not product accuracy" in out
    assert "VERDICT: INSUFFICIENT_N" in out
    assert "false Tier A/B: 0" in out


def test_engine_agrees_with_every_dev_label():
    wrong = [
        r for r in run.evaluate(run.load_golden(GOLDEN)) if r.predicted is not r.item.expected_tier
    ]
    assert wrong == []


def _item(expected: Tier) -> GoldenItem:
    return GoldenItem(
        id="x", family="deep_groove_ball_bearing", split="dev", request_text="t",
        candidate_mpn="m", expected_tier=expected, critical_mismatch=expected is Tier.D,
    )  # fmt: skip


def test_false_ab_definition():
    assert Result(_item(Tier.D), Tier.B, ()).false_ab
    assert Result(_item(Tier.C), Tier.A, ()).false_ab
    assert not Result(_item(Tier.A), Tier.B, ()).false_ab  # under-claim is not a release blocker
    assert not Result(_item(Tier.B), Tier.D, ()).false_ab


def test_injected_false_tier_b_fails_and_lists_it(tmp_path, capsys):
    row = {
        "id": "bad-1", "family": "deep_groove_ball_bearing", "split": "dev",
        "request_text": "Need bearing 6205-2RS/CN", "candidate_mpn": "BT6205-2RSH",
        "expected_tier": "D", "critical_mismatch": True, "synthetic": True, "rationale": "wrong",
    }  # fmt: skip
    p = tmp_path / "x_dev.jsonl"
    p.write_text(json.dumps(row) + "\n")
    assert run.main([str(p)]) == 1
    out = capsys.readouterr().out
    assert "FALSE A/B bad-1" in out and "VERDICT: FAIL" in out


def test_runner_refuses_non_dev_split(tmp_path, capsys):
    row = json.loads(GOLDEN.read_text().splitlines()[0]) | {"split": "sealed"}
    p = tmp_path / "s.jsonl"
    p.write_text(json.dumps(row) + "\n")
    assert run.main([str(p)]) == 2
