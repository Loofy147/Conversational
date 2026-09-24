from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ACT = ROOT / 'conversations' / 'activation-001'
REV = ACT / 'revisions'

def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))

def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')

def digest_event(event):
    body = {k: v for k, v in event.items() if k != 'event_digest'}
    return hashlib.sha256(canonical(body)).hexdigest()

def reduce_events(events):
    events = sorted(events, key=lambda e: e['revision'])
    state = None
    previous_digest = None
    for index, event in enumerate(events, start=1):
        assert event['revision'] == index
        assert event['event_digest'] == digest_event(event)
        assert event['previous_event_digest'] == previous_digest
        if index == 1:
            assert event['parent_revision'] is None
            assert event['event_type'] == 'FRONTIER_CREATED'
            p = event['payload']
            state = {
                'identity': {'conversation_id': event['conversation_id'], 'frontier_id': event['frontier_id']},
                'origin': p['origin'],
                'objective': p['objective'],
                'current_question': p['current_question'],
                'decision_refs': list(p['decision_ids']),
                'rejected_path_refs': list(p['rejected_path_ids']),
                'open_question_refs': list(p['open_question_ids']),
                'next_action_id': p['next_action_id'],
                'constraint_refs': list(p['constraint_ids']),
                'status': dict(p['status']),
            }
        else:
            assert event['parent_revision'] == index - 1
            p = event['payload']
            if 'workstream_ids' in p:
                state['workstreams'] = list(p['workstream_ids'])
            if 'trajectory_register' in p:
                state['trajectory_register'] = p['trajectory_register']
            if 'source_registry' in p:
                state['source_registry'] = p['source_registry']
            if 'opportunity_register' in p:
                state['opportunity_register'] = p['opportunity_register']
            state['open_question_refs'].extend(p.get('add_open_question_ids', []))
            state['status'].update(p.get('status', {}))
            if 'storage_contract' in p:
                state['storage_contract'] = p['storage_contract']
            if 'restore_policy' in p:
                state['restore_policy'] = p['restore_policy']
            if 'canonicalization_policy' in p:
                state['canonicalization_policy'] = p['canonicalization_policy']
            if 'discovery_policy' in p:
                state['discovery_policy'] = p['discovery_policy']
            if 'object_registry' in p:
                state['object_registry'] = p['object_registry']
            if 'revision_manifest' in p:
                state['revision_manifest'] = p['revision_manifest']
            if 'projection_policy' in p:
                state['projection_policy'] = p['projection_policy']
        previous_digest = event['event_digest']
    return state

def main() -> None:
    head = load(ACT / 'HEAD.json')
    assert head['revision'] == 4
    events = [load(REV / f'{i:04d}' / 'FRONTIER_EVENT.json') for i in range(1, head['revision'] + 1)]
    reduced = reduce_events(events)
    stored = load(REV / '0004' / 'FRONTIER_STATE.json')
    lineage = load(ROOT / 'lineage' / 'LINEAGE_REGISTER_v0.3.json')
    objects = load(ROOT / 'lineage' / 'FRONTIER_OBJECTS_v0.3.json')
    manifest = load(REV / '0004' / 'MANIFEST.json')
    sources = load(ROOT / 'lineage' / 'SOURCE_REGISTRY_v0.3.json')
    registry = load(ROOT / 'registry' / 'CONVERSATIONS.json')
    assert head['revision'] == 4
    assert head['frontier_id'] == stored['identity']['frontier_id']
    assert head['conversation_id'] == stored['identity']['conversation_id']
    assert head['revision_path'] == 'conversations/activation-001/revisions/0004'
    assert head['revision_manifest'] == 'conversations/activation-001/revisions/0004/MANIFEST.json'

    assert stored['revision'] == 4
    assert stored['identity'] == reduced['identity']
    assert stored['origin'] == reduced['origin']
    assert stored['objective'] == reduced['objective']
    assert stored['current_question'] == reduced['current_question']
    assert stored['workstreams'] == reduced['workstreams']
    assert stored['decision_refs'] == reduced['decision_refs']
    assert stored['rejected_path_refs'] == reduced['rejected_path_refs']
    assert stored['constraint_refs'] == reduced['constraint_refs']
    assert stored['open_question_refs'] == reduced['open_question_refs']
    assert stored['next_action_ref'] == reduced['next_action_id']
    assert stored['status'] == reduced['status']
    assert stored['object_registry'] == reduced['object_registry']
    assert stored['revision_manifest'] == reduced['revision_manifest']
    assert stored['projection_policy'] == reduced['projection_policy']
    assert set(stored['decision_refs']) == {x['id'] for x in objects['decisions']}
    assert set(stored['rejected_path_refs']) == {x['id'] for x in objects['rejected_paths']}
    assert set(stored['constraint_refs']) == {x['id'] for x in objects['constraints']}
    assert set(stored['workstreams']) == {x['id'] for x in objects['workstreams']}
    assert stored['next_action_ref'] in {x['id'] for x in objects['actions']}
    assert stored['source_registry'] == reduced['source_registry']

    trajectory_ids = {x['id'] for x in lineage['trajectory']}
    opportunity_ids = {x['id'] for x in lineage['opportunities']}
    question_ids = {x['id'] for x in lineage['open_questions']}
    assert set(stored['trajectory_refs']) == trajectory_ids
    assert set(stored['preserved_opportunity_refs']) == opportunity_ids
    assert set(stored['open_question_refs']) == question_ids

    source_ids = {x['id'] for x in sources['sources']}
    referenced_source_ids = {sid for item in lineage['trajectory'] + lineage['opportunities'] for sid in item['sources']}
    assert referenced_source_ids <= source_ids

    entry = registry['entries'][0]
    assert entry['conversation_id'] == stored['identity']['conversation_id']
    assert entry['frontier_id'] == stored['identity']['frontier_id']
    assert entry['head'] == 'conversations/activation-001/HEAD.json'
    assert entry['status'] == 'CANDIDATE'

    projection = (REV / '0003' / 'PROJECTION.md').read_text(encoding='utf-8')
    for heading in ('## Purpose', '## Current question', '## Preserved lineage', '## Preserved opportunities', '## Open questions', '## Next action', '## Authorization'):
        assert heading in projection
    assert 'T001–T019' in projection
    assert 'O001–O014' in projection
    assert 'Q001–Q013' in projection

    restore = load(REV / '0004' / 'RESTORE_RESULT.json')
    assert restore['continuation_permission'] == 'CONTEXT_ONLY'
    assert restore['action_authorization'] == 'SEPARATE_GATE_REQUIRED'
    assert restore['checks']['event_log_reduction'] == 'PASS'
    assert restore['checks']['semantic_projection'] == 'PASS'
    assert restore['checks']['external_boundary'] == 'NOT_RUN'
    manifest_paths = {a['path']: a['git_blob_sha'] for a in manifest['artifacts']}
    for path, expected_sha in manifest_paths.items():
        actual_sha = subprocess.check_output(['git', 'rev-parse', f'HEAD:{path}'], text=True).strip()
        assert actual_sha == expected_sha, (path, actual_sha, expected_sha)

    print('frontier-v0.3 verifier: PASS')

if __name__ == '__main__':
    main()
