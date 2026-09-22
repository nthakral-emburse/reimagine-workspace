# Expense — parity with mercury

Scope: phase 0 and 1 cover expense only. Mercury has 126 routes across
10 areas; 96 of those are admin and out of scope. Expense is 8 routes.

Source commits: see /notes/commit-shas.md

## Request path

Browser -> enterprise-web (served by Apollo at /ent-web/*)
        -> /dispatch/*   (prefix stripped by Apollo in prod, rsbuild locally)
        -> Dispatcher    (mints JWT from cr_s_* session cookie)
        -> enterprise-web-aggregator  /v1/ent-web-api/*
        -> Apollo
        -> backend services

Legacy path, still live:
Browser -> mercury -> Apollo -> backend services

Known trap: a JWT minted against a different environment is accepted for
the report shell but returns empty scoped fields such as lineItems.

## The seven expense flows

| # | Flow | Mercury route | New app | Status |
|---|------|---------------|---------|--------|
| 1 | Report list (draft/returned/submitted) | `expenses/:type(/:id)` | `/expenses` | Built |
| 2 | Create new report | `expense/new` | `/expenses/new` | Built |
| 3 | View / edit report | `expense/:type/:id` | `/expenses/expense-report/:id/{expenses,summary,cover}` | Built |
| 4 | Add / edit line item | `expense/:type/:id/.../:lineitemId` | `.../line-item/:txId` and `.../line-item/new/:transactionId` | Built |
| 5 | Attach receipts (mobile deep link) | `expense/:type/:id/attach/receiptIds=…` | none | **GAP** |
| 6 | Expense management search | `expense/management(/:searchOption)(/:searchTerm)` | none | Not started |
| 7 | Personal charges payment | `expenses/personalCharges` | none | Not started |

Mercury's `expense(s)/*actions` catch-all is a redirect, not a feature.

## Differences that are decisions, not gaps

**List type moved from URL to query param.** Mercury has three separate
list routes. The new app has one route and passes `status` to the
aggregator. The backend accepts only one status per call, so the
dashboard fans out into parallel requests.

**Master-detail split into separate routes.** Mercury shows list and
report side by side at `expenses/draft/123`. The new app has separate
list and detail routes.

**Forms are now server-driven.** Mercury has hard-coded views. The new
app fetches form definitions, validation, and field options from the
aggregator (V4 forms). This means parity cannot be judged by comparing
screens — it has to be judged by comparing which rules fire and which
fields appear.

## Highest risk

Flow 5. Mercury's receipt-attach route is a native mobile app deep link
into a webview, with pagination-retry logic behind feature flags. If the
mobile app still points at that URL, mercury's expense area cannot be
switched off until this is resolved. No corresponding work found in the
new app.

`AddExpensesToReport` is not the same thing — it is report-scoped
"choose unreported expenses to add", entered from within a report.

## Open questions

- Does the mobile app still use the mercury attach URL?
- Are flows 6 and 7 in scope for phase 1, or deferred?
- Does `UnreportedExpenses` in the new app correspond to something in
  mercury, or is it new scope?