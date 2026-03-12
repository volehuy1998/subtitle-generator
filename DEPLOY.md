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
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Dev:
ENVIRONMENT=dev .venv/bin/python main.py

# Prod (with certificates already in place):
ENVIRONMENT=prod \
SSL_CERTFILE=/path/to/fullchain.pem \
SSL_KEYFILE=/path/to/privkey.pem \
.venv/bin/python main.py
```

See `CLAUDE.md` for the full environment variable reference and architecture details.
