# Deployment Guide

SubForge ships with a single script that handles everything:
packages, TLS certificates, virtual environments or Docker, systemd, and health verification.
One command is all you need.

---

## Quick start

```bash
# 1. Download the script (run as root on the target server)
curl -fsSL https://raw.githubusercontent.com/volehuy1998/subtitle-generator/main/scripts/deploy.sh \
  -o deploy.sh

# 2a. Development mode — HTTP only, no certificate needed
sudo bash deploy.sh --mode dev

# 2b. Production mode — HTTPS via Let's Encrypt (bare-metal)
sudo bash deploy.sh --domain example.com --email admin@example.com

# 2c. Production mode — HTTPS via Let's Encrypt + Docker
sudo bash deploy.sh --domain example.com --email admin@example.com --docker
```

When the script finishes it prints the live URLs and useful management commands.

---

## Requirements

| Requirement | Notes |
|---|---|
| Ubuntu Server 24.04 LTS | Other Debian-based distros may work but are untested |
| Root / sudo access | The script must run as root |
| Public IP + DNS (prod) | Your domain must point to this server before running |
| Ports 80 and 443 open (prod) | 80 is used briefly for the ACME challenge, then for HTTP→HTTPS redirect |
| Port 8000 open (dev) | Only needed for local / private access |

The script installs everything else (Python 3, ffmpeg, git, certbot, Docker, etc.).

---

## Modes

### Development mode (`--mode dev`)

- Runs on **HTTP port 8000** — no certificate required.
- Suitable for local testing, air-gapped servers, or evaluating SubForge before going public.
- Use `--mode dev` explicitly, **or** simply omit `--domain` and the script switches automatically.

```bash
sudo bash deploy.sh --mode dev
# → App at http://SERVER_IP:8000
```

### Production mode (default when `--domain` is provided)

- Runs on **HTTPS port 443** with an automatic HTTP → HTTPS redirect on port 80.
- Requires a public domain that resolves to the server's IP address.

```bash
sudo bash deploy.sh --domain example.com --email admin@example.com
# → App at https://example.com
```

---

## TLS certificates

### Option A — Let's Encrypt (recommended)

Provide `--domain` and `--email`.  The script:

1. Installs certbot.
2. Temporarily stops port 80 if needed.
3. Runs `certbot certonly --standalone`.
4. Writes a renewal hook so the service reloads automatically after each renewal.

Renewal runs unattended via the `certbot.timer` systemd timer.  To test it:

```bash
sudo certbot renew --dry-run
```

### Option B — Bring your own certificate

If you already have a certificate (from your CA, an internal PKI, a wildcard cert, etc.),
pass the paths directly and Let's Encrypt is skipped entirely:

```bash
sudo bash deploy.sh \
  --domain example.com \
  --cert /etc/ssl/certs/fullchain.pem \
  --key  /etc/ssl/private/privkey.pem
```

The files are referenced in-place; the script does not copy or move them.

---

## Deployment engines

### Bare-metal (default)

The script creates a Python virtualenv at `<install-dir>/.venv`, installs all
dependencies from `requirements.txt`, and registers a **systemd** service called
`subforge`.

```bash
sudo journalctl -u subforge -f      # live logs
sudo systemctl restart subforge     # restart
sudo systemctl status subforge      # status
```

### Docker Compose (`--docker`)

The script installs Docker Engine, builds the image, and starts the containers using
`docker compose --profile cpu` (or `--profile gpu`).

```bash
cd /opt/subtitle-generator
docker compose logs -f              # live logs
docker compose restart              # restart
docker compose --profile cpu up -d  # start CPU profile
docker compose --profile gpu up -d  # start GPU profile
```

A `.env` file is written to the install directory on first run.
Re-running the script regenerates it with any new options you pass.

---

## GPU support (`--gpu`)

Adds GPU acceleration via faster-whisper / CTranslate2.

| Runtime | What gets installed |
|---|---|
| Bare-metal | `nvidia-driver-550` + `nvidia-cuda-toolkit` via apt |
| Docker | NVIDIA Container Toolkit + docker runtime configuration |

After a fresh driver install on bare-metal, **a reboot is required** to load the kernel
module.  The script warns you if this applies.

---

## All options

```
--mode dev|prod     HTTP only (dev) or HTTPS (prod). Default: prod when --domain is set.
--domain DOMAIN     Public domain name (e.g. example.com). Required for prod.
--email  EMAIL      Email for Let's Encrypt expiry notices. Required with Let's Encrypt.

--docker            Use Docker Compose instead of bare-metal systemd.
--gpu               Install NVIDIA driver / CUDA support.

--api-key KEY       Require this key for all API requests (X-API-Key header).
                    Default: open access (no key required).
--preload MODEL     Warm-start a Whisper model at launch.
                    Values: tiny | base | small | medium | large

--cert FILE         Path to TLS certificate (fullchain.pem). Skips Let's Encrypt.
--key  FILE         Path to TLS private key  (privkey.pem).  Must pair with --cert.

--install-dir DIR   Where to clone the repository. Default: /opt/subtitle-generator
--branch  BRANCH    Git branch to deploy. Default: main
--repo    URL       Override the Git repository URL.

--help              Print usage and exit.
```

---

## Configuration Best Practices

### Use a `.env` file — not CLI flags — for secrets and runtime config

CLI flags are convenient for a first deploy, but they are a poor long-term strategy:
secrets appear in shell history, re-deployments are error-prone if you mistype a value,
and there is no record of what the running service was configured with.

The recommended workflow is:

```bash
# 1. Copy the template (one time, on the server)
cp /opt/subtitle-generator/.env.example /opt/subtitle-generator/.env

# 2. Fill in your values — comments inside explain every variable
nano /opt/subtitle-generator/.env

# 3. Deploy (and re-deploy) with minimal CLI flags — secrets stay in .env
sudo bash deploy.sh --domain example.com --email admin@example.com
```

For bare-metal deployments the script writes environment variables directly into the
systemd unit.  For Docker deployments the script writes them into `.env`, which
`docker-compose.yml` reads automatically.  Either way, once `.env` is in place you only
need the structural flags (`--domain`, `--mode`, `--docker`, etc.) on the command line.

---

### What belongs in `.env`

| Variable | Why it belongs in `.env` |
|---|---|
| `API_KEYS` | Secret — must not appear in shell history |
| `HF_TOKEN` | Secret — Hugging Face download token |
| `DATABASE_URL` | Environment-specific; differs between dev / staging / prod |
| `REDIS_URL` | Infrastructure detail that doesn't belong in a CLI flag |
| `SSL_CERTFILE` / `SSL_KEYFILE` | Paths may change on renewal; centralised in one file |
| `PRELOAD_MODEL` | Affects startup time; worth documenting alongside other runtime settings |
| `FILE_RETENTION_HOURS` | Operational tuning — keep with the rest of the config |
| `CORS_ORIGINS` | Domain-specific; should match `DOMAIN` |
| `WEBHOOK_ALERT_URL` | Optional integration secret |

See [`.env.example`](../.env.example) for the full list with descriptions and defaults.

---

### What NOT to do

**Do not edit `docker-compose.yml` to hardcode configuration values.**
`docker-compose.yml` is version-controlled and shared across all deployments.
Changes made directly to that file will be overwritten the next time you pull from
`main` (the deploy script runs `git reset --hard origin/BRANCH`).  All
deployment-specific values belong in `.env`.

**Do not pass `API_KEYS` or tokens as CLI flags.**
Anything typed at the shell is saved in `.bash_history` and visible in
`/proc/<pid>/cmdline`.  Use `.env` exclusively for secrets.

**Do not commit `.env` to version control.**
The file is listed in `.gitignore`.  Commit `.env.example` with placeholder values
instead, and manage your live `.env` outside of git (or in a secrets manager).

---

### `--env-file` support (future enhancement)

The current script does not accept a `--env-file` flag to pre-seed configuration before
running.  That enhancement has been tracked as a separate feature request.  For now,
ensure `.env` exists at `<install-dir>/.env` before running the script.

---

### Reproducibility — re-deploying with the same config

To guarantee that a re-deploy (update or disaster recovery) produces an identical
configuration:

1. **Keep `.env` under external version control** (private git repo, Vault, AWS Secrets
   Manager, or even a password manager) — not in the public repository.
2. **Store the deploy command** alongside it so you always know which structural flags
   were used:

   ```bash
   # /root/deploy-cmd.sh  (chmod 700, not committed to the public repo)
   sudo bash /opt/subtitle-generator/scripts/deploy.sh \
     --domain example.com \
     --email  admin@example.com \
     --preload small
   # Secrets (API_KEYS, HF_TOKEN, etc.) are read from .env — not repeated here
   ```

3. **Re-deploy** by restoring `.env` and running the stored command:

   ```bash
   # Restore .env from your secrets manager, then:
   bash /root/deploy-cmd.sh
   ```

The script preserves `.env`, `uploads/`, and `outputs/` across updates, so existing
files and configuration are never overwritten by a re-run.

---

## Examples

```bash
# Dev, default install directory
sudo bash deploy.sh --mode dev

# Prod, Let's Encrypt, bare-metal, protect API, preload model
sudo bash deploy.sh \
  --domain example.com \
  --email  admin@example.com \
  --api-key "change-me-secret" \
  --preload small

# Prod, Let's Encrypt, Docker, GPU
sudo bash deploy.sh \
  --domain example.com \
  --email  admin@example.com \
  --docker --gpu

# Prod, bring-your-own certificate, Docker
sudo bash deploy.sh \
  --domain example.com \
  --cert /etc/ssl/certs/fullchain.pem \
  --key  /etc/ssl/private/privkey.pem \
  --docker

# Update an existing installation (re-run with the same arguments)
sudo bash deploy.sh --domain example.com --email admin@example.com
```

---

## Updating

Re-run the script with the same arguments you used to install.
It pulls the latest code (`git reset --hard origin/BRANCH`), reinstalls pip packages,
and restarts the service.  Your `.env` file and `uploads/` / `outputs/` directories are
preserved.

```bash
sudo bash /opt/subtitle-generator/scripts/deploy.sh \
  --domain example.com --email admin@example.com
```

---

## After deployment

| URL | Purpose |
|---|---|
| `https://example.com` | Main application |
| `https://example.com/status` | Public status page |
| `https://example.com/status/manage` | Incident management (requires API key if set) |
| `https://example.com/docs` | Interactive API documentation (Swagger UI) |
| `https://example.com/api/status` | JSON health & metrics |

---

## Optional: fail2ban (brute-force protection)

The `scripts/fail2ban/` directory contains ready-made filter and jail configs.
The deploy script does **not** install fail2ban automatically — set it up manually after deployment:

```bash
sudo apt-get install -y fail2ban
sudo cp /opt/subtitle-generator/scripts/fail2ban/filter.d/subtitle-generator.conf /etc/fail2ban/filter.d/
sudo cp /opt/subtitle-generator/scripts/fail2ban/jail.d/subtitle-generator.conf   /etc/fail2ban/jail.d/
sudo systemctl enable --now fail2ban
sudo fail2ban-client reload
```

Verify the jails are active:

```bash
sudo fail2ban-client status subtitle-generator-auth
sudo fail2ban-client status subtitle-generator-http
```

---

## Troubleshooting

### Service not responding after install

**Bare-metal** — check systemd logs:

```bash
sudo journalctl -u subforge -n 50 --no-pager
```

**Docker** — check container logs:

```bash
docker compose -f /opt/subtitle-generator/docker-compose.yml logs --tail=50
```

### Let's Encrypt certificate fails

- Ensure your domain's A record points to this server's public IP.
- Ensure port 80 is reachable from the internet (not firewalled at the cloud provider level).
- Run `sudo certbot renew --dry-run` to debug renewal separately.

### Port already in use

If something else is already listening on port 80 or 443, stop it before running the
script, or use `--cert` / `--key` with a BYO cert (which does not require port 80).

### GPU: model not using CUDA after install

Run `nvidia-smi` to confirm the driver loaded.  If the command is not found, reboot:

```bash
sudo reboot
```

### Docker: permission denied on cert files

Docker mounts the Let's Encrypt directory read-only.  Ensure the cert directory exists
and is readable before starting the containers:

```bash
ls -la /etc/letsencrypt/live/example.com/
```

---

## Manual installation (without the script)

If you prefer full control:

```bash
git clone https://github.com/volehuy1998/subtitle-generator /opt/subtitle-generator
cd /opt/subtitle-generator

# Copy and fill in the environment config file
cp .env.example .env
# Edit .env with your values — see comments inside for each variable
nano .env

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Dev (reads .env automatically if python-dotenv is installed, or export vars):
ENVIRONMENT=dev .venv/bin/python main.py

# Prod (with certificates already in place):
ENVIRONMENT=prod \
SSL_CERTFILE=/path/to/fullchain.pem \
SSL_KEYFILE=/path/to/privkey.pem \
.venv/bin/python main.py
```

See [`.env.example`](../.env.example) for the full list of configurable environment variables with descriptions and defaults.

---

## Docker: preview subdomain deployment (newui profile)

The `newui` Docker Compose profile runs the current codebase build on an internal port (`127.0.0.1:8001`), allowing an external nginx reverse proxy to serve it at a separate subdomain (e.g. `newui.example.com`) for design review before promoting to production.

**This is required for any frontend design changes.** See [CONTRIBUTING.md §6a](../CONTRIBUTING.md#6a-ui--frontend-design-review-process) for the full subdomain-first design review policy.

```bash
# Start the preview container (builds from current code)
docker compose --profile newui up -d --build

# Verify it is running on port 8001
curl -s http://127.0.0.1:8001/api/health | head -c 100
```

### Host nginx config (two-domain setup)

> **⚠ Reverse proxy note:** When nginx terminates TLS and proxies plain HTTP to the Docker container, **set `ENVIRONMENT=dev` inside the container** — not `ENVIRONMENT=prod`. Setting `prod` causes the app to issue 301 HTTPS redirects internally, which nginx then receives as new HTTP requests, creating an infinite redirect loop.
>
> Concretely:
> 1. **`ENVIRONMENT=dev`** in the container — the app serves plain HTTP; nginx owns all TLS and redirect logic.
> 2. **Remove cert volume mounts** from the container — nginx holds the certificates, not the app.
> 3. **`proxy_pass http://127.0.0.1:<port>`** — always plain HTTP from nginx to the container (never `https://`).
> 4. **HSTS at the nginx level** — add `add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;` in the nginx `server` block, not in the app.

A minimal nginx config that routes both the production domain and the preview subdomain:

```nginx
# /etc/nginx/sites-available/subforge

# HTTP → HTTPS redirect for both domains
server {
    listen 80;
    server_name example.com newui.example.com;
    return 301 https://$host$request_uri;
}

# Production domain → production container (pinned image)
server {
    listen 443 ssl;
    server_name example.com;

    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # HSTS is configured here at the nginx level (not in the app container)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto https;
        # SSE support
        proxy_buffering    off;
        proxy_read_timeout 3600s;
    }
}

# Preview subdomain → preview container (current build)
server {
    listen 443 ssl;
    server_name newui.example.com;

    ssl_certificate     /etc/letsencrypt/live/newui.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/newui.example.com/privkey.pem;

    location / {
        proxy_pass         http://127.0.0.1:8001;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto https;
        # SSE support
        proxy_buffering    off;
        proxy_read_timeout 3600s;
    }
}
```

### Promoting a reviewed design to production

After investor approval:

```bash
# 1. Build and tag the new production image
docker build -t subtitle-generator-prod:v2.2.0 .

# 2. Update PROD_IMAGE_TAG in .env
#    (do NOT hardcode it in docker-compose.yml)
sed -i 's/^PROD_IMAGE_TAG=.*/PROD_IMAGE_TAG=v2.2.0/' .env

# 3. Restart the production container
docker compose --profile cpu up -d
```

See `CLAUDE.md` for the full environment variable reference and architecture details.
