# Parikshak API Contract

This document specifies the communication interfaces, error codes, and consumption strategies for Parikshak as a Capability Provider.

---

## 1. REST Endpoints

### POST `/parikshak/review`
Evaluates a task submission and returns a structured decision result.

#### Request Headers
- `Content-Type`: `application/json`

#### Response Codes
- `200 OK`: Request processed successfully (includes PASS, PARTIAL, and FAIL outcomes).
- `400 Bad Request`: Invalid payload format or missing required fields.
- `422 Unprocessable Entity`: Validation failure on string length constraints.

---

## 2. Versioning & Deprecation Strategy
- **Current Version**: `v1.1.0`
- **URI Prefixing**: Future versions will use `/api/v2/parikshak/review` to prevent breaking changes.
- **Backward Compatibility Guarantee**: Minor updates (v1.x) will never drop or rename payload fields.

---

## 3. Resilience Strategies
- **Retry Strategy**: Downstream clients should retry on HTTP 500/503 errors using **Exponential Backoff** (Base: 1s, Max: 32s, Max attempts: 5).
- **Timeout Strategy**: Evaluator processes generally complete in < 2 ms. The API gateway enforces a strict timeout of **1500 ms** per call, raising a `TIMEOUT_EXPIRED` error thereafter.
