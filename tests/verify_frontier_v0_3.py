from __future__ import annotations

import hashlib
import json
from pathlib import Path

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
                'identity': p['identity'],
                'origin': p['origin'],
                'objective': p['objective'],
                'current_question': p['current_question'],
                'decisions': list(p['decision_ids']),
                'rejected_paths': list(p['rejected_path_ids']),
                'open_question_refs': list(p['open_question_ids']),
                'next_action_id': p['next_action_id'],
                'constraint_ids': list(p['constraint_ids']),
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
        previous_digest = event['event_digest']
    return state

def main() -> None:
    events = [load(REV / f'{i:04d}' / 'FRONTIER_EVENT.json') for i in range(1, 4)]
    reduced = reduce_events(events)
    stored = load(REV / '0003' / 'FRONTIER_STATE.json')
    lineage = load(ROOT / 'lineage' / 'LINEAGE_REGISTER_v0.3.json')
    sources = load(ROOT / 'lineage' / 'SOURCE_REGISTRY_v0.3.json')
    registry = load(ROOT / 'registry' / 'CONVERSATIONS.json')
    head = load(ACT / 'HEAD.json')

    assert head['revision'] == 3
    assert head['frontier_id'] == stored['identity']['frontier_id']
    assert head['conversation_id'] == stored['identity']['conversation_id']
    assert head['revision_path'] == 'conversations/activation-001/revisions/0003'

    assert stored['revision'] == 3
    assert stored['identity'] == reduced['identity']
    assert stored['origin'] == reduced['origin']
    assert stored['objective'] == reduced['objective']
    assert stored['current_question'] == reduced['current_question']
    assert stored['workstreams'] == reduced['workstreams']
    assert stored['open_question_refs'] == reduced['open_question_refs']
    assert stored['next_action']['action_id'] == reduced['next_action_id']
    assert stored['status'] == reduced['status']
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

    restore = load(REV / '0003' / 'RESTORE_RESULT.json')
    assert restore['continuation_permission'] == 'CONTEXT_ONLY'
    assert restore['action_authorization'] == 'SEPARATE_GATE_REQUIRED'
    assert restore['checks']['event_log_reduction'] == 'PASS'
    assert restore['checks']['semantic_projection'] == 'PASS'
    assert restore['checks']['external_boundary'] == 'NOT_RUN'

    print('frontier-v0.3 verifier: PASS')

if __name__ == '__main__':
    main()
