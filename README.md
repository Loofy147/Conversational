# Conversational

Durable, verification-first conversation continuity.

## Source-of-truth rule

This repository is the canonical source for the conversation-continuation protocol and its executable verification artifacts.

Library copies, conversation transcripts, generated projections, and cached material are transport/retrieval surfaces only. They MUST NOT silently become authority.

## First restore entrypoint

Start with CONVERSATION_ENTRYPOINT.md. It defines the exact discovery and restore order for a fresh conversation.

## Current protocol

- Frontier schema: v0.2.2
- Activation fixture: 001
- Current frontier status: CANDIDATE
- Restore status: UNVERIFIED
- Publication status: PUBLISH_PENDING
- Authenticity status: SELF_INTEGRITY_ONLY

## Core model

EventLog -> CanonicalState -> Projection
                 |
                 +-> Lineage
                 +-> RestoreResult
                 +-> Publication HEAD

Identity, semantic state, provenance, integrity, publication, and action authorization are separate concerns.

## First external-boundary test

A fresh conversation MUST discover the current frontier from repository/Library references, verify bindings, rebuild the state from the event log, compare the semantic projection, and return a structured RestoreResult.

Successful restore MUST NOT grant external action authorization.

## Evidence discipline

Every material claim is recorded with provenance, status, evidence, limits, and a next discriminating test.

## Status

Research/reference implementation. Cross-conversation restore remains an open empirical boundary until a genuinely fresh conversation passes the external-boundary restore test.
