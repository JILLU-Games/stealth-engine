# Module: identity.py

**File:** `stealth_engine/identity.py`
**Status:** ✅ Implemented (v0.1.0) — PH-02 seed persistence, PH-03/04 engine consumption, PH-06 pluggable providers

## Purpose

Generate a coherent browser fingerprint through a pluggable provider and manage persistent per-profile seed values consumed by the engine launch path.

## Public names

- `IdentityProvider` — `typing.Protocol`; `build(config, rng) -> dict` contract for custom generators (Feature P)
- `BrowserForgeIdentityProvider` — default provider; wraps `browserforge.fingerprints.FingerprintGenerator` and converts output to the canonical primitive dict
- `IdentityGenerator` — orchestrates provider + config overrides + validation + caching + seed persistence

## Current responsibilities

- `IdentityGenerator(config, provider=None)` accepts an optional `IdentityProvider`; `None` selects `BrowserForgeIdentityProvider`.
- `generate()` delegates raw fingerprint construction to `provider.build(config, self._rng)`, then applies `ProfileConfig.locale`/`timezone` overrides and `_validate()` uniformly for every provider; result is cached and deep-copied per call. Signature and output shape unchanged.
- `fingerprint_hash()` hashes the generated dict; behavior unchanged.
- `get_or_create_seeds()` loads or persists `seeds.json` in the resolved profile root (see `_profile_root()`) with `canvas`, `audio`, `fonts`, `locale`, `timezone_id`, `locale_source`, and `timezone_source`.
- `_profile_root()` mirrors `StealthEngine._derive_base_dir` + `SessionManager`: `config.user_data_dir` is the root when its final component equals `profile_name`, otherwise `<user_data_dir>/<profile_name>`; empty derived base falls back to `./profiles` (PH-07 fix for path-mismatch edge case).
- Loaded `seeds.json` payloads are validated by `_valid_seed_dict()` (required keys + types); invalid files are regenerated with a warning instead of crashing launch (PH-07).
- Numeric seeds derive from `ProfileConfig.seed`; when it is `None`, a random 32-bit base seed is generated and persisted.
- Locale precedence is config → host locale → `en-US`; timezone precedence is config → tzlocal IANA name / `TZ` IANA value → `UTC`. PH-10: `"auto"` (case-insensitive) is treated as unset — it is a launch-time sentinel resolved by the engine, never persisted literally.
- `_detect_host_timezone()` imports `tzlocal.get_localzone_name` lazily; tzlocal maps Windows timezone names to IANA.
- `get_or_create_seeds()` writes through a temporary JSON file and `os.replace()`.
- Engine consumption is live: `StealthEngine.alaunch()` calls `get_or_create_seeds()` and forwards canvas/audio/fonts seeds plus Mode A `webrtc:ipv4` to Camoufox (PH-03/PH-04).

Known limitation: browserforge sampling consumes process-global `random` state; complete cross-instance fingerprint determinism is not guaranteed (documented in docs/FEATURES.md).

## Change History

| Version | Change                                                                       |
| ------- | ---------------------------------------------------------------------------- |
| 0.1.0   | BrowserForge fingerprint generation and hash API                             |
| PH-02   | Added persistent per-profile seed storage and host locale/timezone detection |
| PH-06   | Added `IdentityProvider` protocol, `BrowserForgeIdentityProvider`, and `provider` parameter on `IdentityGenerator` (Feature P) |
| PH-07   | Added `_profile_root()` path resolution, `_valid_seed_dict()` schema validation, and self-healing regeneration for invalid `seeds.json` |
| PH-17   | `launch_salt` parameter — `fingerprint_diversity` derives per-launch RNG from `sha256(seed:salt)`; device seeds in `seeds.json` remain profile-stable |
| PH-18   | `validate_fingerprint(fp)` — consistency scorer (required keys, viewport≤screen, UA↔platform↔OS coherence with aliases, IANA timezone, locale shape, sane ranges) → `{consistent, issues, score}` |

BF-03: `validate_fingerprint` infers OS from UA tokens when fp lacks `"os"` (real browserforge output) — coherence check no longer dead code. `_derive_timezone` normalises locale case and adds bare-language fallbacks (`_LANG_TZ`).
