# fast_deploy_llm

**fast_deploy_llm** is a small FastAPI service to expose **OpenAI-compatible** HTTP endpoints (`/v1`-shaped paths under `/api/v1`). **Right Now** the inference backend is **Amazon Bedrock** (LangChain `ChatBedrockConverse`). The layout is intentionally boring route handlers + a `core/` layer so you can **add other providers** (Vertex, Azure OpenAI, local Ollama/vLLM, etc.) behind the same API surface.

Run it yourself, point any OpenAI-compatible client at it, and keep **API keys**, **usage**, and **model aliases** under your control.

## Why use this

- **Drop-in for OpenAI SDKs and tools** that accept a custom base URL and API key.
- **One place to map** friendly model names → provider-specific IDs (Bedrock: `config/bedrock.py`; future providers beside or instead of Bedrock).
- **Optional auth**: single shared key, or multiple **`sk-…`** keys issued via an admin API; **JSONL usage logs** per key under `logs/`.
- **Streaming and non-streaming** chat completions with provider-reported token usage when the backend exposes it (Bedrock today).
- **Extensible**: swap or combine backends without changing clients that speak OpenAI-style `/chat/completions`.

## Example use cases

| Use case | What you do |
|----------|----------------|
| **Cursor** | In model / OpenAI-compatible provider settings, set **Base URL** to `https://<your-host>/api/v1` (or `http://127.0.0.1:4000/api/v1` locally) and **API key** to `BEDROCK_ENDPOINT_API_KEY` or an admin-issued `sk-…` key. |
| **Continue.dev** | Point the OpenAI-compatible endpoint at the same base URL; use the same header key as above. |
| **Self-hosted “OpenAI API” on Bedrock** | Run uvicorn (systemd, screen, or manual); optionally put **nginx** + **certbot** in front yourself; clients use `/api/v1/chat/completions` and `/api/v1/models`. |
| **Internal gateway** | Centralize Bedrock credentials (instance role or keys), rate limits at the edge, and audit usage via `logs/usage.jsonl` and `GET /api/v1/admin/usage`. |

Exact UI steps for Cursor and Continue.dev change between versions; look for **custom OpenAI-compatible URL**, **override base URL**, or **BYOK**-style provider settings.

## Requirements

- Python **3.11+**
- **Bedrock path (current default):** AWS credentials with permission to invoke your chosen models (API key and/or default boto3 chain), and models enabled in your account/region (`config/bedrock.py` aliases must match what you provisioned).

## Quick start

```bash
cd fast_llm_deploy   # or your clone directory
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip wheel
pip install -r requirements.txt

cp config/.env.example config/.env
# Edit config/.env — at minimum AWS_REGION and either IAM env vars or a Bedrock-capable role.

uvicorn main:backend_app --host 0.0.0.0 --port 4000
```

- **Interactive docs:** `http://127.0.0.1:4000/docs`
- **OpenAI-compatible base path:** `/api/v1`  
  - `GET /api/v1/models`  
  - `POST /api/v1/chat/completions`

## Configuration (`config/.env`)

Create **`config/.env`** from the template:

```bash
cp config/.env.example config/.env
```

Pydantic loads **`config/.env`** first, then an optional **repo-root `.env`** (later overrides on duplicate keys). See **`config/.env.example`** for every variable with comments.

| Variable | Purpose |
|----------|---------|
| `AWS_REGION` | Bedrock region (default in code: `ap-south-1`). |
| `AWS_BEDROCK_API_KEY` | Optional; passed through to LangChain when set. Often left unset so **boto3** uses `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`, SSO, or an **IAM role** on the host. |
| `BEDROCK_ENDPOINT_API_KEY` | Optional “gate” for clients calling **`/api/v1/*`**. If set **or** you have created keys via admin, clients must send `X-API-Key` or `Bearer`. |
| `ADMIN_API_KEY` | Protects **`/api/v1/admin/*`**. If unset, admin routes return **503**. |
| `SERVER_HOST`, `SERVER_PORT`, `SERVER_WORKERS` | Local / process tuning (systemd deploy script uses **127.0.0.1:8000** independently). |
| `DEBUG`, `LOGGING_LEVEL` | Development and logging verbosity. |

**Model list** is not controlled by `.env`; edit **`config/bedrock.py`** (`MODELS` dict). **GET `/api/v1/admin/models`** returns the current map for operators.

## Extending to other providers

The public contract is **OpenAI-style** `/models` and `/chat/completions`. To add another vendor, introduce a backend module under `core/` (or branch inside existing helpers), wire model IDs in config, and route `chat_completions` to the right implementation. Env vars in **`config/.env.example`** will grow per provider (e.g. Azure or GCP keys); keep **endpoint auth** (`BEDROCK_ENDPOINT_API_KEY` / `sk-…` keys / admin API) as the stable gate for clients.

## Admin API (keys & usage)

All require **`ADMIN_API_KEY`** as `X-Admin-Key` or `Authorization: Bearer`.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/admin/keys` | Body `{"label":"optional"}`. Returns **`api_key`** once (`sk-…`) plus `id`, `prefix`. |
| `GET` | `/api/v1/admin/keys` | List keys (no secrets). |
| `DELETE` | `/api/v1/admin/keys/{key_id}` | Revoke a key. |
| `GET` | `/api/v1/admin/usage` | Tail of **`logs/usage.jsonl`**. |
| `GET` | `/api/v1/admin/usage/summary` | Aggregates per key over recent events. |
| `GET` | `/api/v1/admin/models` | Current `MODELS` map (read-only). |

Persisted files (default under repo root):

- `logs/usage.jsonl` — one JSON object per completion (tokens and/or streamed character counts, key id, model).
- `logs/api_keys.json` — key metadata and **hashed** secrets.

## Production deploy (Linux)

Prepare a Python environment yourself (e.g. `python3 -m venv ~/.venv && pip install -r requirements.txt`). Then install the **systemd** unit:

```bash
./scripts/deploy.sh
```

This only writes **`/etc/systemd/system/llm-deploy.service`** (placeholders: `__REPO_ROOT__`, `__DEPLOY_USER__`, `__VENV__`), reloads systemd, and **enable + restart** `llm-deploy.service`. Default venv path is **`$HOME/.venv`** for the service user; override with **`LLM_DEPLOY_VENV`** or **`VENV`**.

**Turn it off:** `./scripts/deploy.sh disable` (same as `sudo systemctl disable --now llm-deploy.service`). The unit file stays on disk; remove it manually if you want.

**Reverse proxy / TLS:** use `deploy/nginx/llm-deploy.conf` and `deploy/certbot-init.sh` manually if you want nginx and HTTPS — they are not run by `deploy.sh`.

## Scripts

- `scripts/deploy.sh` — **systemd only** (`disable` turns the service off; no pip/nginx/certbot).
- `scripts/test_endpoint.sh` — example `curl` calls (adjust host/path if yours differ; this repo serves OpenAI routes under **`/api/v1`**, not bare `/v1`).

## Suggested GitHub metadata

If you publish this repo, a clear name and description help discovery.

| | Suggestion |
|---|-------------|
| **Repository name** | **`fast_llm_deploy`** (or **`fast-llm-deploy`** if you prefer the usual GitHub kebab-case URL) |
| **Tagline / description** (≈ one line) | *Fast self-hosted OpenAI-compatible LLM gateway — Bedrock today; extend to more providers. Works with Cursor, Continue.dev, and any OpenAI client.* |

---

MIT or your preferred license; follow each cloud/vendor’s terms, quotas, and pricing (e.g. AWS Bedrock) when you connect backends.
