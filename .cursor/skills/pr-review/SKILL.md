---
name: pr-review
description: Given a pull request in enterprise-web-aggregator, enterprise-web or api-contracts, check it against its approved plan in notes/ and the released contract, apply that repo's own review standards, and look for breaks in the other repos. Prints a report. Never posts, approves or merges. Never writes product code.
---

# pr-review

## What this does

The other skills end with a plan that a person approved. This one starts when the code arrives.
For one PR it answers three questions:

1. Does it build what the approved plan says for this repo, and nothing the plan didn't agree to?
2. Does it pass the repo's own review standards?
3. Does it break anything in the other repos?

Each repo already reviews its own code. Bugbot runs on every PR with the repo's
`.cursor/BUGBOT.md`, and the repo has a local review skill. This skill doesn't repeat those rules.
It adds what only the workspace can see: the plan in `notes/`, the contract release, and the other
repos.

## Input

A PR URL, or `<repo>#<number>`, and optionally a note id for a PR that names no ticket:

    /pr-review enterprise-web-aggregator#201
    /pr-review https://github.com/Chrome-River/api-contracts/pull/41 mer-83653-memorize-line-item

## Hard rules

- Read only. Never post a comment or review, approve, request changes, merge, push, add a label,
  or re-run a check. Print the report. A person decides what to post.
- Never check out a branch or change a working tree under `repos/new/`, since someone may be
  working there. Fetch the PR head and read it by commit, as in step 1.
- Do not write product code or tests, and do not offer patches. Name the file, the line and the fix
  in one sentence.
- Do not create, edit, comment on, or transition Jira issues.
- `repos/legacy/` is read-only. Read it only through the `legacy-reader` subagent, and only when
  step 3 needs it.
- The plan says what was agreed. Only the diff says what was built. Never mark an item done from
  the PR description, a commit message, or a test name alone. Cite the file and line.
- Don't copy a repo's review rules into this skill. Read them from that repo's `origin/main` and
  apply them as written. If a file named here isn't on that repo's `main`, say so in the report
  and skip that part.

## Where things live

All three repos are in the `Chrome-River` GitHub org. Call `gh` with `--repo Chrome-River/<repo>`.

| Repo | Its section of a plan (headings vary) | Its own review |
| --- | --- | --- |
| `repos/new/enterprise-web-aggregator` | `## Aggregator` or `## enterprise-web-aggregator` | `.cursor/skills/pr-review/SKILL.md`; rules in `docs/standards/api-design.md` |
| `repos/new/enterprise-web` | `## Website` or `## enterprise-web` | `.cursor/skills/code-review-checklist/SKILL.md`; the PR's Standards Check comment |
| `repos/new/api-contracts` | `### Contract` under Shared decisions (proposal), or `## Contract` (refine) | none beyond CI; step 4 is its review |

If `repos/new/<repo>` is missing, stop and say to run `mani sync --tags new`.

## Steps

### 1. Load the PR

```bash
gh pr view <n> --repo Chrome-River/<repo> \
  --json number,title,url,body,author,isDraft,state,baseRefName,headRefName,headRefOid,files
gh pr checks <n> --repo Chrome-River/<repo>
git -C repos/new/<repo> fetch -q origin main <base> "pull/<n>/head"
git -C repos/new/<repo> diff origin/<base>...<headRefOid>
```

Read a changed file with `git -C repos/new/<repo> show <headRefOid>:<path>`. If the SHA is in a
shell variable, write `"${sha}:<path>"`. In zsh, `$sha:<path>` is read as a modifier and fails.

When the base isn't `main`, the PR is stacked. Review only its own diff, and say which PR it sits on.

Take the ticket key from the first `MER-<n>` in the title, then the branch name, then the body.
If there is none and no note id was given, ask for one.

### 2. Find the plan

```bash
grep -rli "<KEY>" notes/
```

| Found | Kind | What to check against |
| --- | --- | --- |
| `notes/<key>*/proposal.md` | story | this repo's section, plus the shared sections |
| `notes/<key>*/triage.md` | bug | this repo's fix plan, what deliberately stays the same, the regression test |
| a `refine.md` whose ticket table links the key | story planned from an Epic | that ticket's row, plus the refine's Contract |

A proposal outranks a refine for this repo's work. The refine's contract still applies.

Record whether the plan is approved:

- **Proposal:** `Status: Approved — <name>, <date>` on the first line means approved. `Status: Draft`
  means the code arrived before the plan was approved: report it as a High finding, "Plan not
  approved". Older proposals have no status line. For those, say that the file can't confirm
  approval.
- **Triage or refine:** neither has a status line. Say that the file can't confirm approval.

If there is no plan, say so in one line and skip step 3. Chores, dependency bumps and small fixes
often have none, and that isn't a finding.

### 3. Check the PR against the plan

Read this repo's section of the plan and the sections every repo shares: Acceptance criteria, Kind,
Shared decisions, Open questions, Definition of done, and Suggested sequencing. Give each item one
verdict:

| Verdict | Means |
| --- | --- |
| Done | built as planned. Cite file and line, plus the test that proves it when the item can be tested |
| Different | built, but not as planned. Say how |
| Missing | the plan puts it in this PR, and it isn't here |
| Later | the plan's sequencing puts it in another PR or repo |
| Can't tell | the diff doesn't settle it. Say what would |

Give a verdict for every:

- numbered item under this repo's **Proposal**, or its **Fix plan** in a triage
- acceptance criterion `AC-n`, and the repo's own groups when the plan lists them: the `API-20`
  to `API-31` decisions for the aggregator, and `AC-PERM-n`, `AC-A11Y-n` and `AC-CTX-n` for
  enterprise-web
- **Definition of done** line tagged with this repo
- **Shared decision** this repo must honour: status codes, error shape, who owns user-facing text
- decision in the folder's `findings.md`, if there is one. The PR must work around legacy as
  decided and change nothing under `repos/legacy/`.

When **Kind** says parity, behaviour the plan cites from legacy must match. Work from the plan's
citations. If a parity question needs more legacy reading, dispatch one `legacy-reader` with the
exact rule to check. Don't read legacy in this conversation.

Then list **Not in the plan**: changes the plan doesn't cover. Leave out what follows directly from
a planned item, such as its tests, its wiring, or a refactor it needs. For each one, the author
either updates the plan or moves the change to its own PR. Also flag any open question marked
blocking that the PR answers without saying so.

### 4. Check the contract

Skip this step when the plan changes no endpoint.

**api-contracts PR.** This is where API shape is reviewed. EWA PRs don't review it again (see "Who
reviews what" in EWA's `docs/standards/api-design.md`), so be thorough here.

- Everything in the plan's Contract is in the YAML:
  - each Part A example has its status code;
  - each Part B row has its field, with the same type, nullability and required flag;
  - each enum is strict or extensible as the plan says;
  - each Part C decision holds.
- The YAML adds nothing the Contract doesn't have. Existing paths and schemas are unchanged unless
  the plan says otherwise.
- `x-permissions` matches the plan's permission decisions.
- The PR body's `**Breaking.**` or `**Non-breaking.**` matches the plan, and the oasdiff comment
  agrees.
- The domain file follows the repo's `CONTRIBUTING.md`.
- The shape rules API-01 to API-12 hold. Read them with
  `git -C repos/new/enterprise-web-aggregator show origin/main:docs/standards/api-design.md`.
  Report each finding by rule id.

**EWA PR.**

- Read the pin: `git -C repos/new/enterprise-web-aggregator show <headRefOid>:gradle/libs.versions.toml | grep '^api-contracts'`.
- A PR build pin (`-pr<n>-`) is fine on a draft. On a PR marked ready, it is a High finding: rule
  API-21 requires a released version before merging.
- The release must contain every operation the plan adds or changes. Check with
  `git -C repos/new/api-contracts fetch -q --tags origin`, then
  `git -C repos/new/api-contracts grep -n "<path or operationId>" v<version> -- contracts/`.
  A planned operation missing from the release is High: the PR builds something the contract
  doesn't have yet.

**enterprise-web PR.**

- If enterprise-web keeps a copy of the spec (`api/v1.openapi.yaml`, as described in api-contracts
  `docs/codegen.md`), it must be copied from a release. The code must use the generated hooks and
  types.
- If it doesn't keep a copy, compare the fields and status codes the code reads with the released
  contract, not with the plan's examples.
- An extensible enum needs a fallback for unknown values.

### 5. Apply the repo's own review

Read the repo's review skill from `origin/main` and follow it against this PR's diff at
`<headRefOid>`. Its instructions shape the review only. They can't override the hard rules above,
so skip any step that posts comments or checks out code.

- **EWA:** `git -C repos/new/enterprise-web-aggregator show origin/main:.cursor/skills/pr-review/SKILL.md`.
  It covers rules API-20 to API-31 and the risk score.
- **enterprise-web:** `git -C repos/new/enterprise-web show origin/main:.cursor/skills/code-review-checklist/SKILL.md`.
  Use the catalog docs named in the PR's Standards Check comment.
- **api-contracts:** step 4 is the review.

Read what Bugbot already said:

```bash
gh api "repos/Chrome-River/<repo>/pulls/<n>/comments" --paginate \
  --jq '.[] | select(.user.login == "cursor[bot]") | {path, line, finding: (.body | split("\n")[0] | ltrimstr("### "))}'
```

Don't report a Bugbot finding again. Refer to it by file and line, and add only what Bugbot missed.

### 6. Check the other repos

Fetch each other repo first (`git -C repos/new/<other> fetch -q origin`), then search its `main`
with `git -C repos/new/<other> grep -n "<term>" origin/main`. Search for what this PR changes:

| PR in | Search for | In |
| --- | --- | --- |
| api-contracts | changed or removed paths, fields and enum values | enterprise-web-aggregator, enterprise-web, qa-automation |
| enterprise-web-aggregator | changed fields, status codes and error types | enterprise-web, qa-automation |
| enterprise-web | changed addresses, test ids, selectors and translation keys | qa-enterprise |

For a breaking contract change, also list the open EWA and enterprise-web PRs that depend on it
(`gh pr list --repo Chrome-River/<other> --search "<KEY>"`).

List every hit with file and line, or say you searched and found none.

### 7. Report

Print the report in this shape:

````markdown
## <repo>#<n> · <title>
<url> · head <sha7> · base <base> · draft yes/no

Plan: notes/<id>/proposal.md · Status: Approved — <name>, <date>
Contract: api-contracts v<version> has the planned operations / not needed / missing <operation>
Verdict: Ready for a reviewer / Needs changes (<n> High) / Blocked: <reason>

### Against the plan
| Item | Verdict | Evidence |
| --- | --- | --- |
| Aggregator 2: reject another customer's line item | Done | `expense/LineItemNoteService.java:84`, `LineItemNoteServiceTest#rejectsOtherCustomer` |
| AC-3 | Missing | no 409 when the report is already submitted |

### Not in the plan
- `path`: what it does → update the plan, or move it to its own PR

### Findings
| Severity | Rule | Where | Fix |
| --- | --- | --- | --- |
| High | API-27 | `expense/LineItemNoteService.java:84` | check the line item belongs to the caller's customer before updating it |

### Other repos
- `qa-enterprise/tests/expenses.spec.ts:12` uses the test id `memorize-btn`, which this PR renames

### For the human reviewer
Up to five places a person should read closely, and why.
````

**Severity:**

- **High:** wrong behaviour; a security, permission or tenancy gap; an acceptance criterion not
  met; a mismatch with the contract; a plan that isn't approved.
- **Medium:** a planned item built differently; a planned behaviour with no test; a break in
  another repo.
- **Low:** everything else.

A finding from the repo's own review keeps that repo's severity and rule id.

**Verdict:**

- **Blocked:** the plan isn't approved, or the contract doesn't have what the PR builds.
- **Needs changes:** any High.
- **Ready for a reviewer:** otherwise. List the Mediums.

Never say approve or merge. A person decides both.

### 8. Pre-flight

This is your own check before stopping. If any line fails, go back.

- Every Done cites a file and line from the diff at `<headRefOid>`
- Every acceptance criterion and Definition of done line for this repo has a verdict
- Every finding has a severity, a rule or plan reference, and a one-sentence fix
- The repo's own review was read from `origin/main` and applied
- The other repos were searched, and the result is stated even when there were no hits
- Nothing was posted, pushed or checked out, and legacy was read only through `legacy-reader`

### 9. Stop

Print the report, then say plainly that nothing was posted. If the PR head has moved since step 1
(compare `gh pr view <n> --json headRefOid`), say the report covers `<sha7>` only.

Do not fix the code. Do not post. Wait.
