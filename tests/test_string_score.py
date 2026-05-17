from __future__ import annotations

from marker.string_score import score


def test_exact_match():
    assert score("hello world", "hello world") == 1.0


def test_empty_abbreviation():
    assert score("hello world", "") == 1.0


def test_nonexistent_char():
    assert score("hello world", "ax1") == 0.0


def test_sequential_requirement():
    assert score("Hello world", "WH") == 0.0
    assert score("Hello world", "HW") > 0.0


def test_case_bonus():
    assert score("Hello world", "Hello") > score("Hello world", "hello")


def test_consecutive_bonus():
    assert score("Hello World", "Hel") > score("Hello World", "Hld")


def test_acronym_bonus():
    assert score("Hello World", "HW") > score("Hello World", "ho")


def test_start_of_string_bonus():
    assert score("Hillsdale", "hi") > score("Chippewa", "hi")


def test_progressive_prefix():
    base = score("hello world", "h")
    for prefix in ("he", "hel", "hell", "hello"):
        s = score("hello world", prefix)
        assert s >= base, f"score({prefix!r}) should increase"
        base = s
