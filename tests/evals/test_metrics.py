import pytest
from evals.metrics import (
    critical_mismatch_upper_bound,
    mcnemar_exact,
    required_n_for_wilson_bound,
    required_n_for_zero_error_bound,
    wilson_interval,
    zero_error_upper_bound,
)


def test_wilson_38_of_40():
    lo, hi = wilson_interval(38, 40)
    assert lo == pytest.approx(0.835, abs=0.001)
    assert hi == pytest.approx(0.986, abs=0.001)


def test_wilson_edges():
    assert wilson_interval(0, 0) == (0.0, 1.0)
    lo, hi = wilson_interval(0, 50)
    assert lo == 0.0 and 0.0 < hi < 0.08
    with pytest.raises(ValueError):
        wilson_interval(5, 4)


def test_zero_error_bounds_match_spec():
    assert required_n_for_zero_error_bound(0.05) == 59
    assert zero_error_upper_bound(59) == pytest.approx(0.0495, abs=0.0001)
    assert zero_error_upper_bound(298) == pytest.approx(0.0100, abs=0.0001)
    assert required_n_for_zero_error_bound(0.01) in (298, 299)


def test_critical_mismatch_bound_is_wilson_upper():
    assert critical_mismatch_upper_bound(0, 298) == wilson_interval(0, 298)[1]
    assert critical_mismatch_upper_bound(0, 0) == 1.0
    assert critical_mismatch_upper_bound(0, 188) > 0.02 >= critical_mismatch_upper_bound(0, 189)


def test_required_n_for_wilson_bound_is_the_smallest_passing_sample():
    # zero errors need 189 items for a Wilson 95% upper bound of 2%; one error 280; two 361
    assert required_n_for_wilson_bound(0.02) == 189
    assert required_n_for_wilson_bound(0.02, errors=1) == 280
    assert required_n_for_wilson_bound(0.02, errors=2) == 361
    for errors in (0, 1, 2):
        n = required_n_for_wilson_bound(0.02, errors=errors)
        assert critical_mismatch_upper_bound(errors, n) <= 0.02
        assert critical_mismatch_upper_bound(errors, n - 1) > 0.02
    with pytest.raises(ValueError):
        required_n_for_wilson_bound(0.0)
    with pytest.raises(ValueError):
        required_n_for_wilson_bound(0.02, errors=-1)


def test_mcnemar_exact():
    assert mcnemar_exact(0, 0) == 1.0
    assert mcnemar_exact(5, 5) == 1.0
    assert mcnemar_exact(0, 10) == pytest.approx(2 / 1024)
    assert mcnemar_exact(3, 9) == pytest.approx(0.146, abs=0.001)
    assert mcnemar_exact(9, 3) == mcnemar_exact(3, 9)
