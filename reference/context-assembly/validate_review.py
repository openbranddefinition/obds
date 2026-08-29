from __future__ import annotations

from canonical import sha256_id

FINDING_CATEGORIES = {"violation", "material_conflict", "opportunity"}
REVIEW_DECISIONS = {"pass", "pass_with_suggestions", "approval_required", "fail"}


def validate_review(compiled_context, package, review):
    if package["sources"]["compiledContextHash"] != compiled_context.get("artifactHash"):
        raise ValueError("review compiledContextHash mismatch")
    by_id = {item["id"]: item for item in compiled_context["elementRecords"]}
    active = set(package["selection"]["activeGuidanceElementIds"])

    if review["modelInputHash"] != package["modelInputHash"]:
        raise ValueError("review modelInputHash mismatch")

    if review.get("decision") not in REVIEW_DECISIONS:
        raise ValueError("invalid review decision")

    blocking_violations = 0
    approval_violations = 0
    any_violation = False

    for finding in review["findings"]:
        category = finding["category"]
        ids = finding["elementIds"]
        if category not in FINDING_CATEGORIES:
            raise ValueError("invalid review finding category")

        for element_id in ids:
            if element_id not in by_id:
                raise ValueError(f"review references unknown element: {element_id}")

        if category == "violation":
            any_violation = True
            rules = [
                by_id[element_id]
                for element_id in ids
                if by_id[element_id].get("family") == "rules"
            ]
            if not rules:
                raise ValueError("violation must reference a RULE")
            for rule in rules:
                enforcement = (rule.get("value") or {}).get("enforcement")
                if enforcement == "block":
                    blocking_violations += 1
                elif enforcement == "require_approval":
                    approval_violations += 1

        elif category in {"material_conflict", "opportunity"}:
            if not set(ids).issubset(active):
                raise ValueError(
                    f"{category} must reference active guidance only"
                )

    decision = review["decision"]
    if decision == "fail" and blocking_violations == 0:
        raise ValueError("fail requires a blocking RULE violation")
    if decision == "approval_required" and approval_violations == 0:
        raise ValueError(
            "approval_required requires an approval-requiring RULE violation"
        )
    if decision in {"pass", "pass_with_suggestions"} and any_violation:
        raise ValueError("pass decision cannot contain a violation")
    if decision == "pass_with_suggestions" and not review["findings"]:
        raise ValueError("pass_with_suggestions requires findings")

    expected_hash = sha256_id(
        {key: value for key, value in review.items() if key != "reviewHash"}
    )
    if review["reviewHash"] != expected_hash:
        raise ValueError("reviewHash mismatch")

    return True
