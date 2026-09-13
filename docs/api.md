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
