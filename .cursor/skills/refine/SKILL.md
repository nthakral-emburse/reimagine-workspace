---
name: refine
description: Turn one Jira Epic into a high-level design, an OpenAPI contract, and a proposed set of stories checked against a story checklist. Works for an Epic with or without tickets: it proposes new stories and suggests what to do with each existing ticket. Writes notes/<epic-id>/refine.md. Never writes product code. Never creates Jira tickets.
disable-model-invocation: true
icon: git-branch
---

# refine

## What this does

You give it an Epic. It reads the code in every repo the Epic touches, then writes **one
document** containing:

1. The solution, in plain language
2. The API contract — written once, so every repo builds the same shape
3. A proposed set of stories, each checked against the story checklist in step 6. When the
   Epic already has tickets, a suggested action for each one

**Output:** one file — `notes/<epic-id>/refine.md`

**What it does not do:** write code, create Jira tickets, open the contract pull request,
or design any single ticket in detail. That last one is `propose`'s job.

## How one design reaches every repo

`refine` does not copy anything into the repos. It writes one planning document here and
stops.

After you approve the split, the contract goes first and everything else follows it:

```
refine (here)          one document, N proposed tickets
     |
     |  you approve the split, then tickets get created
     v
api-contracts          OpenAPI pull request - merged BEFORE any code starts
     |
     +----------------+----------------+
     v                v                v
  backend          frontend           QA
  propose          propose          handoff
     v                v                v
 implement        implement        implement
     |
     v
  review
```

**Contract first.** The shape is written once here, lands in `api-contracts` as an OpenAPI
pull request, and must be merged before any implementation ticket starts. After that the
backend, the frontend, and the tests all build against the same merged spec — nobody is
guessing, and nobody is waiting on someone else to decide.

A story that touches one repo goes to that repo's own `propose`. A story that touches
more than one goes to `/propose <ticket-key>` in this workspace, which reads every repo
the ticket touches.

## Tickets are never created automatically

This skill writes a **table of proposed tickets**. It does not touch Jira.

You read the table, change what you disagree with, and only then does anyone create
tickets — as a separate step you ask for. The `ticket-manager` agent can create them from
the approved table.

A wrong split that is a table costs nothing to fix. A wrong split that is twelve Jira
tickets costs a cleanup.

## Two phases

**Phase 1 — Refine:** Read the Epic and all repos, write `notes/<epic-id>/refine.md`, print the ticket table, wait for approval. Do not create any Jira issues.

**Phase 2 — Update and create:** When the user says the split is approved, apply the approved action to each existing ticket (keep, update, merge, split or close), create the new stories, add dependency links, verify, and record the keys in the refine.md. This is the only time Jira issues are created, changed, or linked.

## Rules

- **Phase 1 only:** Do not create, edit, or transition any Jira issue until the user explicitly approves the split.
- Never write product code, and never open the contract pull request yourself.
- `repos/legacy/` is read-only.
- The Epic says what someone wants. Only the code says what exists. Never describe
  today's behavior from the Epic text.
- **Every story passes the story checklist.** The checklist in step 6b decides how the
  work is split: one outcome per story, the right size, testable, a clear title, and the
  rest. Run every proposed story through it before writing the document.
- **Suggest the best allocation of the work.** Tickets the Epic already has are an input,
  not a limit. For each one, suggest what to do: keep, update its title or description,
  merge, split, or close. Propose new stories wherever the work needs them. An Epic with
  no tickets gets all new stories.
- **No QA automation tickets.** QA automation belongs to the SDET. What needs coverage
  goes in the acceptance criteria and in "Done means".
- Never recommend anything about a repo you have not opened.
- Plain language. No invented nouns. If a technical word is unavoidable, put a short
  glossary at the top of the document.
- **Never create a new YAML file per endpoint or per Epic in `api-contracts`.** Contracts are grouped by resource domain: `expense-reports.yaml`, `ewallet.yaml`, `forms.yaml`, `expense-transactions.yaml`, `session.yaml`. Add new endpoints to the matching domain file. A genuinely new domain (e.g. `customers.yaml`) gets its own file. Before writing any contract section, open the relevant domain file to see what already exists.

## Terminology

Always use these names in every document this skill produces:

| Use this | Not this |
| --- | --- |
| **classic** | old website, mercury UI, legacy UI |
| **reimagine** | new website, new UI, enterprise-web UI |
| **aggregator** | EWA, enterprise-web-aggregator (first use only, then "aggregator") |

Include a short glossary at the top of every refine.md that defines at minimum: classic, reimagine, aggregator, and any domain-specific words the document coins.

## Where the code lives

| Repo | What it is |
| --- | --- |
| `repos/new/api-contracts` | OpenAPI specs — the source of truth for every shape |
| `repos/new/enterprise-web-aggregator` | Java backend (aggregator) |
| `repos/new/enterprise-web` | React frontend (reimagine) |
| `repos/new/qa-enterprise` | Playwright tests (TypeScript) |
| `repos/legacy/mercury`, `repos/legacy/apollo` | How classic behaves today — read-only |

### Reading legacy

Do not read legacy files in this conversation. Dispatch the `legacy-reader` subagent once
per legacy repo and work from its report. Brief it with the Epic and any known entry
points from `notes/survey/mercury-routes.csv`.

Ask it for RULES, not screens: what determines each status, count, or label; what is
excluded; what is gated by a permission or a customer configuration. Every claim it returns carries a
file path and line number — claims it cannot cite come back under "Could not determine",
and those become open questions or spikes, not assertions.

For customer configuration, tell it to search mercury for reads of `customerPreferences`,
`customerExpensePreferences`, and active-user fields that are copied from customer
preferences at login. For each one found, it reports the name, what it changes (hides,
disables, or alters behaviour), and whether the check is browser-only or also enforced on
the server. Server-side checks need the apollo reader; if neither can cite one, it goes
under "Could not determine".

Keep this shallow at refine time. You need enough to split the work, not enough to design
it.

`repos/legacy/` is not indexed, so search will not reach it. The subagent greps and opens
files by path.

---

## 1. Read the Epic

Fetch from Jira: summary, description, goal, acceptance criteria, constraints,
out-of-scope, **and every child ticket that already exists**.

If Jira is unreachable, say so and stop. Do not guess.

For each existing child, write down what it covers and whether its title and description
say that clearly. Step 6c uses this to suggest what to do with each one. If the Epic has
no children, write "none": every story will be new.

Then read every Confluence page linked from the Epic or its children. If one exists, its
shapes are the starting point for step 3: copy them rather than inventing your own, and
note anywhere the code contradicts them. If nothing is linked, write one line saying so.

### Designs in Figma

If the Epic or any child links a Figma file, open it. Frontend work written without
the design will have vague acceptance criteria.

Use `get_screenshot` to see the screen and `get_metadata` for its structure. Use
`get_variable_defs` only when the Epic is about colour, spacing, or typography.

Write down what the frontend has to handle: which screens are involved, and which states
the design shows — loading, empty, error, and validation. Those states become acceptance
criteria on the story that builds the screen, and they are the ones most often missed.

Do **not** call `get_design_context` here. It returns implementation-level detail and
belongs in `enterprise-web` at implement time. Do not write component code, and do not
invent screens the design does not show.

If there is no Figma link, write one line saying so.

## 2. Look at each repo

List the repos the Epic touches. For each, write what exists **today** and cite at least
two real files from that repo.

Always check `api-contracts` first. Contracts live in `contracts/web-aggregator/` split by domain: `expense-reports.yaml`, `ewallet.yaml`, `forms.yaml`, `expense-transactions.yaml`, `session.yaml`. Open the domain file that matches the endpoint you are designing. If the endpoint already exists there, that spec is what exists today. New endpoints go into the matching domain file. New domains (e.g. `customers.yaml` for `/v1/customers/…`) get their own file. **Never propose a new file per endpoint or per Epic.**

Keep this shallow. You need enough to decide how the work splits, not enough to design it
— `propose` does the deep survey later. If you find yourself designing, stop.

Also say which kind of Epic this is:

- **Parity** — match what mercury does today
- **Standard-setting** — mercury shows what can go wrong, but do not copy how it presents it

## 3. Write the contract — once

Do this whenever more than one repo shares a shape: an endpoint, a response body, an error
body, a status code.

**A. Examples.** One JSON example per case — the normal success, the empty result, and
every error. Realistic values only, never `"string"` or `123`.

**B. Field table.** One row per field.

| Field | Type | Nullable | Description |
| --- | --- | --- | --- |

For any field with a fixed set of values, say which kind it is:

- **Strict** — the list never grows; both sides can use a closed type
- **Extensible** — new values will appear; the consumer must handle unknown ones without
  breaking

**C. Decisions.** Number every choice someone could reasonably question, with one sentence
of why. Always cover: do passing items appear in the response or get left out, does one
failure stop other checks, is a field one value or a list, and what a consumer does with a
value it does not recognise.

Then say who serves the shape, who consumes it, and who owns the wording a user sees.

If nothing is shared, write "No shared contract — single-repo Epic" and name the repo.

### Permissions — required for every Epic

Read `enterprise-web/docs/architecture/permissions.md` before writing any ticket that
touches a screen, action, or endpoint.

For everything new this Epic adds, answer:

1. **Which bucket does it belong to?** Run the Config / Permission / Identity / Feature
   flag test from that file. Each bucket maps to a different EWA endpoint — getting this
   wrong means building the wrong endpoint.
2. **If it is a Permission:** name the key in `service:resource[.subResource]:action[.qualifier]`
   format. If the legacy flag starts with `disable`, `hide`, or `isXxxPreviewOnly`, it is
   an inverted permission — check the mapping table in the spike doc and flip to positive
   form before naming the key.
3. **What does the user see without the permission?** Hidden, disabled, or a no-access
   screen. This is a design question — it belongs with the Figma states and becomes
   frontend acceptance criteria.
4. **Does a delegate get a different answer?** Permissions resolve per active person.
5. **Which customer configurations change this feature?** Include settings that alter
   behaviour, not only ones that hide it. For each, name the setting, its home
   (`GET /v1/customers/{id}/preferences` or `GET /v1/customers/{id}/expense/preferences`),
   its effect, and whether the server enforces it. If none are found in classic, write
   "No customer configuration found" and add an open question asking product to confirm.

The backend work always needs its own authorization check. Hiding a button is UX, not
security.

### Where the contract goes

It does not stay in this document. It becomes a pull request in `api-contracts`, which
someone opens after you approve the split. Write the contract section so that PR is easy
to raise, and follow that repo's rules:

- **Add new endpoints and field changes to the matching domain file in `contracts/web-aggregator/`.** The files are `expense-reports.yaml`, `ewallet.yaml`, `forms.yaml`, `expense-transactions.yaml`, `session.yaml`. New domains get their own file. Do not create a new file per endpoint or per Epic.
- Contract only — no implementation code in that PR
- State whether the change is breaking or non-breaking
- `npx spectral lint contracts/**/*.yaml` passes before it opens

Reuse the shared schemas in `schemas/` — `ProblemDetail.yaml`, `Uda.yaml` and the rest —
rather than redefining them.

## 4. Frontend checklist — required for every story with frontend work

Every story with work in `enterprise-web` must answer these four things. If any cannot be
answered, the split is not ready. They are acceptance criteria on that story, never
tickets of their own.

### Functional acceptance criteria
What the user can do that they could not do before. Testable statements — not descriptions
of implementation.

### Permissions and customer configuration
Which permission key gates this screen or action (e.g. `expense:report:recall`). What
does the user see without that permission — hidden element, disabled button, or a
no-access screen? Does acting as a delegate change it?

Which customer configuration changes what this screen shows or does, and what the user
sees when it is on versus off.

If the feature adds nothing new that requires a permission check, write "No new permission
gate — existing gating unchanged." If no customer configuration applies, write "No customer
configuration applies."

### Screen context (AI widget)
The in-app AI widget needs to know what is on screen so it can answer questions and take
actions. Every screen sends it a payload describing the entities visible and the actions
available.

For each new screen or new piece of data this ticket adds, say:

- Which new API entities or UI entities appear (report, line item, form, field, etc.)
- Which new actions the widget can invoke (write, navigate, submit, open, etc.)
- Whether form config needs to be included (required fields, field types) — this is what
  MER-81183 adds for the line item and header screens

If the ticket adds nothing the AI widget needs to know about, write "No screen context
changes."

Reference: [Screen Context Schema V2](https://emburse.atlassian.net/wiki/spaces/EAFF/pages/5032149030)
and [MER-81183](https://emburse.atlassian.net/browse/MER-81183).

### Accessibility (a11y)
What a keyboard-only or screen-reader user needs from this screen. At minimum:

- Every interactive element has a visible focus state and a label
- New content that appears dynamically (errors, loading, empty states) is announced
- The tab order follows the visual reading order
- Any icon-only button has an accessible name

These become testable acceptance criteria, not an afterthought.

---

## 5. Spikes — when investigation comes before implementation

A spike is needed when a risk in the Risks section cannot be resolved by reading the
code — the answer requires a timed experiment or a call with another team.

**Propose a spike when all three are true:**
- There is a specific question that must be answered before implementation ACs can be written
- The answer cannot be found by reading the existing code in this workspace
- Getting it wrong would change the ticket split significantly

**Do not propose a spike** to delay a decision, to learn a technology generally, or when
the question could be answered by reading one more file. A question for product or design
is not a spike: it goes under Open questions. If the Epic already has a technical design
or investigation story, put the question there and do not add a spike.

A spike ticket needs:

| | |
| --- | --- |
| **Title** | "Spike: " + the question in plain language |
| **Repo** | `enterprise-web-aggregator` or `enterprise-web` — whichever team runs it |
| **Question** | Exactly one. The single thing that must be answered |
| **Time box** | Maximum days. When time is up, write the finding and close — even if uncertain |
| **Artifact** | What gets written when done — a decision recorded in `notes/<epic-id>/spike-<slug>.md` |
| **Unblocks** | Which tickets in this list cannot start until the spike closes |

A spike never produces code that goes to production. Its output is a written decision,
not a pull request. Implementation tickets that depend on the spike may be created now
(with a "blocked by spike" dependency) or after the spike closes, depending on whether
the ACs can be written without the answer.

## 6. Split into stories

Three steps: draft the split from the work, run every story through the checklist, then
decide what happens to the tickets the Epic already has.

### 6a. Draft the split

Group the work from steps 2 to 4 by outcome: what someone can do or verify when it is
done. Draft the split from the work itself, as if the Epic had no tickets. The existing
tickets come in at 6c.

### 6b. Story checklist

Run every proposed story through this list. A story that fails an item is reworked
(merged, split by outcome, or rewritten) until it passes. Do not write the document while
any story fails.

1. **One outcome.** When the story is done, someone can use it or verify it by itself: a
   person can do something new, or another story can build on it. "Memorize a line item"
   is one outcome: the endpoint, the button and the dialog together.
2. **Appropriately sized.** Estimate it in pull requests: S is one, M is two or three, L
   is four to six.
   - Larger than L: split it by outcome (item 1), never by repo, layer or endpoint.
   - Smaller than one pull request: it is not a story. Put it in the story that needs it.
     This covers a backend stub, one field added to a response, one setting returned from
     an existing endpoint, and a check of work that is already built.
3. **Testable acceptance criteria of its own.** A person or a test can check each
   criterion. If you cannot write them, the split is wrong.
4. **Work listed by repo.** It names every repo it touches and what changes in each. A
   story may touch more than one repo. Work in a second repo is not a reason for a second
   story.
5. **A title that says the outcome.** Imperative, plain words, under 60 characters. Not an
   endpoint path or a class name.
6. **Complete for its screens.** Permissions, customer configuration, screen context,
   accessibility and translations are acceptance criteria on the story they belong to
   (step 4), never stories of their own.
7. **No question hidden inside it.** A question for product or design goes under Open
   questions, with the stories it blocks. A question that needs an experiment is a spike
   (step 5). Neither is written into a story as work.
8. **No overlap.** It does not ask for something another story or an existing ticket
   already asks for. Two that ask for the same thing become one.
9. **Dependencies named.** "Depends on" lists every story it waits for, and no story
   depends on itself through a chain.
10. **Contract first.** If it uses a shape from step 3, it depends on the contract ticket
    that covers that shape being merged. An Epic with a contract has at least one
    contract ticket. If the Epic already has a technical design or contract story, use
    that one. Add more when parts of the contract can merge separately, for example one
    per group of endpoints, so a story waits only for the part of the contract it uses.

Then check the set as a whole:

- **Coverage.** Map each story to the items in the Epic's scope that it delivers. Every
  scope item has a story.
- **No stray stories.** A story that maps to no scope item is out of scope or too thin:
  drop it or merge it. When two stories map to the same single item, say in one line why
  they are separate.

### 6c. Decide what happens to existing tickets

Skip this when the Epic has no tickets: every story is new.

Compare the split from 6a and 6b with the tickets from step 1. The goal is the best
allocation of the work, not keeping the tickets as they are. For each existing ticket,
suggest one action and give the reason:

| Action | When | What you write |
| --- | --- | --- |
| **Keep** | It matches a story, and its title and description are right | The technical details to add as a comment |
| **Update** | It matches a story, but its title or description is wrong, empty or misleading. A title that is an endpoint path is one example | The new title and the new description, in full |
| **Merge** | It asks for the same thing as another ticket, or it is one part of a story | The ticket that stays, and what moves into it |
| **Split** | It holds more than one outcome | The stories it becomes |
| **Close** | Nothing in the split needs it | Why |

Work that no existing ticket holds becomes a new story.

These are suggestions. Nothing changes in Jira until the user approves, and the user can
change any of them.

### 6d. Write each story

Start the section with the count, for example "6 stories: 4 existing, 2 new", and a table
of the existing tickets with the suggested action for each.

Each story needs:

| | |
| --- | --- |
| **Title** | Imperative (or "Spike: question" for spikes), under 60 characters |
| **Type** | Story or Spike |
| **Existing or new** | "New", or the Jira key with the suggested action from 6c |
| **Repos** | Every repo it touches |
| **Ask** | One sentence |
| **Work by repo** | A few lines under each repo it touches. Not a design: `propose` does that |
| **Acceptance criteria** | Testable. If you cannot write them, the split is wrong — go back. For a spike: the artifact produced and the question answered |
| **Out of scope** | What a reader would assume is included but is not |
| **Depends on** | Other tickets in this list, by number |
| **Size** | S, M or L, as defined in checklist item 2. Spikes: time box only |

The order of work inside an Epic:

0. **Spike** (if needed) — resolves any blocking unknowns first
1. **Contract** — the OpenAPI change in `api-contracts`, merged before any code that uses it starts
2. **Backend and frontend** — at the same time, both against the merged spec

Once the contract merges, the backend and the frontend can start at the same time — that
is what contract first buys you.

Do not propose a ticket for work with no acceptance criteria of its own.

## 7. Write the document

Save to `notes/<epic-id>/refine.md`, where `<epic-id>` is the lowercased Epic key plus a
short slug — e.g. `mer-79896-bulk-validate`.

In this order:

1. **Plain summary** — five sentences, no jargon. What is missing today, what this
   delivers, what someone using the product notices afterward.
2. **Epic** — key, title, goal in one line.
3. **Existing designs** — Confluence pages and Figma screens found, and every place the
   code disagrees with them. Link the Figma file and list the states it shows.
4. **Tickets already open** — from step 1 with what each one covers, or "none".
5. **Each repo today** — the survey from step 2, with its file citations.
6. **Parity or standard-setting** — one line and why.
7. **The contract** — from step 3, in full, including whether it is breaking, and the
   permission key that gates each new screen, action, and endpoint.
8. **Proposed stories** — from step 6, numbered. Start with the count and the table of
   existing tickets with the suggested action for each. Then one section per story.
9. **Order of work** — what goes first, what can run in parallel, what blocks what. Name
   the first ticket that delivers something visible; it should not be last.
10. **Risks** — what could go wrong that reading the code could not settle.
11. **Open questions** — numbered, each saying which repo it affects and whether it blocks.
12. **Done means** — testable statements for the whole Epic.
13. **What happens next** — the table below, filled in for the real tickets.

| Ticket | Next step |
| --- | --- |
| Contract | Run `/contract <epic-id>` in this workspace — it translates this document's contract section into OpenAPI YAML and appends it to the right domain file in `api-contracts`. Then open the PR and merge it before starting anything below. |
| Story in one repo | `/propose` in that repo, then `/implement` there |
| Story in more than one repo | `/propose <ticket-key>` in this workspace, then `/implement` in each repo |
| QA | `handoff` in the backend repo writes the test plan for the SDET. No QA ticket is created |

## 8. Phase 1 complete — pre-flight and stop

This is your own pass, not an approval. Confirm every line before printing:

- [ ] Every repo has a "today" section citing two or more of its own files
- [ ] `api-contracts` was checked for an existing description of this endpoint
- [ ] Any Figma link was opened, and the states it shows became frontend acceptance criteria
- [ ] Every story with frontend work answers all four checklist items: functional ACs, permissions and customer configuration, screen context, and accessibility
- [ ] Every new screen, action, and endpoint names the permission key that gates it
- [ ] Every customer configuration found in classic is named with its home and effect, or an open question asks product to confirm there is none
- [ ] Every proposed story passes every item of the story checklist in step 6b
- [ ] Every item in the Epic's scope maps to a story, and every story maps to an item
- [ ] Every existing ticket has a suggested action (keep, update, merge, split or close) and a reason
- [ ] No QA automation ticket is proposed
- [ ] An Epic with a contract has at least one contract ticket, and every story that uses the contract depends on the contract ticket that covers its shape
- [ ] Every ticket has testable acceptance criteria
- [ ] The contract says whether it is breaking or non-breaking
- [ ] The plain summary has no jargon
- [ ] No Jira issue was created or changed

Then print three things — the file path, the plain summary, and the ticket table — followed
by exactly this:

> This is a proposal, not a plan of record. Nothing has been created in Jira and no
> contract PR has been opened. Review the ticket table. When you are happy with the
> split, say so. The approved changes will then be made to the existing tickets and the
> new stories will be created.

There is no automated gate on this document. It is approved when a person has read it
and said so — never because your own pre-flight passed. Phase 2 starts only on an
explicit human go-ahead.

Do not offer to implement. Wait.

---

## 9. Phase 2 — Update and create tickets (only after user approval)

When the user says the split is approved, run these steps in order. Do not skip any.

### 9a. Apply the approved actions, then create the new stories

Apply only what the user approved. For each existing ticket:

| Approved action | What to do |
| --- | --- |
| **Keep** | Add one comment with `addOrEditJiraIssueComment`: the work by repo, the acceptance criteria this document adds, and a pointer to the contract section. Leave the title and description as they are |
| **Update** | Replace the title and description with the approved text using `editJiraIssue`. Add a comment that says the text was replaced from this refine and why. Jira's history keeps the old text |
| **Merge** | Link the ticket to the one that stays: "duplicates" when it asks for the same thing, otherwise "relates to". Comment on both. Add to the ticket that stays anything it lacks |
| **Split** | Create the new stories, link each one to the original, and update or close the original as approved |
| **Close** | Comment with the reason, then close it |

Never change an assignee. Close or transition a ticket only when the user approved that
for that ticket by name. If a ticket has an assignee and its action is Update, Merge,
Split or Close, tell the user before applying it.

For each new story in the proposed table, call `createJiraIssue`:

- **Project:** the project key of the Epic (e.g. `MER`)
- **Issue type:** Story (or Spike if marked as such)
- **Summary:** the ticket title exactly as written in the table
- **Description:** the full acceptance criteria, out-of-scope, repo, and any notes from the table — in plain text or markdown
- **Parent:** the Epic key (sets the child-of-Epic link)

Create all tickets before adding any links. Record each created key as you go.

### 9b. Add dependency links

For each "Depends on" relationship in the ticket table, create a `Blocks` link:

- The ticket being depended on **blocks** the dependent ticket
- Example: "T4 depends on T2" → create link: T2 blocks T4 (inwardIssue: T2, outwardIssue: T4, type: "Blocks")

Add every dependency in the table, skipping links that already exist. Every contract ticket must block every story that lists it as a dependency.

### 9c. Verify

Fetch each created ticket from Jira and confirm:

| What to check | Why it matters |
| --- | --- |
| Every ticket in the proposed table exists in Jira | Creation can silently fail if a field is invalid |
| Each ticket has the correct type — Story or Spike | A spike created as a Story will be treated like implementation work |
| Acceptance criteria are present and match the proposal | May be truncated if the field limit is exceeded |
| Every "Depends on" relationship has a matching Blocks link | Without links, teams start the wrong things first |
| Every existing ticket shows its approved action: the comment, the new text, the link, or the new status | An action that only half applied leaves two tickets disagreeing |
| Every contract ticket is linked as a blocker on every story that uses it | Most commonly missed link |
| Stories with frontend work have all four checklist sections | Permissions, screen context, and a11y are the ones most often dropped |

If anything is wrong, fix it directly via Jira before continuing.

### 9d. Record the created keys in the refine.md

Append a "Tickets" section to `notes/<epic-id>/refine.md`:

```markdown
## Tickets

| Proposed | Jira key | What was done | Title |
| --- | --- | --- | --- |
| T1 | MER-XXXXX | Kept, comment added | [title](link) |
| T2 | MER-XXXXX | Created | [title](link) |
| - | MER-XXXXX | Merged into T1 | [title](link) |
...
```

This makes the refine.md the permanent record of what was updated and created.

### 9e. Stop

Print the ticket table from 9d and this message:

> All tickets are updated or created, and linked. Next step: run `/contract <epic-id>` to translate
> the contract section into OpenAPI YAML, then open the PR in `api-contracts` and merge
> it before any implementation starts.
