<h1 align="center">VoiceForge</h1>

<p align="center">
  <em>Plataforma cross-platform de clonación y conversión de voz con IA</em>
  <br/>
  <em>Flutter (Android + Web) · FastAPI · Seed-VC · PostgreSQL · Redis</em>
</p>

<p align="center">
  <img alt="Flutter" src="https://img.shields.io/badge/Flutter-3.x-02569B?logo=flutter&logoColor=white" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white" />
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white" />
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white" />
  <img alt="Redis" src="https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white" />
  <img alt="Next.js" src="https://img.shields.io/badge/Next.js-15-000000?logo=nextdotjs&logoColor=white" />
</p>

---

## ¿Qué hace?

Los usuarios graban o suben muestras de referencia para crear un **perfil de voz**.
Luego pueden subir cualquier audio y obtenerlo convertido para que suene como ese
perfil, preservando el contenido hablado. Pensado para creadores de contenido,
locutores y producción de audio.

Dos modos de conversión:
- **Studio** — calidad alta, mayor latencia (más `diffusion_steps`).
- **Live** — latencia baja, pensado para iteración rápida.

## Highlights técnicos

### 🔧 Aislamiento de proceso para el motor Seed-VC
Seed-VC corre en un **venv aislado de Python 3.10** porque su stack es pesado
y versión-sensible. El backend principal usa Python 3.11+ y dispara Seed-VC
como subprocess, evitando conflictos de dependencias entre `torch`, `transformers`,
`librosa`, etc. La comunicación es vía CLI + ficheros WAV, lo que también permite
correr el motor en otra máquina sin tocar la API.

### ⚡ Caching de features con invalidación versionada
Los features de referencia y de fuente (mel-spectrograms, embeddings) se cachean
en disco con versión asociada al `voice_profile_id`. Las invalidaciones son
deterministas: cambiar la referencia bump-ea la versión y recalcula. **Reduce
latencia de conversión ~30%** respecto al baseline (medido y documentado en
`docs/seed-vc-reference-cache.md`).

### 🚀 Resident runtime opcional
Un sidecar mantiene los modelos Seed-VC cargados en memoria (timeout idle 900s).
Convierte conversiones repetidas en operaciones sub-segundo sin pagar el coste
de cold start cada vez.

### 🎙️ Pipeline de audio production-shaped
- Preprocesado real: mono WAV, resampling, normalización, trimming de silencio
- `ResemblyzerSpeakerEmbeddingService` (GE2E 256-dim) con fallback determinista a
  hashes SHA-256 cuando resemblyzer no está disponible
- Modelos abstraídos vía `ModelRegistry` — Seed-VC ya en producción; RVC y
  OpenVoice registrados como adapters stub

### 🔔 WebSocket con Redis pub/sub para notificaciones en tiempo real
`/ws/jobs` con autenticación JWT (query param) y Redis pub/sub para empujar
estados de jobs al cliente Flutter sin polling. `JobNotificationService` en el
cliente vía `web_socket_channel`.

### 🛡️ Cumplimiento legal Colombia (Ley 1581/2012)
- Consentimiento explícito y trazable por perfil de voz (texto + timestamp + evidence key)
- 12+ tipos de eventos en `audit_logs` para compliance
- Políticas de privacidad, términos y reembolso adaptadas a la regulación local

### 💳 Pasarela de pagos Wompi (Bancolombia)
Integración con SHA256 webhook verification, idempotencia, validación de monto
por plan, y URLs de descarga firmadas (HMAC-SHA256, expiry 1h) para prevenir
sharing del APK. Auth0 user IDs encodeados como `__` para evitar ambigüedad de
parsing con el `|` literal del sub de Auth0.

## Stack

| Capa | Tecnología |
|------|-----------|
| Cliente | Flutter 3.x (Android + iOS + Web), Dart 3.11+ |
| API | FastAPI 0.115+, Python 3.11+, SQLAlchemy 2.0, Pydantic v2 |
| Worker | Redis-backed job processor |
| Base de datos | PostgreSQL 17 + Alembic |
| Cola | Redis 7 |
| Motor de voz | Seed-VC (subprocess en venv aislado Python 3.10) |
| Audio | librosa, soundfile, numpy, resemblyzer |
| Auth (app) | JWT (PyJWT) + PBKDF2-SHA256 |
| Storage | S3-compatible filesystem adapter |
| Landing | Next.js 15 (App Router) + TypeScript + Tailwind CSS 4 |
| Auth (landing) | Auth0 (`@auth0/nextjs-auth0` v3) |
| Pagos | Wompi (COP, PSE, Nequi, tarjetas) |
| Infra | Docker Compose |

## Estructura del monorepo

```
VoiceForge/
├── apps/
│   └── voiceforge_flutter/        # Cliente Flutter (Android + iOS + Web)
│       └── lib/
│           ├── app/                # Router, theme, design system VF*
│           ├── core/               # Network, session, repositories, services
│           └── features/           # auth, dashboard, voices, conversions, onboarding
├── packages/
│   └── voiceforge_core/           # Paquete Python compartido (API + Worker)
│       └── src/voiceforge_core/
│           ├── audio/              # Pipeline: load, trim, normalize, VAD, scoring
│           ├── db/                 # Modelos SQLAlchemy + enums
│           ├── inference/          # ABC + Seed-VC real impl + ModelRegistry
│           ├── jobs/               # RedisJobQueue
│           ├── modules/            # Domain services
│           └── storage/            # StorageProvider ABC + LocalS3CompatibleStorage
├── services/
│   ├── api/                       # FastAPI REST
│   │   └── app/api/routes/         # auth, users, voice_profiles, training_jobs,
│   │                               #   conversion_jobs, audit, health, ws
│   └── worker/                    # Polling loop sobre Redis
├── web/
│   └── landing/                   # Next.js 15 — landing comercial + checkout Wompi
├── external/seed-vc/              # Repo de Seed-VC + venv aislado (gitignored)
├── infra/
│   ├── docker/
│   └── scripts/                   # Demo, benchmark, profiling
├── docs/                          # Architecture, Seed-VC, setup de credenciales
├── tests/                         # pytest
└── docker-compose.yml             # postgres + redis + api + worker
```

## Cómo correrlo

### Backend

```bash
# 1. Infra
docker compose up -d postgres redis

# 2. Dependencias (desde la raíz)
pip install -e ./packages/voiceforge_core
pip install -r ./services/api/requirements.txt

# 3. Migraciones
cd services/api && alembic upgrade head

# 4. API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Worker (otra terminal)
cd services/worker && python -m worker_app.main
```

### Cliente Flutter

```bash
cd apps/voiceforge_flutter
flutter pub get
flutter run -d chrome           # Web
flutter run -d <android_id>     # Android
```

### Motor Seed-VC (para conversión real)

```powershell
./infra/scripts/install_seed_vc.ps1
./infra/scripts/run_seed_vc_demo.ps1
```

El primer script instala el runtime oficial en `external/seed-vc/` con su propio
venv. El segundo genera audios demo y corre una conversión end-to-end.

### Landing + checkout

```bash
cd web/landing
npm install
npm run dev          # http://localhost:3000
```

Requiere credenciales de Auth0 y Wompi en `.env.local` — ver
[`web/landing/.env.example`](web/landing/.env.example).

### Tests

```bash
pip install pytest pytest-asyncio httpx
pytest

cd apps/voiceforge_flutter && flutter test
```

## Documentación interna

| Documento | Contenido |
|-----------|-----------|
| [`docs/architecture.md`](docs/architecture.md) | Arquitectura del sistema, módulos, flujos |
| [`docs/seed-vc.md`](docs/seed-vc.md) | Integración Seed-VC offline, instalación, validación local |
| [`docs/seed-vc-profiling.md`](docs/seed-vc-profiling.md) | Profiling por stage, cold vs warm benchmark |
| [`docs/seed-vc-reference-cache.md`](docs/seed-vc-reference-cache.md) | Cache de referencia, invalidación, runtime residente |
| [`docs/seed-vc-source-optimization.md`](docs/seed-vc-source-optimization.md) | Cache de fuente y experimentos de `diffusion_steps` |
| [`docs/seed-vc-quality-vs-speed.md`](docs/seed-vc-quality-vs-speed.md) | Evaluación calidad-vs-velocidad para Studio mode |

## Decisiones de arquitectura

- **Seed-VC vía subprocess** — su stack pesado y version-locked obliga a aislarlo
  del backend principal. La comunicación CLI + WAV es robusta y permite mover
  el motor a otra máquina sin tocar la API.
- **Feature caching versionado** — features grandes en disco con versión asociada
  al `voice_profile_id`. Bump de versión invalida en cascada de forma determinista.
- **Resident runtime opcional** — sidecar que mantiene modelos calientes en RAM
  para conversiones repetidas sub-segundo.
- **Embeddings con fallback** — `ResemblyzerSpeakerEmbeddingService` (GE2E 256-dim)
  como primario; `HashSpeakerEmbeddingService` (SHA-256 determinista) como fallback
  cuando la lib no está instalada, para no romper el flow de desarrollo.
- **API sync, no async** — SQLAlchemy 2.0 con sesiones sync; la concurrencia
  vive en el worker, no en el handler HTTP.
- **DI via `RuntimeContainer`** — `build_runtime()` crea todos los services y
  los inyecta vía FastAPI `Depends`. Tests sustituyen el container.
- **Landing desacoplada del core** — `web/landing/` es un proyecto Next.js
  independiente con su propio deploy (Vercel/Netlify). Los endpoints de pago
  viven ahí, no en FastAPI, para minimizar cross-origin con Auth0.
- **Signed download URLs** — el botón "Descargar APK" no entrega un link directo;
  llama a `/api/download` que firma un token HMAC-SHA256 con expiry de 1h. Evita
  que un enlace compartido en redes deje de ser un asset privado.
- **Suscripción mensual freemium** — Gratis (3 conversiones/mes, watermark),
  Pro (50/mes, $29,900 COP), Unlimited ($79,900 COP). Decidido tras análisis
  competitivo (ElevenLabs, Resemble.AI, Kits.AI, Voicemod) — un pago único
  de $5,000 COP no cubría coste de GPU + fees.
- **Wompi sobre Stripe** — Stripe no soporta PSE ni Nequi en Colombia. Wompi
  da COP nativo, PSE, Nequi y respaldo Bancolombia con fees ~3%.

## Estado actual

✅ Backend funcional con Seed-VC real integrado y benchmarks medidos
✅ Cliente Flutter completo: auth, dashboard, perfiles, grabación de samples, conversiones, historial
✅ Grabación con `record`, reproducción con `just_audio`, waveform player con isolate
✅ Suite de tests pytest cubriendo audio pipeline, auth e integración
✅ Landing Next.js + checkout Wompi + Auth0 + signed download URLs
✅ Cumplimiento legal Colombia (privacidad, términos, reembolso, consentimiento)
✅ WebSocket de notificaciones en tiempo real con Redis pub/sub
✅ Onboarding 3-page + iOS platform setup

🟡 Faltan: CI/CD pipeline, Docker para inferencia con GPU, base de datos
persistente para compras (hoy en memoria), tokenization Wompi para
suscripciones recurrentes reales.
