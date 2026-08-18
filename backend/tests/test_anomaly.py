import numpy as np
from app.anomaly.detectors import BehavioralBaseline


def test_compute_basic_stats():
    baseline = BehavioralBaseline()
    values = [10, 12, 11, 13, 10, 12, 11, 10, 12, 13]
    stats = baseline.compute_stats(values)
    assert "mean" in stats
    assert "std" in stats
    assert "median" in stats
    assert stats["count"] == 10
    assert 10 <= stats["mean"] <= 13


def test_compute_empty():
    baseline = BehavioralBaseline()
    stats = baseline.compute_stats([])
    assert stats == {}


def test_compute_single_value():
    baseline = BehavioralBaseline()
    stats = baseline.compute_stats([42.0])
    assert stats["mean"] == 42.0
    assert stats["std"] == 0.0
    assert stats["count"] == 1


def test_compute_percentiles():
    baseline = BehavioralBaseline()
    values = list(range(1, 101))
    stats = baseline.compute_stats(values)
    assert abs(stats["p25"] - 25.75) < 0.01
    assert abs(stats["p75"] - 75.25) < 0.01
    assert stats["p95"] >= 94.0


def test_zscore_detection():
    baseline = BehavioralBaseline(min_samples=10, z_threshold=3.0)
    values = [10, 10, 10, 10, 10, 10, 10, 10, 10, 11, 100]
    stats = baseline.compute_stats(values[:-1])
    latest = values[-1]
    z_score = abs(latest - stats["mean"]) / stats["std"]
    assert z_score > 3.0
