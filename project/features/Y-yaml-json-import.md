# Feature Y: YAML/JSON profile import-export

**Status:** Implemented (PH-06)  
**Primary module(s):** `config.py`

## Description

`ProfileConfig` can be saved to and loaded from both JSON and YAML files.
JSON uses Pydantic's `model_dump(mode="json")` / `model_validate_json`; YAML
uses `yaml.safe_dump` / `yaml.safe_load` (PyYAML imported lazily inside the
methods). All writes are atomic (`.tmp` file then `os.replace`).

## API

| Method | Kind | Description |
|--------|------|-------------|
| `save_json(path)` | instance | Write pretty-printed sorted JSON |
| `load_json(path)` | classmethod | Read + `model_validate_json` |
| `save_yaml(path)` | instance | Write sorted-key safe YAML |
| `load_yaml(path)` | classmethod | `yaml.safe_load` + `model_validate` |

`path` accepts `str` or `pathlib.Path`. Loads return fully validated
`ProfileConfig` instances; invalid content raises `ValidationError` (or
`yaml.YAMLError` for malformed YAML).

## Location in codebase

- `stealth_engine/config.py` — four methods on `ProfileConfig`
- `pyproject.toml` — `pyyaml>=6.0` dependency

## Change History

| Version | Change |
|---------|--------|
| 0.1.0 | Feature defined and documented |
| PH-06  | Implemented: four file IO methods + pyyaml dependency |
