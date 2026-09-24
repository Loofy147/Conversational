from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from frontier.core import verify_repo

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def run_mutation(name: str, relative: str, mutate) -> str:
    with tempfile.TemporaryDirectory(prefix="frontier-mutation-") as tmp:
        candidate = Path(tmp) / "repo"
        shutil.copytree(ROOT, candidate)
        target = candidate / relative
        mutate(target)

        try:
            verify_repo(candidate)
        except (AssertionError, KeyError, ValueError, json.JSONDecodeError):
            return "KILLED"
        return "SURVIVED"


def main() -> None:
    cases = [
        (
            "event_payload_tamper",
            "conversations/activation-001/revisions/0005/FRONTIER_EVENT.json",
            lambda p: _change_json(p, lambda x: x["payload"].update({"audit_basis": "tampered"})),
        ),
        (
            "state_semantic_tamper",
            "conversations/activation-001/revisions/0005/FRONTIER_STATE.json",
            lambda p: _change_json(p, lambda x: x.update({"current_question": "tampered"})),
        ),
        (
            "state_identity_tamper",
            "conversations/activation-001/revisions/0005/FRONTIER_STATE.json",
            lambda p: _change_json(p, lambda x: x["identity"].update({"frontier_id": "wrong"})),
        ),
        (
            "event_chain_tamper",
            "conversations/activation-001/revisions/0005/FRONTIER_EVENT.json",
            lambda p: _change_json(p, lambda x: x.update({"previous_event_digest": "wrong"})),
        ),
        (
            "manifest_omission",
            "conversations/activation-001/revisions/0005/MANIFEST.json",
            lambda p: _remove_last_manifest_artifact(p),
        ),
        (
            "manifest_hash_tamper",
            "conversations/activation-001/revisions/0005/MANIFEST.json",
            lambda p: _change_json(p, lambda x: x["artifacts"][0].update({"git_blob_sha": "0000000000000000000000000000000000000000"})),
        ),
        (
            "head_revision_tamper",
            "conversations/activation-001/HEAD.json",
            lambda p: _change_json(p, lambda x: x.update({"revision": 4})),
        ),
        (
            "object_reference_tamper",
            "lineage/FRONTIER_OBJECTS_v0.3.json",
            lambda p: _change_json(p, lambda x: x["workstreams"][0].update({"id": "W999"})),
        ),
        (
            "projection_tamper",
            "conversations/activation-001/revisions/0005/PROJECTION.md",
            lambda p: p.write_text(
                p.read_text(encoding="utf-8").replace("## Current question", "## Tampered question"),
                encoding="utf-8",
            ),
        ),
        (
            "restore_permission_escalation",
            "conversations/activation-001/revisions/0005/RESTORE_RESULT.json",
            lambda p: _change_json(p, lambda x: x.update({"continuation_permission": "ACTION_ALLOWED"})),
        ),
        (
            "entrypoint_stale_revision",
            "CONVERSATION_ENTRYPOINT.md",
            lambda p: p.write_text(
                p.read_text(encoding="utf-8").replace("HEAD revision: 5", "HEAD revision: 4"),
                encoding="utf-8",
            ),
        ),
    ]

    results = {}
    for name, relative, mutate in cases:
        results[name] = run_mutation(name, relative, mutate)

    killed = sum(result == "KILLED" for result in results.values())
    survived = sum(result == "SURVIVED" for result in results.values())
    print({"total": len(results), "killed": killed, "survived": survived, "results": results})

    if survived:
        raise SystemExit(1)


def _change_json(path: Path, mutate) -> None:
    data = load(path)
    mutate(data)
    save(path, data)


def _remove_last_manifest_artifact(path: Path) -> None:
    data = load(path)
    data["artifacts"].pop()
    save(path, data)


if __name__ == "__main__":
    main()
