# Feature J: JSON-based profile config

**Status:** Implemented (v0.1.0)  
**Primary module(s):** `config.py`

## Description

`ProfileConfig` is a Pydantic v2 model. Instances can be serialised to JSON via `model_dump()` / `model_dump_json()` and deserialised via `model_validate()` / `model_validate_json()`; file-level JSON/YAML IO is provided by Feature Y (`save_json`/`load_json`/`save_yaml`/`load_yaml`).

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change |
|---------|--------|
| 0.1.0 | Feature defined and documented |
| PH-06  | File-level JSON/YAML IO added via Feature Y methods |
