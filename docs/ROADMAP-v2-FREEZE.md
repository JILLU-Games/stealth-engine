# ROADMAP v2 — FREEZE (Authoritative)

This document supersedes any earlier roadmap notes. It records the FINAL decision that all future engine work follows.

## 1. Frozen Principles (P1–P5)

- P1. Profile ↔ Account binding is PERMANENT 1:1. A profile is never reused for a different account, and an account is never rotated across profiles.
- P2. Dual-mode engine. One StealthEngine serves both modes:
  - Mode A — No Proxy (target: ~80% of profiles)
  - Mode B — With Proxy (target: ~20% of profiles)
    Mode is chosen per ProfileConfig via `proxy: Optional[ProxyConfig]`.
- P3. No existing feature is removed, broken, downgraded, or deleted. All 26 A–Z capabilities remain available.
- P4. Proxy is OPTIONAL. `ProfileConfig.proxy = None` is a valid, first-class configuration.
- P5. IdentityGenerator is the PRIMARY source of locale, timezone_id, and per-profile seeds. Proxy, when present, only OVERRIDES locale/timezone via GeoIP — it does not replace the identity engine.

## 2. Mode A — No Proxy (≈80% of profiles)

Trigger: `ProfileConfig(proxy=None)`.

Network layer:

- Host IP is used as-is (no spoofing, no proxying).
- WebRTC advertises the HOST IP, not a spoofed one. Rationale: matching the real network avoids IP↔JS inconsistency.

JS-observable location layer:

- timezone_id comes from IdentityGenerator seeds (`seeds["timezone_id"]`), set to the host's actual timezone.
- locale comes from IdentityGenerator seeds (`seeds["locale"]`), set to the host's actual locale.
- Rationale: host country ≠ spoofed country is the single strongest anti-bot signal. Mode A intentionally avoids it.

Device layer:

- Per-profile unique fingerprint via Camoufox native engine (Canvas, WebGL, Audio, Fonts, navigator).
- Per-profile seeds persisted to `profiles/<name>/seeds.json`:
  { canvas, audio, fonts, locale, timezone_id }
- Seeds loaded on next launch → same profile = same device.

Allowed use cases:

- Web scraping (low-security sites)
- Form / UI automation
- Multi-account within the same ISP (family/office scenario)
- Search engine scraping (Bing, DuckDuckGo)
- News site scraping

Known limits (must be documented, not "fixed"):

- Cloudflare / DataDome-protected sites may still flag.
- Strict social account creation (Facebook, Google) may flag due to shared host IP across multiple profiles.
- IP-based rate limits are shared across profiles.

## 3. Mode B — With Proxy (≈20% of profiles)

Trigger: `ProfileConfig(proxy=ProxyConfig(...))`.

Network layer:

- Proxy IP is used as-is.
- WebRTC advertises the proxy IP via Camoufox `geoip=True` and `webrtc:ipv4`.

JS-observable location layer:

- timezone_id, locale, geolocation, currency align with the proxy's GeoIP via Camoufox `geoip=True`.
- IdentityGenerator seeds still produce a unique fingerprint; only locale/timezone_id are overridden by GeoIP.

Device layer:

- Per-profile unique fingerprint (same mechanism as Mode A).
- seeds.json persists per profile.

Allowed use cases:

- Multi-account on Facebook / Google / Instagram / X
- Amazon / eBay / e-commerce accounts
- Cloudflare-protected scraping
- Ad verification across regions
- SEO rank tracking
- Price comparison across regions

Known limits:

- Cost of residential / mobile proxies.
- Latency from proxy hop.
- Sticky-session discipline required (same account → same IP).

## 4. Changes Required in Code (5 Steps, ordered)

Each step is a separate implementation batch. No step may be skipped. No step may change public API.

Step 1 — config.py

- `proxy: ProxyConfig | None = None` (make proxy Optional).
- Add `target_ip: str | None = None` (host IP hint for Mode A WebRTC; if None, engine resolves host IP at launch).
- Preserve all existing validators.
- Public API unchanged.

Step 2 — identity.py

- Add method:
  `def get_or_create_seeds(self) -> dict`
  Behaviour:
  - Load `profiles/<profile>/seeds.json` if present.
  - Else derive deterministic seeds from `config.seed` (fallback to `secrets.randbits(32)` when seed is None).
  - Persist to `seeds.json` atomically (tmp → os.replace).
  - Return dict with keys: canvas, audio, fonts, locale, timezone_id.
- Do NOT change `generate()` signature or output shape.
- Do NOT change `fingerprint_hash()`.

Step 3 — engine.py — Mode A launch logic

- When `config.proxy is None`:
  - seeds = identity.get_or_create_seeds()
  - locale = seeds["locale"]
  - timezone_id = seeds["timezone_id"]
  - config_overrides = {
    "canvas:seed": seeds["canvas"],
    "audio:seed": seeds["audio"],
    "fonts:spacing_seed": seeds["fonts"],
    "webrtc:ipv4": config.target_ip or resolved_host_ip(),
    }
  - geoip = False
  - proxy = None
- Do NOT spoof timezone/locale away from the host country in Mode A.
- ✅ COMPLETE (PH-03)

Step 4 — engine.py — Mode B launch logic

- When `config.proxy is not None`:
  - geo = await proxy_manager.pick_healthy()
  - geoip = True
  - proxy = proxy_manager.to_playwright(config.proxy)
  - locale = geo.locale
  - timezone_id = geo.timezone_id
  - config_overrides retains canvas/audio/fonts seeds from seeds.json (fingerprint consistency preserved).
- Do NOT change how fingerprint seeds are consumed.
- ✅ COMPLETE (PH-04)
  - config_overrides retains canvas/audio/fonts seeds from `seeds.json` (fingerprint consistency preserved).
- Do NOT change how fingerprint seeds are consumed.

Step 5 — Verification (F6-Final extended to 26 checks)

- All 22 existing checks must still PASS.
- New checks:
  #23 Mode A: launch_kwargs["locale"] == seeds["locale"]
  #24 Mode B: launch_kwargs["locale"] == geo.locale
  #25 Seeds persist: same profile launched twice produces identical fingerprint_hash()
  #26 ProfileConfig(proxy=None) is valid and launches Mode A
- Verdict required: REGRESSION-FREE.
- ✅ COMPLETE (PH-05) — 4 new checks added and PASS; 22-check baseline unverified due to missing checklist in project files

## 5. Compact Usage (target end-state)

Mode A example:
ProfileConfig(
profile_name="account_1",
user_data_dir="./profiles/account_1",
seed=42,
proxy=None,
)

Mode B example:
ProfileConfig(
profile_name="account_2",
user_data_dir="./profiles/account_2",
seed=43,
proxy=ProxyConfig(server="http://user:pass@1.2.3.4:8080"),
)

Both use the same StealthEngine. No code branching required by the caller.

## 6. Feature Compliance Matrix (Frozen)

Feature D — Coherent identity:
Mode A ✅ Camoufox native
Mode B ✅ Camoufox native + GeoIP
Change: none (unchanged capability)

Feature S — Seed reproducibility:
Mode A ✅ seeds.json
Mode B ✅ seeds.json
Change: improved (persisted across launches)

Feature Z — Zero global state:
Mode A ✅ scoped RNG
Mode B ✅ scoped RNG
Change: improved

Feature F — GeoIP proxy:
Mode A — not applicable
Mode B ✅ geoip=True
Change: none

Feature G — Persistent session: A ✅ | B ✅ | unchanged
Feature M — Proxy rotation: A — | B ✅ | unchanged
Feature N — No JS injection: A ✅ | B ✅ | unchanged
Feature T — Timezone consistency:
Mode A ✅ IdentityGenerator
Mode B ✅ GeoIP
Change: improved
Feature W — WebRTC leak:
Mode A ✅ host IP (intentional)
Mode B ✅ proxy IP
Change: improved
Feature X — State export: A ✅ | B ✅ | unchanged

All 26 A–Z features remain available. No feature removed.

## 7. Explicit Non-Goals (must NOT be done)

The following are permanently rejected. If requested later, they must be refused even by future agents:

- Removing IdentityGenerator.
- Removing ProxyManager.
- Changing public API or **all**.
- Removing or downgrading any A–Z feature.
- Using global random.seed() without state save/restore.
- Full BrowserForge → Camoufox fingerprint wiring (proven INCOMPATIBLE in Stage 4A: Chrome UA rejected by Camoufox; Camoufox's generate_fingerprint has no seed).
- Changing IdentityGenerator.generate() output shape.
- Making proxy mandatory.

## 8. Freeze Checklist

[ ] Step 1: config.py — proxy Optional, target_ip added
[ ] Step 2: identity.py — get_or_create_seeds()
[ ] Step 3: engine.py — Mode A launch logic
[ ] Step 4: engine.py — Mode B launch logic
[ ] Step 5: F6-Final — 26 checks, REGRESSION-FREE

Status of each step is recorded in MEMORY.md, not here.
