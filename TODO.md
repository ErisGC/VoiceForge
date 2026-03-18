# VoiceForge Next Phases

## Phase 1: Real audio capture and upload UX

- Connect Flutter upload flow to file picker and multipart submission.
- Connect Flutter recording flow to microphone capture on Android and Web.
- Add auth persistence and token storage in the app.

## Phase 2: Real preprocessing and embeddings

- Replace heuristic preprocessing with real normalization, VAD, and segmentation.
- Add waveform visualization and clip preview tools.
- Replace deterministic placeholder embeddings with a production speaker encoder.

## Phase 3: Model backend integration

- Deepen the current Seed-VC offline integration with model warm pools, better prompt selection, and richer monitoring.
- Add RVC orchestration for trained profiles.
- Add OpenVoice as an experimental complementary backend.
- Introduce backend-specific config, model artifact manifests, and health checks.

## Phase 4: Streaming/live architecture

- Add WebSocket or WebRTC control channel.
- Implement chunked audio transport and partial responses.
- Create a low-latency worker pool dedicated to live mode.
- Add jitter buffering, session state, and reconnect handling.

## Phase 5: Security and governance hardening

- Add signed consent artifacts and richer evidence collection.
- Move rate limiting to Redis for distributed environments.
- Add role-based admin views and audit filtering.
- Implement provenance watermarking and verification utilities.

## Phase 6: Platform hardening

- Add automated tests for API modules, worker flows, and Flutter navigation.
- Add CI pipelines for lint, analyze, migration checks, and image builds.
- Add object storage adapter for MinIO/S3.
- Add observability with structured logging, tracing, and metrics.
