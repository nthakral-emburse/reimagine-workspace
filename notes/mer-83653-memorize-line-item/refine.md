# Memorize Line Item

## Glossary

| Word | Meaning |
| --- | --- |
| classic | The current production website. Read-only for this work. |
| reimagine | The new React app being built (`enterprise-web`). |
| aggregator | The new Java server reimagine talks to (`enterprise-web-aggregator`). |
| Apollo | The backend server classic talks to. Read-only for this work. |
| unused expenses | The page in reimagine showing expenses not yet on a report (called "eWallet" internally). |
| memorized expense | A saved template created from a line item; it appears in unused expenses so the user can reuse it. |
| customer config | A setting that is the same for every person at a customer — not a per-user permission. |

## Plain summary

When a person fills in the same kind of expense repeatedly — a standing lunch, a regular commute — they re-enter every field each time. Classic has a Memorize feature that saves a line item as a reusable template; a user names it and it appears in their unused expenses so they can start a new expense from it in one tap. Reimagine does not have this feature at all. This Epic adds the Memorize feature to reimagine, matching exactly what classic does. Afterward, a person who regularly expenses "Recurring lunch" names it once and finds it waiting in unused expenses on every future visit.

## Epic

[MER-83653](https://emburse.atlassian.net/browse/MER-83653) — [TEST] Memorize Line Item.

Goal: bring the Memorize feature to reimagine, matching classic behaviour — a user names a saved line item and finds it as a reusable template in unused expenses.

## Existing designs

**Figma:** [Memorize screen](https://www.figma.com/design/O2eRGOwGZkI1cJprkyShOl/T-E---Front-End-Epic?node-id=4919-11889) — shows the action bar with the Memorize button and the naming dialog.

States shown in the design:
- Line item action bar — Memorize button visible alongside Edit, Images, and Delete
- Dialog — header "Memorize", single text input for the name, Cancel and Save buttons
- Save enabled only when the name is non-blank (inferred from classic; confirm with design)
- Success notification banner
- Error notification banner

States **not** shown in the design:
- How a memorized transaction looks in the unused expenses list (open question 1)
- The hidden state (no button) for parent, child, per-diem, or unsaved line items

**Confluence:** [Figma design — APIs](https://emburse.atlassian.net/wiki/spaces/~7120201c1bb597292447e6add2674702c6c889/pages/5129240600/Figma+design+-+APIs) — Section 2 "Memorize". Authored by Venkata Polavarapu, version 15 (Sept 15 2026). This is the primary API design reference.

**Where this document agrees with the Confluence:**
- `POST /expenseTransaction/memorized?name=` is the Apollo upstream for the save
- `GET /v1/customers/{id}/preferences` (Customer service, `tbl_CustomerPreferences`) is the home for `enableMemorizedExpenseTransactions`
- The aggregator loads the Apollo line item and forwards it — reimagine never sees the Apollo shape
- `parentId` needs to be added to the line-item GET so reimagine can detect child lines
- The eWallet transaction list needs to expose the user-given name and the feed code so reimagine can display memorized templates correctly

**Where the code contradicts the Confluence:**
- The Confluence says to pass `parentId` so child detection works. The current `LineItemDetailResponse` (`expense/LineItemDetailResponse.java`) has `isParent` but **no `parentId`**. `isParent` only tells you a line is a parent, not that it is a child.
- The Confluence says `GET /v1/customers/{id}/preferences` should return a narrow DTO. No such endpoint exists in the aggregator yet. The existing `CustomerConfigClient` only fetches mosaic/Tessera config, not `tbl_CustomerPreferences`.
- The eWallet `EwalletTransactionResponse` has no `name` field and no `feedCode`. The upstream `ExpenseTransactionSourceType` enum (CREDITCARDS, CASH, OFFLINE, IMAGE, CREDITCARD_IMG, TRAVEL, AUTH) does not include a Memorized type, so a new field is needed to surface the feed name.

## Tickets already open

None. No child tickets exist under this Epic.

## Each repo today

### `api-contracts`

One file exists: `contracts/web-aggregator/aggregator-baseline.yaml`. Shared schemas are in `schemas/` (`ProblemDetail.yaml`, `Uda.yaml`, `UdaDto.yaml`, `ImageDto.yaml`, `JsonNode.yaml`).

No memorize endpoint or customer preferences schema exists today. Both are new contracts.

### `enterprise-web-aggregator`

The aggregator has no memorize code of any kind. What exists that this Epic touches:

- **`GET /v1/expense-reports/{headerId}/line-items/{lineItemId}`** — controller at `expense/controller/ExpenseReportController.java:616`, response at `expense/LineItemDetailResponse.java`. Has `isParent` but not `parentId`. The mapper (`expense/LineItemDetailMapper.java`) does not read `parentId` from Apollo today.
- **`GET /v1/expense-types`** — returns `ExpenseTypeResponse` which already has `isPerDiem` (`expense/dto/ExpenseTypeResponse.java:68`). The frontend can already determine if an expense type is per diem from this endpoint.
- **`GET /v1/ewallet/transactions`** — controller at `ewallet/EwalletController.java:252`, response at `ewallet/EwalletTransactionResponse.java`. Has `transactionId`, `transactionDate`, `expenseType`, `merchantName`, `spentAmount`, `currencyCode`, `hasAttachment`, `sourceType`, `cardLastFour`, `isMerged`, `isAutoMerged`, `deletable`, `subTransactions`. **No `name` field, no feed code.**
- **`CustomerConfigClient`** — `expense/client/CustomerConfigClient.java`. Fetches Tessera mosaic config only. Does not touch `tbl_CustomerPreferences`.
- **`CustomerExpensePreferences`** — `expense/dto/CustomerExpensePreferences.java`. This is `tbl_CustomerExpenseData` (a different table). Not the right home for `enableMemorizedExpenseTransactions`.
- **`GET /v1/session/context`** — returns `customerPreferences` from some upstream, but no `enableMemorizedExpenseTransactions` is plumbed through (verified: no references in the codebase to that field name).

### `enterprise-web` (reimagine)

The Memorize feature does not exist. What does exist that this Epic touches:

- **Unreported expenses page** — `src/features/expenses/pages/UnreportedExpenses/UnreportedExpenses.tsx`. Uses tabs for expenses and receipts. The `useUnreportedExpensesListData.ts` hook reads from the eWallet transaction list. The `EwalletTransaction` type is consumed here; adding a `name` field to the aggregator response means adding it to the reimagine type as well.
- **Line item action bar** — no Memorize entry in any file under `src/features/expenses/`. The line item action bar and context registrar (`LineItemDetailContextRegistrar.tsx`) are read-only today and do not expose a memorize action.
- **Customer preferences** — no call to `GET /v1/customers/{id}/preferences` exists in the codebase. The `GET /v1/session/context` response already returns some customer preferences; whether `enableMemorizedExpenseTransactions` should come from there or from a separate call is open question 2.

### `repos/legacy/mercury` — classic (read only)

The Memorize feature is fully implemented. Key files:

- **`expense_lineitem_actionbar_template_helper.js:308`** — `allowMemorize(workingModel)` checks three things: `!isNew` (line must be saved), `usingExpenseMemorizeButton` (= `window.customerPreferences.enableMemorizedExpenseTransactions`), and `isValidLineitemType` (not parent, not child, not per diem). If any fail, the Memorize option is removed from the action bar.
- **`expense_lineitem_actionbar_view.js:345`** — `memorizeLineitem()` shows the naming dialog, then calls `this.model.memorizeToServer(name)` on confirm.
- **`data_lineitem_entity.js:1301`** — `memorizeToServer(name)` sends `POST /expenseTransaction/memorized?name=${name}` with the full line-item JSON as the body (stripping add-info UDAs). Also identifies memorized transactions by checking `expenseTransaction.feed.code === 'Memorized Expense'`.
- **`data_add_transaction_lineitem_api.js:97`** — `isMemorizedExpense` = `transaction.feed.code === 'Memorized Expense'`. Memorized transactions keep guest splits instead of dividing them equally.

### `repos/legacy/apollo` (read only)

- **`ExpenseTransactionController.java:1724`** — `POST /expenseTransaction/memorized?name=`. Takes `@RequestBody ExpenseReportLineItem` and the `name` query param. Calls `transactionClient.createMemorizedExpenseTransaction(expenseReportLineItem, personId, name)`. Returns `ExpenseTransaction`.

## Parity

**Parity.** Classic already has the Memorize feature. Classic's `allowMemorize` logic is the rule for visibility; classic's `memorizeToServer` is the API call. Read classic to understand what can go wrong; do not copy any presentation choices.

## Contract

### Permissions

`enableMemorizedExpenseTransactions` answers "same value for every user at this customer?" → **yes** → **Config** bucket → `GET /v1/customers/{id}/preferences`.

| | |
| --- | --- |
| **Bucket** | Config |
| **EWA endpoint** | `GET /v1/customers/{id}/preferences` (new) |
| **Permission key** | None — this is a config gate, not a per-user permission |
| **Without access** | Memorize button is hidden on all line items |
| **Delegate** | No change — config is customer-level, same for everyone including delegates |

The backend MemorizeLineItem endpoint must also check the config before executing. Hiding the button is UX, not security.

### A. JSON examples

#### 1. `GET /v1/customers/{customerId}/preferences` — success

```json
{
  "customerId": 3074,
  "enableMemorizedExpenseTransactions": true
}
```

Empty or false case:

```json
{
  "customerId": 3074,
  "enableMemorizedExpenseTransactions": false
}
```

#### 2. `POST /v1/expense-reports/{headerId}/line-items/{lineItemId}/actions/memorize` — request

```json
{
  "name": "Recurring lunch"
}
```

Success 200:

```json
{
  "transactionId": "987654"
}
```

400 — config disabled for this customer, or line is a parent/child/per-diem/unsaved:

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

#### 3. `GET /v1/ewallet/transactions` — one transaction row (additive change, non-breaking)

Before (today): `name` is absent.

After (this ticket): `name` and `feedCode` are added. Null on all non-memorized transactions.

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

Non-memorized transaction:

```json
{
  "transactionId": "111222",
  "name": null,
  "feedCode": "Credit Card",
  "...": "other fields unchanged"
}
```

#### 4. `GET /v1/expense-reports/{headerId}/line-items/{lineItemId}` — additive change, non-breaking

Added field `parentId`. Null on top-level lines; non-null on child lines.

```json
{
  "lineItemId": "li-456",
  "parentId": null,
  "isParent": false,
  "...": "all other existing fields unchanged"
}
```

Child line example:

```json
{
  "lineItemId": "li-789",
  "parentId": "li-456",
  "isParent": false,
  "...": "other fields"
}
```

### B. Field tables

#### `GET /v1/customers/{customerId}/preferences`

| Field | Type | Nullable | Description |
| --- | --- | --- | --- |
| `customerId` | integer | No | Customer the preferences belong to. |
| `enableMemorizedExpenseTransactions` | boolean | No | When false, the Memorize button is not shown and the memorize action is rejected. |

This DTO is intentionally narrow for this Epic. The same endpoint will carry additional flags as other Epics are refined — `useGroupAllocation`, `usingHeaderLevelTracking`, `showSubmitConfirmation`, and others are identified in the Confluence design. The shape is additive-only.

#### `POST /v1/expense-reports/{headerId}/line-items/{lineItemId}/actions/memorize`

Request:

| Field | Type | Nullable | Description |
| --- | --- | --- | --- |
| `name` | string | No | Display name the user typed. Used as the transaction name in unused expenses. |

Response:

| Field | Type | Nullable | Description |
| --- | --- | --- | --- |
| `transactionId` | string | No | The transaction id of the newly created unused expense. The frontend invalidates the eWallet list to show it. |

#### Additions to `EwalletTransactionResponse`

| Field | Type | Nullable | Description |
| --- | --- | --- | --- |
| `name` | string | Yes | User-given name for a memorized transaction. Null for all other transaction types. |
| `feedCode` | string | Yes | Upstream feed name (e.g. `"Memorized Expense"`, `"Credit Card"`). The frontend uses this to identify memorized rows. Extensible — do not use a closed enum type on the frontend. |

#### Addition to `LineItemDetailResponse`

| Field | Type | Nullable | Description |
| --- | --- | --- | --- |
| `parentId` | string | Yes | ID of the parent line item when this is an itemized child. Null for top-level lines and parent lines. A non-null value means the Memorize button must be hidden. |

### C. Decisions

1. **Button eligibility is checked on the backend, not trusted from the frontend.** The MemorizeLineItem endpoint checks `enableMemorizedExpenseTransactions` and that the line is not a parent, child, or per diem before forwarding to Apollo. The frontend check is UX only.

2. **EWA loads the Apollo line; the website never sees the Apollo shape.** The memorize call takes only `{ name }` from the website. The aggregator calls `GET /expenseReports/{headerId}/lineItems/{lineItemId}` to load the full Apollo object, strips add-info UDAs (matching Mercury), and forwards the rest to `POST /expenseTransaction/memorized?name=`.

3. **200 on success, not 201.** The memorize call creates an unused expense (a transaction), but that is an internal side effect, not an EWA-owned resource being created. The frontend response is the new transaction id and refetches the list.

4. **`feedCode` is extensible (not strict).** New feed codes will appear as other feeds are configured. The frontend must handle unknown feed codes gracefully — do not use a closed TypeScript union.

5. **`parentId` null means top-level.** Both top-level parents (`isParent: true`) and ordinary single lines (`isParent: false`) have `parentId: null`. Only children have a non-null `parentId`. This makes the child check a null check.

6. **Per-diem eligibility comes from `GET /v1/expense-types`**, not from the line item itself. The frontend already fetches expense types and each has `isPerDiem`. The Memorize button can be hidden client-side for per-diem types without a new field on the line item response.

7. **`GET /v1/customers/{customerId}/preferences` uses the customer id from the JWT.** The frontend does not pass the customer id — the aggregator reads it from the JWT claims, matching how other customer endpoints work.

8. **Breaking vs non-breaking.** All contract changes in this Epic are non-breaking (additive fields on existing responses, one new endpoint, one narrowly-scoped new endpoint). No existing field is removed or renamed.

Who serves each shape:

| Shape | Served by | Consumed by |
| --- | --- | --- |
| `GET /v1/customers/{customerId}/preferences` | aggregator | reimagine |
| `POST …/actions/memorize` | aggregator | reimagine |
| eWallet transaction additions | aggregator | reimagine (unused expenses) |
| `parentId` on line-item GET | aggregator | reimagine (line item detail) |

Reimagine owns the wording on notification banners (success and error).

### Where the contract goes

One pull request in `api-contracts`, touching one file: **`contracts/web-aggregator/aggregator-baseline.yaml`**. All aggregator endpoints live in that file — do not create a new YAML per endpoint or per feature.

The PR adds:
- The new `POST …/actions/memorize` endpoint
- The new `GET /v1/customers/{id}/preferences` endpoint
- The two new fields on the eWallet transaction response (`name`, `feedCode`)
- The new `parentId` field on the line-item GET response

All changes are non-breaking (additive only). `npx spectral lint contracts/**/*.yaml` must pass before the PR opens.

## Proposed tickets

### Ticket 1 — Contract

| | |
| --- | --- |
| **Title** | Add Memorize and CustomerPreferences contracts to api-contracts |
| **Type** | Story |
| **Repo** | `api-contracts` |
| **Ask** | Add OpenAPI definitions for the two new endpoints and the additive fields on two existing endpoints. |
| **Acceptance criteria** | `POST /v1/expense-reports/{headerId}/line-items/{lineItemId}/actions/memorize` is defined with the request, success, and error examples from this document. `GET /v1/customers/{customerId}/preferences` is defined with `enableMemorizedExpenseTransactions`. `EwalletTransactionResponse` includes `name` and `feedCode`. `LineItemDetailResponse` includes `parentId`. `spectral lint` passes. All changes are marked non-breaking. |
| **Out of scope** | Implementation code. Other flags on CustomerPreferences. |
| **Depends on** | Nothing |
| **Size** | ~100 lines |

---

### Ticket 2 — Backend: GetCustomerPreferences

| | |
| --- | --- |
| **Title** | Add GET /v1/customers/{id}/preferences to aggregator |
| **Type** | Story |
| **Repo** | `enterprise-web-aggregator` |
| **Ask** | New endpoint that returns a narrow customer preferences DTO from `tbl_CustomerPreferences`, initially containing `enableMemorizedExpenseTransactions`. Customer id comes from the JWT. |
| **Acceptance criteria** | `GET /v1/customers/{customerId}/preferences` returns `{ customerId, enableMemorizedExpenseTransactions }`. Customer id is taken from the JWT, not from the URL path or from a caller-supplied header. Customers without the feature return `false`. 401 when JWT is missing. OpenAPI annotation matches the contract. |
| **Out of scope** | Other `CustomerPreferences` flags (`useGroupAllocation`, `showSubmitConfirmation`, etc.) — they will be added as those Epics land. The `CustomerExpensePreferences` endpoint (`tbl_CustomerExpenseData`) is a different class of data and is not this ticket. |
| **Depends on** | Ticket 1 |
| **Size** | ~150 lines |

---

### Ticket 3 — Backend: Add parentId to line-item GET

| | |
| --- | --- |
| **Title** | Expose parentId on GET line-item detail response |
| **Type** | Story |
| **Repo** | `enterprise-web-aggregator` |
| **Ask** | Add `parentId` to `LineItemDetailResponse` by reading it from the Apollo line-item payload. |
| **Acceptance criteria** | `GET /v1/expense-reports/{headerId}/line-items/{lineItemId}` response includes `parentId` (string, nullable). A child line item returns the parent's id. A top-level or parent line item returns null. Existing tests still pass. |
| **Out of scope** | Any other missing fields from the Apollo line-item payload. |
| **Depends on** | Ticket 1 |
| **Size** | ~50 lines |

---

### Ticket 4 — Backend: MemorizeLineItem + eWallet name

| | |
| --- | --- |
| **Title** | Add memorize endpoint and eWallet name to aggregator |
| **Type** | Story |
| **Repo** | `enterprise-web-aggregator` |
| **Ask** | New memorize endpoint that creates a named template from a saved line item, and additive `name` / `feedCode` fields on the eWallet transaction list so the template can be identified in unused expenses. |
| **Acceptance criteria** | `POST /v1/expense-reports/{headerId}/line-items/{lineItemId}/actions/memorize` with `{ "name": "Recurring lunch" }` returns `{ "transactionId": "..." }`. The aggregator fetches the full Apollo line item and forwards it with the name (not the EWA DTO). Add-info UDAs are stripped before forwarding (matching Mercury). 400 when `enableMemorizedExpenseTransactions` is false, or when the line is a parent, child, per-diem type, or not yet saved. 403 / 404 / 502 use the standard problem document. No 500 for any of the above. `GET /v1/ewallet/transactions` includes `name` (null for non-memorized) and `feedCode` on every row. Memorized rows have `feedCode: "Memorized Expense"` and a non-null `name`. Existing transaction tests still pass. OpenAPI annotations match the contract. |
| **Out of scope** | Guest split behaviour on memorized transactions (Apollo/expense-service layer). Displaying the template in the frontend (that is Ticket 5). Filtering the unused-expenses list by feed type. |
| **Depends on** | Ticket 1, Ticket 2 (to check the config), Ticket 3 (to read parentId for eligibility) |
| **Size** | ~330 lines |

---

### Ticket 5 — Frontend: Memorize button, dialog, and unused expenses display

| | |
| --- | --- |
| **Title** | Add Memorize to line item and unused expenses |
| **Type** | Story |
| **Repo** | `enterprise-web` |
| **Ask** | Add the Memorize button and naming dialog to the line-item screen, wire the save call, and display the user-given name in the unused expenses list. |

**Functional acceptance criteria:**
- Memorize button appears in the line-item action bar when all conditions are met: (a) `enableMemorizedExpenseTransactions` is true, (b) the line item is saved (has an id), (c) `isParent` is false, (d) `parentId` is null, and the expense type's `isPerDiem` is false.
- Tapping Memorize opens a dialog with a name field, Cancel, and Save.
- Save is disabled until the name is non-blank.
- Confirming calls `POST …/actions/memorize`, shows a success notification, and invalidates the eWallet list.
- On error, shows an error notification. The dialog stays open so the user can retry.
- Button is not visible when any eligibility condition fails, and is not visible on unsaved line items.
- A memorized transaction row in the unused expenses list shows the name the user gave it (from `EwalletTransactionResponse.name`) — follow the Figma design for this state once design confirms it (open question 1).
- Rows without a name (`name: null`) render identically to today.
- The frontend types for `EwalletTransaction` include `name: string | null` and `feedCode: string | null`, validated by Zod at the boundary.

**Permissions:**
No new permission key. The Memorize button visibility is gated by `enableMemorizedExpenseTransactions` from `GET /v1/customers/{id}/preferences`. Config bucket — not a per-user permission check. A delegate sees the same config value as any other user at that customer.

**Screen context (AI widget):**
Add `memorize` to the line-item detail screen's available actions in the screen context payload when the line is eligible. Follow the Screen Context Schema V2 and the patterns from [MER-81183](https://emburse.atlassian.net/browse/MER-81183). If MER-81183 has not landed yet, record the action as a placeholder. No new action needed on the unused expenses side — reading the list is already wired.

**Accessibility:**
- Memorize button has an accessible label ("Memorize this expense").
- Dialog has a heading, the input has a visible label, and focus moves to the name field when the dialog opens.
- Cancel and Save buttons have distinct accessible names.
- Success and error notifications are announced to screen readers (`role="status"` or `aria-live`).
- Tab order within the dialog: name field → Cancel → Save.
- If the memorized name is in a visually distinct position in the unused expenses row, it is announced as part of the row, not as a detached element.

| | |
| --- | --- |
| **Out of scope** | Wiring the AI widget to invoke memorize (separate assistant action ticket). Filtering unused expenses to show only memorized transactions. Guest-split behaviour when adding a template to a line — covered by passing through classic's logic on the backend. |
| **Depends on** | Ticket 1 (contract), Ticket 2 (backend preferences), Ticket 4 (backend memorize + eWallet) |
| **Size** | ~380 lines |

---

### Ticket 6 — QA

| | |
| --- | --- |
| **Title** | Playwright coverage for Memorize Line Item |
| **Type** | Story |
| **Repo** | `qa-enterprise` |
| **Ask** | End-to-end tests for the memorize flow and the eligibility conditions. |
| **Acceptance criteria** | A test that taps Memorize on an eligible saved line item, names it, confirms, and then finds the template in unused expenses with that name. A test that verifies the button is absent when the config is off. A test that verifies the button is absent on a parent line item. A test that verifies the button is absent before the line item is saved. |
| **Out of scope** | Per-diem and child-line cases — covered by unit tests on the frontend. |
| **Depends on** | Ticket 5 |
| **Size** | ~150 lines |

---

## Order of work

```
Ticket 1 (Contract)
  ├── Ticket 2 (Backend: CustomerPreferences)  ─┐
  └── Ticket 3 (Backend: parentId on GET)        ├── Ticket 4 (Backend: memorize + eWallet)
                                                 │
                                                 └── Ticket 5 (Frontend: button + dialog + unused expenses)
                                                                                            │
                                                                                            └── Ticket 6 (QA)
```

**Tickets 2 and 3 can start at the same time once Ticket 1 merges.**
**Ticket 4 depends on Ticket 2 (to check config) and Ticket 3 (to read parentId).**
**Ticket 5 depends on Ticket 4 for both the memorize call and the eWallet name fields.**

First ticket that delivers something a user can see: **Ticket 5** (Memorize button + unused expenses display). It requires Tickets 1, 2, 3, and 4 first.

## Risks

1. **Apollo's memorize endpoint takes the full `ExpenseReportLineItem` shape.** The aggregator will need to GET that shape from Apollo and forward it. If the GET and the expected POST body diverge (e.g. after a recent µExpense migration), the forward will fail silently at the transaction creation side. Verify with a real end-to-end test before closing Ticket 4.

2. **Add-info UDA stripping.** Classic strips `addInfo: true` UDAs before memorizing. The aggregator must reproduce this filter. A missing filter means the memorized template carries add-info UDAs that make it harder to reuse.

3. **Per-diem eligibility check via expense types.** The frontend checks `isPerDiem` from the expense types endpoint. If a user's expense type changes between loading the types and clicking Memorize, the frontend check may be stale. The backend check (via the expense type name and its Tessera config) is the authoritative gate.

4. **`GET /v1/customers/{id}/preferences` is a new upstream call.** Customer `GET /v1/customers/{id}/preferences` is not the same as `GET /v1/customers/{id}/expense/preferences` (which is `tbl_CustomerExpenseData`). Getting the upstream path wrong silently reads the wrong table. Confirm the exact customer service path before Ticket 2 ships.

5. **eWallet source type enum gap.** The current `ExpenseTransactionSourceType` enum does not have a Memorized value. If the upstream transaction service returns a type value the mapper does not recognise, `sourceType` will be null. Adding `feedCode` as a separate string field (Ticket 4) avoids depending on a new enum value.

## Open questions

1. **How does a memorized transaction look in unused expenses — reimagine, blocking Ticket 5.** The Figma does not show this state (noted in the Confluence open questions). Classic shows memorized templates inline in the expenses list with no separate tab. Is that the design intent for reimagine, or should there be a distinct row style or label? Needs a Figma update before Ticket 5 acceptance criteria can be finalised.

2. **Should `enableMemorizedExpenseTransactions` come from `GET /v1/session/context` or from a separate call — aggregator and website, not blocking.** Multiple Epics need `CustomerPreferences` fields. If the session/context endpoint already aggregates customer preferences on cold start, adding Memorize's flag there means zero extra round trips. If it does not, Ticket 6 needs a separate `GET /v1/customers/{id}/preferences` call on the line-item screen. Decide before Ticket 6 starts.

3. **What happens on Memorize when the customer pref changes mid-session — aggregator, not blocking.** If a customer admin disables the feature while a user has the line item screen open, the backend check in Ticket 4 will correctly reject the call and return 400. The frontend should handle that 400 with an error notification and hide the button on the next render. No extra design needed, but confirm the error notification wording.

4. **AI widget: can the assistant invoke Memorize — website, not blocking Ticket 6.** The screen context action for `memorize` is registered by Ticket 6 but the assistant's ability to call it is a separate capability. Flag this for the AI team and track under a separate ticket when the capability is designed.

## Done means

- A user with `enableMemorizedExpenseTransactions = true` can tap Memorize on any eligible saved single line item (not a parent, child, or per-diem), type a name, confirm, and find the template in unused expenses with that name.
- The Memorize button is absent when the config is off, when the line is a parent, when the line is a child (parentId non-null), when the expense type is per diem, and when the line item has not yet been saved.
- The backend rejects a memorize call that fails any eligibility condition with 400, not 500.
- Memorized templates in unused expenses show the user-given name.
- Keyboard and screen reader users can use the Memorize dialog without a mouse.
- Classic and Apollo are unchanged.

## What happens next

| Ticket | Next step |
| --- | --- |
| Contract (T1) | Run `/contract mer-83653-memorize-line-item`, open the OpenAPI PR, merge it before starting anything below. |
| Backend: CustomerPreferences (T2) | `/propose` in `enterprise-web-aggregator`, then `/implement` there |
| Backend: parentId on GET (T3) | `/propose` in `enterprise-web-aggregator`, then `/implement` there |
| Backend: memorize + eWallet (T4) | `/propose` in `enterprise-web-aggregator`, then `/implement` there |
| Frontend: button + dialog + unused expenses (T5) | `/propose` in `enterprise-web`, then `/implement` there |
| QA (T6) | `/implement` in `qa-enterprise` using `write-enterprise-web-ui-test` skill |

## Created tickets

| Proposed | Jira key | Title |
| --- | --- | --- |
| T1 — Contract | [MER-83686](https://emburse.atlassian.net/browse/MER-83686) | [TEST] Add Memorize and CustomerPreferences OpenAPI contracts |
| T2 — CustomerPreferences | [MER-83687](https://emburse.atlassian.net/browse/MER-83687) | [TEST] Add GET /v1/customers/{id}/preferences to aggregator |
| T3 — parentId on GET | [MER-83688](https://emburse.atlassian.net/browse/MER-83688) | [TEST] Expose parentId on GET line-item detail response |
| T4 — MemorizeLineItem + eWallet | [MER-83689](https://emburse.atlassian.net/browse/MER-83689) | [TEST] Add memorize endpoint and eWallet name to aggregator |
| T5 — Frontend | [MER-83690](https://emburse.atlassian.net/browse/MER-83690) | [TEST] Add Memorize to line item and unused expenses (reimagine) |
| T6 — QA | [MER-83691](https://emburse.atlassian.net/browse/MER-83691) | [TEST] Playwright coverage for Memorize Line Item |

**Dependency links set:**
- MER-83686 blocks MER-83687, MER-83688
- MER-83687 blocks MER-83689
- MER-83688 blocks MER-83689
- MER-83689 blocks MER-83690
- MER-83690 blocks MER-83691
