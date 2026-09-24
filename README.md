# reimagine-workspace

This is the coordination workspace for the **enterprise-web reimagine project** — migrating the legacy Mercury/Apollo frontend stack to the new `enterprise-web` + `enterprise-web-aggregator` stack.

It does **not** contain application code. Instead it holds:

- **`mani.yaml`** — manifest of all repos (legacy + new), used to clone and manage them in one place
- **`notes/`** — per-ticket proposals, refinements, and survey findings
- **`tools/`** — scripts for generating the manifest and enforcing read-only guards on legacy repos
- **`.cursor/`** — AI agent rules, skills, and hooks for this workspace

Cloned repos live under `repos/` (git-ignored; managed by mani).

---

## Prerequisites

| Tool | Install |
|------|---------|
| [mani](https://manicli.com) | `brew install mani` |
| Git | already on your machine |
| SSH access | to `github.com/Chrome-River` and `github.com/nthakral-emburse` |

---

## First-time setup

### 1. Install mani

```bash
brew install mani
```

Verify:

```bash
mani --version
```

### 2. Clone this workspace

```bash
git clone git@github.com:nthakral-emburse/reimagine-workspace.git
cd reimagine-workspace
```

### 3. Clone all repos

`mani sync` reads `mani.yaml` and clones every project into the right place under `repos/`.

```bash
mani sync
```

This will clone ~270 repos. It runs in parallel (12 forks) so it's fast, but expect it to take a few minutes on a fresh machine.

> **Tip:** To sync only the new-stack repos (much faster):
> ```bash
> mani sync --tags new
> ```
>
> To sync only the legacy core repos:
> ```bash
> mani sync --tags core
> ```

### 4. Lock legacy repos against accidental pushes

```bash
mani run lock-readonly
```

This sets `DISABLED-READ-ONLY` as the push URL on every legacy repo so you can't accidentally push to them.

---

## Day-to-day commands

```bash
# See all projects and their paths
mani list projects

# See all available tasks
mani list tasks

# Run a task across all repos
mani run <task-name>

# Run a task on a specific tag group
mani run <task-name> --tags new
mani run <task-name> --tags legacy

# Run a task on a single project
mani run <task-name> --projects enterprise-web
```

### Built-in tasks

| Command | What it does |
|---------|-------------|
| `mani run shas` | Prints the current HEAD commit SHA for every legacy repo (used to anchor findings to a point in time) |
| `mani run lock-readonly` | Disables push URLs on all legacy repos |
| `mani run check-readonly` | Confirms the push URL is disabled on all legacy repos |

---

## Repo layout

```
reimagine-workspace/
├── mani.yaml              # Repo manifest — do not hand-edit; edit repos.txt instead
├── repos.txt              # Source of truth for repo names, URLs, and status (core/new/unknown)
├── tools/
│   ├── gen_manifest.py    # Regenerates mani.yaml from repos.txt
│   ├── extract_mercury_routes.py
│   └── hooks/
│       └── deny_legacy_writes.py   # Hook that blocks writes to repos/legacy/
├── notes/
│   ├── survey/            # Architecture and feature-parity survey docs
│   └── mer-*/             # Per-ticket proposals and refinements
└── repos/                 # Git-ignored; populated by `mani sync`
    ├── legacy/            # READ ONLY — do not edit
    └── new/               # Active development repos
        ├── enterprise-web
        ├── enterprise-web-aggregator
        ├── api-contracts
        ├── qa-automation
        └── qa-enterprise
```

---

## AI agent skills

This workspace ships four Cursor agent skills that encode the full feature-planning-to-contract workflow. You invoke them by typing the skill name in the Cursor chat.

### `/epic-create` — Feature request → proposed Epics

**When to use:** at the very start, when you have a feature idea or a Confluence doc but no Epics yet.

Give it a plain-language feature request or a Confluence page URL. It checks the [MER-73162 initiative](https://emburse.atlassian.net/browse/MER-73162) for duplicates, reads the codebase, dispatches a `legacy-reader` subagent for classic behavior, and writes a proposed set of Epics to `notes/epic-draft-<slug>/proposal.md`. Nothing is created in Jira until you explicitly approve.

Each proposed Epic includes:
- Background (what's missing and why it matters)
- Scope — including explicit call-outs for out-of-scope items
- Permissions and customer configuration gating
- Testable acceptance criteria (with accessibility and i18n requirements built in)
- Risks, dependencies, and a short technical note

After approval it creates the Epics in Jira under MER-73162 with the `reimagine` label, adds dependency links, and verifies every created issue.

---

### `/refine` — Epic → design document + ticket split

**When to use:** at the start of a new Epic, before any tickets exist.

Give it a Jira Epic key. It reads the code across every repo the Epic touches, writes a single planning document at `notes/<epic-id>/refine.md`, and proposes a ticket-per-repo split for your review. Nothing is created in Jira until you explicitly approve the split.

The document it produces includes:
- A plain-language summary (no jargon)
- A survey of every repo touched, with file citations
- The API contract — written once so every repo builds against the same shape
- A numbered ticket table with acceptance criteria, dependencies, and size estimates
- Permissions, screen-context, and accessibility notes for every frontend ticket

Workflow after `/refine`:

```
/refine <epic-key>          → notes/<epic-id>/refine.md
    you approve the split
/contract <epic-id>         → OpenAPI PR in api-contracts  (merge this first)
/propose <ticket-key>       → per-ticket proposal in each repo
```

---

### `/propose` — Ticket → detailed proposal

**When to use:** after the contract PR is merged, before implementation starts on any individual Story.

Give it a Jira ticket key (or plain-language description). It reads the code in every repo the ticket touches and writes `notes/<scope-id>/proposal.md` — a reviewable, implementation-ready design for that one ticket.

The proposal includes:
- A plain summary (readable by anyone, not just engineers)
- A survey of what exists today in each surface, with file paths
- Shared decisions (response shapes, status codes, who owns user-facing text)
- A full API contract with JSON examples, field tables, and enum types, when the ticket touches an endpoint
- Risks and open questions

The proposal is approved when a person says so — never automatically. After approval, run `/contract` if the ticket changes an endpoint, then implement.

---

### `/contract` — Approved proposal → OpenAPI YAML

**When to use:** after `/refine` or `/propose` is approved and before any implementation starts.

Give it the note ID (e.g. `/contract mer-83653-memorize-line-item`). It reads the **Contract** section of the approved document, translates it into valid OpenAPI 3.1.0 YAML, and appends it to the correct domain file in `repos/new/api-contracts/contracts/web-aggregator/`. It then runs `npx spectral lint` and fixes any errors.

Domain file routing:

| Endpoint prefix | File |
|-----------------|------|
| `/v1/expense-reports/…` | `expense-reports.yaml` |
| `/v1/ewallet/…` | `ewallet.yaml` |
| `/v1/forms/…`, `/v1/expense-types`, `/v1/mosaics` | `forms.yaml` |
| `/v1/expense-transactions/…` | `expense-transactions.yaml` |
| `/v1/users/…`, `/v1/authorization/…`, `/v1/navigation/…` | `session.yaml` |

It stops before opening the PR — that is a human step. Merge the contract PR before starting any implementation.

---

### Skill order of operations

```
Feature idea or Confluence doc
    │
    ▼
/epic-create <request>      Check for duplicates, read code, propose Epics → notes/epic-draft-<slug>/proposal.md
    │  (you approve)
    ▼
Epics created in Jira under MER-73162
    │
    ▼
/refine <epic-key>          Read code, write refine.md, propose ticket split → notes/<epic-id>/refine.md
    │  (you approve)
    ▼
/contract <epic-id>         Translate contract → OpenAPI YAML, lint, stop
    │  (you open + merge PR in api-contracts)
    ▼
/propose <ticket-key>       Per-ticket deep survey + proposal (backend & frontend in parallel)
    │  (you approve)
    ▼
implement                   Done inside each individual repo
```

The skills never write product code, never create Jira issues automatically, and never push or open PRs. Every gate is a human decision.

---

## Adding or updating a repo

`mani.yaml` is **generated** — do not edit it by hand. Instead:

1. Add or update an entry in `repos.txt` (format: `name  git-url  status`)
2. Regenerate the manifest:
   ```bash
   python3 tools/gen_manifest.py
   ```
3. Commit both `repos.txt` and `mani.yaml`.

---

## Legacy repos are read-only

Everything under `repos/legacy/` is read-only by convention and enforced by a git hook. If you need to document a finding about legacy behaviour, write it to `notes/<feature>/findings.md` instead. Changes to legacy code are out of scope until a later phase.
