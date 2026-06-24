import math

from harnesslab.optimize import optimize


def sphere(x):
    return sum(xi * xi for xi in x)


def test_minimizes_sphere():
    res = optimize(sphere, x0=[5.0, -4.0, 3.0], budget=2000, seed=1)
    assert res.fx < 1e-3  # converges near the global minimum at the origin
    assert all(abs(xi) < 0.1 for xi in res.x)


def test_respects_bounds():
    # global min at 0 is outside the box; best feasible point sits on the bound.
    res = optimize(sphere, x0=[5.0], bounds=[(2.0, 6.0)], budget=500, seed=0)
    assert 2.0 <= res.x[0] <= 6.0
    assert abs(res.x[0] - 2.0) < 0.05


def test_deterministic_for_fixed_seed():
    a = optimize(sphere, x0=[3.0, 3.0], budget=300, seed=7)
    b = optimize(sphere, x0=[3.0, 3.0], budget=300, seed=7)
    assert a.x == b.x and a.fx == b.fx


def test_target_early_stop():
    res = optimize(sphere, x0=[10.0, 10.0], budget=100000, target=1.0, seed=0)
    assert res.fx <= 1.0
    assert res.evals < 100000  # stopped as soon as the target was hit
