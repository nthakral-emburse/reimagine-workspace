# Proposal: let a caller change a few fields on a saved expense without resending the rest

## Glossary

| Word | Meaning |
| --- | --- |
| aggregator | The new server the website talks to (`enterprise-web-aggregator`) |
| website | The new React app, including the in-app assistant (`enterprise-web`) |
| old website | Mercury, still in production |
| old server | Apollo, the server mercury talks to |
| expense service | µExpense, the backend service that actually stores expenses. Apollo calls it; the aggregator now calls it directly for one operation. |
| saved expense | One line on an expense report as stored, including custom fields |
| custom field | A customer-configured field stored with the expense (called a UDA upstream) |
| allocation | A cost split row on an expense (called a matter upstream) |
| form check | Testing field values against the customer's form rules without saving |
| lock token | `updateDate`; proves you are editing the version you last read |

## Plain summary

The new server can already save an edited expense, and it already checks the whole form before it writes. The problem is what it demands from the caller: even to change one sentence of business purpose, you must also resend the date, the receipt flag, the expense type, and the complete list of cost splits. Anyone who only holds one field has to fetch the expense first and rebuild all of that, and because the cost splits are rewritten on every save, an unrelated edit disturbs rows nobody touched. We will let the same operation accept only the fields that actually changed, and make the read return the token needed to save safely. Nothing else about how the save behaves changes.

## Ticket

[MER-79895](https://emburse.atlassian.net/browse/MER-79895) — EWA PATCH endpoint for partial field updates - LI.

One-line ask: accept a partial field update for one saved expense, check it against the whole form, write only what was sent, and return field problems rather than a crash.

Related, not this ticket:

- [MER-82431](https://emburse.atlassian.net/browse/MER-82431) — the same for the report header. The body of this ticket still says "line item or header" from before the split; header is out.
- [MER-76910](https://emburse.atlassian.net/browse/MER-76910) (in testing) — built the update endpoint this proposal relaxes. Most of the work this ticket originally described has already shipped here.
- [MER-79892](https://emburse.atlassian.net/browse/MER-79892) — "save calls validate before persisting." Already done inside that same update path. This ticket must not add a second check.
- [MER-79896](https://emburse.atlassian.net/browse/MER-79896) (in testing) — bulk check of saved expenses. Shipped, and it owns a `problems` shape this ticket has to reconcile with.
- [MER-75659](https://emburse.atlassian.net/browse/MER-75659) — wire the website Save button. Still blocked; unblocked by this.
- [MER-79974](https://emburse.atlassian.net/browse/MER-79974) — later wrapper so the assistant can send stored-property names. Sits on top of this.
- [MER-76909](https://emburse.atlassian.net/browse/MER-76909) — finish the read contract (VAT and dropped fields). This ticket takes only the one piece it is blocked by: the lock token on read.
- [MER-81951](https://emburse.atlassian.net/browse/MER-81951) — shared error document. Partly built locally, not yet on main.
- [MER-77729](https://emburse.atlassian.net/browse/MER-77729) — line-item types on the website are hand-written because the API spec is not published.

## Existing designs

No Confluence page or remote design link is attached to [MER-79895](https://emburse.atlassian.net/browse/MER-79895) or to any of its linked tickets. The relevant prior designs are the aggregator's own API rules and two proposals already in this workspace.

**Where this proposal agrees:**

- The aggregator's API rules (`.cursor/rules/confluence-api-standards.mdc`, copied from [API Pattern](https://emburse.atlassian.net/wiki/spaces/EN/pages/3554934923/API+Pattern)): `PATCH` means a partial update, `PUT` means full replacement, and 422 is the status for a body that is understood but cannot be processed.
- Notes for [MER-79896](https://emburse.atlassian.net/browse/MER-79896): one shared idea of a field problem, so the website does not learn several.
- Notes for [MER-81951](https://emburse.atlassian.net/browse/MER-81951): failures are one problem document; do not report failure inside a 200.

**Where this proposal diverges, and from what:**

- **My own earlier draft of this proposal was wrong and is replaced.** It claimed there was no aggregator update for a saved expense and specified merge-on-the-server and validate-before-write as new work. All three already exist. The genuine gap is narrower.
- **The ticket's framing that this is all new.** Four of the five acceptance criteria are already met (evidence in the aggregator section). Only the partial body is missing.
- **David Chen's comment ("we already have a PUT… do we need a separate patch?").** Half right. The existing path already merges, so a second merge engine would be waste. But its required-field gate makes a partial call impossible, so something does have to change. This proposal changes the gate, not the engine.
- **[MER-79896](https://emburse.atlassian.net/browse/MER-79896)'s `problems` shape vs the save's.** Both now exist and disagree. The bulk check returns `problems[]` of per-entity entries (`type`, `id`, `label`, `parentId`, `fields[]`, `compliance[]`); the save returns `problems[]` of flat field problems (`id`, `label`, `message`). Same property name, different element type. This proposal keeps the save's flat list and renames nothing yet — see decision 6 — but the clash must be recorded, not left for the website to discover.
- **The notes for [MER-81951](https://emburse.atlassian.net/browse/MER-81951) assumed field problems would carry a `code` for translation.** The shipped `ValidationFieldProblem` deliberately has no code and its javadoc argues against one, because the server returns an already-localized sentence. This proposal follows the shipped code, not those notes.

## Kind

**Standard-setting.** The old website sends its entire working copy on every save and validates in the browser first. We read it to learn what the storage layer does with omitted data, what the lock token is, and what can fail. We are not copying "send everything you have" — that is precisely the habit this ticket removes.

## Scope

| Surface | Role |
| --- | --- |
| mercury (old website) | Read only. No change. |
| apollo (old server) | Read only. No change. Not on this write path any more. |
| expense service (µExpense) | Read only. No change. Already merges scalars and preserves omitted collections. |
| aggregator | Relax the required-field gate on the existing update, and return the lock token on read. |
| website | Add the client call and a reader for the 422 problems. Wiring Save is [MER-75659](https://emburse.atlassian.net/browse/MER-75659). |

Out:

- Report header partial update ([MER-82431](https://emburse.atlassian.net/browse/MER-82431))
- Assistant stored-property names ([MER-79974](https://emburse.atlassian.net/browse/MER-79974))
- Wiring the website Save button and assistant edit actions ([MER-75659](https://emburse.atlassian.net/browse/MER-75659))
- The rest of the read contract, VAT included ([MER-76909](https://emburse.atlassian.net/browse/MER-76909))
- Switching the website's assistant onto the bulk check ([MER-74934](https://emburse.atlassian.net/browse/MER-74934) phase 2)
- Bulk edit of many expenses at once
- Changing mercury, apollo, or the expense service
- Publishing the API spec for client generation ([MER-77729](https://emburse.atlassian.net/browse/MER-77729))

## Shared decisions

1. **One write path, two gates.** Add `PATCH /v1/expense-reports/{headerId}/line-items/{lineItemId}` that reuses the existing update service, mapper, and client unchanged. `PUT` keeps today's strict gate and full-save meaning. `PATCH` requires only the lock token. No second merge engine, no second validator, no second upstream call.

2. **On `PATCH`, only `updateDate` is required.** `transactionDate`, `havingReceipt`, `expenseTypeName`, and `allocations` stop being mandatory on that path. They remain mandatory on `PUT`.

3. **Omitting a field means "leave it alone"; there is no way to blank one.** The mapper drops nulls before sending upstream, so an omitted scalar keeps its stored value and an omitted collection keeps its stored rows. A caller therefore cannot clear a field through this endpoint. That is a real limitation, stated here rather than discovered later — see open question 1.

4. **Allocations are preserved when omitted.** Today every save resends allocations and the storage layer deletes and reinserts those rows, recalculating amounts. Under `PATCH`, a caller changing business purpose leaves allocation rows untouched. This is the main correctness gain, not just convenience.

5. **The read must return the lock token.** `GET` on one expense does not expose `updateDate` today, so a caller cannot legitimately build any save request; it can only reuse a token from a previous save or scrape one off a 409. Add `updateDate` to the read. This is the one piece of [MER-76909](https://emburse.atlassian.net/browse/MER-76909) this ticket cannot defer.

6. **Field problems keep the shipped save shape.** 422 carries `problems[]` of `{id, label, message}`, already localized. Do not add `code`, `severity`, or `blocking` in this ticket, and do not switch it to the bulk check's per-entity shape. Renaming or unifying the two is its own decision — open question 3.

7. **Policy warnings are not validation failures.** Form-rule failures block the write and return 422. Policy compliance is decided upstream after a successful write and comes back on the 200 body. A person can save an expense that carries a warning.

8. **Unknown fields stay silently ignored.** The service drops JSON properties it does not recognise, matching every other request body in the aggregator. Do not turn on strict rejection for this endpoint alone — see open question 2.

### Contract

`PATCH /v1/expense-reports/{headerId}/line-items/{lineItemId}`

Query parameters are unchanged from `PUT`: optional `inherit`, and `isUpdatedByUser` defaulting to true.

#### Part A — JSON examples

**Request — change one field.** This is the case that is impossible today.

```json
{
  "updateDate": "2026-09-15 14:22:01:000",
  "businessPurpose": "Client dinner after the Chicago workshop"
}
```

**Request — change an amount and answer a policy warning.**

```json
{
  "updateDate": "2026-09-15 14:22:01:000",
  "amountSpent": 47.50,
  "amountSpentConverted": 47.50,
  "complianceItems": [
    { "policyId": "POL-MEALS-CAP", "response": "Approved by Dana Whitfield ahead of the trip" }
  ]
}
```

**Request — replace the cost splits.** Sending the collection at all replaces every stored row, so send the complete set.

```json
{
  "updateDate": "2026-09-15 14:22:01:000",
  "allocations": [
    { "allocationId": 55501, "percent": 60.0 },
    { "allocationId": 55742, "percent": 40.0 }
  ]
}
```

**200 — saved.** Same body `PUT` already returns.

```json
{
  "lineItemId": "li-78421",
  "updateDate": "2026-09-16 10:04:12:331",
  "valid": true,
  "statusValidated": "Validated",
  "hasComplianceItems": false,
  "shouldRefreshReport": false,
  "allowanceCascadingChange": false,
  "complianceItems": [],
  "parentComplianceItems": [],
  "childComplianceItems": []
}
```

**200 — saved, but upstream raised a policy warning.** The write happened. `valid` describes policy, not the form check.

```json
{
  "lineItemId": "li-78421",
  "updateDate": "2026-09-16 10:04:12:331",
  "valid": false,
  "statusValidated": "Violation",
  "hasComplianceItems": true,
  "shouldRefreshReport": true,
  "allowanceCascadingChange": false,
  "complianceItems": [
    {
      "validationStatus": "ERROR",
      "policyId": "POL-MEALS-CAP",
      "shortDescription": "Over the meal limit",
      "description": "Meals over 40.00 USD require a written justification.",
      "response": null,
      "type": 2,
      "lineItemId": "li-78421",
      "receiptType": "IMAGE",
      "messageArgs": ["40.00"]
    }
  ],
  "parentComplianceItems": [],
  "childComplianceItems": []
}
```

**400 — the lock token is missing.** The only required field on this path.

```json
{
  "type": "about:blank",
  "title": "Bad Request",
  "status": 400,
  "detail": "updateDate is required.",
  "instance": "/v1/expense-reports/rpt-88412/line-items/li-78421"
}
```

**422 — the merged expense fails the customer's form rules. Nothing was written.**

```json
{
  "type": "about:blank",
  "title": "Unprocessable Content",
  "status": 422,
  "detail": "Line item li-78421 has validation problems.",
  "instance": "/v1/expense-reports/rpt-88412/line-items/li-78421",
  "problems": [
    { "id": "businessPurpose", "label": "Business Purpose", "message": "This field is required." },
    { "id": "amount", "label": "Amount", "message": "Amount must be greater than zero." }
  ]
}
```

**409 — someone saved first.** The current token comes back so the caller can reload and retry.

```json
{
  "type": "about:blank",
  "title": "Conflict",
  "status": 409,
  "detail": "The request conflicts with the current state of the resource.",
  "instance": "/v1/expense-reports/rpt-88412/line-items/li-78421",
  "updateDate": "2026-09-16 09:58:44:102"
}
```

**403 / 404 / 410 / 502** are unchanged from `PUT`: not the owner is 403; unknown or another customer's report is 404; deleted or already-submitted is 410; expense service unreachable is 502.

#### Part B — Field table

**Request.** Every field below is optional except `updateDate`. The full set is the same record `PUT` accepts; the table groups by behaviour rather than repeating forty rows.

| Field | Type | Nullable | Description |
| --- | --- | --- | --- |
| `updateDate` | string | No | Lock token from the last read or save, format `yyyy-MM-dd HH:mm:ss:SSS`. Only required field. Stale value gives 409. |
| Scalars — `transactionDate`, `description`, `businessPurpose`, `taxLocation`, `currencyCodeCustomer`, `currencyCodeSpent`, `currencyCodeSpentConverted`, `currencyCodeSpentConvertedScale`, `amountSpent`, `amountSpentConverted`, `amountCustomer`, `amountPayMe`, `amountSpentPersonal`, `exchangeRateCustomer`, `exchangeRateEntered`, `exchangeRatePayment`, `havingReceipt`, `isHavingTaxReceipt`, `isFirmPaid`, `isPersonal`, `isParent`, `parentId`, `numberOfDays`, `preApprovalLineItemId`, `isActivityForGuests`, `isDailyAllowanceLinked`, `carPlan`, `expenseTransactionId`, `expenseTypeName`, `locationOnSelect`, `numPeopleForGuests`, `updateRecentMatters` | mixed | Yes | Omit to keep the stored value. Sending a value replaces it. |
| Collections — `allocations`, `guests`, `udas`, `trips`, `crmAllocations`, `perDiem`, `complianceItems`, `notes`, `addInfo`, `lineItemInternalPerson`, `lineItemMatterClient` | array or object | Yes | Omit to keep the stored rows. Sending a non-empty value replaces the entire set, so send the complete list. |
| Computed — VAT percentages, implicit and converted amounts, including `vat.tier3.taxPercentage` and its five siblings | number | Yes | Accepted and then recalculated upstream. Sending them changes nothing. |
| Echoed — `lineItemMatterClient.clientName`, `.clientNumber`, `.clientNumberParent` | string | Yes | Display only; never stored. |

`expenseTransactionId` has one trap worth repeating: if the expense is already linked to a card transaction you must send the id back, because omitting it is rejected upstream with 409 to stop the link being wiped. It behaves like a second lock token.

**200 response**

| Field | Type | Nullable | Description |
| --- | --- | --- | --- |
| `lineItemId` | string | No | The expense that was saved. |
| `updateDate` | string | No | New lock token. Use it on the next save. |
| `valid` | boolean | No | Upstream policy verdict after the write, not the form check. `false` still means saved. |
| `statusValidated` | **extensible enum** | Yes | Upstream policy stamp. Known today: `NewItem`, `Violation`, `Warning`, `Validated`, `NonValidated`, `Info`. Treat anything unknown as "needs attention"; do not use a closed type. |
| `hasComplianceItems` | boolean | No | Whether any policy item came back. |
| `shouldRefreshReport` | boolean | No | Upstream signal that report totals moved and the caller should refetch. |
| `allowanceCascadingChange` | boolean | No | Upstream signal that a daily-allowance chain changed. |
| `complianceItems` | array | No | Policy items on this expense. Empty when clean. |
| `complianceItems[].validationStatus` | **extensible enum** | Yes | Known today: `ERROR`, `WARN`, `INFO`. |
| `complianceItems[].policyId` | string | No | Stable id. This is the key a later reply is matched on. |
| `complianceItems[].shortDescription` | string | Yes | Localized heading. |
| `complianceItems[].description` | string | Yes | Localized sentence. |
| `complianceItems[].response` | string | Yes | The reply already recorded, or null when unanswered. |
| `complianceItems[].type` | integer | Yes | Upstream category code. |
| `complianceItems[].receiptType` | **strict enum** `NONE` \| `IMAGE` \| `DIGITAL_XML` | Yes | Receipt requirement. |
| `complianceItems[].messageArgs` | array of string | Yes | Values already interpolated into `description`; opaque. |
| `parentComplianceItems` | array | No | Same shape, from the parent expense. |
| `childComplianceItems` | array | No | Same shape, from itemized children. |

**422 `problems[]` item**

| Field | Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | string | No | Form field identifier; derived from the custom field name for customer-defined fields. |
| `label` | string | Yes | Localized field label. Null only when the form definition has no label. |
| `message` | string | No | Localized, ready-to-display sentence with any limits already filled in. |

There is deliberately no `code`, `severity`, or `blocking`: the server returns a finished sentence and no consumer branches on the kind of failure.

**Read change.** `GET /v1/expense-reports/{headerId}/line-items/{lineItemId}` gains one field, `updateDate` (string, not nullable), with the same meaning as above. Nothing else on the read changes.

#### Part C — Non-obvious shape decisions

1. **`PATCH` and `PUT` send an identical body upstream.** The difference is entirely the required-field gate, because the mapper already omits nulls. Two verbs are still worth having: `PUT` documents "I am sending the whole expense" and keeps its stronger gate, and the API rules reserve `PATCH` for partial updates. Callers should not have to read the mapper to learn which is safe.

2. **This is not JSON Merge Patch, despite `PATCH`.** In merge patch an explicit `null` clears a field. Here `null` and absent are indistinguishable by the time the body is built, so nothing can be cleared. Anyone who assumes merge-patch semantics from the verb will be wrong, which is why decision 3 states it and open question 1 asks whether to fix it.

3. **Collections are replace-wholesale, not element-wise.** Sending one allocation replaces all of them. This is the storage layer's behaviour, not a choice available to the aggregator, and it is why omitting the collection matters so much.

4. **Passing fields never appear in the 422.** Only failures are listed. The caller already has the form in front of the person.

5. **A failure in one field does not stop others being reported.** The form check runs over the whole merged expense and returns every failing field at once, so the person fixes one round of problems rather than discovering them one at a time.

6. **Policy failure and form failure use different channels on purpose.** Form failure is 422 and nothing is written. Policy failure is a 200 with `valid: false`. The notes for [MER-81951](https://emburse.atlassian.net/browse/MER-81951) argue against reporting failure inside a 200, and by that standard the 200-with-`valid:false` is wrong. It is the shipped behaviour of an endpoint in testing, and changing it is not this ticket — recorded as open question 4.

7. **The 422 `problems[]` is not the same element type as the bulk check's `problems[]`.** The bulk check nests field problems inside a per-entity entry carrying `type`, `id`, `label`, `parentId`, and `compliance`. The save returns the flat field list directly, because a single-expense save already knows the entity. Same name, different shape, on two endpoints the same screen will call. Open question 3.

8. **`updateDate` is the only required field, not an optional concurrency hint.** Making it optional would let a caller silently overwrite someone else's edit. It stays mandatory even though everything else becomes optional.

## Mercury (old website)

### Today

Saving an edited expense is a full replace. The form copies validated values onto the working model and Backbone issues `PUT /apollo/expenseReports/{headerId}/lineItems/{id}?isUpdatedByUser=true` carrying the whole object (`js/data_layer/expense/lineitem/data_lineitem_entity.js`, `js/data_layer/expense/lineitem/api/data_lineitem_api.js`, `js/apps/expense/sections/report/lineitem/form/expense_lineitem_form_save_controller.js`).

Required-field checking happens in the browser before that call (`js/apps/expense/sections/report/lineitem/form/helpers/expense_lineitem_form_validator_helper.js`). Custom fields travel inside the same body. A stale `updateDate` produces a 409 and a dialog offering retry, keep editing, or discard; a 410 shows "item unavailable". There is no partial save.

### Proposal

No change.

### Risks

None. Mercury does not call the aggregator.

## Apollo and the expense service

### Today

Apollo still exposes the full-replace `PUT /{headerID}/lineItems/{expenseLineItemID}` its own website uses (`cr-apollo/src/main/java/com/chromeriver/apollo/controller/ExpenseReportController.java`). When a customer flag is on it forwards the body to the expense service's `PUT /v1/expense-report-line-items/{id}` (`expense-client/src/main/java/com/chromeriver/expense/client/ExpenseClient.java`).

In the expense service, scalars persist through a Hibernate merge, so a property absent from the JSON keeps its stored column. Collections and child rows are deleted and reinserted from the body, so a collection present but short loses the missing rows (`expense-persistence/src/main/java/com/chromeriver/common/expense/service/implementation/ExpenseReportLineItemServiceImpl.java`). That asymmetry is exactly what the aggregator's merge and replace tags describe.

What can fail there: stale `updateDate` gives 409 with the current value; a deleted report or missing expense gives 410; a submitted report gives 409 or 410 depending on path; an owner editing an approved item gives 400; a stale card transaction gives 409. Form rules are not run on this path.

Note that this ticket's write path no longer passes through Apollo at all — the aggregator calls the expense service directly. The bulk edit endpoint still goes through Apollo.

### Proposal

No change to either. The aggregator keeps calling the expense service directly, and keeps sending the complete merged body so the delete-and-reinsert behaviour never sees a short collection.

### Risks

Because collections are rewritten from whatever arrives, any caller that sends a partial list silently deletes rows. The relaxed gate reduces how often that risk is taken, since allocations are no longer forced onto every save, but it does not remove it.

## Aggregator

### Today

Most of what this ticket asks for already exists, shipped under [MER-76910](https://emburse.atlassian.net/browse/MER-76910) and [MER-79896](https://emburse.atlassian.net/browse/MER-79896).

`PUT /v1/expense-reports/{headerId}/line-items/{lineItemId}` exists (`expense/controller/ExpenseReportController.java`, around line 825) and is orchestrated by `expense/LineItemUpdateService.java`. It validates first, checks ownership, then calls the expense service through `expense/client/ExpenseLineItemClient.java` — Apollo is not involved. Request and response are `expense/LineItemUpdateRequest.java` and `expense/LineItemUpdateResponse.java`; the upstream body is built by `expense/LineItemUpdateMapper.java`, which omits nulls via `putIfNonNull` in `expense/ExpenseMappingSupport.java`.

The pre-save check is the important part. `expense/service/ReportValidationService.java` loads the stored expense, extracts its fields through `expense/service/PersistedLineItemFieldExtractor.java`, extracts the submitted fields through `expense/service/RequestLineItemFieldExtractor.java`, merges the two, and validates the merged whole. Omitted fields are filled from stored state, so the form is checked in full context. When the request replaces a collection, the stored copy is stripped first so stale rows are not validated. Failures raise 422 with `problems[]` of `expense/dto/ValidationFieldProblem.java`.

The mapping table is now version 4 (`src/main/resources/form_field_dto_mapping.json`) and distinguishes a read path from a write path per field, with `expense/dto/DtoPath.java` parsing the `matters[].percent` grammar. Resolving form field names for writing already works.

Both check endpoints exist: `POST /{headerId}/actions/validate` and `POST /{headerId}/line-items/{lineItemId}/actions/validate`, both returning 200 with `valid` and per-entity `problems[]` of `expense/dto/ValidationEntry.java`.

What is missing or wrong for this ticket:

- The gate in `validateLineItemUpdateRequest` (`ExpenseReportController.java`, around line 1133) rejects any body without `updateDate`, `transactionDate`, `havingReceipt`, `expenseTypeName`, and a non-empty `allocations`. A one-field call is impossible.
- Because `allocations` is always required, every save replaces allocation rows and recalculates amounts even when they did not change.
- `LineItemDetailResponse.java` has no `updateDate`, so a caller cannot obtain the token the save demands.
- There is no `PATCH` for one expense and no merge-patch support anywhere.
- Unknown JSON properties are dropped silently; there is no rejection of an unwritable field. The sibling bulk DTO test `ignoresUnknownFields` shows this is the house convention.
- `LineItemUpdateService.validationBlocked` builds its 422 with a bare `ProblemDetail`, not through the shared builder. `ErrorType.java` and `ProblemDetails.java` exist only as uncommitted local files, so on main there is no error catalog to route it through.

### Proposal

1. Add `PATCH /v1/expense-reports/{headerId}/line-items/{lineItemId}` on the existing controller, delegating to the unchanged `LineItemUpdateService`. Same request record, same mapper, same client, same validation. What the person notices: an edit to one field no longer requires the caller to know four unrelated ones.

2. Split the gate. Keep `validateLineItemUpdateRequest` for `PUT`. For `PATCH`, require only a non-blank `updateDate`, and keep the structural checks that are about well-formedness rather than completeness — non-null entries in `udas`, a `udaName` on each, a `policyId` on each compliance reply, and the `inherit` name limits. What the person notices: a partial save is accepted; a malformed one is still rejected with the same clear message.

3. Add `updateDate` to `LineItemDetailResponse` and populate it in `LineItemDetailMapper`. What the person notices: the website can save a freshly opened expense instead of having to save once before it can save safely.

4. Document the endpoint in OpenAPI on the controller, stating on the `PATCH` operation that omitted means unchanged, that a collection sent non-empty replaces the whole set, and that no field can be cleared. Reuse the existing 400, 403, 404, 409, 410, 422, and 502 responses.

5. Tests: change one scalar and confirm allocations, custom fields, guests, and trips are untouched upstream; change one scalar and confirm every other scalar is absent from the upstream body; send only `updateDate` and confirm a valid no-op; omit `updateDate` and expect 400; send a value that fails a form rule and expect 422 with nothing written; send a stale token and expect 409; confirm the read now carries `updateDate`; confirm `PUT` still enforces its full gate.

### Risks

- `PATCH` and `PUT` will behave identically on the wire, so a reviewer may reasonably ask why both exist. The answer is the gate and the documented intent; if the team disagrees, alternative 2 is the fallback.
- Relaxing the gate means a caller can now omit `expenseTypeName`, so the form template is resolved from stored state. Confirm the check still picks the right template for an expense whose type was changed in the same call.
- No field can be cleared through this endpoint, and nothing in the response says so. Until open question 1 is answered, the only defence is the OpenAPI note.
- The 422 is not built through the shared error path. Once [MER-81951](https://emburse.atlassian.net/browse/MER-81951) lands, this call must be migrated with the rest rather than left as a one-off.

## Website

### Today

The person can open a saved expense, switch its expense type, and type into fields, and none of it is stored. `handleDoneEdit` in `src/features/expenses/pages/LineItemDetail/components/LineItemDetailFormsPathShell/LineItemDetailFormsPathShell.tsx` is an empty callback whose comment defers persistence to [MER-75659](https://emburse.atlassian.net/browse/MER-75659), and the Save button in `LineItemHeader.tsx` is wired to it. Edits accumulate in a draft through `useLineItemExpenseTypeDraft.ts` and `patchLineItemDtoField.ts` — the latter is an in-memory helper, not an HTTP call.

Other writes do work, and they are the patterns to copy. The Cover tab saves with `PUT /dispatch/v1/ent-web-api/expense-reports/{headerId}` through `updateExpenseReport` in `src/shared/api/v1/generated/expense-reports/expense-reports.ts`, driven by `useExpenseReportCoverSave` and `useUpdateExpenseReport`, which already handles a 409 by reading the fresh token with `readConflictUpdateDate.ts` and retrying once. Creating an expense works through `useCreateLineItem.ts`, which checks the form first, then reads the report to copy an allocation from an existing line, then posts.

Reading one expense is `getLineItemDetails` in `src/shared/api/v1/generated/line-items/line-items.ts`. There is no `PUT` or `PATCH` client for one expense anywhere in `src`.

The assistant still packs field values in the browser and calls the per-form check once per expense in `src/features/ai-chat-ds/utils/fetchReportDetails.ts`; it does not use the new bulk check, and nothing in `src` references `actions/validate`.

For errors, a 422 is flattened to a generic validation toast in `errorHandling.ts`; nothing reads a `problems` list, and the only structured problem-document handling is the Cover 409 token. Line-item types are hand-written stubs because the API spec is not published ([MER-77729](https://emburse.atlassian.net/browse/MER-77729)).

### Proposal

1. Add a `patchLineItem` client next to `getLineItemDetails`, following the shape of `updateExpenseReport`, with request and response types and a schema check at the boundary. What the person notices: nothing yet; this is the piece [MER-75659](https://emburse.atlassian.net/browse/MER-75659) is waiting on.

2. Add a reader for the 422 `problems` list, alongside the existing conflict-token reader, returning field id, label, and message. What the person notices: when Save is wired, problems can appear beside the fields instead of as one vague toast.

3. Add `updateDate` to the read type so the draft carries the lock token from the moment the expense is opened.

4. Leave Save a no-op, leave the assistant on its current check, and leave the create flow alone. Those are [MER-75659](https://emburse.atlassian.net/browse/MER-75659) and [MER-74934](https://emburse.atlassian.net/browse/MER-74934).

### Risks

- If [MER-75659](https://emburse.atlassian.net/browse/MER-75659) sends the whole draft rather than only changed fields, it will replace every collection on every save and reintroduce the row-rewriting this ticket set out to avoid. The client should send a diff, and that expectation belongs in its ticket.
- Hand-written types drift from the server silently. The schema check at the boundary limits the damage until the spec is published.
- The Cover save's single 409 retry reuses the token from the error body. Reusing that pattern here would silently overwrite another person's edit, because unlike Cover the draft may be long-lived. Prefer prompting to reload.

## Alternatives considered

1. **Do nothing; tell callers to use the existing `PUT`.** Rejected. A caller holding one field cannot construct the body, and every save would keep rewriting allocation rows. It also cannot get a lock token from the read.

2. **Relax the existing `PUT` instead of adding `PATCH`.** Tempting, and it avoids two verbs that behave identically. Rejected because `PUT` would then mean "replace, except it actually merges, and omitted means keep", which no caller can infer. If the team prefers one endpoint, this is the fallback and only decision 1 changes.

3. **Build a separate partial-update service with its own merge.** Rejected as duplicated machinery. The merge, the full-form check, and the write already exist and are tested.

4. **True JSON Merge Patch, where explicit `null` clears a field.** Rejected for this ticket, not on merit. The mapper drops nulls before the body is built, so supporting it means distinguishing absent from null throughout the request record — a real change to a path already in testing. Raised as open question 1.

5. **Take a list of form fields (`{"fields":[{"id":"amount","value":47.5}]}`) as my earlier draft proposed.** Rejected. It would need a second write-direction mapper beside the one the request record already provides, and it would not match the create and update bodies the website already builds.

6. **Reject unwritable or unknown fields with a 400.** Rejected for consistency: every other aggregator body ignores unknown properties, and one strict endpoint would surprise people. Worth revisiting globally — open question 2.

7. **Adopt the bulk check's per-entity `problems` shape on the save.** Rejected here. Wrapping a single known expense in an entity envelope adds nesting for no information, and changing the shipped save shape is a breaking change to an endpoint in testing.

## Open questions

1. **Should a caller be able to clear a field? — aggregator, blocking the contract wording.** Today nothing can be blanked through this path. If product needs "remove the business purpose", that is explicit-null support and a change to the mapper. Default: not in this ticket, documented as a limitation.

2. **Should unknown or computed fields be rejected rather than ignored? — aggregator, not blocking.** Default: keep ignoring, matching every other endpoint. A caller that misspells a field gets a silent no-op, which is a real debugging cost; if that is unacceptable it should be fixed across the aggregator, not here.

3. **Do the two `problems` shapes get unified? — aggregator and website, not blocking this ticket but blocking the website's error handling design.** The bulk check returns per-entity entries; the save returns a flat field list. The same screen will call both. Default: leave both, document the difference. Decide before the website builds its reader.

4. **Is a 200 carrying `valid: false` acceptable? — aggregator, not blocking.** The notes for [MER-81951](https://emburse.atlassian.net/browse/MER-81951) say failure should not be reported inside a success. Policy verdicts arguably are not failures, since the write did happen. Default: leave as shipped.

5. **Should the assistant reach this endpoint directly or through the stored-property wrapper? — aggregator, not blocking.** [MER-79974](https://emburse.atlassian.net/browse/MER-79974) assumes a wrapper. If the assistant can speak these field names, that ticket may reduce to nothing.

6. **Does the line-item write staying off Apollo need a decision recorded? — architecture, not blocking.** Single-expense writes now bypass Apollo to the expense service while bulk edit still goes through Apollo, so there are two upstreams for line-item writes. The workspace architecture note treats replacing Apollo as Phase 2. Worth confirming this was intended rather than incidental.

## Definition of done

- **Aggregator:** `PATCH /v1/expense-reports/{headerId}/line-items/{lineItemId}` accepts a body containing only `updateDate` and one changed field, and saves it.
- **Aggregator:** After such a call, allocations, custom fields, guests, trips, notes, and every unsent scalar are unchanged in storage.
- **Aggregator:** Omitting `updateDate` gives 400; a stale one gives 409 carrying the current token; a value that fails the customer's form rules gives 422 with `problems[]` and nothing written; not the owner gives 403; unknown report gives 404; deleted or submitted gives 410; expense service down gives 502. No form problem produces a 500.
- **Aggregator:** The whole merged expense is validated, not only the submitted fields — proven by a test where a stored field fails while the request touches a different one.
- **Aggregator:** `PUT` still rejects a body missing any of its five required fields.
- **Aggregator:** `GET` on one expense returns `updateDate`. The new operation appears in OpenAPI with the omitted-means-unchanged and collections-replace rules stated.
- **Website:** A `patchLineItem` client and a 422 `problems` reader exist and match the contract. Save stays a no-op pending [MER-75659](https://emburse.atlassian.net/browse/MER-75659).
- **Mercury, apollo, expense service:** No change.

## Suggested sequencing

1. **Aggregator, one change:** relax the gate behind `PATCH`, add `updateDate` to the read, document both. Small, because the service underneath is untouched.
2. **Website, one change:** the client and the problems reader. Unblocks [MER-75659](https://emburse.atlassian.net/browse/MER-75659) from guessing the contract.
3. **[MER-75659](https://emburse.atlassian.net/browse/MER-75659)** wires Save, sending only changed fields, and shows problems beside the inputs.
4. **[MER-79974](https://emburse.atlassian.net/browse/MER-79974)** adds the stored-property wrapper for the assistant, if open question 5 still calls for one.
5. **[MER-81951](https://emburse.atlassian.net/browse/MER-81951)** migrates this endpoint's 422 onto the shared error document when the catalog lands.
