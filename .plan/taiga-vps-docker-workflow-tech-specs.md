# Overview

Create a manually-triggered agentic workflow allowing work/specifications/requirements to be agentically added to a Taiga ticketing system and retrieve those ticket details to perform work. Taiga self-hosted docker stack to be used in a hosted VPS environment. Agents live on local machines and should interface with the hosted Taiga environment via MCP tooling when possible and API calls otherwise.

# Definitions

- LATs = Local agentic tools = Cursor, Claude Cowork, Google Gemini/Antigravity, etc.

# Requirements

- All LAT workflows are manually triggered by a human and have a defined end of life.

- No workflows will ever trigger autonomously or run indefinitely.

- Anticipate the addition of local vectorized data stores for RAG purposes in a later project-phase and build with this expansion in mind.

- Create portable skills, agents, rules and/or hooks for Cursor/Claude to handle the ingest, organization and creation of work/tickets so that output is standard, readable, brief and descriptive enough to complete the work.

- If the ingested text of work/requirements is not detailed enough to create high-quality tickets, flag the ticket in the agent's output to the user **and** add a warning in all caps to the ticket's details that the ticket needs human review for accuracy.

- Read `./agent-roles.md` for roles and workflow details.

- Read `./security-recommendations.md` for security requirements.

# Workflow Examples

## Use-Case: On The Fly Requirements

- During a meeting, Venca casually talks about some work that needs to be done.

- Venca breaks the work down verbally *while he types into Discord chat.*

- After Venca's often wordy and large-scoped requirements are dumped into Discord, someone copies that into their local agent to create tickets in Taiga.

- The local Agent takes the input, divides work into categories, breaks up the work into agile actionable items, organizes the work, roadmaps the work, creates sprints in Taiga (if necessary) and assigns work to the sprints accordingly.

## Use-Case: Work On Tickets

- A human team member triggers the agentic workflow by providing it with ticket IDs and directives ("plan x feature", "fullfil the ticket requirements...", "roadmap epic", etc).

- The orchestration agent plans the work based on the supplied tickets, including dependencies.

- A very brief summary of the planned work is provided to the user before starting to ensure token-spend is acceptable.

- Ticket work begins after user accepts and clears agent to continue.

- Tickets should not be left partially complete if possible. Structure/order the ticket work to avoid partial completion.

# Features

LATs can:

- create new tickets, epics, sprints and issues.

- get and modify existing ticket details/data.

- logically organize and catagorize work/tickets.

- ingest ticket details and perform work.

- utilize a custom set of skills to divide work into categories, break up the work into agile actionable items, organize the work, roadmap the work, create sprints in Taiga (if necessary) and assign work to the sprints accordingly at a user-defined velocity.

# Tech Stack

- Taiga Docker with MCP: [taigaio/taiga-docker](https://github.com/taigaio/taiga-docker)

- VPS Hosting: likely Hostinger

- Local Cursor/Gemini agent configured to connect to Taiga MCP.

- Caddy + caddy-docker-proxy for reverse-proxy [lucaslorentz/caddy-docker-proxy](https://github.com/lucaslorentz/caddy-docker-proxy)

# Cost & Token Management Controls

- *Gap:* The plan mentions showing a brief summary before starting work to manage token spend, but lacks concrete constraints or token-guard limits.

- *Suggestion:* Add explicit max-token/cost thresholds per ticket run in your agent rules, and enforce a dry-run mode (`--dry-run`) where the agent outputs the proposed Taiga hierarchy (Epics > User Stories > Tasks) locally in JSON/Markdown for review prior to invoking write-tools via MCP.

# Structure of Ingested Work (Epics vs. Stories vs. Tasks)

- **Epic:** High-level feature domain / theme.

- **User Story:** Actionable end-user value statement + Acceptance Criteria (Definition of Done).

- **Task:** Specific code/file-level implementations assigned to stories.

# Deliverables

| **Layer**              | **Recommended Choice**                                                     |
| ---------------------- | -------------------------------------------------------------------------- |
| **Project Management** | Taiga Docker (`taigaio/taiga-docker`) + Self-hosted Taiga MCP Server       |
| **VPS Infrastructure** | Hostinger VPS + Docker Compose + Caddy (SSL) + Backup Scripts              |
| **Agent Transport**    | MCP over SSH Tunnel                                                        |
| **Local Tooling**      | Cursor / Claude Desktop / Gemini CLI with portable custom prompts & skills |
