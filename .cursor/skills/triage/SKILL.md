---
name: triage
description: Given a Jira bug, trace the request through every layer it passes (new repos, Apollo, mercury), find the root cause with file citations, and write one reviewable fix plan to notes/<scope-id>/triage.md, plus findings.md when legacy is involved. Never writes product code. Never edits Jira.
---

# triage

## What this does

You give it a bug. It finds out **why** the bug happens, using the code rather than the
ticket. Then it writes a fix plan someone can approve.

Use `/triage` for a bug. Use `/propose` for a feature or story. If the fix needs a new or
changed endpoint, `/triage` stops and hands off to `/propose` and then `/contract`.

## Input

A Jira key, a Jira URL, or a bug described in plain language.

## Hard rules

- Do not create, edit, comment on, or transition Jira issues.
- Do not write product code or tests. The only files you produce are
  `notes/<scope-id>/triage.md` and, when legacy is involved, `notes/<scope-id>/findings.md`.
- `repos/legacy/` is read-only. Never stage an edit there and never suggest a legacy patch as
  an action. A legacy cause becomes a finding with a decision.
- The ticket says what someone saw. Only the code says why. Never state a cause from the
  ticket text, a Slack quote, or a comment, however confident it sounds. Treat those as
  hypotheses to confirm or reject, and say which.
- A root cause must explain both the broken case and the nearby case that works (for example,
  why one tab breaks on refresh and its sibling does not). If it explains only one, keep looking.
- Write in plain language. If a technical term is unavoidable, add it to a short glossary.

## Where the code lives

| Repo | What it is |
| --- | --- |
| `repos/new/enterprise-web` | React frontend (reimagine) |
| `repos/new/enterprise-web-aggregator` | Java aggregator (EWA) |
| `repos/new/api-contracts` | OpenAPI specs |
| `repos/new/qa-enterprise` | Playwright UI tests: hard-coded URLs, test ids, selectors |
| `repos/new/qa-automation` | API tests |
| `repos/legacy/apollo`, `repos/legacy/mercury` | Classic, and the server in front of everything. Read-only |

The request path is in `notes/survey/architecture.md`. Every page and API call in the new
experience passes through Apollo first. A bug that shows up in enterprise-web can start in Apollo.

## Reading legacy

Do not read legacy files in this conversation. Dispatch the `legacy-reader` subagent once
per legacy repo and work from its report. Brief it with:
- the exact symptom (address, action, what happened, what was expected)
- the case that works, so it can look for what tells the two apart
- known entry points from `notes/survey/mercury-routes.csv`

Ask it for RULES that could produce the symptom: redirects, filters, allow and deny lists,
session and permission checks, feature flags, and whether each is hard-coded or
configured. Every claim it returns carries a file path and line number. Claims it cannot
cite come back under "Could not determine", and those become open questions, not causes.

`repos/legacy/` is not indexed, so search will not reach it. The subagent greps and opens
files by path. Record the legacy commit you read against: `git -C repos/legacy/<repo> rev-parse HEAD`.

## Steps

### 1. Load the ticket

Fetch the summary, description, steps to reproduce, expected and actual behaviour,
environment, comments, attachments, parent, and linked issues. Also read every Confluence or
remote link on it. If Jira is unreachable, say so and ask for the ticket body. Do not guess.

You cannot watch video attachments. Name them, and say what they would confirm.

### 2. Restate the symptom against the code

Write the symptom as one precise observation: where the user was, what they did, what
happened, what should have happened, and in which environment.

Then check every concrete detail against the code: addresses, screen names, field names,
button labels. Tickets often get these slightly wrong. Note each mismatch and use the code's
version from here on.

Name the nearest case that works: the sibling tab, the other report status, the same action
on a different screen. You will need it in step 5.

### 3. Trace every layer the request passes

Using `notes/survey/architecture.md`, list the layers between the user's action and the
symptom, for example: browser, Apollo, enterprise-web's web server, the app's router,
the dispatcher, EWA, Apollo, backend service.

For each layer, find the code that handles this request and say whether it could produce
the symptom. Do not stop at the repo the ticket names.

Dispatch these in parallel, in one message:
- one `Explore` agent for the new repos (including the QA repos)
- one `legacy-reader` per legacy repo on the path

Brief each with the symptom, the working case, and the layers to check.

### 4. Reproduce, or say why you cannot

- **Locally:** check whether local development includes the failing layer. For example,
  the rsbuild dev server serves every `/ent-web/*` address straight from the app, so
  bugs caused by Apollo do not reproduce locally. Say plainly whether local reproduction is
  possible, and why.
- **With a test:** if the cause is in new code, describe the failing test that would show
  it: file, setup, assertion. Do not write it. The implementer does, as the first step of the fix.
- **In a deployed environment:** list the exact steps, and the evidence that would confirm
  the cause, such as a network capture, a log line with its text, or a response header. Do
  not drive a browser unless the user asks.

### 5. State the root cause

- One paragraph, then the chain of events as a numbered list, each step citing file and line.
- Mark every step as **confirmed** (read in code) or **inferred** (not read). An inferred
  step that the fix depends on is a blocking open question.
- Explain why the working case from step 2 does not hit the same chain.
- For every hypothesis from the ticket or its comments, say whether it is confirmed or
  rejected, and why.

### 6. Measure the blast radius

- **The same cause:** what else hits it? Other routes, screens, or calls that match the same
  rule. List them, or say you searched and found none.
- **The fix:** what depends on whatever the fix would change? Search the new repos and both
  QA repos for addresses, test ids, selectors, API fields, translation keys, and stored
  values. List every hit with file and line.

### 7. Choose where the fix goes

- **Cause in a new repo:** fix it there.
- **Cause in legacy:** legacy stays as it is. Write a finding (see step 8). Plan a fix in
  the new repos that works around it. If no workaround exists, say so and stop.
- **Fix needs a new or changed endpoint:** stop. Say that this is `/propose` work, and then
  `/contract` work.
- **More than one reasonable fix shape**, such as which name, which layer, or whether to keep
  a redirect: present the options with their trade-offs and ask the user. Do not choose
  silently.

Prefer the smallest fix that removes the cause. Do not bundle in renames, refactors, or
clean-up that the bug does not need. Name them as follow-ups instead.

### 8. Write the documents

Use `notes/<scope-id>/`, where `<scope-id>` is the lower-case ticket key plus a short slug,
for example `mer-85636-receipts-tab-refresh`.

**`triage.md`:**
- **Glossary**, only if needed.
- **Plain summary:** at most five sentences, with no framework names, file paths, or acronyms.
  Cover what the user sees, why it happens, what changes, and what they will notice
  afterwards.
- **Ticket:** key, title, parent, and the one-line ask.
- **Symptom:** the restated observation from step 2, with each mismatch against the ticket called out.
- **Request path:** the layers from step 3, marking the one that fails.
- **Root cause:** from step 5, including why the working case works and the verdict on each
  ticket hypothesis.
- **Reproduction:** from step 4.
- **Blast radius:** from step 6.
- **Fix plan:** for each repo, a numbered list of changes in plain sentences. Each item names
  the file, the change, and what the user notices. Then list what deliberately stays the
  same.
- **Regression test:** the test that would have caught this, and where it goes.
- **Alternatives considered:** and why not.
- **Open questions:** numbered, each tagged with its repo and as blocking or not.
- **Definition of done:** testable statements tagged by repo. Include a deployed-environment
  check whenever local reproduction is impossible.

**`findings.md`** (only when legacy behaviour is part of the cause or the blast radius).
Follow the existing format (see `notes/mer-85636-receipts-tab-refresh/findings.md`):
- one heading per finding: `## F<n>. <what is wrong>`
- **What**, with citations
- **Why it matters**
- **Decision**: what the new repos do, and that legacy stays as it is
- a closing **Could not determine** section

Name the legacy commit the citations come from.

### 9. Pre-flight

This is your own check before stopping. It is not an approval. If any line fails, go back.

- The root cause cites file and line for every confirmed step
- The root cause explains the working case
- Every ticket hypothesis is confirmed or rejected
- Every layer on the request path was checked, and legacy was read only through
  `legacy-reader`
- The blast radius covers both QA repos
- No step of the fix plan touches `repos/legacy/`
- Local reproduction is stated as possible or impossible, with the reason
- Every open question names its repo and says whether it blocks
- The plain summary contains no jargon

### 10. Stop

Print the file paths and the plain summary.

If step 7 found that an endpoint changes, print:

> This fix changes an endpoint. Run `/propose <ticket>` next, then `/contract <note-id>`.

Otherwise, print:

> No endpoint changes. Once this is approved, implement it in the repo named in the fix plan.

There is no automated gate on this document. It is approved when a person has read it and
said so, never because your own pre-flight passed. Say plainly that it is awaiting review.

Do not implement. Do not open tickets. Wait.
