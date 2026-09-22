---
name: contract
description: Translate an approved proposal or refine document into OpenAPI YAML and add it to the right domain file in api-contracts. Runs spectral lint. Never writes product code.
---

# contract

## What this does

Reads an approved `refine.md` or `proposal.md` from the `notes/` directory and
translates the **Contract** section into OpenAPI YAML. Appends the result to the
correct domain file in `repos/new/api-contracts/contracts/web-aggregator/`. Runs
`npx spectral lint` and fixes any errors. Does not open the PR — that is a human step.

## When to use this

- After `/refine` is approved and before any implementation tickets start
- After `/propose` is approved for a Story that introduces or changes an endpoint
- Not needed when a ticket changes no endpoint shape (frontend-only styling, copy changes)

## Input

A note id — the slug under `notes/`. Examples:

    /contract mer-83653-memorize-line-item
    /contract mer-82700-display-status

## Hard rules

- Never write product code.
- Never open a pull request or push to git.
- Only the **Contract** section of the source document is translated. Do not invent
  shapes that are not there.
- Do not change any existing path, operation, parameter, or schema that is already in
  a domain file. Append only.
- If spectral lint reports an error, fix it before stopping. Warnings are acceptable if
  they are pre-existing (check by running lint before your changes).
- The source document is the source of truth. If the contract section is ambiguous,
  stop and ask — do not guess.

---

## Steps

### 0. Check the branch

Before touching any file in `repos/new/api-contracts`, confirm that repo is on a feature
branch, not `main`:

```bash
cd repos/new/api-contracts && git branch --show-current
```

If it is on `main`, stop and ask the user to create a branch first:

> "Please create a feature branch in `repos/new/api-contracts` before I make changes.
> Suggested name: `feat/<note-id>-contract`"

Do not proceed until the branch is confirmed.

### 1. Find the source document

Look for the note in this order:

1. `notes/<id>/refine.md`
2. `notes/<id>/proposal.md`

If neither exists, stop: "No approved document found at notes/<id>/. Run /refine or
/propose first."

Read the entire document. Identify the **Contract** or **Shared decisions → Contract**
section. If no contract section exists, stop: "No contract section found in <file>.
This document may not introduce a new endpoint."

### 2. Extract what needs to go in the YAML

From the contract section, pull out:

**New or changed endpoints** — each `POST /v1/...` or `PATCH /v1/...` heading.
For each endpoint you need:
- HTTP method and path
- Summary (one line from the ticket or document)
- All query parameters
- Request body shape (from Part A examples + Part B field table)
- All response status codes and their bodies (from Part A)
- Whether the change is breaking or non-breaking (from Part C or the document)

**New or changed fields on existing endpoints** — for example "add `displayStatus`
to `GET /v1/expense-reports`". These are schema additions, not new paths.

**New schemas** — any named type in Part B that is not already in a domain file or
in `schemas/`.

If the contract section only describes adding fields to an existing endpoint (no new
path), there is no new path block to add — only schema changes in the relevant
`components/schemas` section of the domain file.

### 3. Choose the right domain file

| Paths starting with | Domain file |
| --- | --- |
| `/v1/expense-reports/…` | `expense-reports.yaml` |
| `/v1/ewallet/…` | `ewallet.yaml` |
| `/v1/forms/…`, `/v1/expense-types`, `/v1/mosaics` | `forms.yaml` |
| `/v1/expense-transactions/…` | `expense-transactions.yaml` |
| `/v1/users/…`, `/v1/authorization/…`, `/v1/navigation/…`, `/v1/config`, `/v1/echo`, `/v1/activity-log` | `session.yaml` |
| A genuinely new top-level resource (e.g. `/v1/customers/…`) | Create a new file named after the resource (`customers.yaml`). Use the same `openapi: 3.1.0` / `info` / `servers` header as the other domain files. |

All domain files live in `repos/new/api-contracts/contracts/web-aggregator/`.

### 4. Check what already exists in the domain file

Open the domain file. Confirm:

- The path does not already exist (if it does, compare and note the difference — do
  not silently overwrite).
- The schema names you plan to add do not already exist under `components/schemas`.

Shared schemas (`ProblemDetail`, `Uda`, `UdaDto`, `ImageDto`, `JsonNode`) live in
`repos/new/api-contracts/schemas/` and are already referenced with
`$ref: '../../schemas/Foo.yaml'`. Use those references — do not redefine them.

### 5. Write the OpenAPI YAML

Use the examples and field tables from the contract section to write valid
OpenAPI 3.1.0 YAML. Follow the patterns already in the domain file exactly.

**Translating Part A (examples) → YAML:**

```yaml
# Request body example from contract:
# { "name": "Recurring lunch" }
# becomes:
requestBody:
  required: true
  content:
    application/json:
      schema:
        $ref: '#/components/schemas/MemorizeLineItemRequest'
      example:
        name: "Recurring lunch"
```

**Translating Part B (field table) → schema:**

```yaml
# Field | Type | Nullable | Description
# name  | string | No    | Display name the user typed.
# becomes:
MemorizeLineItemRequest:
  type: object
  required:
    - name
  properties:
    name:
      type: string
      description: Display name the user typed.
```

**Enums:**
- Strict enum → `enum: [value1, value2]`
- Extensible enum → `type: string` with `description` listing known values and noting
  "consumers must handle unknown values"

**Nullable fields** → `nullable: true` in OpenAPI 3.0 style, or `type: [string, 'null']`
in OpenAPI 3.1.

**Status codes:** include all cases documented in Part A (200, 400, 403, 404, 409,
410, 422, 502 etc.). Error responses reference `$ref: '../../schemas/ProblemDetail.yaml'`.

**Breaking vs non-breaking:** add an `x-breaking: false` or `x-breaking: true`
extension on the path object, matching the document's declaration.

### 6. Append to the domain file

Add the new path block under `paths:` and new schemas under `components/schemas:`.
Do not touch any existing content.

### 7. Run spectral lint

```bash
cd repos/new/api-contracts
npx spectral lint contracts/**/*.yaml
```

Read the full output. Fix every **error** (exit code non-zero). Warnings that were
already present before your change are acceptable — confirm by checking if the same
warning exists on an untouched file.

If lint fails and you cannot fix it, restore the file to its pre-change state, report
what went wrong, and stop.

### 8. Stop and report

Print:

1. Which domain file was changed (or created)
2. Which paths were added or changed
3. Which schemas were added
4. Whether the change is breaking or non-breaking
5. The spectral lint result (output verbatim)
6. **What to do next:**

```
cd repos/new/api-contracts
git add -A
git commit -m "feat(<domain>): <one-line description> (<ticket-id>)"
git push
```

Then open a PR on GitHub. Merge it before starting any implementation.
After the PR merges, run `/propose` on the backend and frontend tickets.

Do not offer to implement. Do not open the PR. Wait.
