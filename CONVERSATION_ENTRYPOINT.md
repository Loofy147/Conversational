# Conversation Continuation Entrypoint

This is the entrypoint for a genuinely fresh conversation.

## Required order
1. Read this file.
2. Read README.md.
3. Resolve registry/CONVERSATIONS.json.
4. Resolve the selected conversation HEAD.json.
5. Resolve the revision referenced by HEAD.
6. Verify the frontier event chain and reduce the events through the revision named by HEAD.
7. Verify every manifest Git blob identity, then resolve lineage/LINEAGE_REGISTER_v0.3.json, lineage/SOURCE_REGISTRY_v0.3.json, and lineage/FRONTIER_OBJECTS_v0.3.json.
8. Compare reduced state with FRONTIER_STATE.json.
9. Verify projection and restore policy.
10. Emit a structured RestoreResult.
11. Do not treat restored context as authorization for external action.

## Current activation
- Conversation: conv-e274d6a5-0989-4a1f-8df9-53da53ed55bc
- Frontier: conv-e274d6a5-0989-4a1f-8df9-53da53ed55bc:frontier
- HEAD revision: resolve from HEAD.json
- Lifecycle: CANDIDATE
- Restore: UNVERIFIED
- Continuation permission: CONTEXT_ONLY
- External action authorization: SEPARATE_GATE_REQUIRED

## Canonical distinction
The transcript is not durable operating memory.
The repository event history is the canonical frontier history. FRONTIER_STATE.json and PROJECTION.md are derived representations. Registry and HEAD files are discovery/publication projections.

## Expected first response
Report discovered identity, resolved revision, integrity/reduction checks, lineage/source resolution, restored current question, restored next action, unresolved gates/unknowns, and the authorization boundary.
Do not claim fresh-conversation restore success until the checks actually pass.
