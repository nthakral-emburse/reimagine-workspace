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
