# 01 — BROWSER ENGINE COMPARISON (research)

Question: which browser runtime/engine for control + automation?

## Candidates evaluated

| Engine | Anti-detect | Automation API | Maintenance | Verdict |
|---|---|---|---|---|
| **camoufox + playwright** (current) | C++-level, Firefox-based, per-identity fingerprint gen | Playwright sync+async, full API | Active (daijro/camoufox) | ✅ BEST |
| patchright | Patched playwright, Chromium | Same playwright API | Active | Chromium; weaker fp depth than camoufox |
| nodriver | Undetected chromedriver | Custom async API | Moderate | Chrome-only; maintenance-heavy |
| rebrowser-playwright | Patched playwright | Playwright API | Active | Comparable tier below camoufox |
| selenium | None native | WebDriver | Stable | Detectable — unacceptable for stealth |
| puppeteer | CDP detectable | Good | Stable | Same problem |
| playwright (vanilla) | None | Best | Stable | No fingerprint layer |

## Key reasoning

1. **Anti-detect depth**: camoufox spoofs at C++ engine level
   (navigator/screen/WebGL/canvas/fonts/media devices) — JS-level patches
   are detectable; camoufox is not.
2. **API quality**: playwright is the best Python automation API
   (async+sync, auto-wait, routing, HAR, video, tracing, CDP access).
3. **Fingerprint coherence**: camoufox generates coherent per-identity
   fingerprints (UA↔screen↔GPU↔fonts↔voices↔media devices) — other tools
   patch values independently → inconsistency = detection.
4. **Replacement = downgrade**: any switch loses C++-level coverage.
5. **Residual surface is identical across engines**: TLS/JA3/JA4 and
   HTTP/2 fingerprints are browser-controlled regardless of wrapper;
   JS-patch engines can't fix that either.

## Conclusion

Keep **camoufox + playwright**. Investment should go into *depth*
(CDP access, recording, verification, multi-context) not engine swap.
Optional future: `BrowserBackend` adapter protocol ONLY if a second
engine is ever needed — premature now (YAGNI).
