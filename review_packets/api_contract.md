# Parikshak API Contract Specification

This document details the interface guidelines, versioning rules, and retry/timeout strategies for Parikshak.

## Contract Boundaries & Versioning
* **Current Version**: `v1.0` (indicated by `schema_version`)
* **Strategy**: Backward compatibility is enforced. Any schema update increments the major or minor identifier. If `schema_version` is unsupported, the `registry_validator` throws a `schema_violation` rejection immediately.

## Retry and Timeout Strategy
* **GitHub API Timeout**: If the GitHub API or crawler timeout is reached (network_failure), the system falls back gracefully to title and description scoring only (max 60 points). It does not block execution or raise uncaught 500 errors.
* **Client Retry**: Consumers are advised to implement an exponential backoff retry for downstream writes only if a network exception occurs. Double submissions are prevented by checking unique trace IDs.

*Verified: 2026-06-30T10:38:25.844917Z UTC*
