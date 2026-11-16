# 02 — FEATURE VERIFICATION MATRIX

Legend: ✅ real-browser verified · 🧪 unit-tested only · ⚠️ partial ·
❌ broken · 🚫 documented-unavailable

| Feature | Status | Evidence |
|---|---|---|
| `StealthEngine.alaunch()` | ❌→✅* | fails on bad kwargs (B-27); works with corrected kwargs |
| `launch()` sync | ❌→✅* | same path via asyncio.run |
| `session.page` / `new_page_async` | ✅ | real page object returned |
| `new_page()` sync | 🚫 by design | raises AutomationError → use async |
| `save_state_async` / aclose persist | ✅ | storage_state.json written on real close |
| `save_state()` sync | 🚫 by design | raises AutomationError |
| `probe_fingerprint` | ✅ | real UA/viewport/hw values returned |
| `verify_stealth` | ✅ | consistent=True, risk=5/100 on real session |
| `ban_risk_score` | 🧪 | unit-tested; consumed by verify_stealth |
| `validate_fingerprint` | 🧪 | unit-tested incl. OS inference |
| `validate_geo_consistency` | 🧪 | unit-tested |
| `new_context` (multi-context) | ✅ | real second context created + closed |
| `cdp_session` | 🚫 | Firefox/Juggler — no CDP; graceful error |
| `human_move/type/scroll/dwell` (sync) | ❌ | unawaited coroutines — B-25 |
| `ahuman_move/type/scroll` + `adwell` | 🧪 | code correct; not run on live page |
| `warmup` + templates | 🧪 | uses ahuman_* correctly; not run live |
| `block_trackers` / `add_route` / `add_listener` | 🧪 | route API correct; not run live |
| `fetch_headers` | 🧪 | `await ctx.request.get` correct |
| `expect_download` / `attach_file` | 🧪 | timeout ms correct for pl
