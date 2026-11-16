# Project Dependencies

| Package | Purpose | Status |
|---------|---------|--------|
| camoufox | Camoufox browser runtime | Required |
| playwright | Browser automation API | Required |
| browserforge | Browser fingerprint generation | Required |
| pydantic | Configuration models and validation | Required |
| aiohttp | Async proxy/GeoIP requests | Required |
| loguru | Structured logging | Required |
| tzlocal>=5.0 | Host IANA timezone detection, including Windows registry mapping | Added in PH-02 |
| pyyaml>=6.0 | YAML serialisation for `ProfileConfig.load_yaml`/`save_yaml` (lazy import) | Added in PH-06 |