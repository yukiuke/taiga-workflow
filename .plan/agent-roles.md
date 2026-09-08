## The File-Based Chain Architecture

```
[ Human Trigger: /ingest-requirements ]
                   │
                   ▼
 ┌───────────────────────────────────┐
 │ Pass 1: Systems Architect         │ ──> Writes `.ai/draft_spec.md`
 └─────────────────┬─────────────────┘
                   │ (Auto-triggers next step)
                   ▼
 ┌───────────────────────────────────┐
 │ Pass 2: The Challenger (Auditor)  │ ──> Writes `.ai/audit_report.md`
 └─────────────────┬─────────────────┘
                   │ (Checks Confidence Score)
                   ▼
 ┌───────────────────────────────────┐
 │ Pass 3: Product Owner             │ ──> Writes `.ai/taiga_payload.json`
 └─────────────────┬─────────────────┘
                   │
                   ▼
 [ Human Gate / Final Execution via Taiga MCP ]
```

## Workflow Roles

### 1. 🏗️ The Systems Architect (The Builder)

- **Objective:** Ingest wordy, high-level, unstructured chat dumps (e.g., Venca's Discord notes) and transform them into technical domain boundaries and system specs.

- **Key Responsibilities:**
  
  - Extract hidden technical assumptions and list implicit dependencies.
  
  - Define input/output signatures, data schema requirements, and architecture constraints.

- **System Prompt Persona:** *"You are a Principal Systems Architect. Your job is to extract technical scope from informal product context, identify implied technical requirements, and define concrete system boundaries."*

### 2. 🥊 The Challenger / Red Teamer (The Adversary)

- **Objective:** Audit the Architect’s draft to prevent scope inflation, missing edge cases, and missing acceptance criteria *before* anything reaches Taiga.

- **Key Responsibilities:**
  
  - Find underspecified logic and flag missing error handling or fallback paths.
  
  - Check for scope creep and enforce the Definition of Done (DoD).
  
  - **Trigger Flagging:** If the draft is vague, calculate a "Confidence Score." If $\text{Score} < 0.8$, inject the mandatory `[HUMAN REVIEW NEEDED]` tag for Taiga.

- **System Prompt Persona:** *"You are an uncompromising Lead Auditor. Your job is to aggressively challenge specifications, find ambiguities, stress-test edge cases, and block incomplete work from reaching execution."*

### 3. 🎯 The Agile Product Owner (The Orchestrator)

- **Objective:** Convert the validated technical spec into clean, well-structured, human-friendly Taiga entities.

- **Key Responsibilities:**
  
  - Enforce structural hierarchy rules (Epic $\rightarrow$ User Story $\rightarrow$ Task).
  
  - Standardize format: Ensure User Stories follow *"As a... I want to... So that..."* with explicit markdown checkboxes for Acceptance Criteria.
  
  - Calculate initial velocity and task estimates, flagging oversized stories for further breakdown.

- **System Prompt Persona:** *"You are a Technical Product Owner. Your sole job is to translate validated software requirements into crisp, prioritized, and perfectly formatted Agile backlog items."*

### 4. 🔍 The Verification Agent (Post-Work Auditor)

- **Objective:** Runs when the agentic workflow is triggered to *work* on existing tickets (`Use-Case: Work On Tickets`).

- **Key Responsibilities:**
  
  - Inspect git diffs or file changes produced during ticket execution against the ticket's Acceptance Criteria.
  
  - Ensure no collateral changes were made to code outside the ticket scope.
  
  - Auto-generate a "Proof of Work" comment on the Taiga ticket detailing tests passed and files touched before closing out the ticket.

## Implementation: The Master Prompt / Custom Command

1. Step-by-Step Chain (Parent agent kicks off subagents for each pass):
   
   - Pass 1: Archetect
   
   - Pass 2: Challenger / Red Team
   
   - Pass 3: Product Owner

2. **Sub-Agent Execution (Claude Cowork / Custom Hooks):**
   
   Give your primary LAT a rule: *“Before executing `taiga_create_story`, query the Auditor prompt to score the spec quality.”*

### Step-by-Step Orchestrator Instructions for your LAT:

You can save this configuration into a project file (e.g., `.cursorrules` or a custom prompt template in Claude) so that a single command kicks off the entire automated pipeline.

```markdown
# Workflow Directive: Automated Taiga Ingest Pipeline

When the user runs the command `/ingest-requirements [paste raw chat text here]`, execute the following multi-pass subagent chain sequentially. Do not stop until Phase 3 is complete and results are saved to disk.

### Phase 1: The Systems Architect Subagent
- **Action:** Read the raw chat text. Expand implicit requirements, define technical boundaries, and map out dependencies.
- **Output:** Save the result strictly to `.ai/draft_spec.md`.
- **Transition:** Automatically proceed to Phase 2.

### Phase 2: The Challenger / Red-Teamer Subagent
- **Action:** Read `.ai/draft_spec.md`. Aggressively red-team the spec for missing edge cases, security flaws, and scope creep. Calculate a Confidence Score (0.0 to 1.0).
- **Output:** Append the audit findings and score to `.ai/audit_report.md`. 
- **Condition Check:** If the score is $< 0.8$, explicitly inject the warning text `[HUMAN REVIEW NEEDED]` into the audit report.
- **Transition:** Automatically proceed to Phase 3.

### Phase 3: The Agile Product Owner Subagent
- **Action:** Read `.ai/draft_spec.md` and `.ai/audit_report.md`. Transform the validated spec into an optimized Taiga hierarchy (Epics $\rightarrow$ User Stories $\rightarrow$ Tasks) matching the schema required by the Taiga MCP tools.
- **Output:** Save the payload to `.ai/taiga_payload.json`.
- **Final Step:** Pause execution, output a brief summary of the generated ticket structure to the user, display any warning flags, and wait for human clearance before calling Taiga MCP write tools.tool..."
```

## Why This Approach Fits Your Requirements

1. **Zero Infinite Loops:** Because each pass reads a static file and writes a discrete next file, the agent has a clear beginning, middle, and end. It cannot loop indefinitely.

2. **Total Auditability:** If a ticket looks wrong in Taiga, you can look inside the `.ai/` folder to see exactly what the Architect wrote, what the Challenger flagged, and what the Product Owner formatted.

3. **Low Friction:** It runs entirely inside your existing local development environment (Cursor or Claude Desktop) using standard file I/O without requiring complex server infrastructure.
