# Full Lineage Revalidation — 2026-09-24

## Scope
Reconstruct the path from the first Skill Engine experiments through Capability Lab, experimental semantics, epistemic/relational/dependency layers, Machine research, and the conversation-continuity system.

## Rule
Historical artifacts are evidence for their own bounded scope. Current repository state is the authoritative implementation source for this protocol. Library material is transport/provenance only.

## Preserved trajectory
T001–T019 are stored in lineage/LINEAGE_REGISTER_v0.3.json.

## High-value preserved opportunities
O001–O014 are stored with immutable source fingerprints and explicit reopen conditions.

## Critical findings that changed the Frontier design
1. Activation status, frontier lifecycle, restore status, publication status, and authenticity status are separate state machines.
2. Frontier semantic state must be reconstructible from append-only frontier events.
3. Identity/storage metadata must not contaminate semantic equivalence.
4. Integrity is not authenticity.
5. Human projections need deterministic rendering rules.
6. Discovery indexes are projections; they cannot create state.
7. Partial publication must never advance the active HEAD.
8. Restore never grants action authorization.
9. Cross-domain reusable mechanisms do not transfer qualification, authority, or trust.
10. Evidence usability depends on integrity, scope, temporal validity, first-seen ordering, and claim matching where applicable.
11. Dependency traversal must not traverse authority semantics.
12. Preserved opportunities and rejected paths are part of the durable reasoning frontier, not optional commentary.

## Verification baseline
The Frontier revision has an independent local reducer/checker and a repository CI workflow. A fresh-conversation restore remains deliberately OPEN because this repository cannot manufacture evidence that a separate conversation boundary has already occurred.

## Current state
activation_status = ACTIVE
frontier_status = CANDIDATE
restore_status = UNVERIFIED
publication_status = PUBLISHED_TO_REPO_BRANCH
authenticity_status = SELF_INTEGRITY_ONLY

## Next discriminating test
Open a genuinely new conversation and restore from this repository without using the prior transcript as a source. Compare the structured RestoreResult against the repository canonical state and event reduction. External action authorization remains a separate gate.
