---
name: propose
description: Given a Jira ticket, read the actual code across every repo the ticket touches, then write one reviewable proposal. Never creates Jira issues. Never writes product code.
---

# propose

## Input

A Jira key, a Jira URL, or a feature described in plain language.

## Hard rules

- Do not create, edit, or transition Jira issues.
- Do not write product code. The only file you produce is `notes/<scope-id>/proposal.md`.
- `repos/legacy/` is read-only. Never stage an edit there.
- The ticket says what someone wants. Only the code says what exists. Never describe
  current behavior from the ticket text.
- Do not make a recommendation about a repo you have not read. Saying "out of scope"
  is fine. Saying "the web app will do it this way later" without having opened the
  web app is not.
- Write the whole document in plain language, not just the summary. A reader who does
  not write Java or React must be able to follow every section. Do not invent nouns
  like "factory", "producer", or "envelope". If a technical term is unavoidable, list
  it in a short glossary at the top of the document.

## Where the code lives

- `repos/new/enterprise-web-aggregator` — Java aggregator (EWA)
- `repos/new/enterprise-web` — React SPA
- `repos/legacy/mercury`, `repos/legacy/apollo` — current production behavior, read-only

`repos/legacy/` is excluded from indexing, so semantic search will not reach it.
Grep and open files by path.

## Steps

### 1. Load the ticket
Fetch summary, description, acceptance criteria, constraints, out-of-scope, linked issues.
If Jira is unreachable, say so and ask for the ticket body. Do not guess.

### 2. List the surfaces
Name every repo the ticket touches. Most tickets touch both EWA and enterprise-web.

### 3. Survey every surface — required
For each surface, document what exists **today**: what is built, what patterns are
already in use, what is missing.

Cite real file paths from that surface's own repo. Three or more per surface.
A section with no citations from its own repo means the step was skipped.

Sequencing is decided later, in step 5. You may recommend one surface goes first.
You may not skip surveying a surface because you plan to sequence it later.

To learn a repo quickly: read its `AGENTS.md` and `.cursor/rules/*.mdc` first, then
confirm against source. Rules describe intent; source describes reality.

### 4. Decide: parity or standard-setting
Say which this ticket is.

- **Parity** — mercury's behavior is the target. Match it.
- **Standard-setting** — mercury is an inventory of what can happen, not a model to
  copy. Error handling, loading states, and validation are usually this. Read mercury
  and apollo to learn what can fail; do not carry their presentation forward.

### 5. Write `notes/<scope-id>/proposal.md`

- **Plain summary** — five sentences. No framework names, no file paths, no acronyms.
  What is broken today, what changes, what a user or support person notices afterward.
  Written for someone who has never opened either repo.
- **Ticket** — key, title, one-line ask
- **Scope** — surfaces covered, and explicitly what is out
- **Shared decisions** — anything both surfaces must agree on: response shapes, status
  codes, who owns user-facing text, correlation ids. Stated once, here.

Then for **each** surface:
- **Today** — what exists, with file paths from that repo
- **Proposal** — a numbered list of the actual changes, in plain sentences. Each item
  says what changes and what it means for a user. No invented nouns.
- **Risks**

Then once, at the end:
- **Alternatives considered** — and why not
- **Open questions** — numbered, each tagged with its surface and blocking or not
- **Definition of done** — testable statements, tagged by surface
- **Suggested sequencing** — which surface goes first and why. Every slice named here
  must already have its own surveyed "Today" section above.

### 6. Self-check
Confirm before writing. If any fails, go back.

- Every surface in scope has a "Today" section citing three or more files from its
  own repo
- No recommendation mentions a surface that has no "Today" section
- Every open question names its surface
- The plain summary contains no jargon

### 7. Stop
Print the file path and the plain summary. Do not offer to implement. Do not open
tickets. Wait.