# Roadmap

## Phase 1 — submission-ready foundation

- [x] Repository structure and documentation
- [x] In-memory simulator
- [x] Dry-run and idempotent enrollment
- [x] Unit tests and CI
- [ ] Structured logging and local result history
- [ ] Configuration validation

## Phase 2 — demonstrate engineering depth

- [ ] Local mock HTTP server with expiring sessions
- [ ] Bounded polling scheduler with jitter and backoff
- [ ] SQLite persistence and database migrations
- [ ] Concurrent-student simulation and capacity invariant tests
- [ ] Metrics: attempts, latency, success rate, duplicate prevention
- [ ] Small read-only dashboard

## Phase 3 — assessment presentation

- [ ] Reproducible demo script
- [ ] Architecture decision records
- [ ] Failure-injection demo: timeout, session expiry, last-seat race
- [ ] Benchmark report and screenshots
- [ ] Release package for Windows and macOS

## Explicitly out of scope

- CAPTCHA or MFA bypass
- Credential sharing
- High-frequency requests to a real course system
- Circumventing access controls or school policy
- Real enrollment without written authorization and a controlled test environment

