# Memorize Line Item

## Glossary

| Word | Meaning |
| --- | --- |
| classic | The current production website (mercury). Read-only for this work. |
| reimagine | The new React app being built (`enterprise-web`). |
| aggregator | The new Java server reimagine talks to (`enterprise-web-aggregator`). |
| Apollo | The backend server classic talks to. Read-only for this work. |
| unused expenses | The page in reimagine showing expenses not yet on a report (eWallet). |
| memorized expense | A saved template created from a line item; it appears in unused expenses for reuse. |
| customer config | A setting that is the same for every person at a customer — not a per-user permission. |

## Plain summary

When a person fills in the same kind of expense repeatedly — a regular lunch, a recurring commute — they re-enter every field each time. Classic has a Memorize feature that copies a saved line item into a reusable template; the person names it and finds it in unused expenses on every future visit. Reimagine has no Memorize button, no naming dialog, and no way to identify memorized expenses in the unused expenses list. This Epic adds all three: the button (shown only when the customer has the feature and the line is eligible), the dialog, the server action that creates the template, and the label in unused expenses so the person can find what they saved.

## Epic

[MER-83653](https://emburse.atlassian.net/browse/MER-83653) — [TEST] Memorize Line Item.

Goal: bring parity with classic's Memorize feature — a user names a saved line item and finds it as a reusable template in unused expenses.

## Existing designs

**Figma:** [Memorize screen](https://www.figma.com/design/O2eRGOwGZkI1cJprkyShOl/T-E---Front-End-Epic?node-id=4919-11889)

States shown in the design:
- Line item action bar — Memorize button visible alongside other actions
- Dialog — header "Memorize", single name field, Cancel and Save buttons
- Success notification banner
- Error notification banner

States **not** shown in the design:
- How a memorized transaction looks in the unused expenses list (open question 1)
- Hidden state (no button) for parent, child, per-diem, or unsaved line items

**Confluence:** [Figma design — APIs](https://emburse.atlassian.net/wiki/spaces/~7120201c1bb597292447e6add2674702c6c889/pages/5129240600/Figma+design+-+APIs) — Section 2 "Memorize". Primary API design reference.

Key decisions from Confluence that this document adopts:
- `GET /v1/customers/{id}/preferences` (Customer service, `tbl_CustomerPreferences`) is the home for `enableMemorizedExpenseTransactions`
- The aggregator loads the Apollo line item and forwards it — reimagine never sees the Apollo shape
- `parentId` must be added to the line-item GET so reimagine can detect child lines
- The eWallet list must expose the user-given name and feed code so reimagine can display memorized templates

## Tickets already open

The following 6 children already exist under this Epic. The ticket split below reuses them:

| Key | Title | Status |
| --- | --- | --- |
| [MER-83686](https://emburse.atlassian.net/browse/MER-83686) | [TEST] Add Memorize and CustomerPreferences OpenAPI contracts | New |
| [MER-83687](https://emburse.atlassian.net/browse/MER-83687) | [TEST] Add GET /v1/customers/{id}/preferences to aggregator | New — **already implemented**, see below |
| [MER-83688](https://emburse.atlassian.net/browse/MER-83688) | [TEST] Expose parentId on GET line-item detail response | New |
| [MER-83689](https://emburse.atlassian.net/browse/MER-83689) | [TEST] Add memorize endpoint and eWallet name to aggregator | New |
| [MER-83690](https://emburse.atlassian.net/browse/MER-83690) | [TEST] Add Memorize to line item and unused expenses (reimagine) | New |
| [MER-83691](https://emburse.atlassian.net/browse/MER-83691) | [TEST] Playwright coverage for Memorize Line Item | New |

## Each repo today

### `api-contracts`

Five domain files exist: `expense-reports.yaml`, `ewallet.yaml`, `forms.yaml`, `expense-transactions.yaml`, `session.yaml`.

No memorize endpoint exists in any file. No `customers.yaml` exists. Both are missing — that is what T1 delivers.

### `enterprise-web-aggregator` (aggregator)

**Already shipped (on `testing-aidlc` branch):**
- `GET /v1/customers/{customerId}/preferences` — `customers/CustomerPreferencesController.java`, `customers/CustomerPreferencesService.java`, `customers/CustomerPreferencesResponse.java`. Returns `{ customerId, enableMemorizedExpenseTransactions }`. Customer id read from JWT. This is T2 — already done.

**Missing:**
- No `parentId` on `LineItemDetailResponse` (`expense/LineItemDetailResponse.java`). Has `isParent` but not `parentId`. A child line has a parent — today reimagine cannot tell that a line is a child.
- No `name` or `feedCode` on `EwalletTransactionResponse` (`ewallet/EwalletTransactionResponse.java`). Has `transactionId`, `transactionDate`, `expenseType`, `merchantName`, `spentAmount`, `currencyCode`, `hasAttachment`, `sourceType`, `cardLastFour`, `isMerged`, `isAutoMerged`, `deletable`, `subTransactions` — but nothing to identify a memorized template.
- No memorize endpoint anywhere.

### `enterprise-web` (reimagine)

**Nothing memorize-related exists.**

The unused expenses page exists (`src/features/expenses/pages/UnreportedExpenses/`) and consumes `EwalletTransaction` from `src/shared/api/v1/ewalletTransactions`. Adding `name` and `feedCode` to the aggregator response means adding them to the frontend type and rendering them.

`GET /v1/customers/{customerId}/preferences` is never called from reimagine — there is no hook or API client for it.

The line-item action bar (`LineItemDetailFormsPathShell.tsx`) has no Memorize button.

### `repos/legacy/mercury` — classic (read only)

Memorize is fully implemented:
- `expense_lineitem_actionbar_template_helper.js:308` — `allowMemorize()` checks: `!isNew`, `enableMemorizedExpenseTransactions` from `window.customerPreferences`, not parent/child/per-diem.
- `expense_lineitem_actionbar_view.js:345` — shows dialog, calls `memorizeToServer(name)`.
- `data_lineitem_entity.js:1301` — sends `POST /expenseTransaction/memorized?name=` with the full line-item JSON, stripping add-info UDAs. Identifies memorized transactions via `expenseTransaction.feed.code === 'Memorized Expense'`.

### `repos/legacy/apollo` (read only)

- `ExpenseTransactionController.java:1724` — `POST /expenseTransaction/memorized?name=` with `@RequestBody ExpenseReportLineItem`. Calls `transactionClient.createMemorizedExpenseTransaction(...)`. Returns `ExpenseTransaction`.

## Parity

**Parity.** Classic already has Memorize. Classic's `allowMemorize` logic is the rule for button visibility; classic's `memorizeToServer` is the API call. We read classic to understand what can go wrong; we do not copy how classic presents it.

## Contract

### Permissions

`enableMemorizedExpenseTransactions` is the same for every user at a customer → **Config** bucket → `GET /v1/customers/{id}/preferences`.

| | |
| --- | --- |
| **Bucket** | Config |
| **EWA endpoint** | `GET /v1/customers/{customerId}/preferences` — **already implemented** |
| **Permission key** | None — this is a config gate, not a per-user permission |
| **Without access** | Memorize button is hidden; memorize endpoint rejects with 400 |
| **Delegate** | No change — config is customer-level, same for all including delegates |

The backend memorize endpoint must also check the config before executing. Hiding the button is UX, not security.

### A. JSON examples

**`GET /v1/customers/{customerId}/preferences`** (already exists):
```json
{ "customerId": 3074, "enableMemorizedExpenseTransactions": true }
```

**`POST /v1/expense-reports/{headerId}/line-items/{lineItemId}/actions/memorize`** — request:
```json
{ "name": "Recurring lunch" }
```

200 success:
```json
{ "transactionId": "987654" }
```

400 — config off, or line is parent/child/per-diem/unsaved:
```json
{
  "type": "about:blank",
  "title": "Bad Request",
  "status": 400,
  "detail": "This line item cannot be memorized.",
  "instance": "/v1/expense-reports/rpt-123/line-items/li-456/actions/memorize"
}
```

403, 404, 502 follow the standard aggregator problem document.

**`GET /v1/ewallet/transactions`** — additive, non-breaking. New fields `name` and `feedCode` on every row:
```json
{
  "transactionId": "987654",
  "transactionDate": "2026-09-15 00:00:00:000",
  "expenseType": "Meals",
  "merchantName": "Recurring lunch",
  "spentAmount": 42.50,
  "currencyCode": "USD",
  "hasAttachment": false,
  "sourceType": "OFFLINE",
  "cardLastFour": null,
  "isMerged": false,
  "isAutoMerged": false,
  "deletable": true,
  "name": "Recurring lunch",
  "feedCode": "Memorized Expense",
  "subTransactions": []
}
```

Non-memorized row: `"name": null, "feedCode": "Credit Card"`.

**`GET /v1/expense-reports/{headerId}/line-items/{lineItemId}`** — additive, non-breaking. New field `parentId`:
```json
{
  "lineItemId": "li-456",
  "parentId": null,
  "isParent": false,
  "...": "all other existing fields unchanged"
}
```
Child line: `"parentId": "li-456"`.

### B. Field tables

**`POST …/actions/memorize` request:**

| Field | Type | Nullable | Description |
| --- | --- | --- | --- |
| `name` | string | No | Display name the user typed. Used as the transaction name in unused expenses. |

**`POST …/actions/memorize` response:**

| Field | Type | Nullable | Description |
| --- | --- | --- | --- |
| `transactionId` | string | No | The new unused-expense transaction id. Reimagine invalidates the eWallet list to show it. |

**Additions to `EwalletTransactionResponse`:**

| Field | Type | Nullable | Description |
| --- | --- | --- | --- |
| `name` | string | Yes | User-given name for a memorized template. Null for all other types. |
| `feedCode` | string | Yes | Upstream feed name. Known today: `"Memorized Expense"`, `"Credit Card"`. **Extensible** — consumer must not use a closed TypeScript union; handle unknown values gracefully. |

**Addition to `LineItemDetailResponse`:**

| Field | Type | Nullable | Description |
| --- | --- | --- | --- |
| `parentId` | string | Yes | Parent line-item id when this is an itemized child. Null for top-level and parent lines. Non-null → Memorize button must be hidden. |

### C. Decisions

1. **Button eligibility is enforced on the backend.** The memorize endpoint checks `enableMemorizedExpenseTransactions`, line type, and saved state. The frontend check is UX only.
2. **EWA loads the Apollo line; reimagine never sees the Apollo shape.** The memorize call accepts only `{ name }`. The aggregator fetches the full Apollo line, strips add-info UDAs (matching classic), and forwards to Apollo's memorize endpoint.
3. **200 on success, not 201.** The memorize call creates an unused expense as a side effect, not an EWA-owned resource.
4. **`feedCode` is extensible.** New feed codes appear as feeds are configured. Do not use a closed enum on the frontend.
5. **`parentId` null means top-level.** Both `isParent: true` lines and ordinary single lines have `parentId: null`. Only children have a non-null `parentId` — the child check is a null check.
6. **Per-diem eligibility comes from `GET /v1/expense-types`.** Each expense type already has `isPerDiem`. No new field needed on the line-item response.
7. **All changes are non-breaking.** Additive fields on existing responses; two new endpoints.

### Where the contract goes

`contracts/web-aggregator/` in `api-contracts`. Domain split:
- `expense-reports.yaml` — `POST …/actions/memorize`, `parentId` on line-item GET
- `customers.yaml` (new file) — `GET /v1/customers/{customerId}/preferences`
- `ewallet.yaml` — `name` and `feedCode` on eWallet transaction response

Run `/contract mer-83653-memorize-line-item` to produce the YAML from this document.

## Proposed tickets

The 6 existing tickets are reused with updated understanding of what is already built.

### T1 — Contract ([MER-83686](https://emburse.atlassian.net/browse/MER-83686))

| | |
| --- | --- |
| **Ask** | Add OpenAPI definitions to `api-contracts` for the memorize endpoint, eWallet additions, `parentId`, and the already-implemented `GET /v1/customers/{id}/preferences`. |
| **Acceptance criteria** | `POST …/actions/memorize` is defined. `customers.yaml` exists with the preferences endpoint. `EwalletTransactionResponse` includes `name` and `feedCode`. `LineItemDetailResponse` includes `parentId`. `spectral lint` passes with 0 errors. All changes are marked non-breaking. |
| **Out of scope** | Implementation code. |
| **Depends on** | Nothing |
| **Size** | ~120 lines of YAML |

### T2 — Backend: GetCustomerPreferences ([MER-83687](https://emburse.atlassian.net/browse/MER-83687))

**Status: already implemented on `testing-aidlc`.** `GET /v1/customers/{customerId}/preferences` exists in `customers/CustomerPreferencesController.java`. This ticket's acceptance criteria are met. Mark done after the contract PR merges.

| | |
| --- | --- |
| **Remaining work** | OpenAPI annotation on the existing controller must match the merged `customers.yaml`. Verify and adjust if needed. |
| **Depends on** | T1 (for the contract to verify against) |

### T3 — Backend: parentId on line-item GET ([MER-83688](https://emburse.atlassian.net/browse/MER-83688))

| | |
| --- | --- |
| **Ask** | Add `parentId` to `LineItemDetailResponse` by reading it from the Apollo line-item payload. |
| **Acceptance criteria** | `GET …/line-items/{lineItemId}` response includes `parentId`. Child lines return the parent's id. Top-level and parent lines return null. Existing tests still pass. |
| **Out of scope** | Any other missing Apollo fields. |
| **Depends on** | T1 |
| **Size** | ~50 lines |

### T4 — Backend: MemorizeLineItem + eWallet name ([MER-83689](https://emburse.atlassian.net/browse/MER-83689))

| | |
| --- | --- |
| **Ask** | New memorize endpoint that creates a named template, plus `name`/`feedCode` on the eWallet list. |
| **Acceptance criteria** | `POST …/actions/memorize` with `{ "name": "Recurring lunch" }` returns `{ "transactionId": "..." }`. The aggregator fetches the full Apollo line and forwards it (not the EWA DTO). Add-info UDAs are stripped. 400 when config is off or line is ineligible. 403/404/502 use the standard problem document. No 500 for any eligibility failure. `GET /v1/ewallet/transactions` includes `name` (null for non-memorized) and `feedCode` on every row. Memorized rows have `feedCode: "Memorized Expense"` and a non-null `name`. Existing tests still pass. OpenAPI matches the contract. |
| **Out of scope** | Guest split behaviour (Apollo/expense-service layer). Frontend display (T5). |
| **Depends on** | T1, T2 (to check the config), T3 (to read parentId for eligibility) |
| **Size** | ~330 lines |

### T5 — Frontend: Memorize button, dialog, and unused expenses display ([MER-83690](https://emburse.atlassian.net/browse/MER-83690))

| | |
| --- | --- |
| **Ask** | Add the Memorize button and dialog to the line-item screen; show the user-given name in unused expenses. |

**Functional acceptance criteria:**
- Button appears when: `enableMemorizedExpenseTransactions` is true, line is saved, `isParent` is false, `parentId` is null, and expense type's `isPerDiem` is false
- Tapping opens a dialog with a name field, Cancel, and Save (disabled until name is non-blank)
- Confirming calls the memorize endpoint, shows a success notification, and invalidates the eWallet list
- On error, shows an error notification; dialog stays open for retry
- A memorized transaction in unused expenses shows the user-given name

**Permissions:** No new permission key. Config bucket — gated by `enableMemorizedExpenseTransactions` from `GET /v1/customers/{id}/preferences`. Delegates see the same config value.

**Screen context (AI widget):** Add `memorize` action to the line-item detail screen context when eligible. Follow Screen Context Schema V2 and MER-81183 patterns.

**Accessibility:** Button has accessible label. Dialog heading, visible input label, focus moves to name field on open. Cancel and Save have distinct names. Notifications are announced (`role="status"`). Tab order: name field → Cancel → Save.

| | |
| --- | --- |
| **Out of scope** | AI widget invoking memorize. Filtering unused expenses by memorized type. |
| **Depends on** | T1, T2, T4 |
| **Size** | ~380 lines |

### T6 — QA ([MER-83691](https://emburse.atlassian.net/browse/MER-83691))

| | |
| --- | --- |
| **Ask** | Playwright end-to-end tests for the memorize flow and eligibility conditions. |
| **Acceptance criteria** | Test: tap Memorize on an eligible saved line item, name it, confirm, find it in unused expenses with that name. Test: button absent when config is off. Test: button absent on a parent line item. Test: button absent on an unsaved line item. |
| **Out of scope** | Per-diem and child-line cases — covered by unit tests in the frontend. |
| **Depends on** | T5 |
| **Size** | ~150 lines |

## Order of work

```
T1 (Contract)
  ├── T2 (verify CustomerPreferences annotation) ─┐
  └── T3 (parentId on GET)                        ├── T4 (MemorizeLineItem + eWallet)
                                                   │
                                                   └── T5 (Frontend) ── T6 (QA)
```

T2 is already implemented — the remaining work is confirming the OpenAPI annotation matches the contract. T3 and T4 can start at the same time once T1 merges. T5 waits on T4. First ticket that delivers something a user can see: **T5**.

## Risks

1. **Apollo's memorize endpoint takes the full `ExpenseReportLineItem` shape.** The aggregator GETs that shape and forwards it. If the GET and the expected POST body diverge after a µExpense migration, the forward fails silently. Verify end-to-end in test before closing T4.
2. **Add-info UDA stripping.** Classic strips `addInfo: true` UDAs before memorizing. The aggregator must reproduce this filter. Missing filter → memorized templates carry add-info UDAs that make them harder to reuse.
3. **Per-diem eligibility check via expense types.** Frontend checks `isPerDiem` from expense types on load. If type changes mid-session the check may be stale. Backend check is authoritative.
4. **eWallet source type enum gap.** `ExpenseTransactionSourceType` does not include a Memorized value. Adding `feedCode` as a separate string (T4) avoids depending on a new enum value.

## Open questions

1. **How does a memorized transaction look in unused expenses — reimagine, blocking T5.** Figma does not show this state. Classic shows memorized templates inline in the expenses list with no separate tab. Is that the design intent for reimagine, or should there be a distinct row style or label? Needs a Figma update before T5 acceptance criteria can be finalised.

2. **Should `enableMemorizedExpenseTransactions` come from `GET /v1/session/context` or a separate call — aggregator and reimagine, not blocking.** Multiple Epics need CustomerPreferences fields. If session/context already aggregates them on cold start, adding Memorize's flag there means zero extra round trips. Decide before T5 starts.

## Done means

- A user with `enableMemorizedExpenseTransactions = true` can tap Memorize on any eligible saved single line item, type a name, confirm, and find the template in unused expenses with that name.
- The Memorize button is absent when config is off, when the line is a parent, child, per-diem, or unsaved.
- The backend rejects ineligible memorize calls with 400, not 500.
- Memorized templates in unused expenses show the user-given name.
- Keyboard and screen reader users can complete the flow without a mouse.
- Classic and Apollo are unchanged.

## What happens next

| Ticket | Next step |
| --- | --- |
| T1 — Contract (MER-83686) | Run `/contract mer-83653-memorize-line-item` in this workspace, open the PR in `api-contracts`, merge before anything below starts |
| T2 — CustomerPreferences (MER-83687) | Already implemented. Verify OpenAPI annotation matches `customers.yaml` after T1 merges. Close. |
| T3 — parentId on GET (MER-83688) | `/propose` → `/implement` → `/review` in `enterprise-web-aggregator` |
| T4 — MemorizeLineItem + eWallet (MER-83689) | `/propose` → `/implement` → `/review` → `/handoff` in `enterprise-web-aggregator` |
| T5 — Frontend (MER-83690) | `/propose` → `/implement` → `/review` in `enterprise-web` |
| T6 — QA (MER-83691) | `/handoff` output from T4 feeds into `write-enterprise-web-ui-test` in `qa-enterprise` |

Each repo's `/propose` reads the merged contract from `api-contracts` first — that YAML outranks this document once the T1 PR has landed.
