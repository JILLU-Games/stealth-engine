# P-03 — Exact Post-Patch Code Evidence and Offline Verification

- **Date (UTC):** 2026-11-16; **repository:** `ivibtools/stealth-engine`; **branch:** `main`.
- **Immutable project baseline:** `a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5`.
- **Pre-P03 main head:** `c490501d175fd1a3bd164ecf855594c0573279a1`; **P-03 source commit:** [`b2d1884a8e7534d28f492d9f3274eb17c5551b3a`](https://gitlab.com/ivibtools/stealth-engine/-/commit/b2d1884a8e7534d28f492d9f3274eb17c5551b3a).
- **Audited findings:** F-05, F-11, F-12, F-14, F-15 (5) ONLY. **U-05 remains conditional** and is not a completed engine multi-proxy feature.
- **Status:** Code patch applied, **59/59 focused Linux offline tests PASS**, **live/Windows/HTTPS browser acceptance NOT VERIFIED**. This is NOT a production-ready certificate.

## Direct code excerpts from the committed source revision

Each block below was extracted by line number directly from the source bytes whose post-commit Git blobs were verified; the links are pinned to the P-03 source commit. No baseline-only Markdown or inferred behavior is used as code proof.

## F-05 — Scheme-specific SOCKS or HTTP transport

Native SOCKS5 method negotiation, optional RFC1929 authentication and SOCKS4a target-DNS through proxy; HTTP GET/Geo JSON over the established tunnel. Verification uses local bound socket (not remote provider).

**[`stealth_engine/proxy.py:324-348`](https://gitlab.com/ivibtools/stealth-engine/-/blob/b2d1884a8e7534d28f492d9f3274eb17c5551b3a/stealth_engine/proxy.py#L324-348)**

```python
 324 | 
 325 |         is_socks = proxy.server.startswith(("socks5://", "socks4://"))
 326 |         # aiohttp's proxy= argument speaks HTTP CONNECT, never SOCKS.
 327 |         session = None if is_socks else await self._get_session()
 328 |         proxy_url = self._build_proxy_url(proxy)
 329 |         proxy_auth = self._build_proxy_auth(proxy)
 330 |         timeout = aiohttp.ClientTimeout(total=self._timeout_s)
 331 |         masked = self.mask(proxy)
 332 | 
 333 |         data: dict[str, Any] | None = None
 334 |         last_exc: ProxyError | None = None
 335 |         for attempt in range(self._geo_retries + 1):
 336 |             try:
 337 |                 if is_socks:
 338 |                     # Native SOCKS4a/SOCKS5 handshake; TLS peer validation
 339 |                     # happens inside _fetch_geo_via_socks. No optional deps.
 340 |                     data = await asyncio.wait_for(
 341 |                         asyncio.to_thread(self._fetch_geo_via_socks, proxy),
 342 |                         timeout=self._timeout_s,
 343 |                     )
 344 |                     break
 345 |                 assert session is not None
 346 |                 async with session.get(
 347 |                     self._geo_endpoint,
 348 |                     proxy=proxy_url,
```

**[`stealth_engine/proxy.py:568-610`](https://gitlab.com/ivibtools/stealth-engine/-/blob/b2d1884a8e7534d28f492d9f3274eb17c5551b3a/stealth_engine/proxy.py#L568-610)**

```python
 568 |     def _fetch_geo_via_socks(self, proxy: ProxyConfig) -> dict[str, Any]:
 569 |         """GET GeoIP through a SOCKS5 or SOCKS4a TCP tunnel in a worker thread.
 570 | 
 571 |         Uses target hostname at the proxy (no local target DNS), validates
 572 |         HTTPS certificates, limits response bytes and avoids credential-bearing
 573 |         exceptions. This is only the SOCKS GeoIP/health request transport.
 574 |         """
 575 |         endpoint = urlsplit(self._geo_endpoint)
 576 |         if endpoint.scheme not in ("http", "https") or not endpoint.hostname:
 577 |             raise ProxyError("unsupported GeoIP endpoint", details={"stage": "resolve_geo"})
 578 |         proxy_url, embedded_user, embedded_pass = self._proxy_parts(proxy)
 579 |         address = urlsplit(proxy_url)
 580 |         username = proxy.username if proxy.username is not None else embedded_user
 581 |         password = proxy.password if proxy.password is not None else embedded_pass
 582 |         host = endpoint.hostname
 583 |         port = endpoint.port or (443 if endpoint.scheme == "https" else 80)
 584 |         masked = self.mask(proxy)
 585 | 
 586 |         def recv_exact(conn: socket.socket, size: int) -> bytes:
 587 |             result = bytearray()
 588 |             while len(result) < size:
 589 |                 chunk = conn.recv(size - len(result))
 590 |                 if not chunk:
 591 |                     raise OSError("SOCKS peer closed connection")
 592 |                 result.extend(chunk)
 593 |             return bytes(result)
 594 | 
 595 |         try:
 596 |             with socket.create_connection((address.hostname, address.port), timeout=self._timeout_s) as sock:
 597 |                 sock.settimeout(self._timeout_s)
 598 |                 if address.scheme == "socks5":
 599 |                     use_auth = username is not None or password is not None
 600 |                     sock.sendall(b"\x05\x01" + (b"\x02" if use_auth else b"\x00"))
 601 |                     selection = recv_exact(sock, 2)
 602 |                     if selection[0] != 5 or selection[1] != (2 if use_auth else 0):
 603 |                         raise OSError("SOCKS5 method rejected")
 604 |                     if use_auth:
 605 |                         u = (username or "").encode("utf-8")
 606 |                         pw = (password or "").encode("utf-8")
 607 |                         if not 1 <= len(u) <= 255 or len(pw) > 255:
 608 |                             raise OSError("invalid SOCKS5 credential length")
 609 |                         sock.sendall(b"\x01" + bytes([len(u)]) + u + bytes([len(pw)]) + pw)
 610 |                         if recv_exact(sock, 2) != b"\x01\x00":
```

**[`stealth_engine/proxy.py:611-658`](https://gitlab.com/ivibtools/stealth-engine/-/blob/b2d1884a8e7534d28f492d9f3274eb17c5551b3a/stealth_engine/proxy.py#L611-658)**

```python
 611 |                             raise OSError("SOCKS5 authentication rejected")
 612 |                     # Domain name always sent for remote DNS (IPv4/IPv6 included).
 613 |                     target = host.encode("idna")
 614 |                     if len(target) > 255:
 615 |                         raise OSError("target hostname too long")
 616 |                     sock.sendall(b"\x05\x01\x00\x03" + bytes([len(target)]) + target + port.to_bytes(2, "big"))
 617 |                     response = recv_exact(sock, 4)
 618 |                     if response[:3] != b"\x05\x00\x00":
 619 |                         raise OSError("SOCKS5 connect rejected")
 620 |                     addr_type = response[3]
 621 |                     if addr_type == 1:
 622 |                         recv_exact(sock, 4)
 623 |                     elif addr_type == 4:
 624 |                         recv_exact(sock, 16)
 625 |                     elif addr_type == 3:
 626 |                         recv_exact(sock, recv_exact(sock, 1)[0])
 627 |                     else:
 628 |                         raise OSError("unknown SOCKS5 address type")
 629 |                     recv_exact(sock, 2)
 630 |                 elif address.scheme == "socks4":
 631 |                     if password:
 632 |                         raise OSError("SOCKS4 does not support password authentication")
 633 |                     user = (username or "").encode("utf-8")
 634 |                     if b"\x00" in user:
 635 |                         raise OSError("invalid SOCKS4 user ID")
 636 |                     target = host.encode("idna")
 637 |                     if b"\x00" in target:
 638 |                         raise OSError("invalid SOCKS4 hostname")
 639 |                     # SOCKS4a avoids resolving target DNS on the client host.
 640 |                     sock.sendall(b"\x04\x01" + port.to_bytes(2, "big") + b"\x00\x00\x00\x01" + user + b"\x00" + target + b"\x00")
 641 |                     reply = recv_exact(sock, 8)
 642 |                     if reply[0] != 0 or reply[1] != 90:
 643 |                         raise OSError("SOCKS4 connect rejected")
 644 |                 else:
 645 |                     raise OSError("unsupported SOCKS protocol")
 646 | 
 647 |                 conn = sock
 648 |                 if endpoint.scheme == "https":
 649 |                     conn = ssl.create_default_context().wrap_socket(sock, server_hostname=host)
 650 |                 path = endpoint.path or "/"
 651 |                 if endpoint.query:
 652 |                     path += "?" + endpoint.query
 653 |                 host_header = host if port in (80, 443) else f"{host}:{port}"
 654 |                 conn.sendall((f"GET {path} HTTP/1.1\r\nHost: {host_header}\r\nAccept: application/json\r\nAccept-Encoding: identity\r\nConnection: close\r\n\r\n").encode("ascii"))
 655 |                 response = http.client.HTTPResponse(conn)
 656 |                 response.begin()
 657 |                 if response.status != 200:
 658 |                     raise ProxyError("geo endpoint returned HTTP " + str(response.status), details={"stage": "resolve_geo", "proxy": masked})
```

**[`stealth_engine/proxy.py:659-677`](https://gitlab.com/ivibtools/stealth-engine/-/blob/b2d1884a8e7534d28f492d9f3274eb17c5551b3a/stealth_engine/proxy.py#L659-677)**

```python
 659 |                 payload = response.read(1024 * 1024 + 1)
 660 |                 if len(payload) > 1024 * 1024:
 661 |                     raise ProxyError("geo endpoint response too large", details={"stage": "resolve_geo", "proxy": masked})
 662 |                 try:
 663 |                     data = json.loads(payload.decode("utf-8"))
 664 |                 except (UnicodeError, ValueError):
 665 |                     raise ProxyError("geo endpoint returned non-JSON response", details={"stage": "resolve_geo", "proxy": masked}) from None
 666 |                 if not isinstance(data, dict):
 667 |                     raise ProxyError("geo endpoint returned non-object JSON", details={"stage": "resolve_geo", "proxy": masked})
 668 |                 return data
 669 |         except ProxyError:
 670 |             raise
 671 |         except (OSError, ssl.SSLError, ValueError, http.client.HTTPException) as exc:
 672 |             raise ProxyError(
 673 |                 "SOCKS proxy GeoIP request failed",
 674 |                 details={"stage": "resolve_geo", "proxy": masked, "reason_type": type(exc).__name__},
 675 |             ) from None
 676 | 
 677 |     async def _get_session(self) -> aiohttp.ClientSession:
```

## F-11 — Error redaction for proxy-file parsing

Invalid line errors contain stage+line only. Raw credentials and chained Pydantic errors are suppressed. Pydantic server ValidationError hides raw input in its printed error.

**[`stealth_engine/proxy.py:768-782`](https://gitlab.com/ivibtools/stealth-engine/-/blob/b2d1884a8e7534d28f492d9f3274eb17c5551b3a/stealth_engine/proxy.py#L768-782)**

```python
 768 |     def _err(msg: str) -> ProxyError:
 769 |         # Neither error details nor exception chain may expose credentials.
 770 |         return ProxyError(
 771 |             f"proxy file line {lineno}: {msg}",
 772 |             details={"stage": "load_proxies", "line": lineno},
 773 |         )
 774 | 
 775 |     line = line.strip()
 776 |     if "://" in line:
 777 |         # scheme://[user:pass@]host:port
 778 |         try:
 779 |             return ProxyConfig(server=line)
 780 |         except Exception as exc:
 781 |             raise _err("invalid URL proxy address") from None
 782 | 
```

**[`stealth_engine/proxy.py:790-815`](https://gitlab.com/ivibtools/stealth-engine/-/blob/b2d1884a8e7534d28f492d9f3274eb17c5551b3a/stealth_engine/proxy.py#L790-815)**

```python
 790 |         server = f"http://{quote(user, safe='')}:{quote(pw, safe='')}@{hostport}"
 791 |         try:
 792 |             return ProxyConfig(server=server)
 793 |         except Exception as exc:
 794 |             raise _err("invalid credentialed proxy address") from None
 795 | 
 796 |     parts = line.split(":")
 797 |     if len(parts) == 2:
 798 |         host, port = parts
 799 |         server = f"http://{host}:{port}"
 800 |     elif len(parts) == 4:
 801 |         host, port, user, pw = parts
 802 |         from urllib.parse import quote
 803 |         server = (
 804 |             f"http://{quote(user, safe='')}:{quote(pw, safe='')}"
 805 |             f"@{host}:{port}"
 806 |         )
 807 |     else:
 808 |         raise _err(
 809 |             "expected host:port[:user:pass], user:pass@host:port, "
 810 |             "or scheme:// URL"
 811 |         )
 812 |     try:
 813 |         return ProxyConfig(server=server)
 814 |     except Exception as exc:
 815 |         raise _err("invalid proxy address") from None
```

## F-12 — URL authority validation

Host+port required; path/query and whitespace rejected; port 0 rejected; socks5h alias preserved.

**[`stealth_engine/config.py:32-78`](https://gitlab.com/ivibtools/stealth-engine/-/blob/b2d1884a8e7534d28f492d9f3274eb17c5551b3a/stealth_engine/config.py#L32-78)**

```python
  32 |     # Prevent pydantic ValidationError output from echoing credentialed URLs.
  33 |     model_config = ConfigDict(str_strip_whitespace=True, hide_input_in_errors=True)
  34 | 
  35 |     server: str
  36 |     username: str | None = None
  37 |     password: str | None = None
  38 | 
  39 |     @field_validator("server")
  40 |     @classmethod
  41 |     def _validate_server(cls, v: str) -> str:
  42 |         """Ensure server URL uses an accepted scheme.
  43 | 
  44 |         Args:
  45 |             v: Raw server string.
  46 | 
  47 |         Returns:
  48 |             Validated server string.
  49 | 
  50 |         Raises:
  51 |             ValueError: If the scheme is not one of the accepted proxy schemes.
  52 |         """
  53 |         accepted = ("http://", "https://", "socks5://", "socks5h://", "socks4://")
  54 |         if not v.startswith(accepted):
  55 |             raise ValueError("proxy server requires http(s):// or socks4/5://")
  56 |         try:
  57 |             parsed = urlsplit(v)
  58 |             hostname = parsed.hostname
  59 |             port = parsed.port  # raises on invalid/non-numeric/out-of-range ports
  60 |         except ValueError:
  61 |             raise ValueError("proxy server has invalid host or port") from None
  62 |         if (
  63 |             not hostname or port is None or port < 1
  64 |             or any(ch.isspace() for ch in v)
  65 |             or parsed.path or parsed.query or parsed.fragment
  66 |             or any(ch in hostname for ch in "/?#@")
  67 |         ):
  68 |             raise ValueError("proxy server requires a valid host and port without path/query")
  69 |         # Maintain the established socks5h alias contract for downstream engines.
  70 |         if parsed.scheme == "socks5h":
  71 |             return "socks5://" + v[len("socks5h://"):]
  72 |         return v
  73 | 
  74 | 
  75 | class ProfileConfig(BaseModel):
  76 |     """Full configuration for a single stealth browser profile.
  77 | 
  78 |     Attributes:
```

## F-14 — Geo auto sentinel

Auto sentinel compared using resolved Geo value. Explicit nonmatching locale/timezone still reported.

**[`stealth_engine/geo.py:130-151`](https://gitlab.com/ivibtools/stealth-engine/-/blob/b2d1884a8e7534d28f492d9f3274eb17c5551b3a/stealth_engine/geo.py#L130-151)**

```python
 130 |     for field, geo_value, cfg_value in (
 131 |         ("locale", geo.locale, config.locale),
 132 |         ("timezone_id", geo.timezone_id, config.timezone),
 133 |     ):
 134 |         if cfg_value is None:
 135 |             checks[field] = {"status": "skipped", "reason": "config unset"}
 136 |             continue
 137 |         # 'auto' requests the resolved GeoIP value, not a literal persona.
 138 |         # Compare against the effective value rather than against 'auto'.
 139 |         effective = geo_value if isinstance(cfg_value, str) and cfg_value.strip().lower() == "auto" else cfg_value
 140 |         match = geo_value == effective
 141 |         checks[field] = {
 142 |             "status": "match" if match else "mismatch",
 143 |             "geo": geo_value,
 144 |             "config": cfg_value,
 145 |             "resolved": effective,
 146 |         }
 147 |         if not match:
 148 |             mismatches.append(field)
 149 | 
 150 |     return {
 151 |         "consistent": not mismatches,
```

## F-15 — WebRTC hint guard

A private interface IP is not a verified public egress IP. For direct launch, only global IPv4 is forwarded. Invalid explicit values are rejected; non-global guessed values omit the hint, which cannot guarantee no ICE leaks in the real browser.

**[`stealth_engine/engine.py:558-572`](https://gitlab.com/ivibtools/stealth-engine/-/blob/b2d1884a8e7534d28f492d9f3274eb17c5551b3a/stealth_engine/engine.py#L558-572)**

```python
 558 |     def _resolve_host_ip() -> str:
 559 |         """Resolve the actual host IP address for WebRTC in Mode A.
 560 | 
 561 |         Uses a best-effort UDP route lookup and hostname fallback to find a
 562 |         *local interface* IPv4. Behind NAT this is NOT the public egress IP.
 563 |         _build_launch_kwargs() refuses non-global values and omits the manual
 564 |         WebRTC hint if no verified public IPv4 is available.
 565 | 
 566 |         Returns:
 567 |             The host IP address as a string (e.g. "203.0.113.10").
 568 | 
 569 |         Raises:
 570 |             LaunchError: If IP resolution fails for any reason.
 571 |         """
 572 |         try:
```

**[`stealth_engine/engine.py:705-733`](https://gitlab.com/ivibtools/stealth-engine/-/blob/b2d1884a8e7534d28f492d9f3274eb17c5551b3a/stealth_engine/engine.py#L705-733)**

```python
 705 |         }
 706 | 
 707 |         # Proxy + GeoIP.
 708 |         if proxy_cfg is not None and self._proxy_manager is not None:
 709 |             kwargs["proxy"] = self._proxy_manager.to_playwright(proxy_cfg)
 710 |             kwargs["geoip"] = cfg.geoip
 711 |             # Mode B: WebRTC advertises proxy IP via geoip=True
 712 |         else:
 713 |             kwargs["geoip"] = False
 714 |             # Mode A: never advertise an interface/LAN address as the
 715 |             # external WebRTC egress. An explicit target must be public IPv4;
 716 |             # the best-effort local host lookup is used only if globally routed.
 717 |             candidate = cfg.target_ip if cfg.target_ip else self._resolve_host_ip()
 718 |             try:
 719 |                 public_ip = ipaddress.ip_address(candidate)
 720 |                 valid_public_v4 = public_ip.version == 4 and public_ip.is_global
 721 |             except ValueError:
 722 |                 valid_public_v4 = False
 723 |             if cfg.target_ip and not valid_public_v4:
 724 |                 raise LaunchError(
 725 |                     "target_ip must be a globally routable IPv4 address for WebRTC",
 726 |                     details={"stage": "launch_options", "reason": "invalid_public_target_ip"},
 727 |                 )
 728 |             if valid_public_v4:
 729 |                 launch_config["webrtc:ipv4"] = str(public_ip)
 730 |             else:
 731 |                 _log.warning("WebRTC public egress IP unverified; omitting manual IPv4 hint")
 732 | 
 733 |         # Extra HTTP headers.
```

## Focused test evidence — exact scope and limitations

**Command run (test shim is external to Git repository):**

```bash
cd /mnt/data/stealth_audit_workspace
PYTHONPATH=/mnt/data/stealth_audit_workspace python /mnt/data/stealth_phase01_test_shim/run_p03_tests.py
```

- **Environment:** Linux x86_64, Python 3.13, `aiohttp` 3.13.3, real local loopback TCP sockets for SOCKS protocol mock; no external proxy or real browser. `camoufox` and `browserforge` are absent, so a test-only module stub is used for import only; this does not emulate browser network/WebRTC output.
- **Final focused result:** `Ran 59 tests ... OK` — **59 passed / 0 failed / 0 errors; exit code 0**.
- **New targeted P-03 tests:** **11** in `P03SocksWireTests` and `P03ValidationAndWebRTCTests`. **48 adjacent tests** cover HTTP proxy, Geo policy/auto, prior P-01 and P-02 lifecycle/ownership. Existing WebRTC fixture using reserved documentation IP `203.0.113.10` was replaced with globally routable fixture `8.8.8.8` only where a public-IP assertion was required.
- **Observed first run (not hidden):** 1 validator failure (`socks5://host:0` accepted) and 1 test-runner typo (`GeoConsistencyTests` vs actual `ValidateGeoConsistencyTests`). Port 0 was rejected in the validator and runner selection fixed before the final PASS.
- **SOCKS5 mock evidence:** server observed greeting `05 01`, method `00` (no auth) or `02` (user/password), target connect `05 01 00 03`, remote domain `geo.invalid`, HTTP request `GET /geo?v=1 HTTP/1.1`. The local server returned Geo JSON and code parsed `country=US`; SOCKS4a server observed `04 01 ... 00 00 00 01` followed by remote hostname. These are real loopback socket protocol observations, not a third-party egress test.
- **Proxy redaction:** malformed input with `ultrasecret` is absent in `ProxyError` string and `details` and the exception has no chained credential-bearing `ValidationError` in tested parse paths.
- **HTTP existing path:** fake aiohttp session assert `proxy=` and `proxy_auth=` behavior unchanged for HTTP case; surrounding existing tests passed.
- **WebRTC:** tested `_build_launch_kwargs` only; no remote ICE candidate/leak probe. Unknown/private default host IP results in no manual `webrtc:ipv4`, not proven browser privacy.

## Source diff and Scope Lock proof

| Changed path | Allowed function(s) / region | Pre-P03 Git blob → P-03 Git blob |
|---|---|---|
| `stealth_engine/proxy.py` | `ProxyManager.resolve_geo`, new `_fetch_geo_via_socks` transport, `_parse_proxy_line`, transport-only imports | `59706d4b...` → `41465fa8...` |
| `stealth_engine/config.py` | `ProxyConfig` server validation and input masking in its model config | `dc9fc5ae...` → `a2852936...` |
| `stealth_engine/geo.py` | `validate_geo_consistency` only | `6b696b2f...` → `fa847d04...` |
| `stealth_engine/engine.py` | `_resolve_host_ip` doc only and `_build_launch_kwargs` direct WebRTC policy; `ipaddress` import | `8059a36f...` → `eab1e326...` |
| `tests/test_forensic_regressions.py` | P-03 tests plus a pre-existing WebRTC-specific public-IP fixture | `0200bde5...` → `8a758279...` |

**AST audit:** `StealthEngine.launch`, `StealthEngine.alaunch`, `StealthEngine._emergency_cleanup`, all `BrowserSession` P-01 lifecycle methods and P-02 metadata methods unchanged. `SessionManager` entire source blob unchanged. Identity, orchestrator, behavior, logging, risk, session and all UI paths untouched. `pyproject.toml` unchanged. All pre-P03 five source/test blobs matched the then-current GitLab tree exactly; all five post-patch blobs matched the P-03 GitLab commit.

## Blocking production verification (not run)

1. **External SOCKS4a/SOCKS5** paid/owned proxy with consenting target: real GeoIP result, TLS-over-SOCKS certificate chain, egress IP and DNS leak behavior; HTTPS branch is coded but not exercised by local mock (mock uses HTTP).
2. **Real Camoufox/Playwright** launch and fingerprint/WebRTC ICE/STUN readback against controlled test endpoint, plus direct/proxy mode checks. Omission of manual hint **does not imply no browser-internal LAN candidates**.
3. **Windows-specific** native Python socket/TLS transport compatibility and P-02 lock behavior; no real Windows target used.
4. **Existing pending gates:** P-01/P-02 real-browser Windows/production acceptance, U-05 conditional multi-proxy-engine integration remains unsupported, release cannot be certified.

**Gate conclusion:** `P-03 CODE PATCH APPLIED / LINUX OFFLINE 59/59 PASS / REAL PROXY + HTTPS + BROWSER + WINDOWS UNVERIFIED`. **Three of five code phases patched, zero fully accepted.** Remaining code findings: F-03/F-04/F-10/F-13/F-19 (P-04) and F-16/F-17 (P-05), seven total. No P-04 work was performed.
