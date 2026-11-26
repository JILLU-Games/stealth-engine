# Module: config.py

**File:** `stealth_engine/config.py`
**Status:** ✅ Implemented (v0.1.0)
**Public names:** `ProxyConfig`, `ProfileConfig`

## Purpose

Defines all profile and proxy configuration as Pydantic v2 models, plus atomic JSON/YAML file serialisation (Feature Y).

## Models

### ProxyConfig

| Field    | Type        | Default  | Description                        |
| -------- | ----------- | -------- | ---------------------------------- |
| server   | str         | required | Full proxy URL (http/https/socks5/socks5h/socks4) |
| username | str \| None | None     | Auth username                      |
| password | str \| None | None     | Auth password                      |

### ProfileConfig

| Field          | Type                         | Default  | Description                                                       |
| -------------- | ---------------------------- | -------- | ----------------------------------------------------------------- |
| profile_name   | str                          | required | Unique profile identifier                                         |
| os             | Literal[windows,macos,linux] | windows  | OS persona for fingerprint                                        |
| user_data_dir  | str                          | required | Isolated browser profile path                                     |
| proxy          | ProxyConfig \| None          | None     | Proxy settings                                                    |
| target_ip      | str \| None                  | None     | Optional host IP hint for Mode A WebRTC; consumed by engine launch (PH-03) |
| geoip          | bool                         | True     | Derive locale/timezone from proxy GeoIP                           |
| seed           | int \| None                  | None     | Deterministic identity seed                                       |
| headless       | bool                         | True     | Headless browser mode                                             |
| locale         | str \| None                  | None     | BCP-47 locale override; `"auto"` = derive from GeoIP at launch (PH-10) |
| timezone       | str \| None                  | None     | IANA timezone override; `"auto"` = derive from GeoIP at launch (PH-10) |
| disable_ipv6   | bool                        | False    | Set `network.dns.disableIPv6` Firefox pref — prevents IPv6 leaks (PH-13) |
| hardware_concurrency | int \| None               | None     | `navigator.hardwareConcurrency` override → camoufox `config` (PH-14)      |
| webgl_config   | tuple[str, str] \| None    | None     | `(vendor, renderer)` → camoufox `webgl_config`; requires `os` set (PH-14) |
| fonts          | list[str] \| None         | None     | Explicit font list → camoufox `fonts` (PH-14)                            |
| custom_fonts_only | bool                   | False    | Restrict rendering to `fonts` list only (PH-14)                           |
| screen_bounds  | tuple[int,int,int,int] \| None | None | `(min_w,max_w,min_h,max_h)` → camoufox `Screen` bounds (PH-14)           |
| fingerprint_diversity | bool                  | False    | Per-launch identity salt — different fingerprint each launch, loses seed reproducibility (PH-17) |
| record_har_path | str \| None              | None     | HAR recording path; relative resolves under profile dir (PH-19)              |
| record_har_content | str \| None           | None     | HAR content mode: omit/embed/attach (PH-19)                                  |
| record_video_dir | str \| None             | None     | Video recording dir; relative resolves under profile dir (PH-19)             |
| js_noise | bool                        | False    | Experimental JS canvas/WebGL readback noise via init script — detectable-risk trade-off (PH-20) |
| seed_localstorage | bool                     | False    | Seed plausible localStorage keys per origin via init script (PH-16)       |
| proxy_remote_dns | bool                      | True     | SOCKS proxies: set `network.proxy.socks_remote_dns` — DNS via proxy (PH-13) |
| extra_headers  | dict[str,str]                | {}       | Extra HTTP headers                                                |
| log_level      | str                          | INFO     | Loguru log level                                                  |
| schema_version | str                          | 1        | Config schema version                                             |

## Validators

- `profile_name`, `user_data_dir`: strip whitespace, reject empty
- `server`: must start with `http://`, `https://`, `socks5://`, `socks5h://`, or `socks4://`. `socks5h://` is normalised to `socks5://` at validation (PH-13 — downstream Playwright/aiohttp only understand `socks5`).
- `seed`: must be >= 0 if provided
- `extra_headers`: keys must be non-empty strings; values must be strings

## Methods

- `to_public_dict()`: returns the model dict with URL-embedded and explicit proxy credentials removed from the server URL and replaced by `"***"`
- `save_json(path)` / `load_json(path)`: atomic pretty-printed JSON write; classmethod load via `model_validate_json` (Feature Y)
- `save_yaml(path)` / `load_yaml(path)`: atomic sorted-key YAML write via `yaml.safe_dump`; classmethod load via `yaml.safe_load` + `model_validate` (Feature Y; PyYAML imported lazily)
- `ProfileConfig.preset(name, **overrides)` classmethod + `preset_names()` (PH-18, N7): built-in presets `us-desktop`, `eu-desktop`, `mobile-android`; unknown name → `ConfigError`

## Change History

| Version | Change                                                              |
| ------- | ------------------------------------------------------------------- |
| 0.1.0   | Initial implementation                                              |
| 0.1.0   | Redact credentials embedded in proxy server URLs                    |
| PH-06   | Added `save_json`/`load_json`/`save_yaml`/`load_yaml` (Feature Y)   |
| PH-18   | Added `preset()` classmethod + `preset_names()` (N7)                |

## SDK-LIFECYCLE-01 (candidate; CI pending)

Optional `StealthEngine(config, on_close=..., on_error=...)` callbacks run on the owning asyncio loop, accept sync or async callables, and are isolated from cleanup. `on_close(profile_name)` runs once after cleanup attempts; `on_error(profile_name, exception)` reports launch/cleanup errors. Dispatch GUI updates to the GUI thread as appropriate. The context-close notification is post-close: final storage capture is best effort and the previous export is retained on capture failure. Explicit close saves before closing. Session lock/disk operations and lazy behavior-profile loading are offloaded; this does not claim all engine work is nonblocking. `auto_resolve_host_ip=True` preserves the original lookup; false skips only that lookup when no explicit target is provided. `restore_state=False` preserves native persistent storage. True loads only the same profile snapshot and uses the supported Playwright context API (1.59+); this replaces storage, not a merge. No existing public methods or test suites removed.
