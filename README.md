StockCell
=========

A compact platform for typed monitoring, persistence, and live application state.
It uses an application-layer API over stable domain and storage layers and keeps raw state
visible for analysis.

Core goals:

* Predictable application and infrastructure flows.
* Deterministic handling of two-phase boundaries.
* Correctness of the `Observation` type and its navigation.
* Small, reviewable, and extensible codebase.
