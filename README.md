# Conversational

Durable, verification-first conversation continuity.

## Source-of-truth rule

This repository is the canonical source for the conversation-continuation protocol and its executable verification artifacts.

Library copies, conversation transcripts, generated projections, and cached material are transport/retrieval surfaces only. They MUST NOT silently become authority.

## First restore entrypoint

Start with CONVERSATION_ENTRYPOINT.md. It defines the exact discovery and restore order for a fresh conversation.

## Current protocol

- Frontier protocol: v0.3
- Activation fixture: 001, candidate revision 6 with a reported external-boundary restore result
- Current frontier status: CANDIDATE
- Restore status: UNVERIFIED
- Publication status: PUBLISHED_TO_REPO_BRANCH
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

The first submitted fresh-context report states that repository-based reconstruction passed. Revision 6 records that report as PASS_REPORTED, not as an independently attested result. Historical source-byte revalidation and a trusted authenticity root remain unresolved; lifecycle remains CANDIDATE. Successful restore MUST NOT grant external action authorization.

## Evidence discipline

Every material claim is recorded with provenance, status, evidence, limits, and a next discriminating test.

## Status

Research/reference implementation. The first external-boundary attempt is recorded as a reported pass with limitations. Trusted authenticity, historical source-byte revalidation, and external-action authorization remain separate unresolved gates.
