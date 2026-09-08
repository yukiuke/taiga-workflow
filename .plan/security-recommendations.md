# Security Suggestions

The **simplest, lowest-friction, zero-trust security stack** relies on standard infrastructure tools: **SSH Tunnels (stdio pipe)** for the Agent-to-MCP connection, and **Caddy** for local web browser access.

## The Low-Friction Security Architecture

```
[ Local Machine ]                          [ VPS Hostinger ]
+-------------------------+                +-------------------------+
| Local LATs              |                | Firewall (UFW)          |
| (Cursor/Claude Desktop) |                |   - Port 22 (SSH Open)  |
|                         |                |   - Ports 80/443 (Web)  |
|   | (MCP via stdio)     |                |                         |
|   v                     |                |                         |
| Local SSH Client -------|-- SSH Tunnel ->| SSH Daemon (Port 22)    |
+-------------------------+  (Port 22)     |   |                     |
                                           |   +-> Taiga MCP Container
                                           |       (stdio over docker)
                                           |
[ Human Browser ]                          |
  https://taiga.yourdomain.com ----------->| Caddy Reverse Proxy     |
                                           |   |                     |
                                           |   +-> Taiga Docker Net  |
                                           +-------------------------+
```

## Core Security Layers

### 1. Zero-Exposure Agent Access (SSH Tunneling via stdio)

Instead of launching the Taiga MCP server over an HTTP/SSE port exposed to the internet, run the MCP server executable **directly on the VPS over SSH**.

Your local agent (Cursor, Claude, or custom script) initiates a subprocess command via `ssh`. The MCP stdio stream pipes directly through the encrypted SSH channel without exposing any extra ports on the server.

#### Configuration Example (`mcp.json` on local machine):

JSON

```
{
  "mcpServers": {
    "taiga-mcp": {
      "command": "ssh",
      "args": [
        "-i", "~/.ssh/vps_taiga_key",
        "-T",
        "deploy@your-vps-ip",
        "docker exec -i taiga-mcp-container taiga-mcp-server"
      ]
    }
  }
}
```

- **Why it’s secure:** Zero new inbound firewall ports are opened. No authorization headers or JWT tokens are sent across HTTP. Authentication uses SSH Public Key Infrastructure (`Ed25519`).

- **Why it’s low-friction:** It relies on `ssh`, which is pre-installed on Linux, macOS, and Windows. No complex gateway setup is required.

### 2. Minimal VPS Firewall (UFW) Policy

Strictly limit inbound traffic at the OS layer.

Bash

```
# Default deny
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow standard web and SSH only
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # Web (Cert verification)
sudo ufw allow 443/tcp  # Web (HTTPS)

sudo ufw enable
```

### 3. Caddy for Web Browser Access (Self-Managed HTTPS)

For human access (e.g., viewing boards, clearing flags, or updating user stories), avoid manually configuring Nginx or Let's Encrypt certbot cron jobs. Use **Caddy** as a lightweight reverse proxy.

#### `Caddyfile` Example:

Code snippet

```
taiga.yourdomain.com {
    reverse_proxy localhost:9000
}
```

- **Why it's low-friction:** Caddy automatically provisions and updates Let's Encrypt/ZeroSSL TLS certificates with zero manual setup.

- **Security boundary:** Human browser traffic goes over HTTPS \rightarrow Caddy \rightarrow Local Docker network (`localhost:9000`). Agent traffic circumvents Caddy entirely, running straight through SSH.

### 4. Hardened SSH Configuration (`/etc/ssh/sshd_config.d/taiga.conf`)

Ensure the SSH access point is locked down against brute-force attempts:

Ini, TOML

```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AllowUsers deploy
```

## Implementation Checklist

| **Task**                   | **Component**                                                      | **Effort** |
| -------------------------- | ------------------------------------------------------------------ | ---------- |
| **1. SSH Keys**            | Generate dedicated `Ed25519` keypair for local agent use.          | ~2 mins    |
| **2. Firewall Setup**      | Apply UFW rules (Port 22, 80, 443 only).                           | ~1 min     |
| **3. Caddy Reverse Proxy** | Spin up Caddy container or binary bound to `taiga.yourdomain.com`. | ~3 mins    |
| **4. Local MCP Config**    | Add the `ssh` wrapper command into local `mcp.json`.               | ~2 mins    |

## Why This Beats HTTP/SSE Gateways

1. **No Token Storage in Code:** Credentials live safely in local SSH keys or local `ssh-agent` sessions rather than API tokens in HTTP headers or local files.

2. **Zero Maintenance:** No OAuth middleware, reverse proxy certs for local tools, or IP whitelisting to manage.

3. **Identical Local/Remote Experience:** Local LATs interact with the remote Taiga MCP server as if it were running on `localhost`.
