"""
Tests for PersonalityService.

No mocks needed — purely functional evaluation logic.
"""
from __future__ import annotations

import pytest

from app.models.schemas import PersonalityEvaluationRequest, PersonalityProfile
from app.services.personality_service import PersonalityService

SERVICE = PersonalityService()


def _make_profile(
    traits: list[str] | None = None,
    must_say: list[str] | None = None,
    must_avoid: list[str] | None = None,
) -> PersonalityProfile:
    return PersonalityProfile(
        name="test-agent",
        traits=traits or [],
        must_say=must_say or [],
        must_avoid=must_avoid or [],
    )


def _evaluate(profile: PersonalityProfile, answer: str):
    return SERVICE.evaluate(PersonalityEvaluationRequest(profile=profile, answer=answer))


class TestMustSay:
    def test_passes_when_phrase_present(self) -> None:
        result = _evaluate(_make_profile(must_say=["rollback"]), "The rollback plan is ready.")
        assert "missing required phrase: rollback" not in result.findings

    def test_penalises_missing_phrase(self) -> None:
        result = _evaluate(_make_profile(must_say=["rollback"]), "The plan is ready.")
        assert any("missing required phrase" in finding for finding in result.findings)
        assert result.score < 1.0


class TestMustAvoid:
    def test_passes_when_phrase_absent(self) -> None:
        result = _evaluate(_make_profile(must_avoid=["trust me"]), "The rollback plan is ready.")
        assert not any("forbidden phrase" in finding for finding in result.findings)

    def test_penalises_forbidden_phrase(self) -> None:
        result = _evaluate(_make_profile(must_avoid=["trust me"]), "rollback plan ready, trust me")
        assert not result.passed
        assert any("forbidden phrase present: trust me" in finding for finding in result.findings)


class TestScoreClamp:
    def test_score_never_below_zero(self) -> None:
        """Many violations should not produce a negative score."""
        profile = _make_profile(
            must_say=["a", "b", "c", "d", "e"],
            must_avoid=["bad1", "bad2", "bad3"],
        )
        result = _evaluate(profile, "bad1 bad2 bad3")
        assert result.score >= 0.0

    def test_score_never_above_one(self) -> None:
        result = _evaluate(_make_profile(), "any answer")
        assert result.score <= 1.0


class TestPassThreshold:
    def test_passes_at_75_percent(self) -> None:
        # With no constraints, score is 1.0 → passes.
        result = _evaluate(_make_profile(), "great answer")
        assert result.passed

    def test_fails_below_threshold(self) -> None:
        # Missing 2 must_say (−0.4) + 1 must_avoid present (−0.3) = 0.3 → fails.
        profile = _make_profile(must_say=["alpha", "beta"], must_avoid=["gamma"])
        result = _evaluate(profile, "gamma is here")
        assert not result.passed
