from __future__ import annotations

from app.models.schemas import PersonalityEvaluationRequest, PersonalityProfile
from app.services.personality_service import PersonalityService


def test_personality_flags_forbidden_phrase() -> None:
    service = PersonalityService()
    result = service.evaluate(
        PersonalityEvaluationRequest(
            profile=PersonalityProfile(
                name="ops",
                traits=["concise"],
                must_say=["rollback"],
                must_avoid=["trust me"],
            ),
            answer="rollback plan ready, trust me",
        )
    )
    assert not result.passed
    assert any("forbidden phrase" in finding for finding in result.findings)
