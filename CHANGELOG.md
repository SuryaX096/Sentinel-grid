# Changelog

All notable changes to the SentinelMind AI Cyber Resilience Platform will be documented in this file.

## [1.2.0] - 2026-07-20
### Added
- Model integrity checksum checking (`model.pkl.sha256` SHA-256 validation) to prevent arbitrary code execution on deserialization.
- Strict input range validations (`anomaly_score` and `technique_confidence` in `[0.0, 1.0]`) and enum status validations in `schema_validator.py`.
- Lifespan context manager using `asynccontextmanager` in `detect_api.py` to replace the deprecated `@app.on_event("startup")` hook.
- Pinned exact dependency versions in `requirements.txt` based on active system environment mappings.

### Fixed
- Fixed resource leak issues by refactoring all SQLite connections to use context managers (`with sqlite3.connect(...)`).
- Fixed duplicate markdown heading injection bugs in `evaluate_attribution.py`.
- Fixed shallow copy array/dictionary mutations inside responses by changing `alert.copy()` to `copy.deepcopy(alert)`.
- Sanitized exception trace details from client-facing API error outputs to prevent path disclosure.

## [1.1.0] - 2026-07-20
### Added
- Standard project MIT `LICENSE` file.
- Wired auto-refresh slider in `app.py` using `streamlit-autorefresh` to trigger real-time console reloads dynamically.

### Fixed
- Fixed critical replay simulator crash when `--count` parameter was less than 10 or dataset files contained scarce attack patterns.
- Localized the dashboard logo by replacing the external icons8 link with an offline-compatible styled emoji component.

## [1.0.0] - 2026-07-17
### Added
- Initial release of SentinelMind AI platform containing Hero Agent (anomaly detection), Attribution Agent (MITRE vector store classification), and Supporting Agent (playbook incident responder).
