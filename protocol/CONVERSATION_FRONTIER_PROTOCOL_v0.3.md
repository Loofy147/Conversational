# Conversation Frontier Protocol v0.3

## Purpose
Durable continuation across conversation boundaries without treating transcript, model memory, or reconstructed prose as canonical truth.

The durable frontier preserves:
- origin problem;
- current objective;
- current question per workstream;
- established decisions;
- rejected paths and reasons;
- preserved opportunities and reopen conditions;
- open questions;
- next discriminating action;
- constraints and forbidden assumptions;
- provenance and dependency bindings.

Hidden chain-of-thought is not persisted.

## Truth ownership
The Frontier is a projection/orchestration layer. Domain facts, evidence, claims, capability state, execution outcomes, organizational decisions, and live-world state retain their own canonical authorities.

## Canonical objects
ConversationIdentity: immutable conversation lineage identity. Folder names and dates are locators only.
FrontierRevision: immutable revision identified by frontier_id, revision, and parent_revision.
FrontierEvent: append-only event with event_id, event_type, parent_revision, payload, and event_digest.
CanonicalSemanticState: deterministic reduction of the frontier event log.
SourceBinding: versioned reference to an upstream source with digest, freshness, dependency scope, and required/optional status.
ProjectionPolicy: deterministic rendering rule.
RestoreResult: structured result of discovery, integrity, schema, reduction, dependency, provenance, and policy checks.
PublicationHead: pointer to the latest verified revision; never canonical truth.

## Canonicality
State_n = Reduce(Event_1 ... Event_n).
A state field that cannot be reconstructed from the event history is shadow state.

## Semantic equivalence
Semantic equivalence excludes conversation identity, folder/path, publication metadata, authenticity metadata, runtime metadata, storage metadata, integrity metadata, and HEAD metadata.
Provenance compatibility is checked separately.

## Publication
1. Write immutable revision artifacts.
2. Verify the revision independently.
3. Advance HEAD only when the expected parent revision still matches.
Conflict means BLOCK. A partially published revision is NON_ACTIVE.

## Discovery
Use a rebuildable registry/index plus direct repository paths. A missing, stale, or ambiguous index cannot create authoritative state.

## Restore states
BLOCKED; CANDIDATE; VERIFIED; VERIFIED_REQUIRES_LIVE_REVALIDATION.

VERIFIED means semantic, provenance, schema, integrity, and dependency checks passed. It does not mean that live-world state is current.

## Authorization separation
Restore never grants external action authorization. Current-world validation and the applicable authority/policy gate remain mandatory.

## Fresh-start semantics
Reusable mechanisms, contracts, tests, and research knowledge may transfer. Context-local qualification, authority, trust, and live-world truth do not transfer automatically.

## Acceptance invariant
stored semantic frontier == restored semantic frontier == rebuilt semantic frontier
with semantic and provenance-aware comparison, not transcript equality.

## Non-goals
No claim of arbitrary transcript reconstruction, external-world persistence, distributed consensus, exactly-once external execution, or external authenticity without a trusted root.
