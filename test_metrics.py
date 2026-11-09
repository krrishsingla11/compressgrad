"""Offline checks for scoring and statistics. Run: python -m pytest test_metrics.py"""
from metrics import abstains, exact_match, f1_score, normalize, sign_test


def test_normalize_drops_case_punctuation_and_articles():
    assert normalize("The Royal Air Force.") == "royal air force"


def test_exact_match():
    assert exact_match("Dutch.", "dutch") == 1.0
    assert exact_match("Dutch heritage", "Dutch") == 0.0


def test_f1_partial_credit():
    assert f1_score("Salma Hayek", "Salma Hayek Pinault") == 0.8
    assert f1_score("Paris", "London") == 0.0
    assert f1_score("", "") == 1.0


def test_f1_handles_unusual_spaces():
    assert f1_score("Rudolf Hoss", "Rudolf Hoss") == 1.0


def test_abstains():
    assert abstains("Not stated in the context")
    assert not abstains("1998")


def test_sign_test():
    assert sign_test(0, 0) == 1.0
    assert sign_test(3, 3) == 1.0
    assert abs(sign_test(12, 2) - 0.0129) < 1e-3   # exact binomial, n=14
