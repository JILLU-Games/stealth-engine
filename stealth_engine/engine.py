"""Core stealth browser engine lifecycle management."""

from __future__ import annotations

import asyncio
import ipaddress
import os
import random
import socket
import time
import types
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from .behavior import BehaviorProfile, bezier_path, dwell_plan
from .config import ProfileConfig
from .exceptions import (
    AutomationError,
    LaunchError,
    ProxyError,
    StealthEngineError,
)
from .geo import GeoResolver
from .identity import IdentityGenerator, IdentityProvider
from .proxy import GeoInfo, ProxyManager
from .session import SessionManager
from .utils.logging import get_logger, get_profile_logger

_log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Type aliases — avoids importing playwright/camoufox at type-check time.
# ---------------------------------------------------------------------------
PlaywrightPage = Any
PlaywrightBrowserContext = Any


def _localstorage_init_script(seed: int | None) -> str:
    """Build a JS init script seeding plausible localStorage keys (PH-16).

    Keys are deterministic per ``seed`` so the same profile presents the
    same storage fingerprint on every origin.  Values are innocuous
    preference-style keys — nothing that could conflict with real sites.

    Args:
        seed: ``ProfileConfig.seed`` (``None`` → derived from id entropy).

    Returns:
        JavaScript source for ``context.add_init_script``.
    """
    import hashlib

    token = hashlib.sha256(f"sp-ls-{seed}".encode()).hexdigest()[:16]
    theme = ["light", "dark", "system"][seed % 3] if seed is not None else "system"
    return (
        "(() => {"
        "try {"
        f"localStorage.setItem('_sp_id','{token}');"
        f"localStorage.setItem('sp_theme','{theme}');"
        f"localStorage.setItem('sp_ver','{seed if seed is not None else 0}');"
        "localStorage.setItem('sp_ts', String(Date.now()));"
        "} catch (e) {}"
        "})();"
    )


def _js_noise_init_script(seed: int | None) -> str:
    """Build a JS init script adding deterministic canvas/WebGL noise (PH-20, G1).

    Patches ``toDataURL``, ``getImageData`` (2d context), and ``readPixels``
    (WebGL) to perturb a deterministic subset of pixels using a mulberry32
    PRNG seeded from ``seed`` — same profile, same noise pattern every
    launch.  **Experimental:** JS-level patching is detectable by
    sophisticated probes; camoufox provides no canvas noise natively.

    Args:
        seed: ``ProfileConfig.seed``.

    Returns:
        JavaScript source for ``context.add_init_script``.
    """
    import hashlib

    s = int(hashlib.sha256(f"jsn-{seed}".encode()).hexdigest()[:8], 16)
    return f"""
(() => {{
  const _seed = {s} | 0;
  // A real Camoufox/Firefox native canvas export can advance its internal
  // noise stream even when pixel content is unchanged. Cache 2D exports
  // between writes, rather than treating JS-only _perturb as sufficient.
  const _serializations = new WeakMap();
  const _imageReads = new WeakMap();
  const _versions = new WeakMap();
  const _invalidate = canvas => {{
    _versions.set(canvas, (_versions.get(canvas) || 0) + 1);
    _serializations.delete(canvas);
    _imageReads.delete(canvas);
  }};
  const _perturb = (data, step) => {{
    // F-16: reset the seeded stream for each readback. Identical pixels
    // yield identical output even when other canvas/WebGL reads intervene.
    let state = _seed;
    const rnd = () => {{
      state = state + 0x6D2B79F5 | 0;
      let t = Math.imul(state ^ state >>> 15, 1 | state);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    }};
    for (let i = 0; i < data.length; i += step * 4) {{
      const jitter = (rnd() < 0.5 ? -1 : 1) * (rnd() * 3 | 0);
      data[i] = Math.max(0, Math.min(255, data[i] + jitter));
    }}
  }};
  try {{
    // Increment generation whenever 2D pixels are written. This preserves
    // distinct exports after drawing while keeping consecutive unchanged
    // reads stable. HTML canvas dimensions reset pixels even at equal size.
    const proto = CanvasRenderingContext2D.prototype;
    for (const method of ['fillRect', 'strokeRect', 'clearRect', 'drawImage',
                          'putImageData', 'fillText', 'strokeText', 'fill',
                          'stroke', 'reset']) {{
      const original = proto[method];
      if (typeof original !== 'function') continue;
      proto[method] = function (...args) {{
        const result = original.apply(this, args);
        try {{ _invalidate(this.canvas); }} catch (e) {{}}
        return result;
      }};
    }}
    for (const dim of ['width', 'height']) {{
      try {{
        const descriptor = Object.getOwnPropertyDescriptor(HTMLCanvasElement.prototype, dim);
        if (descriptor && descriptor.get && descriptor.set && descriptor.configurable) {{
          Object.defineProperty(HTMLCanvasElement.prototype, dim, {{
            configurable: true,
            enumerable: descriptor.enumerable,
            get() {{ return descriptor.get.call(this); }},
            set(value) {{
              const result = descriptor.set.call(this, value);
              _invalidate(this);
              return result;
            }}
          }});
        }}
      }} catch (e) {{}}
    }}
    const _td = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function (...a) {{
      try {{
        const cx = this.getContext('2d');
        if (cx && this.width * this.height < 4000000) {{
          const key = [this.width, this.height, a[0] || '', a[1] || ''].join(':');
          const version = _versions.get(this) || 0;
          const cached = _serializations.get(this);
          if (cached && cached.key === key && cached.version === version) {{
            return cached.result;
          }}
          // BF-02/B-06: render to an OFFSCREEN clone — never mutate the
          // live canvas (putImageData would alter real pixels).
          const tmp = document.createElement('canvas');
          tmp.width = this.width; tmp.height = this.height;
          const tctx = tmp.getContext('2d');
          tctx.drawImage(this, 0, 0);
          const d = tctx.getImageData(0, 0, tmp.width, tmp.height);
          _perturb(d.data, 7);
          tctx.putImageData(d, 0, 0);
          const result = _td.apply(tmp, a);
          _serializations.set(this, {{ key, version, result }});
          return result;
        }}
      }} catch (e) {{}}
      return _td.apply(this, a);
    }};
    const _gid = CanvasRenderingContext2D.prototype.getImageData;
    CanvasRenderingContext2D.prototype.getImageData = function (...a) {{
      const d = _gid.apply(this, a);
      try {{
        const canvas = this.canvas;
        const version = _versions.get(canvas) || 0;
        const key = JSON.stringify(a);
        let frame = _imageReads.get(canvas);
        if (!frame || frame.version !== version) {{
          frame = {{ version, reads: new Map() }};
          _imageReads.set(canvas, frame);
        }}
        const previous = frame.reads.get(key);
        if (previous && previous.length === d.data.length) {{
          // Native Camoufox can vary pixels across successive reads on
          // some Linux builds. Return the same *independent* ImageData bytes
          // until the live canvas is actually changed.
          d.data.set(previous);
        }} else {{
          _perturb(d.data, 7);
          // Keep the per-canvas cache bounded for tiled image readers.
          if (frame.reads.size >= 16) {{
            frame.reads.delete(frame.reads.keys().next().value);
          }}
          frame.reads.set(key, new Uint8ClampedArray(d.data));
        }}
      }} catch (e) {{}}
      return d;
    }};
    const _rp = WebGLRenderingContext.prototype.readPixels;
    WebGLRenderingContext.prototype.readPixels = function (...a) {{
      _rp.apply(this, a);
      try {{
        const px = a[a.length - 1];
        if (px && px.length) _perturb(px, 11);
      }} catch (e) {{}}
    }};
    // BF-03/B-13: WebGL2 shares the same readPixels signature.
    if (typeof WebGL2RenderingContext !== 'undefined') {{
      const _rp2 = WebGL2RenderingContext.prototype.readPixels;
      WebGL2RenderingContext.prototype.readPixels = function (...a) {{
        _rp2.apply(this, a);
        try {{
          const px = a[a.length - 1];
          if (px && px.length) _perturb(px, 11);
        }} catch (e) {{}}
      }};
    }}
  }} catch (e) {{}}
}})();
"""


# Warmup flow presets (PH-20, G3).
_WARMUP_TEMPLATES: dict[str, dict[str, Any]] = {
    "default": {"scrolls": 2, "dwell_s": (1.5, 4.0)},
    "social": {"scrolls": 4, "dwell_s": (3.0, 8.0)},
    "commerce": {"scrolls": 3, "dwell_s": (2.0, 6.0)},
    "search": {"scrolls": 1, "dwell_s": (0.8, 2.0)},
}

# Common tracker/analytics domains aborted by block_trackers (PH-20, G2).
_TRACKER_DOMAINS: tuple[str, ...] = (
    "google-analytics.com", "googletagmanager.com", "googleadservices.com",
    "doubleclick.net", "facebook.net", "connect.facebook.net",
    "analytics.twitter.com", "ads-twitter.com", "bat.bing.com",
    "snap.licdn.com", "px.ads.linkedin.com", "hotjar.com", "hotjar.io",
    "segment.io", "segment.com", "mixpanel.com", "amplitude.com",
    "scorecardresearch.com", "quantserve.com", "criteo.com", "outbrain.com",
    "taboola.com", "scorecardresearch.com",
)


class StealthEngine:
    """Factory for stealth browser sessions.

    Wires together identity generation, session management, and proxy
    resolution, then launches a camoufox browser context via the sync or
    async API.  Each instance is fully independent and shares no state
    with other instances.

    Args:
        config: Validated profile configuration.
        identity_provider: Optional custom
            :class:`~stealth_engine.identity.IdentityProvider` used for
            fingerprint generation. ``None`` selects the default
            browserforge-backed provider.
    """

    def __init__(
        self,
        config: ProfileConfig,
        *,
        identity_provider: IdentityProvider | None = None,
    ) -> None:
        """Store configuration and instantiate sub-components.

        Does **not** launch a browser, make network calls, or touch the
        filesystem.  All heavy work is deferred to :meth:`launch` /
        :meth:`alaunch`.

        Args:
            config: Validated profile configuration.
            identity_provider: Optional custom
                :class:`~stealth_engine.identity.IdentityProvider`.
                ``None`` uses the default browserforge-backed provider.
        """
        self._config: ProfileConfig = config
        # A profile-local severity gate affects only engine-owned log records;
        # it does not reconfigure global loguru handlers for other profiles.
        secret_values: list[str] = []
        if config.proxy is not None:
            from .config import _split_proxy_credentials
            _, embedded_user, embedded_password = _split_proxy_credentials(config.proxy.server)
            secret_values.extend(v for v in (embedded_password, config.proxy.password) if v)
        self._profile_log = get_profile_logger(
            __name__, config.profile_name, config.log_level, secrets=tuple(secret_values)
        )
        _base = self._derive_base_dir(config)
        self._session: SessionManager = SessionManager(
            config, base_dir=_base
        )
        # PH-17: optional per-launch identity diversity.
        launch_salt: str | None = None
        if config.fingerprint_diversity:
            import uuid

            launch_salt = uuid.uuid4().hex
        self._launch_salt: str | None = launch_salt
        self._identity: IdentityGenerator = IdentityGenerator(
            config, provider=identity_provider, launch_salt=launch_salt
        )
        self._proxy_manager: ProxyManager | None = (
            ProxyManager([config.proxy], seed=config.seed)
            if config.proxy is not None
            else None
        )

    # ------------------------------------------------------------------
    # Public launch methods
    # ------------------------------------------------------------------

    def launch(self) -> "BrowserSession":
        """Launch a stealth browser session synchronously.

        Keeps a dedicated background asyncio event loop alive for the
        session lifetime, so async Camoufox resources are not bound to a
        prematurely closed loop.  Call :meth:`BrowserSession.close` to
        close both the session and its owned loop.  Async Playwright page
        operations remain async; sync session helpers remain unsupported.
        Calls within an already-running event loop must use ``alaunch``.

        Returns:
            A ready :class:`BrowserSession` instance.

        Raises:
            LaunchError: If a running event loop is detected, or if the
                launch sequence fails at any step.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None and loop.is_running():
            raise LaunchError(
                "Cannot call launch() from a running event loop. "
                "Use 'await engine.alaunch()' instead.",
                details={"stage": "launch", "reason": "running event loop detected"},
            )

        # A live async browser cannot survive asyncio.run(): that helper
        # closes its loop before returning the session (F-01).  Keep one
        # owned loop running until BrowserSession.close()/aclose().
        import threading

        worker_loop = asyncio.new_event_loop()
        ready = threading.Event()

        def _loop_worker() -> None:
            asyncio.set_event_loop(worker_loop)
            ready.set()
            try:
                worker_loop.run_forever()
            finally:
                try:
                    worker_loop.run_until_complete(worker_loop.shutdown_asyncgens())
                    worker_loop.run_until_complete(worker_loop.shutdown_default_executor())
                finally:
                    worker_loop.close()
                    asyncio.set_event_loop(None)

        worker = threading.Thread(
            target=_loop_worker,
            name="stealth-engine-sync-session",
            daemon=True,
        )
        try:
            worker.start()
            ready.wait()
            result = asyncio.run_coroutine_threadsafe(self.alaunch(), worker_loop).result()
        except BaseException:
            if worker.is_alive():
                worker_loop.call_soon_threadsafe(worker_loop.stop)
                worker.join()
            else:
                worker_loop.close()
            raise

        result._sync_loop = worker_loop
        result._sync_thread = worker
        return result

    async def alaunch(self) -> "BrowserSession":
        """Launch a stealth browser session asynchronously.

        Executes the mandatory launch sequence in order:

        a. ``session.ensure_dirs()``
        b. ``session.acquire_lock()``
        c. ``fp = identity.generate()``
        d. proxy resolution (if a proxy is configured)
        e. GeoIP overrides applied to fingerprint
        f. camoufox launch
        g. storage state import (if previous state exists)
        h. return :class:`BrowserSession`

        On any failure the lock is released, the proxy session is closed,
        and a :class:`LaunchError` is raised (unless the originating
        exception is already a :class:`StealthEngineError`, in which case
        it propagates unchanged).

        Returns:
            A ready :class:`BrowserSession` instance.

        Raises:
            LaunchError: If camoufox fails to start.
            StealthEngineError: Subclass exceptions from identity / proxy /
                session modules propagate unchanged.
        """
        cfg = self._config
        session = self._session
        ctx_handle: Any = None  # camoufox context manager handle
        stage = "init"

        try:
            # a) ensure dirs
            stage = "ensure_dirs"
            session.ensure_dirs()

            # b) acquire lock
            stage = "acquire_lock"
            session.acquire_lock()

            # c) Load or create persistent seeds (PH-02/PH-03/PH-04)
            stage = "identity.get_or_create_seeds"
            seeds = self._identity.get_or_create_seeds()

            # d) generate fingerprint (lazy — cached after first call)
            stage = "identity.generate"
            fp: dict[str, Any] = self._identity.generate()
            # Work on a mutable copy — do not mutate the cached fingerprint.
            fp = dict(fp)

            # e) proxy resolution
            stage = "proxy.pick_healthy"
            proxy_cfg = None
            geo: GeoInfo | None = None
            if self._proxy_manager is not None:
                proxy_cfg, geo = await self._proxy_manager.pick_healthy()

            # f) locale/timezone resolution
            auto_locale = (
                isinstance(cfg.locale, str)
                and cfg.locale.strip().lower() == "auto"
            )
            auto_tz = (
                isinstance(cfg.timezone, str)
                and cfg.timezone.strip().lower() == "auto"
            )

            # g) GeoIP overrides (PH-04)
            if geo is not None and cfg.geoip:
                fp["timezone_id"] = geo.timezone_id
                fp["locale"] = geo.locale
            else:
                # Mode A: use seeds for locale/timezone (PH-03)
                fp["timezone_id"] = seeds["timezone_id"]
                fp["locale"] = seeds["locale"]

            # h) "auto" sentinel (PH-10): explicitly derive locale/timezone
            #    from GeoIP.  Uses the proxy's GeoInfo when available
            #    (regardless of the geoip gate — "auto" is an explicit opt-in),
            #    otherwise resolves the host IP via GeoResolver.
            if auto_locale or auto_tz:
                auto_geo = geo
                if auto_geo is None:
                    auto_geo = await self._resolve_host_geo()
                if auto_geo is not None:
                    if auto_locale:
                        fp["locale"] = auto_geo.locale
                    if auto_tz:
                        fp["timezone_id"] = auto_geo.timezone_id

            # i) Build camoufox launch kwargs
            stage = "camoufox.launch"
            launch_kwargs = self._build_launch_kwargs(
                fp,
                proxy_cfg,
                seeds=seeds,
            )

            # j) Import existing storage state path if present.
            #    With persistent_context + user_data_dir, camoufox/playwright
            #    reads cookies/storage from user_data_dir automatically.
            #    We still export state on close via context.storage_state().

            # Launch camoufox asynchronously.
            try:
                from camoufox.async_api import AsyncCamoufox  # type: ignore[import]
            except ImportError as exc:
                raise LaunchError(
                    "camoufox is not installed; run: pip install 'camoufox[geoip]'",
                    details={"stage": stage, "reason": str(exc)},
                ) from exc

            ctx_handle = AsyncCamoufox(**launch_kwargs)
            playwright_ctx: PlaywrightBrowserContext = await ctx_handle.__aenter__()

            # PH-16: optional seeded localStorage so origins don't see
            # completely empty storage (a common bot signal).
            if cfg.seed_localstorage:
                await playwright_ctx.add_init_script(
                    _localstorage_init_script(cfg.seed)
                )

            # PH-20 G1: opt-in experimental canvas/WebGL readback noise.
            if cfg.js_noise:
                await playwright_ctx.add_init_script(
                    _js_noise_init_script(cfg.seed)
                )

            # k) Wrap in BrowserSession and ensure an actual first Page.
            # Empty persistent contexts require awaiting new_page() (F-02).
            stage = "wrap"
            session_obj = BrowserSession(
                ctx=playwright_ctx,
                ctx_handle=ctx_handle,
                session=session,
                proxy_manager=self._proxy_manager,
                config=cfg,
            )
            stage = "initial_page"
            if session_obj.page is None:
                await session_obj.new_page_async()

            # Fingerprint history is written only after a fully usable
            # session has been created; failed page setup is not a launch.
            self._record_fingerprint()

            # B-011: mask any credentials embedded in the server URL before logging.
            _proxy_log: str | None = None
            if proxy_cfg is not None:
                import re as _re
                _proxy_log = _re.sub(r"//[^@]*@", "//***@", proxy_cfg.server)
            self._profile_log.info(
                "stealth session launched",
                profile=cfg.profile_name,
                headless=cfg.headless,
                proxy=_proxy_log,
                fp_hash=self._identity.fingerprint_hash()[:12],
            )
            return session_obj

        except asyncio.CancelledError:
            # Cancellation is BaseException on supported Python versions;
            # release browser/proxy resources before propagating it.
            await self._emergency_cleanup(ctx_handle, session, self._proxy_manager)
            raise
        except StealthEngineError:
            # Preserve typed sub-exceptions from sub-modules unchanged.
            await self._emergency_cleanup(ctx_handle, session, self._proxy_manager)
            raise
        except Exception as exc:
            await self._emergency_cleanup(ctx_handle, session, self._proxy_manager)
            raise LaunchError(
                f"camoufox launch failed at stage={stage!r}: {exc}",
                details={"stage": stage, "reason": str(exc)},
            ) from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    _FP_HISTORY_FILE = "fingerprint_history.json"
    _FP_HISTORY_META_FILE = "fingerprint_history_meta.json"
    _FP_HISTORY_MAX = 50

    def _record_fingerprint(self) -> bool:
        """Record recent fingerprints without losing immutable first-seen age.

        Existing history remains a JSON list (max 50). On first migration,
        copy the original history to a one-time backup before writing an
        atomic, versioned first-seen metadata sidecar. A previous, already
        truncated history cannot reconstruct an earlier unknown timestamp.
        """
        try:
            import json as _json
            import math as _math
            import os as _os
            import time as _time
            from pathlib import Path

            fp_hash = self._identity.fingerprint_hash()
            path = Path(self._session.profile_dir) / self._FP_HISTORY_FILE
            meta_path = path.with_name(self._FP_HISTORY_META_FILE)
            history: list[dict[str, Any]] = []
            if path.exists():
                history = _json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(history, list) or any(not isinstance(h, dict) for h in history):
                    raise ValueError("invalid legacy fingerprint history; refusing to overwrite")

            now = round(_time.time(), 3)
            if meta_path.exists():
                metadata = _json.loads(meta_path.read_text(encoding="utf-8"))
                if not isinstance(metadata, dict) or metadata.get("schema_version") != 1:
                    raise ValueError("invalid first-seen metadata; refusing to overwrite")
                first_seen = float(metadata["first_seen_ts"])
                if not _math.isfinite(first_seen) or first_seen <= 0:
                    raise ValueError("invalid first-seen timestamp")
            else:
                # Legacy histories have no separate first-seen record; use
                # their oldest valid timestamp as the *known* lower bound.
                known = [float(h["ts"]) for h in history
                         if isinstance(h.get("ts"), (int, float))
                         and _math.isfinite(float(h["ts"])) and float(h["ts"]) > 0]
                first_seen = min(known) if known else now
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.exists():
                    backup = path.with_name("fingerprint_history.legacy.json.bak")
                    if not backup.exists():
                        with open(backup, "xb") as handle:
                            handle.write(path.read_bytes())
                            handle.flush()
                            _os.fsync(handle.fileno())
                metadata = {"schema_version": 1, "first_seen_ts": first_seen,
                            "origin": "legacy_oldest_known" if known else "first_record"}
                meta_tmp = meta_path.with_suffix(".json.tmp")
                meta_tmp.write_text(_json.dumps(metadata, indent=2), encoding="utf-8")
                _os.replace(meta_tmp, meta_path)

            drifted = bool(history) and history[-1].get("hash") != fp_hash
            if drifted and not self._config.fingerprint_diversity:
                _log.warning("fingerprint drift detected across launches",
                             profile=self._config.profile_name,
                             previous=str(history[-1].get("hash", ""))[:12],
                             current=fp_hash[:12])
            history.append({"ts": now, "hash": fp_hash,
                            "diversity": self._config.fingerprint_diversity})
            history = history[-self._FP_HISTORY_MAX:]
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(_json.dumps(history, indent=2), encoding="utf-8")
            _os.replace(tmp, path)
            return drifted
        except Exception as exc:
            _log.warning("fingerprint history write failed", reason=str(exc))
            return False

    @staticmethod
    def _resolve_host_ip() -> str:
        """Resolve the actual host IP address for WebRTC in Mode A.

        Uses a best-effort UDP route lookup and hostname fallback to find a
        *local interface* IPv4. Behind NAT this is NOT the public egress IP.
        _build_launch_kwargs() refuses non-global values and omits the manual
        WebRTC hint if no verified public IPv4 is available.

        Returns:
            The host IP address as a string (e.g. "203.0.113.10").

        Raises:
            LaunchError: If IP resolution fails for any reason.
        """
        try:
            # UDP connection to a public DNS server — no data sent, just routing.
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.settimeout(5)
                s.connect(("8.8.8.8", 53))
                host_ip = s.getsockname()[0]
            if host_ip:
                return host_ip
        except OSError:
            pass
        # BF-02/B-05: best-effort fallbacks — never kill the launch just
        # because the WebRTC IP hint couldn't be resolved.
        try:
            host_ip = socket.gethostbyname(socket.gethostname())
            if host_ip and host_ip != "127.0.0.1":
                _log.warning(
                    "host IP via UDP probe failed; using hostname resolution",
                    host_ip=host_ip,
                )
                return host_ip
        except OSError:
            pass
        _log.warning(
            "could not resolve host IP for WebRTC; using 0.0.0.0 "
            "(launch continues — camoufox may ignore the hint)"
        )
        return "0.0.0.0"

    async def _resolve_host_geo(self) -> "GeoInfo | None":
        """Resolve host-IP geolocation for the ``"auto"`` locale/timezone
        sentinel (PH-10).

        Returns:
            :class:`GeoInfo` for the host's public IP, or ``None`` when the
            geo endpoint is unreachable (launch continues with seed values).
        """
        resolver = GeoResolver(cache_ttl_s=0)
        try:
            return await resolver.resolve(None)
        except ProxyError as exc:
            _log.warning(
                "auto locale/timezone: host geo resolve failed; "
                "falling back to seeds: {}",
                exc,
            )
            return None
        finally:
            await resolver.aclose()

    def _derive_base_dir(self, config: ProfileConfig) -> str | None:
        """Derive the SessionManager base_dir from config.user_data_dir.

        ``config.user_data_dir`` is the **full profile-specific directory**
        (e.g. ``/data/myapp/account_1``).  ``SessionManager`` appends
        ``config.profile_name`` to whatever ``base_dir`` it receives, so
        this method must return the **parent** of ``config.user_data_dir``
        when the path already ends with ``profile_name``.

        Falls back to passing the path as-is (base-dir interpretation) when
        the final path component does not match ``profile_name``, and emits
        a WARNING so the caller is aware.

        Args:
            config: Validated profile configuration.

        Returns:
            The base directory string to pass to ``SessionManager``, or
            ``None`` to use ``SessionManager``'s default (``./profiles``).

        Raises:
            ConfigError: If ``config.user_data_dir`` strips to an empty
                string.
        """
        from .exceptions import ConfigError

        udd = config.user_data_dir.rstrip(os.sep) if config.user_data_dir else None
        if udd is None:
            return None  # SessionManager defaults to ./profiles
        if not udd:
            raise ConfigError(
                "user_data_dir is empty after stripping separators",
                details={"stage": "init", "user_data_dir": config.user_data_dir},
            )
        if os.path.basename(udd) != config.profile_name:
            _log.warning(
                "user_data_dir '%s' does not end with profile_name '%s'; "
                "treating it as the base directory. To get exact path "
                "control, set user_data_dir to '<parent>/%s'.",
                udd,
                config.profile_name,
                config.profile_name,
            )
            return udd  # legacy / base-dir interpretation
        return os.path.dirname(udd)  # normal case: strip the profile_name suffix

    def _build_launch_kwargs(
        self,
        fp: dict[str, Any],
        proxy_cfg: Any | None,
        seeds: dict[str, Any],
    ) -> dict[str, Any]:
        """Assemble keyword arguments for ``AsyncCamoufox`` / ``Camoufox``.

        Args:
            fp: Mutable fingerprint dict (post GeoIP overrides).
            proxy_cfg: Active :class:`~stealth_engine.config.ProxyConfig`
                or ``None``.
            seeds: Persistent seed dict from ``get_or_create_seeds()`` with
                keys canvas, audio, fonts, locale, timezone_id.

        Returns:
            Dict of keyword arguments ready to pass to camoufox.
        """
        cfg = self._config
        kwargs: dict[str, Any] = {
            "os": cfg.os,
            "headless": cfg.headless,
            "persistent_context": True,
            "user_data_dir": self._session.user_data_dir,
            "locale": fp.get("locale", "en-US"),
        }

        # PF-01/B-27: camoufox patch properties (seeds, webrtc IP,
        # hardwareConcurrency, timezone) are CONFIG-dict keys — they
        # must go inside ``config``, never as top-level kwargs (which
        # playwright's launch_persistent_context rejects with TypeError).
        # Verified against camoufox properties.json: canvas:seed,
        # audio:seed, fonts:spacing_seed, webrtc:ipv4, timezone and
        # navigator.hardwareConcurrency are all valid uint/str keys.
        launch_config: dict[str, Any] = {
            "canvas:seed": seeds["canvas"],
            "audio:seed": seeds["audio"],
            "fonts:spacing_seed": seeds["fonts"],
        }

        # Proxy + GeoIP.
        if proxy_cfg is not None and self._proxy_manager is not None:
            kwargs["proxy"] = self._proxy_manager.to_playwright(proxy_cfg)
            kwargs["geoip"] = cfg.geoip
            # Mode B: WebRTC advertises proxy IP via geoip=True
        else:
            kwargs["geoip"] = False
            # Mode A: never advertise an interface/LAN address as the
            # external WebRTC egress. An explicit target must be public IPv4;
            # the best-effort local host lookup is used only if globally routed.
            candidate = cfg.target_ip if cfg.target_ip else self._resolve_host_ip()
            try:
                public_ip = ipaddress.ip_address(candidate)
                valid_public_v4 = public_ip.version == 4 and public_ip.is_global
            except ValueError:
                valid_public_v4 = False
            if cfg.target_ip and not valid_public_v4:
                raise LaunchError(
                    "target_ip must be a globally routable IPv4 address for WebRTC",
                    details={"stage": "launch_options", "reason": "invalid_public_target_ip"},
                )
            if valid_public_v4:
                launch_config["webrtc:ipv4"] = str(public_ip)
            else:
                _log.warning("WebRTC public egress IP unverified; omitting manual IPv4 hint")

        # Extra HTTP headers.
        if cfg.extra_headers:
            kwargs["extra_http_headers"] = dict(cfg.extra_headers)

        # PH-13: network-layer leak guards via firefox_user_prefs.
        ff_prefs: dict[str, Any] = {}
        if cfg.disable_ipv6:
            ff_prefs["network.dns.disableIPv6"] = True
        if (
            cfg.proxy_remote_dns
            and proxy_cfg is not None
            and proxy_cfg.server.startswith(("socks5://", "socks4://"))
        ):
            # Resolve DNS through the SOCKS proxy, not the host resolver —
            # prevents ISP/DNS-leak correlation with the proxy exit IP.
            ff_prefs["network.proxy.socks_remote_dns"] = True
        if ff_prefs:
            kwargs["firefox_user_prefs"] = ff_prefs

        # PH-19 M3: HAR recording passthrough — relative paths resolve
        # under the profile directory.  PF-03/B-33: video recording is
        # Chromium-only in Playwright — on camoufox/Firefox it crashes
        # the driver during launch, so reject it up-front with a clear
        # error instead of a confusing connection failure.
        if cfg.record_har_path:
            hp = Path(cfg.record_har_path)
            kwargs["record_har_path"] = str(
                hp if hp.is_absolute() else Path(self._session.profile_dir) / hp
            )
        if cfg.record_har_content:
            kwargs["record_har_content"] = cfg.record_har_content
        if cfg.record_video_dir:
            raise AutomationError(
                "record_video_dir is unsupported on camoufox/Firefox "
                "(Playwright video recording is Chromium-only); use "
                "record_har_path for session capture",
                details={
                    "stage": "launch_options",
                    "reason": "video recording unsupported on Firefox",
                },
            )

        # Apply only Camoufox-supported keys from the generated proposal.
        # Camoufox itself draws the UA, viewport, screen, platform, memory,
        # color-scheme and touch properties; our separately generated values
        # cannot truthfully be claimed browser-visible without a live readback.
        # A user-requested hardware concurrency override wins over the draw.
        concurrency = (cfg.hardware_concurrency if cfg.hardware_concurrency is not None
                       else fp.get("hardware_concurrency"))
        if isinstance(concurrency, int) and not isinstance(concurrency, bool) and concurrency > 0:
            launch_config["navigator.hardwareConcurrency"] = concurrency
        if cfg.webgl_config is not None:
            kwargs["webgl_config"] = cfg.webgl_config
        if cfg.fonts is not None:
            kwargs["fonts"] = list(cfg.fonts)
            if cfg.custom_fonts_only:
                kwargs["custom_fonts_only"] = True
        if cfg.screen_bounds is not None:
            from camoufox.fingerprints import Screen  # lazy import

            min_w, max_w, min_h, max_h = cfg.screen_bounds
            kwargs["screen"] = Screen(
                min_width=min_w, max_width=max_w,
                min_height=min_h, max_height=max_h,
            )

        # PH-11: when Camoufox geoip is disabled (Mode A always; Mode B with
        # geoip=False), pass the resolved timezone via the `config` dict so
        # the browser timezone matches fp["timezone_id"] instead of silently
        # falling back to the host OS timezone.  When geoip=True Camoufox
        # derives timezone from the exit IP itself — do NOT override it.
        if kwargs.get("geoip") is False and fp.get("timezone_id"):
            launch_config["timezone"] = fp["timezone_id"]
            # PF-04: the manual timezone config is intentional (Mode A has
            # no geoip source) — silence camoufox's LeakWarning for this
            # launch via its designed escape hatch.
            kwargs["i_know_what_im_doing"] = True
        if launch_config:
            kwargs["config"] = launch_config

        return kwargs

    @staticmethod
    async def _emergency_cleanup(
        ctx_handle: Any | None,
        session: SessionManager,
        proxy_manager: ProxyManager | None = None,
    ) -> None:
        """Best-effort cleanup after a failed launch.

        Closes the camoufox handle, proxy manager and session lock (F-06).
        Errors during cleanup are logged but never re-raised.

        Args:
            ctx_handle: The camoufox async context manager handle, or
                ``None`` if launch failed before it was created.
            session: The :class:`SessionManager` whose lock must be freed.
            proxy_manager: Proxy manager to close when launch fails.
        """
        if ctx_handle is not None:
            try:
                await ctx_handle.__aexit__(None, None, None)
            except Exception as exc:
                _log.warning("emergency cleanup: camoufox close failed", reason=str(exc))
        if proxy_manager is not None:
            try:
                await proxy_manager.aclose()
            except Exception as exc:
                _log.warning("emergency cleanup: proxy close failed", reason=str(exc))
        try:
            session.release_lock()
        except Exception as exc:
            _log.warning("emergency cleanup: release_lock failed", reason=str(exc))


# ---------------------------------------------------------------------------
# BrowserSession
# ---------------------------------------------------------------------------


class BrowserSession:
    """A live stealth browser session wrapping a camoufox persistent context.

    Provides access to the underlying Playwright context and page, plus
    convenience methods for saving state and human-like interaction
    primitives.

    Instances are created exclusively by :meth:`StealthEngine.alaunch` /
    :meth:`StealthEngine.launch` and should not be constructed directly.

    Args:
        ctx: The Playwright :class:`BrowserContext` returned by camoufox.
        ctx_handle: The camoufox async context manager whose
            ``__aexit__`` closes the browser.
        session: The :class:`SessionManager` owning this profile.
        proxy_manager: The active :class:`ProxyManager`, or ``None``.
        config: The :class:`ProfileConfig` for this session.
    """

    # Class-level default so __new__-constructed sessions (tests) also
    # have a sane start point; __init__ sets the per-instance value.
    _last_mouse: tuple[float, float] = (0.0, 0.0)

    def __init__(
        self,
        ctx: PlaywrightBrowserContext,
        ctx_handle: Any,
        session: SessionManager,
        proxy_manager: ProxyManager | None,
        config: ProfileConfig,
    ) -> None:
        self._ctx: PlaywrightBrowserContext = ctx
        self._ctx_handle: Any = ctx_handle
        self._session: SessionManager = session
        self._proxy_manager: ProxyManager | None = proxy_manager
        self._config: ProfileConfig = config
        self._closed: bool = False
        # Set only by StealthEngine.launch(); async launches own no worker.
        self._sync_loop: asyncio.AbstractEventLoop | None = None
        self._sync_thread: Any | None = None

        # Isolated RNG for human hooks — never touches the global random state.
        seed = config.seed
        self._rng: random.Random = (
            random.Random(seed) if seed is not None else random.Random()
        )

        # Per-profile persisted behavioral parameters (PH-15) — lazily
        # loaded on first hook use so construction stays cheap.
        self._behavior: BehaviorProfile | None = None

        # Last known mouse position for bezier start points (BF-03/B-07).
        # Playwright's Mouse exposes no position getter — track it ourselves.
        self._last_mouse: tuple[float, float] = (0.0, 0.0)

        # Only an existing page can be exposed synchronously.  The engine
        # awaits new_page_async() after construction when context is empty.
        try:
            pages = ctx.pages
            self._page: PlaywrightPage = pages[0] if pages else None
        except Exception:
            self._page = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def page(self) -> PlaywrightPage:
        """The current active page in this session.

        Returns:
            The Playwright ``Page`` object.
        """
        return self._page

    @property
    def context(self) -> PlaywrightBrowserContext:
        """The underlying Playwright ``BrowserContext``.

        Returns:
            The camoufox persistent context.
        """
        return self._ctx

    # ------------------------------------------------------------------
    # Page management
    # ------------------------------------------------------------------

    async def new_page_async(self) -> PlaywrightPage:
        """Open and return a new page in this session's context (async).

        BF-04/B-24: the underlying context is async — ``new_page()`` is a
        coroutine and must be awaited.  The initial page is available
        synchronously via :attr:`page`.

        Returns:
            A new Playwright ``Page`` object.

        Raises:
            AutomationError: If the context is closed or page creation fails.
        """
        try:
            page = await self._ctx.new_page()
            self._page = page
            return page
        except Exception as exc:
            raise AutomationError(
                "failed to open new page",
                details={"stage": "new_page", "reason": str(exc)},
            ) from exc

    def new_page(self) -> PlaywrightPage:
        """Sync page creation — unsupported on async contexts.

        BF-04/B-24: ``context.new_page()`` is a coroutine; it cannot be
        awaited from sync code.  Use ``await session.new_page_async()``
        or the already-open :attr:`page`.

        Raises:
            AutomationError: Always — directs caller to the async API.
        """
        raise AutomationError(
            "new_page() cannot run synchronously on an async browser "
            "context; use 'await session.new_page_async()' or session.page",
            details={"stage": "new_page", "reason": "async context"},
        )

    # ------------------------------------------------------------------
    # State persistence
    # ------------------------------------------------------------------

    async def save_state_async(self) -> None:
        """Export the current browser storage state to disk (async).

        BF-01 fix: the underlying context is async — ``storage_state()``
        must be awaited.  Captures cookies and origins via
        ``await context.storage_state()`` and persists them atomically
        via :meth:`~SessionManager.export_state`.

        Raises:
            AutomationError: If the storage-state capture fails.
            SessionError: Propagated from :meth:`~SessionManager.export_state`.
        """
        try:
            state: dict = await self._ctx.storage_state()
        except Exception as exc:
            raise AutomationError(
                "failed to capture storage state",
                details={"stage": "save_state", "reason": str(exc)},
            ) from exc
        self._session.export_state(state)
        _log.debug(
            "storage state saved",
            profile=self._config.profile_name,
            cookies=len(state.get("cookies", [])),
        )

    def save_state(self) -> None:
        """Sync storage-state export — unsupported on async contexts.

        BF-01: the camoufox context is asynchronous, so
        ``context.storage_state()`` is a coroutine that cannot be awaited
        from sync code.  Use ``await session.save_state_async()`` or let
        :meth:`aclose`/:meth:`close` persist state automatically.

        Raises:
            AutomationError: Always — directs caller to the async API.
        """
        raise AutomationError(
            "save_state() cannot run synchronously on an async browser "
            "context; use 'await session.save_state_async()'",
            details={"stage": "save_state", "reason": "async context"},
        )

    # ------------------------------------------------------------------
    # Close / cleanup
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the browser session synchronously.

        Saves state (best-effort), closes the camoufox context, releases
        the profile lock, and closes the proxy manager session.  Safe to
        call multiple times (idempotent).
        """
        if self._closed:
            return

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            raise AutomationError(
                "close() was called from inside a running event loop; "
                "use 'await session.aclose()' instead.",
                details={"stage": "close", "reason": "running event loop detected"},
            )

        if self._sync_loop is not None:
            # Dispatch teardown onto the SAME loop that launched Camoufox.
            try:
                future = asyncio.run_coroutine_threadsafe(self.aclose(), self._sync_loop)
                future.result()
            finally:
                self._stop_sync_loop()
            return

        self._closed = True

        # Merge state save + camoufox teardown + proxy cleanup into ONE
        # asyncio.run() call so they share the same event loop and the
        # aiohttp session is closed on the loop it was created on.
        _proxy_mgr = self._proxy_manager

        async def _async_close() -> None:
            # BF-01: save state via the async storage_state() call.
            try:
                await self.save_state_async()
            except Exception as exc:
                _log.warning("close: save_state_async failed", reason=str(exc))
            try:
                await self._ctx_handle.__aexit__(None, None, None)
            except Exception as exc:
                _log.warning("close: ctx_handle.__aexit__ failed", reason=str(exc))
            finally:
                if _proxy_mgr is not None:
                    try:
                        await _proxy_mgr.aclose()
                    except Exception as exc:
                        _log.warning("close: proxy_manager.aclose() failed", reason=str(exc))

        try:
            asyncio.run(_async_close())
        except Exception as exc:
            _log.warning("close: async cleanup failed", reason=str(exc))

        self._session.release_lock()

        _log.info("session closed", profile=self._config.profile_name)

    def _stop_sync_loop(self) -> None:
        """Stop/join the owned launch worker after closing the browser."""
        loop, thread = self._sync_loop, self._sync_thread
        if loop is None or thread is None:
            return
        if thread.is_alive():
            loop.call_soon_threadsafe(loop.stop)
            thread.join()
        self._sync_loop = None
        self._sync_thread = None

    async def aclose(self) -> None:
        """Close the browser session asynchronously.

        Async counterpart to :meth:`close`.  Idempotent.  Sessions started
        via sync ``launch()`` are closed on their owning worker loop.
        """
        if self._sync_loop is not None and asyncio.get_running_loop() is not self._sync_loop:
            try:
                await asyncio.wrap_future(
                    asyncio.run_coroutine_threadsafe(self.aclose(), self._sync_loop)
                )
            finally:
                await asyncio.to_thread(self._stop_sync_loop)
            return
        if self._closed:
            return
        self._closed = True

        # Best-effort state save (BF-01: async storage_state()).
        try:
            await self.save_state_async()
        except Exception as exc:
            _log.warning("aclose: save_state_async failed", reason=str(exc))

        try:
            await self._ctx.close()
        except Exception as exc:
            _log.warning("aclose: context.close() failed", reason=str(exc))

        try:
            await self._ctx_handle.__aexit__(None, None, None)
        except Exception as exc:
            _log.warning("aclose: ctx_handle.__aexit__ failed", reason=str(exc))

        self._session.release_lock()

        if self._proxy_manager is not None:
            try:
                await self._proxy_manager.aclose()
            except Exception as exc:
                _log.warning("aclose: proxy_manager.aclose() failed", reason=str(exc))

        _log.info("session closed", profile=self._config.profile_name)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "BrowserSession":
        """Return self; session is already open on construction.

        Returns:
            This :class:`BrowserSession` instance.
        """
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc: BaseException | None,
        tb: object,
    ) -> None:
        """Close the session unconditionally; never suppresses exceptions.

        Args:
            exc_type: Exception type, or ``None``.
            exc: Exception instance, or ``None``.
            tb: Traceback, or ``None``.
        """
        self.close()

    async def __aenter__(self) -> "BrowserSession":
        """Async context-manager entry — returns self (BF-03/B-22).

        Enables ``async with session:`` which correctly routes teardown
        through :meth:`aclose` instead of the sync :meth:`close`.
        """
        return self

    async def __aexit__(
        self,
        exc_type: type | None,
        exc: BaseException | None,
        tb: object,
    ) -> None:
        """Async context-manager exit — awaits :meth:`aclose` (BF-03/B-22)."""
        await self.aclose()

    def _get_behavior(self) -> BehaviorProfile:
        """Return the persisted per-profile behavior parameters (lazy)."""
        if self._behavior is None:
            self._behavior = BehaviorProfile.load_or_create(
                self._session, self._config.seed
            )
        return self._behavior

    # ------------------------------------------------------------------
    # Human-like interaction hooks
    # ------------------------------------------------------------------

    def human_move(self, page: PlaywrightPage, x: int, y: int) -> None:
        """Sync mouse move — unsupported on async contexts.

        PF-02/B-25: the session context is always async, so
        ``page.mouse.move()`` returns a coroutine that cannot be
        awaited here; the previous implementation silently did
        nothing.  Use ``await session.ahuman_move(page, x, y)``.

        Raises:
            AutomationError: Always — directs caller to the async API.
        """
        raise AutomationError(
            "human_move() cannot run synchronously on an async browser "
            "context; use 'await session.ahuman_move(page, x, y)'",
            details={"stage": "human_move", "reason": "async context"},
        )

    def human_type(
        self, page: PlaywrightPage, selector: str, text: str
    ) -> None:
        """Sync typing — unsupported on async contexts.

        PF-02/B-25: ``page.click()``/``keyboard.type()`` are coroutines.
        Use ``await session.ahuman_type(page, selector, text)``.

        Raises:
            AutomationError: Always — directs caller to the async API.
        """
        raise AutomationError(
            "human_type() cannot run synchronously on an async browser "
            "context; use 'await session.ahuman_type(page, selector, text)'",
            details={"stage": "human_type", "reason": "async context"},
        )

    def human_scroll(self, page: PlaywrightPage, dy: int) -> None:
        """Sync scroll — unsupported on async contexts.

        PF-02/B-25: ``page.mouse.wheel()`` is a coroutine.
        Use ``await session.ahuman_scroll(page, dy)``.

        Raises:
            AutomationError: Always — directs caller to the async API.
        """
        raise AutomationError(
            "human_scroll() cannot run synchronously on an async browser "
            "context; use 'await session.ahuman_scroll(page, dy)'",
            details={"stage": "human_scroll", "reason": "async context"},
        )

    # ------------------------------------------------------------------
    # Async human-like interaction hooks (PH-11)
    # ------------------------------------------------------------------

    async def ahuman_move(self, page: PlaywrightPage, x: int, y: int) -> None:
        """Async variant of :meth:`human_move` — non-blocking sleeps.

        Same jittered micro-step algorithm; uses ``await page.mouse.move``
        and :func:`asyncio.sleep` so the event loop stays responsive.

        Args:
            page: The async Playwright ``Page``.
            x: Target X coordinate in pixels.
            y: Target Y coordinate in pixels.

        Raises:
            AutomationError: If the mouse movement fails.
        """
        behavior = self._get_behavior()
        steps = behavior.mouse_steps(self._rng)
        # BF-03/B-07: Playwright Mouse has no position getter — use the
        # position tracked by this session (updated after each move).
        current_x, current_y = self._last_mouse

        total_sleep_s = behavior.mouse_total_s(self._rng)
        sleep_per_step = total_sleep_s / steps
        path = bezier_path(current_x, current_y, float(x), float(y), self._rng, steps)

        try:
            for px, py in path[1:]:
                await page.mouse.move(px, py)
                await asyncio.sleep(sleep_per_step)
            await page.mouse.move(x, y)
            self._last_mouse = (float(x), float(y))
        except Exception as exc:
            raise AutomationError(
                "ahuman_move failed",
                details={"stage": "ahuman_move", "reason": str(exc), "target": (x, y)},
            ) from exc

    async def ahuman_type(
        self, page: PlaywrightPage, selector: str, text: str
    ) -> None:
        """Async variant of :meth:`human_type`.

        Clicks ``selector`` then types ``text`` with per-keystroke delays
        via :func:`asyncio.sleep`.

        Args:
            page: The async Playwright ``Page``.
            selector: CSS/XPath selector for the input element.
            text: Text to type.

        Raises:
            AutomationError: If the click or typing fails.
        """
        behavior = self._get_behavior()
        try:
            await page.click(selector)
            for char in text:
                await page.keyboard.type(char)
                await asyncio.sleep(behavior.typing_delay(self._rng, char))
        except Exception as exc:
            raise AutomationError(
                "ahuman_type failed",
                details={
                    "stage": "ahuman_type",
                    "selector": selector,
                    "reason": str(exc),
                },
            ) from exc

    async def ahuman_scroll(self, page: PlaywrightPage, dy: int) -> None:
        """Async variant of :meth:`human_scroll`.

        Scrolls ``dy`` pixels in jittered chunks with non-blocking sleeps.

        Args:
            page: The async Playwright ``Page``.
            dy: Total vertical scroll distance in pixels.

        Raises:
            AutomationError: If the scroll fails.
        """
        behavior = self._get_behavior()
        plan = behavior.scroll_plan(dy, self._rng)
        try:
            for delta, pause in plan:
                await page.mouse.wheel(0, delta)
                await asyncio.sleep(pause)
        except Exception as exc:
            raise AutomationError(
                "ahuman_scroll failed",
                details={"stage": "ahuman_scroll", "reason": str(exc), "dy": dy},
            ) from exc

    # ------------------------------------------------------------------
    # Attention / dwell hooks (PH-15)
    # ------------------------------------------------------------------

    def human_dwell(
        self, page: PlaywrightPage, min_s: float = 1.5, max_s: float = 6.0
    ) -> None:
        """Sync dwell — unsupported on async contexts.

        PF-02/B-25: jiggle moves are coroutines on the async context.
        Use ``await session.adwell(page, min_s, max_s)``.

        Raises:
            AutomationError: Always — directs caller to the async API.
        """
        raise AutomationError(
            "human_dwell() cannot run synchronously on an async browser "
            "context; use 'await session.adwell(page, min_s, max_s)'",
            details={"stage": "human_dwell", "reason": "async context"},
        )

    async def adwell(
        self, page: PlaywrightPage, min_s: float = 1.5, max_s: float = 6.0
    ) -> None:
        """Async variant of :meth:`human_dwell`.

        Args:
            page: The async Playwright ``Page``.
            min_s: Minimum dwell seconds.
            max_s: Maximum dwell seconds.

        Raises:
            AutomationError: If a jiggle move fails.
        """
        for kind, dur in dwell_plan(self._rng, min_s, max_s):
            if kind == "jiggle":
                # PF-02/B-26: Playwright Mouse has no position getter —
                # jiggle around the last tracked position.
                cx, cy = self._last_mouse
                await self.ahuman_move(
                    page,
                    cx + self._rng.uniform(-30, 30),
                    cy + self._rng.uniform(-30, 30),
                )
            else:
                await asyncio.sleep(dur)

    # ------------------------------------------------------------------
    # Download / upload helpers (PH-14)
    # ------------------------------------------------------------------

    @asynccontextmanager
    async def expect_download(self, page: PlaywrightPage, timeout_s: float = 30.0):
        """Async context manager wrapping Playwright ``page.expect_download``.

        Usage::

            async with session.expect_download(page) as dl_info:
                await page.click("#download-btn")
            download = await dl_info.value
            await download.save_as("out.bin")

        Args:
            page: The async Playwright ``Page``.
            timeout_s: Max wait for the download to start.

        Yields:
            The Playwright download event info object.
        """
        async with page.expect_download(timeout=timeout_s * 1000) as event:
            yield event

    async def attach_file(
        self, page: PlaywrightPage, selector: str, path: str
    ) -> None:
        """Attach a local file to a file-input element.

        Thin wrapper over ``page.set_input_files`` for symmetry with the
        other ``BrowserSession`` helpers.

        Args:
            page: The async Playwright ``Page``.
            selector: CSS selector of the ``<input type="file">``.
            path: Local filesystem path to attach.

        Raises:
            AutomationError: If the attachment fails.
        """
        try:
            await page.set_input_files(selector, path)
        except Exception as exc:
            raise AutomationError(
                "attach_file failed",
                details={
                    "stage": "attach_file",
                    "selector": selector,
                    "path": path,
                    "reason": str(exc),
                },
            ) from exc

    # ------------------------------------------------------------------
    # Fingerprint / hygiene probes (PH-16)
    # ------------------------------------------------------------------

    async def probe_fingerprint(self, page: PlaywrightPage) -> dict[str, Any]:
        """Read back live fingerprint signals from the page (PH-16).

        Returns a dict of consistency-checkable values:
        ``canvas_hash`` (simple hash of a drawn canvas dataURL),
        ``webgl_renderer``, ``user_agent``, ``language``,
        ``languages``, ``hardware_concurrency``, ``device_memory``,
        ``max_touch_points``, ``gamepad_count``, ``has_usb``,
        ``has_serial``, ``notification_permission``, ``timezone``.

        Use it to verify the browser presents a coherent identity —
        e.g. ``webgl_renderer`` should look like a real GPU, not "SwiftShader".

        Args:
            page: The async Playwright ``Page``.

        Returns:
            Dict of probe values. Individual failures degrade to ``None``.

        Raises:
            AutomationError: If the evaluate call itself fails.
        """
        js = """
        () => {
          const out = {};
          try {
            const c = document.createElement('canvas');
            c.width = 200; c.height = 50;
            const g = c.getContext('2d');
            g.textBaseline = 'top'; g.font = '14px Arial';
            g.fillStyle = '#f60'; g.fillRect(0,0,100,30);
            g.fillStyle = '#069'; g.fillText('stealth-probe', 2, 15);
            out.canvas_hash = c.toDataURL().length + ':' +
              c.toDataURL().slice(-64);
          } catch (e) { out.canvas_hash = null; }
          try {
            const gl = document.createElement('canvas').getContext('webgl');
            const dbg = gl && gl.getExtension('WEBGL_debug_renderer_info');
            out.webgl_renderer = dbg
              ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : null;
          } catch (e) { out.webgl_renderer = null; }
          out.user_agent = navigator.userAgent;
          out.language = navigator.language;
          out.languages = navigator.languages ? [...navigator.languages] : null;
          out.hardware_concurrency = navigator.hardwareConcurrency;
          out.device_memory = navigator.deviceMemory;
          out.max_touch_points = navigator.maxTouchPoints;
          try {
            out.gamepad_count = navigator.getGamepads
              ? navigator.getGamepads().filter(Boolean).length : null;
          } catch (e) { out.gamepad_count = null; }
          out.has_usb = 'usb' in navigator;
          out.has_serial = 'serial' in navigator;
          out.notification_permission =
            (typeof Notification !== 'undefined') ? Notification.permission : null;
          try { out.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone; }
          catch (e) { out.timezone = null; }
          return out;
        }
        """
        try:
            result: dict[str, Any] = await page.evaluate(js)
        except Exception as exc:
            raise AutomationError(
                "probe_fingerprint failed",
                details={"stage": "probe_fingerprint", "reason": str(exc)},
            ) from exc
        return result or {}

    async def fetch_headers(self, url: str, timeout_s: float = 15.0) -> dict[str, str]:
        """Fetch response headers for ``url`` via the browser context's
        request API (PH-16).

        Useful for cache-header / server-consistency checks without a
        full page navigation.

        Args:
            url: Target URL.
            timeout_s: Request timeout in seconds.

        Returns:
            Dict of lower-cased header name → value.

        Raises:
            AutomationError: If the request fails.
        """
        try:
            resp = await self._ctx.request.get(url, timeout=timeout_s * 1000)
            headers = await resp.all_headers()
            return {k.lower(): v for k, v in headers.items()}
        except Exception as exc:
            raise AutomationError(
                "fetch_headers failed",
                details={"stage": "fetch_headers", "url": url, "reason": str(exc)},
            ) from exc

    # ------------------------------------------------------------------
    # Warmup flows + event hooks (PH-18)
    # ------------------------------------------------------------------

    async def warmup(
        self,
        url: str,
        *,
        template: str = "default",
        scrolls: int | None = None,
        dwell_s: tuple[float, float] | None = None,
    ) -> None:
        """Run a human-like warmup flow on ``url`` (PH-18 N5 / PH-20 G3).

        Sequence: navigate → mouse move → scroll down/up with physics
        chunks → attention dwell.  ``template`` selects a preset
        (``default``, ``social``, ``commerce``, ``search``); explicit
        ``scrolls``/``dwell_s`` override the preset values.

        Args:
            url: Page to warm up on (typically the site homepage).
            template: Warmup preset name (see ``_WARMUP_TEMPLATES``).
            scrolls: Number of down+up scroll cycles (overrides template).
            dwell_s: ``(min, max)`` dwell seconds (overrides template).

        Raises:
            AutomationError: If template unknown, navigation, or hooks fail.
        """
        preset = _WARMUP_TEMPLATES.get(template)
        if preset is None:
            raise AutomationError(
                f"unknown warmup template: {template!r}",
                details={
                    "stage": "warmup",
                    "template": template,
                    "available": sorted(_WARMUP_TEMPLATES),
                },
            )
        n_scrolls = preset["scrolls"] if scrolls is None else scrolls
        dwell = preset["dwell_s"] if dwell_s is None else dwell_s
        page = self._page
        if page is None:
            raise AutomationError(
                "warmup requires an active page",
                details={"stage": "warmup", "reason": "no page"},
            )
        try:
            await page.goto(url, wait_until="domcontentloaded")
            await self.ahuman_move(page, 400, 300)
            for _ in range(max(0, n_scrolls)):
                await self.ahuman_scroll(page, 400)
                await self.ahuman_scroll(page, -250)
            await self.adwell(page, dwell[0], dwell[1])
        except AutomationError:
            raise
        except Exception as exc:
            raise AutomationError(
                "warmup failed",
                details={"stage": "warmup", "url": url, "reason": str(exc)},
            ) from exc

    def add_listener(self, event: str, callback: Any) -> None:
        """Register a Playwright context event listener (PH-18, N6).

        Supported events: ``"request"``, ``"response"``,
        ``"requestfailed"``, ``"requestfinished"``, ``"console"``,
        ``"page"``.  Callbacks receive the Playwright event object.

        Args:
            event: Context event name.
            callback: Callable invoked with the event.

        Raises:
            AutomationError: If registration fails.
        """
        try:
            self._ctx.on(event, callback)
        except Exception as exc:
            raise AutomationError(
                "add_listener failed",
                details={"stage": "add_listener", "event": event, "reason": str(exc)},
            ) from exc

    async def add_route(self, url_pattern: str, handler: Any) -> None:
        """Register a request route handler (PH-18, N6).

        ``handler`` receives ``(route, request)`` and must call
        ``route.continue_()``, ``route.fulfill()``, or ``route.abort()``.
        Use for header injection, tracker blocking, or request logging.

        Args:
            url_pattern: Glob/regex URL pattern (e.g. ``"**/*tracker*"``).
            handler: Async callable ``(route, request) -> None``.

        Raises:
            AutomationError: If registration fails.
        """
        try:
            await self._ctx.route(url_pattern, handler)
        except Exception as exc:
            raise AutomationError(
                "add_route failed",
                details={"stage": "add_route", "pattern": url_pattern, "reason": str(exc)},
            ) from exc

    async def block_trackers(
        self, extra_domains: list[str] | None = None
    ) -> int:
        """Abort requests to common tracker/analytics domains (PH-20, G2).

        Registers a ``**/*`` route that aborts requests whose *destination
        hostname* equals a known tracker domain or is its subdomain. URL
        paths, queries and lookalike suffixes are never treated as hosts.

        Args:
            extra_domains: Additional domain names to block (including
                subdomains); optional leading ``*.`` is accepted.

        Returns:
            Number of domains now blocked.

        Raises:
            AutomationError: If route registration fails.
        """
        from urllib.parse import urlsplit

        domains = list(_TRACKER_DOMAINS) + list(extra_domains or [])
        # F-17: normalize domain rules once; use label boundaries, not URL
        # substring matching (which also matches queries and lookalikes).
        blocked_hosts = tuple(
            domain.strip().lower().removeprefix("*.").strip(".")
            for domain in domains
            if isinstance(domain, str) and domain.strip(".* ")
        )

        async def _handler(route: Any, request: Any) -> None:
            try:
                host = (urlsplit(request.url).hostname or "").lower().rstrip(".")
            except ValueError:  # Invalid URL authority must not become a tracker match.
                host = ""
            if host and any(host == d or host.endswith("." + d) for d in blocked_hosts):
                await route.abort()
            else:
                await route.continue_()

        try:
            await self._ctx.route("**/*", _handler)
        except Exception as exc:
            raise AutomationError(
                "block_trackers failed",
                details={"stage": "block_trackers", "reason": str(exc)},
            ) from exc
        return len(domains)

    def session_age_days(self) -> float | None:
        """Age since immutable first-known launch, or legacy oldest record.

        A capped pre-migration history can only reveal its oldest *retained*
        timestamp. A malformed metadata sidecar returns None, not a guessed
        age derived from a later truncated entry.
        """
        import json as _json
        import math as _math

        path = Path(self._session.profile_dir) / "fingerprint_history.json"
        meta = path.with_name("fingerprint_history_meta.json")
        try:
            if meta.exists():
                data = _json.loads(meta.read_text(encoding="utf-8"))
                if not isinstance(data, dict) or data.get("schema_version") != 1:
                    return None
                first_ts = float(data["first_seen_ts"])
            else:
                if not path.exists():
                    return None
                history = _json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(history, list) or not history:
                    return None
                first_ts = float(history[0].get("ts", 0))
            if not _math.isfinite(first_ts) or first_ts <= 0:
                return None
            return round((time.time() - first_ts) / 86400.0, 3)
        except (OSError, KeyError, ValueError, TypeError, OverflowError, IndexError, AttributeError):
            return None

    # ------------------------------------------------------------------
    # PH-19: engine depth — audit, CDP, contexts
    # ------------------------------------------------------------------

    async def verify_stealth(
        self,
        page: PlaywrightPage | None = None,
        *,
        geo: GeoInfo | None = None,
        fingerprint: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Composite stealth audit for the live session (PH-19, M1).

        Composes existing verifiers — no new scoring logic:

        - ``probe_fingerprint(page)`` → live readback signals
        - ``ban_risk_score(probe, geo, config)`` → 0-100 risk
        - ``validate_geo_consistency(geo, config)`` when ``geo`` given
        - ``validate_fingerprint(fingerprint)`` when ``fp`` given

        Args:
            page: Page to probe; defaults to ``self.page``.
            geo: Optional resolved :class:`GeoInfo` for consistency check.
            fingerprint: Optional generated fp dict for consistency check.

        Returns:
            ``{"probe", "risk", "geo", "fp", "consistent", "summary"}``.
            ``consistent`` is False when risk level is "high" or any geo/fp
            check reports mismatches.

        Raises:
            AutomationError: If probing fails entirely.
        """
        target = page if page is not None else self._page
        probe = await self.probe_fingerprint(target)

        from .geo import validate_geo_consistency
        from .identity import validate_fingerprint
        from .risk import ban_risk_score

        risk = ban_risk_score(probe, geo=geo, config=self._config)
        geo_report = (
            validate_geo_consistency(geo, self._config) if geo is not None else None
        )
        fp_report = (
            validate_fingerprint(fingerprint) if fingerprint is not None else None
        )

        # BF-03/B-10: normalise mismatches into {"source", "detail"} dicts
        # so consumers can distinguish geo vs fingerprint issues.
        mismatches: list[dict[str, str]] = []
        if geo_report is not None and not geo_report.get("consistent", True):
            for m in geo_report.get("mismatches", []):
                mismatches.append({"source": "geo", "detail": str(m)})
        if fp_report is not None and not fp_report.get("consistent", True):
            for issue in fp_report.get("issues", []):
                mismatches.append({"source": "fingerprint", "detail": str(issue)})

        consistent = risk["level"] != "high" and not mismatches
        summary = (
            f"risk={risk['score']}/100 ({risk['level']}), "
            f"signals={len(risk['signals'])}, "
            f"geo={'ok' if geo_report is None or geo_report.get('consistent') else 'mismatch'}, "
            f"fp={'ok' if fp_report is None or fp_report.get('consistent') else 'issues'}"
        )
        return {
            "probe": probe,
            "risk": risk,
            "geo": geo_report,
            "fp": fp_report,
            "consistent": consistent,
            "summary": summary,
            "mismatches": mismatches,
        }

    async def cdp_session(self, page: PlaywrightPage) -> Any:
        """Return a raw CDP session for ``page`` (PH-19, M2).

        Exposes Chrome DevTools Protocol for network interception, cookie
        control, console capture, and metrics.  PF-03 verified: camoufox
        is Firefox/Juggler-based and does NOT implement CDP — this
        method always raises ``AutomationError`` on the supported
        backend.  Kept for API completeness; use Playwright routing,
        ``fetch_headers``, and ``add_listener`` for equivalent
        interception on Firefox.

        Args:
            page: Playwright page to attach the session to.

        Returns:
            The Playwright ``CDPSession`` object.

        Raises:
            AutomationError: If the context is closed, page invalid, or
                CDP is unsupported by the browser backend.
        """
        if self._closed:
            raise AutomationError(
                "cdp_session on closed session",
                details={"stage": "cdp_session", "reason": "session closed"},
            )
        try:
            return await self._ctx.new_cdp_session(page)
        except Exception as exc:
            raise AutomationError(
                "cdp_session failed (CDP may be unsupported on Firefox/Juggler)",
                details={"stage": "cdp_session", "reason": str(exc)},
            ) from exc

    async def new_context(self, **kwargs: Any) -> Any:
        """Spawn an additional isolated browser context (PH-19, M4).

        Uses camoufox ``AsyncNewContext`` so each context gets its own
        fpgen fingerprint identity (navigator/screen/WebGL/fonts/voices)
        when possible.  Falls back to a plain ``browser.new_context``
        if the camoufox helper is unavailable.

        The returned context is NOT wired to this profile's
        ``user_data_dir``/seeds — it is ephemeral; caller owns lifecycle
        (``await ctx.close()``).  Supported kwargs mirror camoufox
        ``AsyncNewContext`` (``os``, ``preset``, ``proxy``,
        ``webrtc_ip``, ``geolocation``) plus raw playwright context
        options.

        Returns:
            A Playwright ``BrowserContext``.

        Raises:
            AutomationError: If the browser object is unreachable or
                context creation fails.
        """
        if self._closed:
            raise AutomationError(
                "new_context on closed session",
                details={"stage": "new_context", "reason": "session closed"},
            )
        browser = getattr(self._ctx, "browser", None)
        if browser is None:
            raise AutomationError(
                "new_context unavailable: persistent context exposes no "
                "browser object",
                details={"stage": "new_context", "reason": "no browser"},
            )
        try:
            from camoufox.async_api import AsyncNewContext  # type: ignore[import]

            return await AsyncNewContext(browser, **kwargs)
        except ImportError:
            try:
                return await browser.new_context(**kwargs)
            except Exception as exc:
                raise AutomationError(
                    "new_context failed",
                    details={"stage": "new_context", "reason": str(exc)},
                ) from exc
        except Exception as exc:
            raise AutomationError(
                "new_context failed",
                details={"stage": "new_context", "reason": str(exc)},
            ) from exc
