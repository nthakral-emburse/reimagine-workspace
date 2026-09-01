---
name: investigate
description: Document how one existing mercury/apollo flow works today. Produces a spec, not a recommendation. Optional — /propose does its own code reading, so you do not need to run this first.
---

> Use this only when you want a standalone record of current behavior.
> If you have a Jira ticket and want a solution, run `/propose` directly.

# Investigate one feature

You are the conductor. You do not read legacy code yourself — you dispatch
`legacy-reader` and work from its reports. Your context holds the plan, the
questions, and the output. Nothing else.

## 1. Scope it

Confirm exactly one feature: one screen, one endpoint group, or one named
capability. If what I asked for is bigger, say so and propose a split. Stop.

Create `notes/<NNN>-<slug>/` and copy in the templates from `notes/_template/`.

Record commit SHAs: `mani run shas --output markdown`. Do not continue without them.

## 2. Ask questions — BLOCKING

Before reading any code, write questions to `questions.md`:

    ## Q1 — <title>   [BLOCKING]
    Why it matters: <one sentence tied to a decision downstream>
    Evidence: <file:line or "none yet">
    - A) <option>
    - B) <option>
    - C) <option>
    - X) Something else: ___
    ANSWER:
    ANSWERED BY:

Max 7 per round. Questions about *what this feature is for* and *what correct
means* belong here — asking them later is worthless.

Never conclude you have no questions. When unsure, ask.

## 3. Read the legacy side

Dispatch `legacy-reader` per repo. Brief it with the feature and any known
entry points from `notes/survey/mercury-routes.csv`.

Ask it for RULES, not screens: what determines each status, count, or label;
what is excluded; what is gated.

## 4. Read the new side

Read `repos/new/enterprise-web` and `repos/new/enterprise-web-aggregator`
yourself — they are small enough. What exists, what endpoint serves it.

## 5. Write findings

Fill `findings.md`. Every rule needs:
- file:line evidence
- who depends on it
- whether the new app already covers it

## 6. Self-check

Run `python3 tools/check_stage.py notes/<NNN>-<slug>/` and fix what it reports.

## 7. Gate

Ask: approve, or request changes? On the third revision, also offer
"accept as-is" — it archives the current version and moves on.