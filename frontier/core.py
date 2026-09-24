from __future__ import annotations

import hashlib
import json
import math
import subprocess
import unicodedata
from pathlib import Path
from typing import Any, Iterable


def _normalize(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key in sorted(value):
            normalized_key = unicodedata.normalize("NFC", key)
            out[normalized_key] = _normalize(value[key])
        return out
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite number is forbidden in canonical state")
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        _normalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_json(root: Path, relative: str) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def digest_event(event: dict[str, Any]) -> str:
    body = dict(event)
    body.pop("event_digest", None)
    return digest(body)


def reduce_events(root: Path, head_revision: int) -> dict[str, Any]:
    previous_event_digest: str | None = None
    state: dict[str, Any] | None = None

    for revision in range(1, head_revision + 1):
        event = load_json(
            root,
            f"conversations/activation-001/revisions/{revision:04d}/FRONTIER_EVENT.json",
        )
        assert event["revision"] == revision
        assert event["parent_revision"] == (None if revision == 1 else revision - 1)
        assert event["conversation_id"] == "conv-e274d6a5-0989-4a1f-8df9-53da53ed55bc"
        assert event["frontier_id"] == "conv-e274d6a5-0989-4a1f-8df9-53da53ed55bc:frontier"
        assert event["event_digest"] == digest_event(event)
        assert event["previous_event_digest"] == previous_event_digest

        payload = event["payload"]

        if revision == 1:
            state = {
                "identity": {
                    "conversation_id": event["conversation_id"],
                    "frontier_id": event["frontier_id"],
                },
                "origin": payload["origin"],
                "objective": payload["objective"],
                "current_question": payload["current_question"],
                "decision_refs": list(payload["decision_ids"]),
                "rejected_path_refs": list(payload["rejected_path_ids"]),
                "open_question_refs": list(payload["open_question_ids"]),
                "next_action_ref": payload["next_action_id"],
                "constraint_refs": list(payload["constraint_ids"]),
                "status": dict(payload["status"]),
            }
        else:
            assert state is not None
            if "workstream_ids" in payload:
                state["workstreams"] = list(payload["workstream_ids"])
            if "trajectory_register" in payload:
                state["trajectory_register"] = payload["trajectory_register"]
            if "source_registry" in payload:
                state["source_registry"] = payload["source_registry"]
            if "opportunity_register" in payload:
                state["opportunity_register"] = payload["opportunity_register"]
            if "add_open_question_ids" in payload:
                state["open_question_refs"].extend(payload["add_open_question_ids"])
            if "storage_contract" in payload:
                state["storage_contract"] = payload["storage_contract"]
            if "restore_policy" in payload:
                state["restore_policy"] = payload["restore_policy"]
            if "canonicalization_policy" in payload:
                state["canonicalization_policy"] = payload["canonicalization_policy"]
            if "discovery_policy" in payload:
                state["discovery_policy"] = payload["discovery_policy"]
            if "object_registry" in payload:
                state["object_registry"] = payload["object_registry"]
            if "revision_manifest" in payload:
                state["revision_manifest"] = payload["revision_manifest"]
            if "projection_policy" in payload:
                state["projection_policy"] = payload["projection_policy"]
            if "trajectory_refs" in payload:
                state["trajectory_refs"] = list(payload["trajectory_refs"])
            if "preserved_opportunity_refs" in payload:
                state["preserved_opportunity_refs"] = list(payload["preserved_opportunity_refs"])
            if "forbidden_assumption_refs" in payload:
                state["forbidden_assumption_refs"] = list(payload["forbidden_assumption_refs"])
            if "manifest_policy" in payload:
                state["manifest_policy"] = payload["manifest_policy"]
            if "canonicalization_policy" in payload:
                state["canonicalization_policy"] = payload["canonicalization_policy"]
            if "projection_policy" in payload:
                state["projection_policy"] = payload["projection_policy"]
            if "semantic_equivalence_profile" in payload:
                state["semantic_equivalence_profile"] = payload["semantic_equivalence_profile"]
            state["status"].update(payload.get("status", {}))

        previous_event_digest = event["event_digest"]

    assert state is not None
    return state


def _indexed(items: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in items}


def _ordered(objects: dict[str, dict[str, Any]], refs: list[str]) -> list[dict[str, Any]]:
    out = []
    for ref in refs:
        assert ref in objects, f"dangling reference: {ref}"
        out.append(objects[ref])
    return out


def semantic_projection(state: dict[str, Any], objects: dict[str, Any], lineage: dict[str, Any]) -> dict[str, Any]:
    workstreams = _indexed(objects["workstreams"])
    decisions = _indexed(objects["decisions"])
    rejected = _indexed(objects["rejected_paths"])
    constraints = _indexed(objects["constraints"])
    actions = _indexed(objects["actions"])
    trajectory = _indexed(lineage["trajectory"])
    opportunities = _indexed(lineage["opportunities"])
    questions = _indexed(lineage["open_questions"])

    action = actions[state["next_action_ref"]]

    return {
        "origin": state["origin"],
        "objective": state["objective"],
        "current_question": state["current_question"],
        "workstreams": [
            {
                "name": item["name"],
                "status": item["status"],
                "objective": item["objective"],
                "current_question": item["current_question"],
            }
            for item in _ordered(workstreams, state["workstreams"])
        ],
        "trajectory": [
            {"status": item["status"], "statement": item["statement"]}
            for item in _ordered(trajectory, state["trajectory_refs"])
        ],
        "preserved_opportunities": [
            {"statement": item["statement"], "reopen_if": item["reopen_if"]}
            for item in _ordered(opportunities, state["preserved_opportunity_refs"])
        ],
        "open_questions": [
            {"status": item["status"], "question": item["question"]}
            for item in _ordered(questions, state["open_question_refs"])
        ],
        "decisions": [
            {
                "status": item["status"],
                "statement": item["statement"],
                "superseded_by": item.get("superseded_by"),
                "reason": item.get("reason"),
            }
            for item in _ordered(decisions, state["decision_refs"])
        ],
        "rejected_paths": [
            {
                "status": item["status"],
                "statement": item["statement"],
                "reason": item["reason"],
            }
            for item in _ordered(rejected, state["rejected_path_refs"])
        ],
        "constraints": [
            item["statement"] for item in _ordered(constraints, state["constraint_refs"])
        ],
        "next_action": {
            "purpose": action["purpose"],
            "action": action["action"],
            "expected_signal": action["expected_signal"],
            "failure_condition": action["failure_condition"],
            "rollback": action["rollback"],
            "status": action["status"],
        },
    }


def semantic_digest(state: dict[str, Any], objects: dict[str, Any], lineage: dict[str, Any]) -> str:
    return digest(semantic_projection(state, objects, lineage))


def render_projection(state: dict[str, Any], objects: dict[str, Any], lineage: dict[str, Any]) -> str:
    workstreams = _indexed(objects["workstreams"])
    decisions = _indexed(objects["decisions"])

    lines = [
        f"# Conversation Frontier — Activation 001 — Revision {state['revision']}",
        "",
        f"**Activation:** {state['status']['activation']}  ",
        f"**Frontier:** {state['status']['frontier']}  ",
        f"**Restore:** {state['status']['restore']}  ",
        f"**Publication:** {state['status']['publication']}  ",
        f"**Authenticity:** {state['status']['authenticity']}  ",
        f"**Revision:** {state['revision']}",
        "",
        "## Purpose",
        "",
        state["objective"],
        "",
        "## Current question",
        "",
        state["current_question"],
        "",
        "## Workstreams",
        "",
    ]

    for index, ref in enumerate(state["workstreams"]):
        suffix = "  " if index < len(state["workstreams"]) - 1 else ""
        lines.append(f"{ref} {workstreams[ref]['name']}" + suffix)

    lines += [
        "",
        "## Preserved lineage",
        "",
        "T001–T019 are retained in the canonical lineage register, covering the progression from Skill Engine falsification through capability execution, experiment semantics, epistemic state, continuation, relational applicability, dependency/authority separation, evidence validity, cross-domain reuse, mechanism-frontier research, and execution assurance.",
        "",
        "## Preserved opportunities",
        "",
        "O001–O014 remain linked to source fingerprints and explicit reopen conditions.",
        "",
        "## Open questions",
        "",
        "Q001–Q013 remain OPEN.",
        "",
        "## Decisions",
        "",
        "D001 is superseded by D005." if decisions["D001"]["status"] == "SUPERSEDED" else "D001 remains established.",
        "D002–D005 remain established.",
        "",
        "## Rejected paths",
        "",
        "R001–R004 remain rejected.",
        "",
        "## Next action",
        "",
        "A001 — Run the first genuine external-boundary restore from a fresh conversation.",
        "",
        "## Constraints",
        "",
        "C001–C005 remain binding restore constraints.",
        "",
        "## Authorization",
        "",
        "Successful restoration grants context continuity only. External action authorization remains a separate gate.",
        "",
    ]
    return "
".join(lines)


def _git_blob_sha(root: Path, relative: str) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", f"HEAD:{relative}"],
        cwd=root,
        text=True,
    ).strip()


def verify_repo(root: Path) -> dict[str, Any]:
    act = root / "conversations" / "activation-001"
    head = load_json(root, "conversations/activation-001/HEAD.json")
    assert head["revision"] == 5

    reduced = reduce_events(root, head["revision"])
    stored = load_json(root, "conversations/activation-001/revisions/0005/FRONTIER_STATE.json")
    objects = load_json(root, "lineage/FRONTIER_OBJECTS_v0.3.json")
    lineage = load_json(root, "lineage/LINEAGE_REGISTER_v0.3.json")
    manifest = load_json(root, "conversations/activation-001/revisions/0005/MANIFEST.json")
    policy = load_json(root, "protocol/PROJECTION_POLICY_v0.3.1.json")
    semantic_profile = load_json(root, "protocol/SEMANTIC_EQUIVALENCE_PROFILE_v0.3.1.json")
    manifest_policy = load_json(root, "protocol/FRONTIER_MANIFEST_POLICY_v0.3.1.json")
    canonicalization = load_json(root, "protocol/CANONICALIZATION_v0.3.1.json")
    restore = load_json(root, "conversations/activation-001/revisions/0005/RESTORE_RESULT.json")
    registry = load_json(root, "registry/CONVERSATIONS.json")

    assert head["frontier_id"] == stored["identity"]["frontier_id"]
    assert head["conversation_id"] == stored["identity"]["conversation_id"]
    assert head["revision_path"] == "conversations/activation-001/revisions/0005"
    assert head["revision_manifest"] == "conversations/activation-001/revisions/0005/MANIFEST.json"

    for field in (
        "origin",
        "objective",
        "current_question",
        "workstreams",
        "trajectory_refs",
        "preserved_opportunity_refs",
        "open_question_refs",
        "decision_refs",
        "rejected_path_refs",
        "constraint_refs",
        "next_action_ref",
        "forbidden_assumption_refs",
        "source_registry",
        "lineage_register",
        "object_registry",
        "projection_policy",
        "semantic_equivalence_profile",
        "manifest_policy",
        "canonicalization_policy",
        "revision_manifest",
        "status",
    ):
        assert stored[field] == reduced[field], field

    assert stored["revision"] == 5

    object_ids = {
        "workstreams": {x["id"] for x in objects["workstreams"]},
        "decisions": {x["id"] for x in objects["decisions"]},
        "rejected_path_refs": {x["id"] for x in objects["rejected_paths"]},
        "constraints": {x["id"] for x in objects["constraints"]},
        "actions": {x["id"] for x in objects["actions"]},
    }
    assert set(stored["workstreams"]) == object_ids["workstreams"]
    assert set(stored["decision_refs"]) == object_ids["decisions"]
    assert set(stored["rejected_path_refs"]) == object_ids["rejected_path_refs"]
    assert set(stored["constraint_refs"]) == object_ids["constraints"]
    assert stored["next_action_ref"] in object_ids["actions"]

    assert set(stored["trajectory_refs"]) == {x["id"] for x in lineage["trajectory"]}
    assert set(stored["preserved_opportunity_refs"]) == {x["id"] for x in lineage["opportunities"]}
    assert set(stored["open_question_refs"]) == {x["id"] for x in lineage["open_questions"]}

    source_ids = {x["id"] for x in load_json(root, "lineage/SOURCE_REGISTRY_v0.3.json")["sources"]}
    referenced_source_ids = {
        sid
        for item in lineage["trajectory"] + lineage["opportunities"]
        for sid in item["sources"]
    }
    assert referenced_source_ids <= source_ids

    semantic_a = semantic_projection(stored, objects, lineage)
    semantic_b = semantic_projection(reduced, objects, lineage)
    assert semantic_a == semantic_b
    digest_a = digest(semantic_a)
    digest_b = digest(semantic_b)
    assert digest_a == digest_b

    identity_variant = json.loads(json.dumps(stored))
    identity_variant["identity"] = {
        "conversation_id": "different-conversation",
        "frontier_id": "different-frontier",
    }
    identity_variant["revision"] = 999
    assert semantic_digest(identity_variant, objects, lineage) == digest_a

    generated_projection = render_projection(stored, objects, lineage)
    stored_projection = (root / "conversations/activation-001/revisions/0005/PROJECTION.md").read_text(encoding="utf-8")
    assert generated_projection == stored_projection

    assert policy["renderer"] == "frontier.core.render_projection"
    assert policy["projection_authority"] == "DERIVED_ONLY"
    assert semantic_profile["schema"] == "conversation-frontier-semantic-equivalence-profile-v0.3.1"
    assert "current_question" in semantic_profile["semantic_fields"]
    assert semantic_profile["invariance"] == "Changing only excluded fields must not change semantic_digest."
    assert canonicalization["schema"] == "conversation-frontier-canonicalization-v0.3.1"
    assert canonicalization["semantic_resolution"]["resolve_references"] is True
    assert canonicalization["serialization"]["unicode_normalization"] == "NFC"
    assert canonicalization["serialization"]["non_finite_numbers"] == "REJECT"

    entry = registry["entries"][0]
    assert entry["conversation_id"] == stored["identity"]["conversation_id"]
    assert entry["frontier_id"] == stored["identity"]["frontier_id"]
    assert entry["head"] == "conversations/activation-001/HEAD.json"
    assert entry["revision"] == 5
    assert entry["status"] == "CANDIDATE"

    assert restore["continuation_permission"] == "CONTEXT_ONLY"
    assert restore["action_authorization"] == "SEPARATE_GATE_REQUIRED"
    assert restore["checks"]["event_log_reduction"] == "PASS"
    assert restore["checks"]["object_reference_closure"] == "PASS"
    assert restore["checks"]["external_boundary"] == "NOT_RUN"

    manifest_paths = {item["path"]: item["git_blob_sha"] for item in manifest["artifacts"]}
    required_paths = set(manifest_policy["required_artifacts"]["revision"] + manifest_policy["required_artifacts"]["dependency"])
    assert set(manifest_paths) == required_paths
    assert len(manifest_paths) == len(required_paths)
    for relative, expected in manifest_paths.items():
        actual = _git_blob_sha(root, relative)
        assert actual == expected, (relative, actual, expected)

    entrypoint = (root / "CONVERSATION_ENTRYPOINT.md").read_text(encoding="utf-8")
    assert "HEAD revision: 5" in entrypoint
    assert "CONTEXT_ONLY" in entrypoint
    assert "external action authorization" in entrypoint

    return {
        "status": "PASS",
        "revision": 5,
        "semantic_digest": digest_a,
        "manifest_artifacts": len(manifest_paths),
        "continuation_permission": restore["continuation_permission"],
        "external_boundary": restore["checks"]["external_boundary"],
    }
