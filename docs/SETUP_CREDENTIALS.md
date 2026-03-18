# Guía de configuración de credenciales — VoiceForge

Paso a paso para configurar todos los servicios externos que necesita VoiceForge.

---

## 1. Auth0 (autenticación de la landing page)

### 1.1 Crear cuenta

1. Ve a **https://auth0.com/signup**
2. Regístrate con tu email o con GitHub/Google
3. Cuando te pida crear un **tenant**, usa:
   - **Tenant domain**: `voiceforge` (resultará en `voiceforge.auth0.com`)
   - **Region**: `US` (más cercana a la mayoría de usuarios)

### 1.2 Crear la Application

1. En el dashboard (`https://manage.auth0.com/`), ve a **Applications → Applications**
2. Haz clic en **"+ Create Application"**
3. Configura:
   - **Name**: `VoiceForge Landing`
   - **Application Type**: selecciona **Regular Web Applications**
4. Haz clic en **Create**

### 1.3 Configurar la Application

Ve a la pestaña **Settings** de la application que acabas de crear y configura:

| Campo | Valor (desarrollo local) | Valor (producción) |
|-------|--------------------------|---------------------|
| **Allowed Callback URLs** | `http://localhost:3000/api/auth/callback` | `https://tudominio.com/api/auth/callback` |
| **Allowed Logout URLs** | `http://localhost:3000` | `https://tudominio.com` |
| **Allowed Web Origins** | `http://localhost:3000` | `https://tudominio.com` |

> Si necesitas ambos entornos simultáneamente, sepáralos con coma: `http://localhost:3000, https://tudominio.com`

Haz scroll hasta abajo y haz clic en **"Save Changes"**.

### 1.4 Obtener credenciales

En la misma pestaña **Settings**, encuentra:

| Credencial | Ubicación en el dashboard |
|------------|--------------------------|
| **Domain** | Parte superior, campo "Domain" (ej: `voiceforge.auth0.com`) |
| **Client ID** | Parte superior, campo "Client ID" |
| **Client Secret** | Parte superior, campo "Client Secret" (clic en el ojo para revelarlo) |

### 1.5 Habilitar Google como Social Connection

1. En el menú lateral, ve a **Authentication → Social**
2. Busca **Google / Gmail** y haz clic en él
3. Activa el toggle para habilitarlo
4. Para desarrollo, puedes usar las credenciales de desarrollo de Auth0 (vienen pre-configuradas)
5. Para producción:
   - Ve a **https://console.cloud.google.com/**
   - Crea un proyecto nuevo o usa uno existente
   - Ve a **APIs & Services → Credentials → Create Credentials → OAuth client ID**
   - Tipo: Web application
   - Authorized redirect URI: `https://voiceforge.auth0.com/login/callback`
   - Copia el **Client ID** y **Client Secret** de Google al formulario de Auth0
6. En la pestaña **Applications** del connection de Google en Auth0, asegúrate de que tu app `VoiceForge Landing` esté activada

### 1.6 Mapeo a .env.local

Crea el archivo `web/landing/.env.local` con estos valores:

```env
# Auth0
AUTH0_SECRET=<genera con: openssl rand -hex 32>
AUTH0_BASE_URL=http://localhost:3000
AUTH0_ISSUER_BASE_URL=https://voiceforge.auth0.com
AUTH0_CLIENT_ID=<Client ID del dashboard>
AUTH0_CLIENT_SECRET=<Client Secret del dashboard>
```

Para generar `AUTH0_SECRET` en PowerShell:
```powershell
-join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Max 256) })
```

O en bash/WSL:
```bash
openssl rand -hex 32
```

---

## 2. Wompi (pasarela de pagos Colombia)

### 2.1 Crear cuenta

1. Ve a **https://comercios.wompi.co/registro**
2. Completa el registro con tus datos
3. Verifica tu correo electrónico

### 2.2 Acceder al dashboard

1. Inicia sesión en **https://comercios.wompi.co**
2. Por defecto estarás en el entorno de **Sandbox** (pruebas)

### 2.3 Obtener llaves

En el dashboard de Wompi, ve a **Configuración → Llaves** (o el menú equivalente de API Keys):

| Llave | Prefijo (Sandbox) | Prefijo (Producción) | Uso |
|-------|-------------------|----------------------|-----|
| **Llave pública** | `pub_test_` | `pub_prod_` | Frontend (widget de checkout) |
| **Llave privada** | `prv_test_` | `prv_prod_` | Backend (crear transacciones, consultar estado) |
| **Llave de eventos** | — | — | Verificar firma de webhooks (SHA256) |

> **Importante**: La **llave de eventos** (events secret) es diferente a la llave privada. Se encuentra en la sección de **Eventos/Webhooks** del dashboard, no en la sección de llaves de API.

### 2.4 Configurar webhook

1. En el dashboard de Wompi, ve a **Configuración → Eventos** (o **Webhooks**)
2. Haz clic en **"Agregar endpoint"** (o "Configurar webhook")
3. Configura:
   - **URL del endpoint**:
     - Desarrollo: usa **ngrok** o similar para exponer tu localhost → `https://TU_SUBDOMINIO.ngrok.io/api/payments/webhook`
     - Producción: `https://tudominio.com/api/payments/webhook`
   - **Eventos a suscribir**: `transaction.updated` (el más importante — notifica cambios de estado en transacciones)
4. Guarda la configuración
5. Copia la **llave de eventos** que te muestra Wompi después de configurar el webhook

### 2.5 Activar medios de pago

En el dashboard, ve a **Medios de pago** y activa:
- **Tarjetas de crédito/débito** (Visa, Mastercard, Amex)
- **PSE** (transferencia bancaria)
- **Nequi** (billetera digital)
- **Bancolombia** (transferencias QR)

> Nota: en Sandbox todos los medios están habilitados por defecto para pruebas.

### 2.6 Mapeo a .env.local

Agrega al archivo `web/landing/.env.local`:

```env
# Wompi
NEXT_PUBLIC_WOMPI_PUBLIC_KEY=pub_test_XXXXXXXXXX
WOMPI_PRIVATE_KEY=prv_test_XXXXXXXXXX
WOMPI_EVENTS_SECRET=test_events_XXXXXXXXXX
WOMPI_ENVIRONMENT=sandbox
```

### 2.7 Transacción de prueba en Sandbox

Wompi provee datos de prueba para Sandbox:

| Dato | Valor de prueba |
|------|-----------------|
| **Número de tarjeta** | `4242 4242 4242 4242` |
| **Fecha de expiración** | Cualquier fecha futura (ej: `12/29`) |
| **CVC** | `123` |
| **Nombre en la tarjeta** | Cualquier nombre |
| **Email** | Tu email real (para recibir notificaciones) |

Para PSE de prueba, la pasarela te mostrará un banco ficticio.

Flujo de prueba:
1. `cd web/landing && npm run dev`
2. Abre `http://localhost:3000`
3. Haz clic en "Comprar" → inicia sesión con Auth0
4. Acepta los checkboxes legales y haz clic en "Pagar"
5. Usa los datos de tarjeta de prueba
6. Verifica que el webhook llegue (revisa los logs de tu servidor)
7. Verifica que el estado de compra se registre

---

## 3. Backend principal (FastAPI)

### 3.1 Variables de entorno

El backend usa el prefijo `VF_` para todas sus variables. Crea un archivo `.env` en la raíz del proyecto:

```env
# Core
VF_APP_NAME=VoiceForge API
VF_ENVIRONMENT=development
VF_API_HOST=0.0.0.0
VF_API_PORT=8000

# Base de datos
VF_DATABASE_URL=postgresql+psycopg://voiceforge:voiceforge@localhost:5432/voiceforge

# Redis
VF_REDIS_URL=redis://localhost:6379/0

# Storage
VF_STORAGE_ROOT=./data/storage
VF_STORAGE_BUCKET=voiceforge-local

# Jobs
VF_JOB_QUEUE_NAME=voiceforge:jobs

# Auth (JWT para la app Flutter)
VF_JWT_SECRET=<genera con: openssl rand -hex 32>
VF_ACCESS_TOKEN_EXP_MINUTES=1440

# Límites
VF_MAX_UPLOAD_MB=50
VF_RATE_LIMIT_PER_MINUTE=120

# CORS
VF_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:5173

# Seed-VC (motor de voz)
VF_SEED_VC_PYTHON=python
VF_SEED_VC_REPO_DIR=./external/seed-vc
VF_SEED_VC_WORKING_ROOT=./data/seed-vc
VF_SEED_VC_DIFFUSION_STEPS=25
VF_SEED_VC_LENGTH_ADJUST=1.0
VF_SEED_VC_INFERENCE_CFG_RATE=0.7
VF_SEED_VC_F0_CONDITION=false
VF_SEED_VC_AUTO_F0_ADJUST=false
VF_SEED_VC_SEMI_TONE_SHIFT=0
VF_SEED_VC_FP16=false
VF_SEED_VC_TIMEOUT_SECONDS=3600
VF_SEED_VC_TARGET_SAMPLE_RATE=22050
VF_SEED_VC_REFERENCE_MAX_SECONDS=25.0
VF_SEED_VC_REFERENCE_CLIP_LIMIT=3
VF_SEED_VC_REFERENCE_CACHE_ENABLED=true
VF_SEED_VC_SOURCE_CACHE_ENABLED=true
VF_SEED_VC_RESIDENT_REFERENCE_RUNTIME_ENABLED=true
VF_SEED_VC_RESIDENT_SOURCE_RUNTIME_ENABLED=true
VF_SEED_VC_RESIDENT_RUNTIME_IDLE_SECONDS=900
VF_SEED_VC_RESIDENT_RUNTIME_LAUNCH_TIMEOUT_SECONDS=120
```

### 3.2 Variables opcionales (Seed-VC avanzado)

Estas solo se necesitan si usas checkpoints personalizados:

```env
VF_SEED_VC_CHECKPOINT_PATH=          # Ruta a .pth personalizado
VF_SEED_VC_CONFIG_PATH=              # Ruta a config YAML
VF_SEED_VC_HF_ENDPOINT=             # Endpoint de HuggingFace alternativo
```

### 3.3 Base de datos

Para desarrollo local con Docker:

```bash
docker compose up -d postgres redis
```

Para desarrollo sin Docker, necesitas PostgreSQL 17 y Redis 7 instalados localmente. Ajusta `VF_DATABASE_URL` y `VF_REDIS_URL` según corresponda.

---

## 4. Resumen de archivos de configuración

| Archivo | Ubicación | Para qué |
|---------|-----------|----------|
| `.env` | Raíz del proyecto | Backend FastAPI + Worker |
| `web/landing/.env.local` | Landing page | Auth0 + Wompi + App URL |
| `.env.example` | Raíz del proyecto | Template del backend (versionado) |
| `web/landing/.env.example` | Landing page | Template de la landing (versionado) |

> **Nunca** subas `.env` o `.env.local` al repositorio. Están incluidos en `.gitignore`.

---

## 5. Variables nuevas de Fase 2B vs preexistentes

| Variable | Fase | Servicio |
|----------|------|----------|
| `VF_DATABASE_URL` | Original | Backend |
| `VF_REDIS_URL` | Original | Backend |
| `VF_JWT_SECRET` | Original | Backend |
| `VF_SEED_VC_*` (19 vars) | Original | Backend |
| `AUTH0_SECRET` | **2B** | Landing |
| `AUTH0_BASE_URL` | **2B** | Landing |
| `AUTH0_ISSUER_BASE_URL` | **2B** | Landing |
| `AUTH0_CLIENT_ID` | **2B** | Landing |
| `AUTH0_CLIENT_SECRET` | **2B** | Landing |
| `NEXT_PUBLIC_WOMPI_PUBLIC_KEY` | **2B** | Landing |
| `WOMPI_PRIVATE_KEY` | **2B** | Landing |
| `WOMPI_EVENTS_SECRET` | **2B** | Landing |
| `WOMPI_ENVIRONMENT` | **2B** | Landing |
| `NEXT_PUBLIC_APP_URL` | **2B** | Landing |
| `VOICEFORGE_API_URL` | **2B** | Landing |

---

## 6. Exposición local para webhooks (desarrollo)

Wompi necesita enviar webhooks a una URL pública. Para desarrollo local:

### Opción A: ngrok

```bash
# Instalar ngrok: https://ngrok.com/download
ngrok http 3000
```

Esto te dará una URL como `https://abc123.ngrok.io`. Configura esta URL + `/api/payments/webhook` como tu endpoint de webhook en el dashboard de Wompi.

### Opción B: Cloudflare Tunnel

```bash
# Instalar: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/
cloudflared tunnel --url http://localhost:3000
```

---

## Checklist de configuración

```
[ ] Auth0: tenant creado en https://auth0.com
[ ] Auth0: application "VoiceForge Landing" creada (Regular Web Application)
[ ] Auth0: Allowed Callback URLs configurado con /api/auth/callback
[ ] Auth0: Allowed Logout URLs configurado
[ ] Auth0: Allowed Web Origins configurado
[ ] Auth0: Google social connection habilitada
[ ] Auth0: variables en web/landing/.env.local (5 variables)
[ ] Wompi: cuenta creada en https://comercios.wompi.co
[ ] Wompi: llaves sandbox obtenidas (pública, privada, eventos)
[ ] Wompi: webhook configurado apuntando a /api/payments/webhook
[ ] Wompi: variables en web/landing/.env.local (4 variables)
[ ] Wompi: transacción de prueba exitosa con tarjeta 4242...
[ ] Backend: .env creado en raíz con todas las VF_ variables
[ ] Backend: PostgreSQL y Redis accesibles
[ ] Backend: migraciones ejecutadas (alembic upgrade head)
[ ] Landing: npm run dev funciona sin errores en http://localhost:3000
[ ] Flujo completo: registro → login → checkout → pago sandbox → webhook → descarga
```
