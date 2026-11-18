# Feature U: Uniform error model

**Status:** Implemented for engine-defined exceptions; external/Pydantic exceptions may remain distinct.
**Primary module(s):** `exceptions.py`

## Description

The engine-defined exception classes inherit from `StealthEngineError`, including typed config, identity, proxy, session, launch, and automation errors. This does not convert every possible exception: Pydantic validation, filesystem/network libraries, and other external exceptions may remain distinct at API boundaries.

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change                         |
| ------- | ------------------------------ |
| 0.1.0   | Feature defined and documented |
