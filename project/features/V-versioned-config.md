# Feature V: Versioned config schema

**Status:** Implemented (v0.1.0)  
**Primary module(s):** `config.py`

## Description

ProfileConfig carries a schema_version field (default '1'). Unknown fields are ignored by Pydantic, making the schema forward-compatible.

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change |
|---------|--------|
| 0.1.0 | Feature defined and documented |
