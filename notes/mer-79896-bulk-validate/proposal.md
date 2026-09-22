# Proposal: check every saved expense on a report in one call

## Glossary

| Word | Meaning |
| --- | --- |
| aggregator | The new server the website talks to |
| website | The new React app, including the in-app assistant |
| old website | Mercury, still in production |
| old server | Apollo, the server mercury talks to |
| form check | The existing aggregator call that tests one form’s field values |
| saved expense | A line on an expense report as stored on the server, including custom fields |
| custom field | A customer-configured field stored with the expense (called a UDA in the old server) |
| mosaic tile | The customer’s expense-type card; it names which form template that type uses |

## Plain summary

When a person opens a report, the new website asks the server to check each expense one at a time, and it can only send the few field values it already has on the page. Fields the website cannot fill in are treated as “we could not check this,” so the assistant sometimes hedges instead of saying what is actually missing. The old website never ran this kind of check; it only kept a pass or fail flag after save. We will add one server call that loads every saved expense on the report, runs the field checks the new server already knows how to run, and returns what is missing or invalid on each expense, including custom fields. The website then uses that list for the assistant’s prompt, so the person hears an accurate message without a long wait.

## Ticket

[MER-79896](https://emburse.atlassian.net/browse/MER-79896) — Reimagined Experience - BE Bulk validate + get missing fields for proactive messages (GET).

One-line ask: one call that checks every saved expense on a report (or a named subset) and returns, per expense, which fields are missing or invalid, for the in-app assistant.

Related, not this ticket:

- [MER-79887](https://emburse.atlassian.net/browse/MER-79887) (in testing) — form check must not change submitted values while it runs. This ticket should wait until that behavior is the one in production.
- [MER-80755](https://emburse.atlassian.net/browse/MER-80755) — same ask; treat as a duplicate, not a second build.
- [MER-81898](https://emburse.atlassian.net/browse/MER-81898) — later: also check that people, places, and allocations actually exist. Out of scope here.
- [MER-74934](https://emburse.atlassian.net/browse/MER-74934) — the website already documents this call as the way to drop its client-side field packing.

## Existing designs

[Validation API Contract — Stateful Report and Line-Item Validation (MER-79896)](https://emburse.atlassian.net/wiki/spaces/~712020b89f1f478bd74e6ba75b2dca9930290c/pages/5109841924) — authored by Neil Yang, version 0.3 (2026-09-03). This is the primary design reference for the API contract. Version 0.3 incorporates a review with Neha Thakral and is marked FOR REVIEW.

**Where this proposal agrees with v0.3:** nested `fields[]` under each entry, unprefixed field names (`type`, `id`, `label`, `parentId`), `blocking` and `category` on each field problem, `code` for machine-readable errors, `groupId` for multi-entity violations, `path` reserved as null, plain Problem Detail on 422 (no validation array embedded in error responses).

**Where this proposal diverges from v0.3:**
- **Array name:** v0.3 uses `validationErrors`. This proposal uses `problems` — clearer for readers who do not write code. Update the Confluence page to match before implementation.
- **`path` deferred but included:** v0.3 has `path` as an open decision (Section 11 item 4). This proposal includes it as always `null` for this ticket — present in the shape but never populated until MER-81898 ships.
- **`reportId` at top level:** v0.3 does not include it. This proposal drops it (client already knows it from the request URL).

**Open decisions from v0.3 not yet resolved:** what a `component` type is (Section 5.1); the compliance approach in Section 6; inner array name `fields[]` vs `problems[]` (resolved here as `fields[]`); path syntax string vs structured (Section 7.2).

## Kind

**Standard-setting.** The old website does not check forms this way, and we will not copy it. We read it only to see what a “valid expense” meant there (a flag after save, not a list of missing fields). The target is: the aggregator is the source of truth for missing and invalid fields on saved expenses; the website stops guessing.

## Scope

| Surface | Role |
| --- | --- |
| mercury (old website) | Read only. No code change. |
| apollo (old server) | Read only. No code change. Used only to load saved expenses. |
| aggregator | New report-level check. Loads saved expenses, runs the existing form checker, returns one result per expense. |
| website (including the in-app assistant) | One call instead of N form checks. Drop the client field map and the “could not verify” hedge. Still owns the wording of the chat bubble. |

Out:

- Changing mercury or apollo
- Changing the existing one-form check used while a person is editing a form (`POST /v1/forms/{formType}/{formName}/validate`)
- Checking that people, places, and allocations exist in the database ([MER-81898](https://emburse.atlassian.net/browse/MER-81898))
- Replacing apollo (Phase 2)
- A second “get missing fields” call that only repeats this result

## Shared decisions

1. **One call, not two.** The ticket allows a bulk check plus a separate “get missing fields” call. Use one: the bulk check already returns missing and invalid fields. A second call would only copy the first.

2. **POST, not GET.** The ticket title says GET; the ticket body and the aggregator’s URL rules say POST for a named action. The body can list optional expense ids. The result is not a cacheable document. Path: `POST /v1/expense-reports/{reportId}/actions/validate`.

3. **The website sends ids only.** No field values in the request. Omit `lineItemIds` to check every expense on the report. Send a list to check a subset (for example the expense just saved).

4. **The aggregator loads saved state.** It reads the report from the old server once (that payload already includes custom fields on each expense). It must not fan out one old-server get per expense. The list shape the website sees today drops custom fields; this new path must use the full saved expense, not that trimmed list.

5. **Reuse the existing form checker.** For each expense: resolve the form template from the mosaic tile’s `formName` (fallback `Default`, same as the website today), build field values from the saved expense plus custom fields (join custom-field name to the form field’s `udaName` metadata), then call the same checker the one-form endpoint already uses, with the report id so header context (for example settlement currency) is present. Do not invent a second checker.

6. **HTTP 200 with per-expense results.** A report that exists and can be read returns 200 even when some expenses fail checks. Unknown report: 404. Identity mismatch: 403. Malformed body or an id that is not on the report: 400. Upstream down: the same problem document other aggregator failures use. Do not hide a failed expense as “could not verify.”

7. **Each failing field says missing or invalid, with a code.** `missing` means required and empty. `invalid` means a value is present but fails a rule. Each field problem carries a `code` (machine-readable, the translation key) and a `message` (singular English string, the fallback). Labels come from the form definition so the website does not keep a label map. One problem = one entry in `fields[]`. A field with two independent failures produces two entries with the same `id` — not one entry with two messages. The current engine stops at the first failure per field, so this does not occur today, but the shape supports it.

8. **Child expenses are included.** A parent (for example a hotel) and its children are each one entry. The old server does not nest further.

9. **The website still writes the chat sentence.** “Consume without additional processing” means: do not pack aliases, do not invent an unverifiable bucket, do not guess severity. Grouping “Currency is missing on 3 of 10 expenses” remains website copy. The assistant’s hidden context may include the per-expense list as returned.

10. **Do not add a second nested URL in this ticket.** Optional `lineItemIds` on the report action covers “just this expense.” A `…/line-items/{id}/actions/validate` path can wait until a second caller needs it.

11. **Always run line item validation even if the report header fails.** When header validation ships (MER-82046), a header failure does not short-circuit line item checks. The person needs the complete picture in one call — fixing the header and then discovering line item failures is a bad experience. Both `"type": "report"` and `"type": "lineItem"` entries appear in `problems[]` together. The top-level `valid: false` captures the aggregate. Example when both fail:

```json
{
  "valid": false,
  "problems": [
    {
      "type": "report",
      "id": "rpt-123",
      "label": "Q3 Travel",
      "parentId": null,
      "fields": [
        {
          "id": "reportName",
          "label": "Report Name",
          "severity": "missing",
          "blocking": true,
          "category": "fieldValidation",
          "code": "FIELD_REQUIRED",
          "message": "This field is required.",
          "path": null,
          "groupId": null
        }
      ]
    },
    {
      "type": "lineItem",
      "id": "li-1",
      "label": "Alaska Airlines",
      "parentId": null,
      "fields": [
        {
          "id": "currency",
          "label": "Currency",
          "severity": "missing",
          "blocking": true,
          "category": "fieldValidation",
          "code": "FIELD_REQUIRED",
          "message": "This field is required.",
          "path": null,
          "groupId": null
        }
      ]
    }
  ]
}
```

---

## Mercury (old website)

### Today

There is no form-check HTTP call. Before save, the browser runs Parsley on the visible form (`js/apps/expense/sections/report/lineitem/form/helpers/expense_lineitem_form_validator_helper.js`). Server policy is a side effect of save to `/apollo/expenseReports/{id}/lineItems/{id}` (`js/data_layer/expense/lineitem/data_lineitem_entity.js`). Success copies `validated` / `statusValidated`. The report’s “all acceptable” flag is a client fold of those flags (`js/data_layer/expense/expense_report/helpers/data_expense_report_model_bindings_helper.js`). Bulk HTTP is save, not check (`POST …/lineItemGroup`).

The in-app assistant in mercury only forwards `validationStatus: li.statusValidated` per expense. It does not compute missing fields (`js/common/emburseChat/screenContext.js`). Form template comes from the mosaic tile’s `formName` (`js/products/expense/expenseMosaicsAPI.js`).

### Proposal

No change.

### Risks

None. The new website’s assistant already lives on a different path (`/ent-web/ai-api`).

---

## Apollo (old server)

### Today

There is no Tessera/form-check HTTP API. Persist is `POST`/`PUT /expenseReports/{headerID}/lineItems` (`cr-apollo/.../controller/ExpenseReportController.java`). `POST …/lineItemGroup` is bulk save then compliance, not a form check. Report `GET /expenseReports/{headerID}` returns lines and localizes custom fields on each line. Single-line `GET` loads custom fields from µExpense or from the old UDA service depending on a flag (`ExpenseLineItemProviderFactory.java`). Expense type mapping from Tessera is name and display name only — not a form template (`ExpenseTypeController.java`, `ExpenseReportItemTypeApollo.java`). Required-field form rules are not executed in apollo.

### Proposal

No change. The aggregator continues to load saved expenses through the existing apollo report get.

### Risks

If a customer’s get-line path omits custom fields (flag off, old loader), the new check would miss those fields the same way today’s website does. The report get is the better source because it already localizes custom fields on each line. Confirm in implementation that the report get used here is the full header (not `headerOnly`, which mercury already treats as skipping server validation).

---

## Aggregator

### Today

One-form check already exists: `POST /v1/forms/{formType}/{formName}/validate` (`FormV1Controller.java`). The caller must send field values. The checker (`ServerSideValidator.java`) re-runs show/hide/required rules, skips fields a rule has hidden, flags required-and-empty with “This field is required.”, and returns `{ valid, fields }` where `fields` is only the failures (`ValidationResponse.java`, `ValidationStatus.java` — `valid` plus `messages`, no missing-vs-invalid flag). Header context is optional (`expenseHeaderId` on the one-form call).

Saved expense detail, including custom fields, is `GET /v1/expense-reports/{headerId}/line-items/{lineItemId}` → `LineItemDetailResponse` with `uda: List<UdaDto>` (`LineItemDetailResponse.java`, `UdaDto.java`). The report get’s list shape is trimmed and has no custom fields (`LineItemResponse.java`), even though apollo’s report get includes them. Form template per type is `GET /v1/expense-types` → mosaic `formName` (`ExpenseTypeController.java`, `ExpenseTypeResponse.java`). Custom fields on the form carry `udaName` / `udaDataType` metadata (`FieldTransformer.java`). There is no `…/actions/validate` on expense reports (`ExpenseReportController.java` has get, create, submit, get-one-line).

Controllers in this feature still call the apollo client directly. New work should go through a service (`spring-layering.mdc`).

### Proposal

1. Add `POST /v1/expense-reports/{reportId}/actions/validate`. Optional body `{ "lineItemIds": ["…"] }`. Empty or omitted list means every expense on the report, including children.

2. Put orchestration in a service, not the controller. One apollo report get (full header, not header-only). Filter to requested ids. If any requested id is absent, 400. Map each saved expense to a form-check request: standard fields from the saved expense (merchant, amount, date, currency, type, business purpose, allocations) plus custom fields joined by `udaName`. Resolve `formName` from the expense-type map; if the tile has none, use `Default`.

3. Run the existing checker with the report id as header context so currency and other header rules match an edit, not a create. Do not change the one-form endpoint’s JSON in this ticket. On the bulk result only, add `severity` (`missing` vs `invalid`) and `label` per failing field. Derive `missing` from the required-empty path (the existing “This field is required.” message); everything else is `invalid`.

4. Response shape — one `problems` array, one entry per entity, each tagged with `type`:

```json
// Case 1 — some expenses have problems (only failing entries appear)
{
  "valid": false,
  "problems": [
    {
      "type": "lineItem",
      "id": "li-1",
      "label": "Alaska Airlines",
      "parentId": null,
      "fields": [
        {
          "id": "currency",
          "label": "Currency",
          "severity": "missing",
          "blocking": true,
          "category": "fieldValidation",
          "code": "FIELD_REQUIRED",
          "message": "This field is required.",
          "path": null,
          "groupId": null
        },
        {
          "id": "taxLocation",
          "label": "Tax Location",
          "severity": "missing",
          "blocking": true,
          "category": "fieldValidation",
          "code": "FIELD_REQUIRED",
          "message": "This field is required.",
          "path": null,
          "groupId": null
        }
      ]
    },
    {
      "type": "lineItem",
      "id": "li-9a",
      "label": "Room Rate — Oct 12",
      "parentId": "li-9",
      "fields": [
        {
          "id": "amountSpent",
          "label": "Amount",
          "severity": "invalid",
          "blocking": true,
          "category": "fieldValidation",
          "code": "FIELD_INVALID",
          "message": "Value must be positive.",
          "path": null,
          "groupId": null
        }
      ]
    }
  ]
}

// Case 2 — all expenses pass
{ "valid": true, "problems": [] }
```

   **Entry object** (one per expense that has problems):

   | Field | Type | Nullable | Notes |
   | --- | --- | --- | --- |
   | `type` | strict enum | No | `lineItem` (this ticket), `report` (MER-82046). `component` discussed but undefined — do not implement until defined. |
   | `id` | string | No | Line item ID. |
   | `label` | string | No | Display name — merchant name, falling back to expense type label. |
   | `parentId` | string | Yes | ID of the parent line item for itemized children (e.g. hotel room nights). `null` for top-level expenses. Always present so callers can group without checking for key existence. |

   `problems[]` today contains only `"type": "lineItem"` entries. When report-level field validation ships (MER-82046), a `"type": "report"` entry appears in the same array — no contract change needed.

   **Field object** (one per distinct problem on that expense):

   | Field | Type | Nullable | Notes |
   | --- | --- | --- | --- |
   | `id` | string | No | Form field ID. |
   | `label` | string | No | Display name from the form definition — website does not keep a label map. |
   | `severity` | strict enum | No | `missing` = required and empty. `invalid` = value present but fails a rule. |
   | `blocking` | boolean | No | Always `true` for field validation. `false` only for compliance warnings (future). A caller checking "can I submit?" reads only this field. |
   | `category` | strict enum | No | Always `fieldValidation` for this ticket. `compliance` is reserved for future compliance emission — no behavior change needed when it arrives. |
   | `code` | extensible enum | No | Machine-readable key, used as the translation key. `message` is the English fallback. New codes are not breaking changes — consumer must treat unknown codes the same as `FIELD_INVALID` and fall back to `message`. Known codes: `FIELD_REQUIRED` (missing), `FIELD_INVALID` (catch-all). Full catalog owned by MER-81951. Do not use a closed TypeScript union or Java enum on the consumer side. |
   | `message` | string | No | English sentence from the checker. One problem, one message. If a field later has two independent failures they appear as two entries in `fields[]` with the same `id`. The current engine stops at the first failure per field so this will not occur today. |
   | `path` | string | Yes | Always `null` for this ticket. Reserved for sub-structure failures (e.g. `"allocations[2].percentage"` — row 3 of the allocations list). Used by MER-81898 (entity/allocation validation). Adding it now means adding it later is not a breaking change. |
   | `groupId` | string | Yes | Always `null` for this ticket. Reserved for correlating problems across multiple entities (e.g. duplicate detection, where two line items share one violation). |

   Only expenses with at least one failing field appear in `problems[]`. Passing expenses are omitted — the website already has the full expense list from its report GET.

5. Bound work for the 50-expense / 2 second target: one old-server load, then in-process checks with the form-definition cache already used by the one-form call. Do not N+1 get-one-line. If a form template is missing after `Default` fallback, that expense is `valid: false` with one message, not a 404 for the whole report.

6. Tests: empty report; all valid; mixed missing and invalid; custom field present vs empty; subset of ids; unknown id; child expenses; hidden-required field not flagged (same as MER-79887); identity 403; missing report 404.

### Risks

- Mapping saved custom fields onto form field ids is the new logic. A missed join looks like “all valid” to the person. Cover it with tests using a real `udaName` on both the saved expense and the form definition.
- Report get vs get-one-line may differ when the µExpense flag is off. Prefer the report get and document any field the mapper still drops.
- Fifty sequential checker runs on large forms could still miss 2 seconds if form definitions are cold. Cache hits are the expected path; measure with a 50-line fixture before calling the AC done.
- `ExpenseReportController` already injects the apollo client. Do not add this action there as another client call. New service keeps the layering rule for this work even if older methods stay as they are.

---

## Website

### Today

Opening a report (dashboard focus or report page) runs `fetchReportDetails` (`src/features/ai-chat-ds/utils/fetchReportDetails.ts`). It loads the report, then **N** line-item details, then **N** form checks via `apiClient.validateForm` (`src/shared/services/ApiClient.ts`). It packs values using `INLINE_FIELD_ALIASES` and `LINE_ITEM_DETAIL_FIELD_MAP` (business purpose only). Failures on submitted ids become “missing”; failures on ids it never sent become “unverifiable.” That hedge is shown in the activity-aware report message (`buildReportMessage.ts`) so the assistant does not say the report is complete. The shorter proactive bubble (`buildMissingFieldsMessage.ts` / `tryPostMissingFields.ts`) uses only the confirmed-missing list. Tech debt already names this as Phase 2 of [MER-74934](https://emburse.atlassian.net/browse/MER-74934) (`docs/maintenance/tech-debt.md`). Form template resolution already uses `GET /v1/expense-types` (`src/shared/api/v1/expenseTypes.ts`, fallback `Default`). The one-form check from this path does **not** pass the report id, so header context is missing for the assistant’s check today.

The line-item edit screen still uses the one-form check with live typed values. That stays.

### Proposal

1. Replace the N detail fetches and N form checks in `fetchReportDetails` with one `POST /v1/expense-reports/{reportId}/actions/validate`. Keep the report get for names, amounts, and mosaic labels used in other chat copy.

2. Build `missingFieldsByExpense` from fields with `severity: missing` (use `label`). Treat `invalid` as failing fields the bubble can mention the same way, or as a separate sentence if product wants “wrong” vs “blank.” Default: both severities count as “needs attention” in the bubble; hidden context keeps severity so the agent can tell them apart.

3. Delete `INLINE_FIELD_ALIASES`, `LINE_ITEM_DETAIL_FIELD_MAP`, the unverifiable bucket, and `buildUnverifiableText`. If every expense is valid, the existing “fields complete” copy is honest.

4. Do not use the new call while the person is mid-edit on a form. Live typing still uses the one-form check with the values on screen (those are not saved yet). After save, invalidate the report-context cache the same way other writes already do, so the next assistant prompt uses saved state.

5. On 4xx/5xx from the new call, do not invent missing fields. Skip the proactive bubble (same as today’s “validate threw → skip that expense,” but for the whole report). Log the tracking id; do not show stacks.

### Risks

- Chat copy that assumed only “missing” will start seeing “invalid” if saved data can fail a rule. That is intended; confirm wording with product if “invalid” should be a different sentence.
- Session cache of report context still only clears on known write paths (`docs/maintenance/tech-debt.md`). This ticket does not fix stale copy after an edit in another tab.

---

## Alternatives considered

1. **Two endpoints (bulk check + get missing fields).** Rejected. The missing-field list is the bulk result. Two calls add latency the ticket is trying to remove.

2. **GET with query-string ids.** Rejected. Long id lists, no body, and the aggregator already uses POST for named actions (`/submit` today; `/actions/{verb}` in the URL rules).

3. **N aggregator form checks, but run them on the server.** Rejected if those checks still require the website to send values. The point is the server reads saved state, including custom fields the website cannot pack.

4. **Fan-out get-one-line on the aggregator.** Rejected for the 2 second / 50 expense target. One report get already has custom fields on each line.

5. **Nested per-expense URL in the same ticket.** Rejected as extra surface. Optional ids on the report action are enough.

6. **Copy mercury’s `statusValidated` into the assistant.** Rejected. That flag is compliance-after-save, not a field list, and mercury’s assistant already only forwards it.

---

## Open questions

1. **Child expenses in the list — aggregator, blocking.** This proposal includes children as their own rows. If product wants only parents (to match the chat’s current expense count), say so before the contract ships.

2. **Invalid vs missing in the visible bubble — website, not blocking.** Default: both count as “needs attention.” If product wants two sentences, that is copy only.

3. **Nested per-expense URL — aggregator, not blocking.** Ticket also says “add a line item endpoint.” This proposal defers it. If a caller already needs `…/line-items/{id}/actions/validate` in the same sprint, it should be a thin wrapper on the same service.

4. **Wait for MER-79887 — aggregator, blocking.** If the one-form checker still mutates values or still flags hidden required fields, bulk check will copy that bug onto every expense. Do not ship this until 79887 is the checker in the environment you test against.

---

## Definition of done

- **Aggregator:** `POST /v1/expense-reports/{reportId}/actions/validate` with no body checks every saved expense on that report, including custom fields, and returns per-expense missing/invalid fields with labels. Optional `lineItemIds` checks only those ids. Unknown id → 400. Missing report → 404. Fifty expenses complete in under 2 seconds on a warm form cache in the test environment used for the AC.
- **Aggregator:** One old-server report get per call, not one get per expense. New logic lives in a service, not a controller calling the apollo client.
- **Website:** Opening a report for the assistant makes one validate call, not N. `INLINE_FIELD_ALIASES`, `LINE_ITEM_DETAIL_FIELD_MAP`, and the unverifiable hedge are gone from the detection path. The line-item edit screen still uses the one-form check with on-screen values.
- **Website:** A report whose saved expenses are complete no longer shows “please double-check” for custom fields the website used to skip.
- **Mercury / apollo:** No change.

---

## Suggested sequencing

1. **Aggregator** first. The website cannot drop its packing until the server reads saved state. Blocked on MER-79887 being the checker you hit in the test environment.
2. **Website** second. Point `fetchReportDetails` at the new call, delete the packing and unverifiable path, keep the one-form check on the edit screen.
3. **Mercury and apollo** stay as they are.
