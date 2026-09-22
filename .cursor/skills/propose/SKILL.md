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

## Reading legacy

Do not read legacy files in this conversation. Dispatch the `legacy-reader` subagent
once per legacy repo and work from its report. Brief it with the feature and any known
entry points from `notes/survey/mercury-routes.csv`.

Ask it for RULES, not screens: what determines each status, count, or label; what is
excluded; what is gated by a permission or feature flag. Every claim it returns carries
a file path and line number — claims it cannot cite come back under "Could not
determine", and those become open questions, not assertions.

`repos/legacy/` is excluded from indexing, so semantic search will not reach it. The
subagent greps and opens files by path.

## Steps

### 1. Load the ticket
Fetch summary, description, acceptance criteria, constraints, out-of-scope, linked issues.
If Jira is unreachable, say so and ask for the ticket body. Do not guess.

Also fetch every linked ticket (blocked-by, duplicates, related). Step 2 will read
any design pages linked from these tickets.

### 2. Find existing designs — required before writing anything
Read every Confluence link and remote link attached to the ticket and its linked
issues (blocked-by, duplicates, related). Do not search Confluence broadly — the
relevant pages are already referenced in the ticket if they exist.

If a design page exists:
- Read it fully.
- Note where it agrees and where it conflicts with what the code says.
- The proposal must explicitly reconcile the two. Do not silently adopt one or ignore
  the other. State the conflict, state which side this proposal takes, and say why.

If no design page is linked, say so in one line and continue.

### 3. List the surfaces
Name every repo the ticket touches. Most tickets touch both EWA and enterprise-web.

### 4. Survey every surface — required
For each surface, document what exists **today**: what is built, what patterns are
already in use, what is missing.

Cite real file paths from that surface's own repo. Three or more per surface.
A section with no citations from its own repo means the step was skipped.

Sequencing is decided later, in step 6. You may recommend one surface goes first.
You may not skip surveying a surface because you plan to sequence it later.

To learn a repo quickly: read its `AGENTS.md` and `.cursor/rules/*.mdc` first, then
confirm against source. Rules describe intent; source describes reality.

### 5. Decide: parity or standard-setting
Say which this ticket is.

- **Parity** — mercury's behavior is the target. Match it.
- **Standard-setting** — mercury is an inventory of what can happen, not a model to
  copy. Error handling, loading states, and validation are usually this. Use the
  `legacy-reader` report to learn what can fail; do not carry their presentation forward.

### 6. Write `notes/<scope-id>/proposal.md`

- **Plain summary** — five sentences. No framework names, no file paths, no acronyms.
  What is broken today, what changes, what a user or support person notices afterward.
  Written for someone who has never opened either repo.
- **Ticket** — key, title, one-line ask
- **Existing designs** — one paragraph. Name any Confluence pages or prior proposals
  found in step 2. If there are conflicts with this proposal, name each conflict
  explicitly: what the other design says, what this proposal says, and why.
- **Scope** — surfaces covered, and explicitly what is out
- **Shared decisions** — anything both surfaces must agree on: response shapes, status
  codes, who owns user-facing text, correlation ids. Stated once, here.

#### API contract rule — required whenever the ticket introduces or changes an endpoint

Every new or changed endpoint must include a **Contract** subsection inside Shared
decisions. The contract must contain all three parts below. Prose descriptions of
shape are not enough — the example is the contract.

**Part A — JSON examples.** One example per distinct response case:
- Success with failures (the main case)
- Success with nothing wrong (empty result)
- Every error status the endpoint can return

Use realistic values in every example. No `"string"` placeholders, no `123` IDs.

**Part B — Field table.** One row per field, immediately after the examples:

| Field | Type | Nullable | Description |
| --- | --- | --- | --- |

For every field whose values come from a fixed set, add one of:
- **Strict enum** — the set is closed; the consumer may reject unknown values. List
  all values. Both server and consumer should use a closed enum type.
- **Extensible enum** — the set grows as new cases are added; a new value is not a
  breaking change. List the known values today. The consumer must treat unknown values
  gracefully (fall back to a default or ignore). Do not use a closed enum type on the
  consumer side.

**Part C — Non-obvious shape decisions.** For every choice in the contract that a
reasonable person could question, state it as a numbered decision with a one-sentence
rationale. Decisions that must always be explicit:
- Whether passing entities appear in the response or are omitted
- Whether a failure in one section (e.g. header) stops processing another (e.g. line items)
- Whether a field is a singular value or an array, and why
- What the consumer must do with an unknown enum value
- Whether the same shape is shared with other endpoints (e.g. save endpoint errors)

These are the decisions that cause the most review back-and-forth if left implicit.

Then for **each** surface:
- **Today** — what exists, with file paths from that repo
- **Proposal** — a numbered list of the actual changes, in plain sentences. Each item
  says what changes and what it means for a user. No invented nouns.
- **Risks**

Then once, at the end:
- **Alternatives considered** — and why not
- **Open questions** — numbered, each tagged with its surface and blocking or not.
  Include any product or UX decisions the contract shape depends on that have not been
  answered. Examples: "should passing entities appear in the response?",
  "should a header failure stop line item checks?". Tag each as blocking or not.
- **Definition of done** — testable statements, tagged by surface
- **Suggested sequencing** — which surface goes first and why. Every slice named here
  must already have its own surveyed "Today" section above.

### 7. Pre-flight
This is your own pass before writing. It is not an approval. Confirm each line; if any
fails, go back.

- Every surface in scope has a "Today" section citing three or more files from its
  own repo
- No recommendation mentions a surface that has no "Today" section
- Every open question names its surface
- The plain summary contains no jargon
- Every new or changed endpoint has a concrete JSON example for every response case
- Every field in the contract has a row in the field table
- Every enum field is marked strict or extensible, with all known values listed
- Every non-obvious shape decision is stated explicitly with a rationale
- Any Confluence or prior design found in step 2 is named, with conflicts called out

### 8. Stop
Print the file path and the plain summary. Then print:

> **If this proposal introduces or changes an endpoint:** run `/contract <note-id>` next.
> It will translate the Contract section above into OpenAPI YAML and add it to the right
> domain file in `api-contracts`. Merge that PR before starting any implementation.

There is no automated gate on this document. It is approved when a person has read it
and said so — never because your own pre-flight passed. Say plainly that it is awaiting
review.

Do not offer to implement. Do not open tickets. Wait.
