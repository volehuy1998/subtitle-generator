# Scripts

Operational scripts for the subtitle-generator service.

## Certbot Auto-Renewal Hook

`renew-certs.sh` is called by certbot after a successful certificate renewal. It copies the new
certificates into the project directory and restarts the Docker container.

**To activate certbot auto-renewal:**

```bash
sudo ln -sf /home/claude-user/subtitle-generator/scripts/renew-certs.sh \
    /etc/letsencrypt/renewal-hooks/deploy/
```

Certbot will then call this script automatically after each successful renewal.

## Fail2ban Configuration

The `fail2ban/` directory contains a filter definition and two jail configs that protect the
service against brute-force and abuse.

| File | Purpose |
|------|---------|
| `fail2ban/filter.d/subtitle-generator.conf` | Regex rules matching auth failures and HTTP error bursts |
| `fail2ban/jail.d/subtitle-generator.conf` | Two jails: auth failures (ban 1 h) and HTTP flood (ban 10 min) |

**To install:**

```bash
# Copy filter and jail configs into fail2ban's config directories
sudo cp fail2ban/filter.d/subtitle-generator.conf /etc/fail2ban/filter.d/
sudo cp fail2ban/jail.d/subtitle-generator.conf   /etc/fail2ban/jail.d/

# Reload fail2ban to pick up the new rules
sudo fail2ban-client reload
```

Verify the jails are active:

```bash
sudo fail2ban-client status subtitle-generator-auth
sudo fail2ban-client status subtitle-generator-http
```
