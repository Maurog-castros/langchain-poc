from __future__ import annotations

from app.models.schemas import PersonalityEvaluationRequest, PersonalityEvaluationResponse


class PersonalityService:
    def evaluate(self, request: PersonalityEvaluationRequest) -> PersonalityEvaluationResponse:
        answer = request.answer.lower()
        findings: list[str] = []
        score = 1.0

        for phrase in request.profile.must_say:
            if phrase.lower() not in answer:
                score -= 0.2
                findings.append(f"missing required phrase: {phrase}")

        for phrase in request.profile.must_avoid:
            if phrase.lower() in answer:
                score -= 0.3
                findings.append(f"forbidden phrase present: {phrase}")

        for trait in request.profile.traits:
            if trait.lower() not in answer:
                score -= 0.05
                findings.append(f"trait not explicit: {trait}")

        score = max(0.0, min(1.0, score))
        return PersonalityEvaluationResponse(
            score=score,
            passed=score >= 0.75,
            findings=findings,
        )
