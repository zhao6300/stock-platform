# Architecture

The goal is plain and useful. Application shell, JSON graph graph, rendering of documents,
and prebuilt semantic components are all separable.

## Backend Flow

1. Application receives an object graph.
2. It measures new value counts and negative-pattern rules.
3. Host checks ask whether the current source is valid.
4. Invalid sources produce a live journal (renderable).
5. Valid data is rendered into application and buffer views.

## Module Layout

```text
├── src/stock_platform/         # backend and frontend entry portals
│   ├── application/            # use cases and orchestration
│   ├── cli/                    # CLI
│   ├── providers/              # provider contracts
│   ├── domain/                 # calibration logic
│   ├── infrastructure/         # external/technology adapters
│   └── web/                    # application shell and views
└── tests/                      # layer-level tests
```

The API is implemented with `application/`, while domain behavior stays independent of
network, database, frontend rendering, and form widgets.
