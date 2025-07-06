# SPIKE-CFG-001: Config Model Framework Comparison

## Summary
This spike compares three frameworks for defining configuration models in `src/config`.
The current implementation uses Python `dataclasses` with custom JSON Schema generation.
We evaluate `dataclasses`, `pydantic`, and `attrs` in terms of features, JSON Schema support, and IDE compatibility.

## 1. Dataclasses (Current)
- Built into the standard library with minimal dependencies.
- Simple classes with type hints make mental models easy to grasp.
- JSON Schema is produced via custom helpers in `src/config/models.py`.
- IDEs recognize fields thanks to type hints, but validation must be written manually.

## 2. Pydantic
- Provides runtime type checking and rich validation out of the box.
- Built-in `.model_json_schema()` generates JSON Schema with field metadata.
- IDEs often offer autocomplete and error highlighting due to explicit fields.
- Adds an external dependency and has slightly higher runtime cost.

## 3. attrs
- Uses the `attrs` library for concise class definitions.
- Validation requires `attrs` converters or third-party packages like `cattrs` for JSON Schema generation.
- IDE support is comparable once type hints are added, but tooling is less widespread than Pydantic.

## Comparison
| Feature                 | dataclasses | pydantic | attrs |
|-------------------------|-------------|---------|-------|
| Type enforcement        | Manual      | Automatic | Optional via validators |
| JSON Schema             | Custom helpers | Built-in | Requires extra packages |
| IDE Autocomplete        | Good (via type hints) | Excellent | Good |
| Dependency footprint    | None        | Additional | Additional |
| Runtime overhead        | Low         | Moderate | Low |

`dataclasses` keep dependencies light and integrate with existing code, but require manual validation and schema logic.
`pydantic` offers strong validation and schema generation, improving error messages and IDE experience at the cost of an extra dependency.
`attrs` provides flexible class definitions and can mimic dataclasses, yet lacks first‑party schema tools.

## Recommendation
For small configuration objects, `dataclasses` plus simple helpers remain straightforward.
If validation grows complex or tight IDE feedback is needed, `pydantic` may be worth adopting.
`attrs` is less compelling here unless its additional features (e.g., field transformers) become necessary.
