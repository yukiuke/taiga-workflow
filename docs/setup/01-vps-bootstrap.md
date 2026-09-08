# 01 — VPS bootstrap (Docker, UFW, SSH)

Run these on a fresh Ubuntu/Debian VPS as a sudo-capable user, then switch to `deploy`.

## 1. System updates

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl git ufw
```

## 2. Create `deploy` user

```bash
sudo adduser --disabled-password --gecos "" deploy
sudo usermod -aG sudo deploy
```

On your **local** machine, generate a dedicated agent key (do not reuse personal keys):

```bash
ssh-keygen -t ed25519 -f ~/.ssh/vps_taiga_key -C "taiga-agent@$(hostname)"
ssh-copy-id -i ~/.ssh/vps_taiga_key.pub deploy@YOUR_VPS_IP
```

Verify:

```bash
ssh -i ~/.ssh/vps_taiga_key deploy@YOUR_VPS_IP 'echo ok'
```

## 3. Install Docker Engine + Compose plugin

```bash
# As deploy (or root) — official convenience script or distro packages.
# Example (Docker's apt repo): follow https://docs.docker.com/engine/install/ubuntu/
sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker deploy
```

Log out and back in so `docker` group applies, then:

```bash
docker version
docker compose version
```

## 4. UFW firewall

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status verbose
```

Confirm **no** other ports (especially MCP `8000`) are open.

## 5. Harden SSH

Create `/etc/ssh/sshd_config.d/taiga.conf`:

```bash
sudo tee /etc/ssh/sshd_config.d/taiga.conf >/dev/null <<'EOF'
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AllowUsers deploy
EOF

sudo sshd -t
sudo systemctl reload ssh
```

**Keep an active SSH session open** until you confirm a second session with the key still works.

## 6. Directory layout on VPS

```bash
sudo mkdir -p /opt/taiga /opt/taiga-mcp /opt/caddy /opt/backups/taiga
sudo chown -R deploy:deploy /opt/taiga /opt/taiga-mcp /opt/caddy /opt/backups
```

## Done when

- [ ] `deploy` can SSH with `~/.ssh/vps_taiga_key`
- [ ] `docker` works without root for `deploy`
- [ ] UFW shows only 22/80/443
- [ ] Root password login is disabled
