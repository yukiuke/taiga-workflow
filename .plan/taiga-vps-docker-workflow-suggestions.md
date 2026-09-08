# Feature Gaps

- **Cost & Token Management Controls:**
  
  - *Gap:* The plan mentions showing a brief summary before starting work to manage token spend, but lacks concrete constraints or token-guard limits.
  
  - *Suggestion:* Add explicit max-token/cost thresholds per ticket run in your agent rules, and enforce a dry-run mode (`--dry-run`) where the agent outputs the proposed Taiga hierarchy (Epics $\rightarrow$ User Stories $\rightarrow$ Tasks) locally in JSON/Markdown for review prior to invoking write-tools via MCP.

- **Structure of Ingested Work (Epics vs. Stories vs. Tasks):**
  
  - *Gap:* The requirements mention breaking down work into "agile actionable items" and assigning to sprints, but do not specify mapping logic for Taiga's data model.
  
  - *Suggestion:* Explicitly define the mapping rules in your custom skills:
    
    - **Epic:** High-level feature domain / theme.
    
    - **User Story:** Actionable end-user value statement + Acceptance Criteria (Definition of Done).
    
    - **Task:** Specific code/file-level implementations assigned to stories.

# Tech Gaps

- **MCP Protocol Transport & Security Boundaries:**
  
  - *Gap:* Running a local LAT (Cursor/Claude) against a remote VPS Taiga instance via MCP requires a secure transport strategy. Exposing raw MCP server endpoints over the open internet creates security risks.
  
  - *Suggestion:* Use an SSH Tu**Epic:** High-level feature domain / theme.
  
  - **User Story:** Actionable end-user value statement + Acceptance Criteria (Definition of Done).
  
  - **Task:** Specific code/file-level implementations assigned to stories.nnel (stdio over SSH) or an authenticated HTTP/SSE proxy with strict reverse proxy boundaries (e.g., Traefik/Caddy with OAuth2/mTLS) for connecting local agents to the hosted Taiga MCP server.

# Proposed Updated Deliverables & Stack Summary

| **Layer**              | **Recommended Choice**                                                      |
| ---------------------- | --------------------------------------------------------------------------- |
| **Project Management** | Taiga Docker (`taigaio/taiga-docker`) + Self-hosted Taiga MCP Server        |
| **VPS Infrastructure** | Hostinger VPS + Docker Compose + Caddy (SSL) + Backup Scripts               |
| **Agent Transport**    | MCP over SSH Tunnel ~~/ Protected HTTPS SSE~~                               |
| **~~Spec Framework~~** | ~~Spec-Driven Development (`AGENTS.md`, `PRODUCT.md`, `SYSTEM_PROMPT.md`)~~ |
| **Local Tooling**      | Cursor / Claude Desktop / Gemini CLI with portable custom prompts & skills  |

### Suggested Action Items

1. Update `taigavps-docker-workflow-tech-specs.md` to include explicit `AGENTS.md` and `SPEC.md` formatting guidelines.

2. Define a `--dry-run` stage in the local skill workflow to validate Taiga payload creation prior to running write actions.

3. Add Caddy reverse proxy and SSH-tunneling guidelines to the VPS Deployment Plan deliverable.
