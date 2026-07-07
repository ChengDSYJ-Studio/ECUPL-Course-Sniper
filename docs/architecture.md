# Architecture

## Data flow

```text
CLI / future UI
      │
      ▼
CourseSniper orchestration
  ├─ inspect current seats
  ├─ enforce dry-run policy
  └─ make one idempotent attempt
      │
      ▼
CourseGateway protocol
  ├─ InMemoryGateway (current)
  ├─ Mock HTTP gateway (planned)
  └─ Authorized adapter (out of scope by default)
```

## Why a gateway boundary?

The orchestration code should be testable without a network, credentials, or a real course
system. A gateway also makes safety policy explicit: the default application can ship with only
the simulator, while an authorized integration remains separate.

## Core invariants

1. Dry-run never changes enrollment state.
2. One student-course pair can create at most one simulated enrollment.
3. A full course cannot exceed capacity, including concurrent attempts.
4. Credentials and sessions never enter source control.
5. Network adapters must implement rate limits, timeouts, and bounded retries.

