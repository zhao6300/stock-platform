# HTTP JSON API

## Conventions

* The API path is `/api/v1`.
* Requests and responses use JSON.
* Exit codes for JSON objects are `0 = ok`, `1 = invalid`, `2 = conflict`, `3 = missing`.
* Every API result can be either:
  ```json
  {"status": "ok", "data": "some payload"}
  ```
  or
  ```json
  {"status": "error", "error": {"code": "...", "message": "..."}}
  ```
* `GET` requests are read-only by default. Mutators are implemented as explicit calls,
  never implicit in request handlers.
* Synchronous APIs use the same field names as interactive analysis; analytics correctness
  helps the frontend stay accurate.

## JSON and duration values

* `raw` is the direct data payload.
* Use JSON for durable persistence. Use application-native data formats for rendering.
* Do not use locale-specific time or duration values in database state. Keep them in
  application data model fields (for example, `open_time` as `HH:MM:SS`).

## AI research endpoints

`POST /api/v1/research/ai-analysis` remains the single-purpose analysis entry. Every
request must name a pinned snapshot and is subject to the research query limit.
`provider_id` is optional and must be registered.

`GET /api/v1/research/ai-providers` returns only stable provider IDs and the default
provider ID. It deliberately does not expose endpoint details, prompts, model text, or
credential material.

`POST /api/v1/research/ai-workflow` runs the fixed lifecycle in this order:

1. `INGESTION_READINESS`
2. `DATA_QUALITY`
3. `RESEARCH_REVIEW`
4. `RISK_DECISION`
5. `REPORT_BRIEFING`

A successful response contains `workflow_id`, provider and snapshot identifiers, and the
`analysis_id` of each stage. A stage failure produces a local 400-series error and does
not publish a workflow artifact.
