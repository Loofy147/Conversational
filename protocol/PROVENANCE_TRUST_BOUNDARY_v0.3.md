# Provenance and Trust Boundary v0.3

## Repository authority
Loofy147/Conversational is the canonical implementation source for this conversation-continuation protocol.
Git history establishes repository content identity within the repository trust boundary. It is not an independent external signature over every historical claim.

## Historical source bindings
lineage/SOURCE_REGISTRY_v0.3.json records fingerprints for historical artifacts retrieved from Library.
These bindings identify the historical artifact, observed SHA-256, provenance class, and role. They do not make that artifact globally authoritative.

## Authenticity
Current status: SELF_INTEGRITY_ONLY.
A trusted external signing or attestation root is not implemented yet.

## Restore rule
A restore may be semantically valid while retaining provenance or authenticity limitations. Those limitations must not be hidden.

## Anti-confusion rule
- integrity != authenticity
- provenance != truth
- historical evidence != current live state
- repository presence != production authority
- restored context != action authorization
