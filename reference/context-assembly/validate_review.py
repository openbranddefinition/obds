from __future__ import annotations

from canonical import identity_key, sha256_id, text_hash
from model_input import ModelInputContractError, render_model_input

# Section 14. The review validator is a Compiled Brand Context executor: it
# derives a governed review decision from `elementRecords`, so it executes the
# published contract and reproduces the seal, from the one implementation of
# each that Context Assembly already carries. Importing them is the point —
# a second copy of either is the defect this closes.
from assemble_context import (
    artifact_hash,
    compiled_context_contract_errors,
    model_input_package_contract_errors,
    review_result_contract_errors,
)

FINDING_CATEGORIES = {"violation", "material_conflict", "opportunity"}
REVIEW_DECISIONS = {"pass", "pass_with_suggestions", "approval_required", "fail"}


def validate_review(compiled_context, package, review):
    # All three governed documents, each against its published contract, before
    # any field of any of them is read. Only the artefact's contract was executed
    # here, so a package and a review declaring another kind at another schema
    # version still produced a governed review decision.
    for what, document, errors in (
        ("compiled context", compiled_context, compiled_context_contract_errors),
        ("model input package", package, model_input_package_contract_errors),
        ("review result", review, review_result_contract_errors),
    ):
        violations = errors(document)
        if violations:
            raise ValueError(f"{what} does not satisfy its published contract: {violations[0]}")
    # The seal is reproduced, not read. This compared the package's claim against
    # the artefact's own declared `artifactHash` — two claims about the same
    # thing, and neither of them checked. A rule could be added to
    # `elementRecords`, or a `block` enforcement downgraded to `inform`, with
    # both declared values left untouched, and the governed review decision
    # derived from `elementRecords` below changed with nothing to notice.
    computed = artifact_hash(compiled_context)
    if compiled_context.get("artifactHash") != computed:
        raise ValueError("compiled context artifactHash mismatch")
    if package["sources"]["compiledContextHash"] != computed:
        raise ValueError("review compiledContextHash mismatch")

    # Every hash this function acts on is reproduced from the payload it claims
    # to describe. `artifactHash` was closed first and these were left: the
    # package's `assemblyHash` was never checked at all, and `modelInputHash`
    # was only compared between two supplied claims — so replacing it in both
    # the package and the review, or editing `slots.taskInput` under the old
    # value, produced a review decision bound to a model input that was never
    # sent. Equality between two claims is not verification.
    package_payload = {key: value for key, value in package.items() if key != "assemblyHash"}
    if package.get("assemblyHash") != sha256_id(package_payload):
        raise ValueError("package assemblyHash mismatch")
    try:
        rendered_hash = text_hash(render_model_input(package["slots"]))
    except (ModelInputContractError, TypeError, ValueError) as error:
        raise ValueError(f"package slots do not render a model input: {error}") from error
    if package.get("modelInputHash") != rendered_hash:
        raise ValueError("package modelInputHash mismatch")
    if review["modelInputHash"] != rendered_hash:
        raise ValueError("review modelInputHash mismatch")

    # Section 8.0a: the package and the review must be about the artefact this
    # review claims to be about. Reproducing four hashes proved the documents
    # were intact; nothing tied their governed identities together, so a package
    # naming another brand at another version, or another target, validated.
    context_manifest = compiled_context["manifest"]
    package_manifest = package["manifest"]
    if identity_key(package_manifest["id"]) != identity_key(context_manifest["id"]):
        raise ValueError("review package manifest id does not match the compiled context")
    for field in ("version", "contentHash"):
        if package_manifest.get(field) != context_manifest.get(field):
            raise ValueError(f"review package manifest {field} does not match the compiled context")
    target = identity_key(compiled_context["targetId"])
    for where, claimed in (("package", package.get("targetId")), ("review", review.get("targetId"))):
        if not isinstance(claimed, str) or identity_key(claimed) != target:
            raise ValueError(f"review {where} targetId does not match the compiled context")

    # Section 8.0a: identities are compared on their canonical form.
    by_id = {identity_key(item["id"]): item for item in compiled_context["elementRecords"]}
    active = {identity_key(item) for item in package["selection"]["activeGuidanceElementIds"]}

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
            if identity_key(element_id) not in by_id:
                raise ValueError(f"review references unknown element: {element_id}")

        if category == "violation":
            any_violation = True
            rules = [
                by_id[identity_key(element_id)]
                for element_id in ids
                if by_id[identity_key(element_id)].get("family") == "rules"
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
            if not {identity_key(element_id) for element_id in ids}.issubset(active):
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
