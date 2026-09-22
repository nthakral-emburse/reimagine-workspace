# Proposal: standardized error handling

## Glossary

Short names used below. Everything else is written in ordinary English.

| Word | Meaning |
| --- | --- |
| aggregator | The new server the website talks to (`enterprise-web-aggregator`) |
| website | The new React app (`enterprise-web`) |
| old website | Mercury, still in production |
| old server | Apollo, the server mercury talks to |
| `code` | A short stable name for the kind of failure, for example `not-found` |
| `detail` | An English sentence on the error that is safe to show a person |
| `chainId` | A tracking id already sent on every request; support uses it to find logs |
| `retryable` | Yes/no: is it safe to try the same request again |

## Plain summary

When something goes wrong today, the old app and the new app each invent their own failure messages, and the new app never reads what the server sent. A person investigating a complaint cannot match what the user saw to a log line. We will define every failure type in one place on the server and always return the same kind of error document, including a tracking id. The website will show a translated sentence for that type when one exists, or the English sentence from the server if it does not. The in-app assistant will use the type of failure and whether it is safe to try again to decide what to do next.

## Ticket

[MER-81951](https://emburse.atlassian.net/browse/MER-81951) — Re-Imagined Experience - Standardized Error Handling Strategy.

One-line ask: one list of error types and one error document so the website, the in-app assistant, and support can all use a failure without seeing internals. Each app owns its own translations.

## Kind

**Standard-setting.** We read the old app to learn what can fail (missing report, two people editing at once, session dead, another service down). We do not copy how the old app presents those failures: it uses several different JSON shapes, sometimes says “success” on the HTTP status while the body says fail, and sometimes includes Java stack traces.

## Scope

| Surface                         | Role                                                                                                                      |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| mercury (old website)           | Read only. No code change.                                                                                                |
| apollo (old server)             | Read only. No code change.                                                                                                |
| aggregator                      | Owns the list of error types. Builds the error document every caller receives. English `detail` is the fallback sentence. |
| website (including in-app chat) | Reads that document. Translates using `code`. Falls back to `detail`. Never shows internals.                              |

Out:

- Building an MCP server (ticket)
- Changing how logs are shipped or searched
- Automatic retry loops or circuit breakers on the aggregator
- Changing mercury or apollo
- Changing when the website logs the user out. Login failures still use the same error document.

There is no separate Ember AI service in this workspace. Assistant behavior in scope is the chat widget already in the website (`src/features/ai-chat-ds/`).

## Shared decisions

These bind the aggregator and the website. Neither side may invent a second meaning.

1. **One error document.** When the aggregator fails a request, the body is always the same kind of JSON: `type`, `title`, `status`, `detail`, `instance`, plus `code`, `retryable`, `chainId`, and `traceId` when tracing produced one.
2. **One file on the aggregator defines every product error type.** That is the only place `not-found` or `conflict` is born. The website does not keep a second list of those types. Failures with no server body (network drop, cancelled request) stay on the website.
3. **Who owns the words the user reads.** The aggregator sends English `detail` (fallback and logs). The website looks up a translation for `code` (for example French for `not-found`). If that string is missing, it shows `detail`. It never shows `type`, internal service names, `traceId`, stack traces, or class names. Looking up a translation is allowed. Turning a Java exception or `Request failed: 404 Not Found` into a message is not. The ticket line “no transformation on the frontend” means: do not decode internals. It does not forbid translation by `code`.
4. **Adding a user-visible error.** Add one entry in the aggregator’s list, then add language strings on the website. “One file” in the ticket means the *type*, not every language string.
5. **`code` and `retryable` are for machines.** The assistant and the website’s “try again” logic read these. We will not add a second English hint field for the assistant.
6. **`chainId` is the support id.** The website already sends it on the request. The aggregator puts it on the error body. Put it in structured logs. Do not put it in the toast the user sees.
7. **Login failures (401/403) use the same document** (`code`, `chainId`, English `detail`). Do not change refresh or logout behavior in this ticket.
8. **Do not copy** the old app’s pattern of HTTP 200 with a fail flag inside the body.

Example both sides implement against:

```json
{
  "type": "urn:emburse:ewa:error:not-found",
  "title": "Not Found",
  "status": 404,
  "detail": "The requested resource was not found.",
  "instance": "/v1/expense-reports/123",
  "code": "not-found",
  "retryable": false,
  "chainId": "…",
  "traceId": "…"
}
```

Website: show the translated string for `not-found` if present, else `detail`. Assistant: read `code` and `retryable`. Support: search logs with `chainId`.

---

## Mercury

### Today

There is no single list of error types. Each screen reads different fields.

- Any 401 on a background request sends the user to logout (`repos/legacy/mercury/js/utils/initializeAjaxHandlers_util.js`).
- Opening a report: on fetch fail, go home and show a dialog (`repos/legacy/mercury/js/routes/ExpenseReportRoute.js`). The fail value is the raw request, so the useful conflict dialog usually never fires; the user gets a generic unknown-error dialog (`repos/legacy/mercury/js/common/dialog/dialog_type_view.js`).
- Many saves treat HTTP 200 with a fail flag and a list of message keys as the real error (`repos/legacy/mercury/js/apps/expense/helpers/expense_submit_helper.js`).
- Other screens read `message`, `errorMessage`, or a misspelled `errroMessageStr`.

### Proposal

1. Do not change mercury. People still on the old website keep talking to the old server.

### Risks

None for this ticket. Do not make the aggregator speak mercury’s old JSON so mercury could switch. Mercury is not a caller of the aggregator.

---

## Apollo

### Today

The old server returns **at least five different JSON shapes**, depending on which path failed:

- A fail flag plus `errorMessage` and optional `chainId` (`repos/legacy/apollo/cr-apollo/src/main/java/com/chromeriver/apollo/controller/GlobalController.java`, `repos/legacy/util/util/src/main/java/com/chromeriver/common/service/ResponseMessageEnvelope.java`).
- `{ "chain-id", "code": "FAILED", "message" }` (`repos/legacy/apollo/cr-apollo/src/main/java/com/chromeriver/apollo/util/ApolloErrorUtil.java`).
- An expense error object with `httpStatusCode` and `errroMessageStr` (`repos/legacy/expense/expense-data/src/main/java/com/chromeriver/common/expense/error/ExpenseErrorObject.java`).
- A small map `{ errorMessage, updateDate }` for “someone else edited this.”
- Invoice/PO errors whose `detail` can be a Java stack (`repos/legacy/apollo/cr-apollo/src/main/java/com/chromeriver/apollo/controller/PoAppExceptionHandler.java`).

Business rules often return HTTP 200 with fail inside the body. A 500 response strips the stack field but can still send the Java exception text. There is no yes/no “safe to retry.”

Do not copy into the new document: stack traces, Java package names, `_class`, or misspelled field names.

### Proposal

1. Do not change apollo.
2. When the aggregator calls apollo and apollo fails, the aggregator turns that into the shared error document. It does not forward apollo’s JSON to the website.

### Risks

Today, if apollo already returns a problem-shaped body, the aggregator copies that whole string into `detail`. The website could then show apollo internals. Step 2 above stops that copy.

---

## enterprise-web-aggregator

### Today

The aggregator already returns a standard error JSON. It does not yet have a list of types, a retry flag, or a tracking id on the body.

Three places build that JSON today:

- The global error handler for website calls (`repos/new/enterprise-web-aggregator/src/main/java/com/emburse/enterprise/ewa/errors/GlobalExceptionHandler.java`). Missing resource gets a generic sentence. Unexpected failures get a generic 500 sentence. That is good: Java text is not echoed.
- A small writer used when login filters fail before the main handler (`.../errors/ProblemDetailWriter.java`, used from `.../security/ProblemDetailAuthenticationEntryPoint.java`).
- The helper that turns another service’s HTTP failure into an error (`.../errors/ExternalServiceErrorHandler.java`). For some 4xx it copies the other service’s raw body into `detail`. For 5xx it uses a generic sentence. For “someone else edited this” it may attach `updateDate`.

On the wire today the type field is always `about:blank`. There is no `code`, `retryable`, `chainId`, or `traceId` on the body. Those ids exist only in logs. The written rules ask for `type` and `instance` (`.cursor/rules/error-handling.mdc`); the running code rarely sets them. There is no list of error types. Adding a new failure means a new exception class plus a handler, or a one-off throw in a controller.

### Proposal

1. **Keep the current error JSON.** Add a `code`, `retryable`, `chainId`, and English `detail` to every failure. Users do not see a new screen; support can search logs from the id on the error; the website can look up a translation.
2. **Put every product error type in one file** on the aggregator. First types: `bad-request`, `not-found`, `conflict`, `gone`, `unauthorized`, `forbidden`, `upstream-unavailable`, `unexpected`. Adding a type later is one new line in that file. Meaning for users: the same “not found” always has the same `code`, wherever it came from.
3. **Build every error body through one shared method** (the global handler, the login-filter writer, and the “other service failed” helper all call it). Meaning for users: no path accidentally sends a Java stack again.
4. **When another service fails:** map 404 → `not-found`, 409 → `conflict` (keep `updateDate` if present), 5xx or timeout → `upstream-unavailable`. Do not copy the other service’s JSON into `detail`. Meaning for users: they see our sentence, not apollo’s.
5. **Login 401/403** get the same fields (`code`, `chainId`, English `detail`). Do not change when we log the user out.
6. **Do not translate on the aggregator.** Do not read the browser language header. English `detail` only. Do not add an assistant hint field.

### Risks

- Extra fields on the JSON are safe for a website that already expects this kind of error object. Keep today’s English sentences for 404 and 502 so wording does not surprise anyone.
- One client (`ExpenseDashboardClient`) still maps failures by itself. Point it at the shared helper in the same change if the diff stays small.
- The errors package and the security package already depend on each other (`docs/TECH_DEBT.md`). The shared method must read the tracking id from the log context without making that cycle worse.
- If some one-off throws are not switched, those paths will miss `code`. Prefer one change that covers all of them.

---

## enterprise-web

### Today

The website has toasts, page error screens, and language files — and **never reads the error body from the aggregator**.

- The shared HTTP helper throws `Request failed: {status} {statusText}` and does not read the body (`repos/new/enterprise-web/src/shared/api/fetchWithAuth.ts`). It sends `x-chain-id`. A 401 against the login service refreshes the token or logs the user out.
- Local error names (`NOT_FOUND`, `SERVER_ERROR`, …) are guessed from the HTTP status (`repos/new/enterprise-web/src/shared/utils/errorHandling.ts`). A “is this retryable?” helper exists and is not used for real requests.
- Failed loads and saves log and show a toast (`repos/new/enterprise-web/src/shared/query/queryClient.ts`). The toast **ignores the error** and shows a language-file string (`repos/new/enterprise-web/src/shared/observability/GlobalErrorToastBridge.tsx`).
- Opening one report turns the failure into a hardcoded English sentence (`repos/new/enterprise-web/src/features/expenses/hooks/useExpenseReportQuery.ts`). The list uses a language-file load-error string. Submit uses a specific language key.
- The in-app assistant shows a language-file chat bubble and sends telemetry (`repos/new/enterprise-web/src/features/ai-chat-ds/hooks/useChatActionsValue.ts`, `.../utils/reportChatbotActionError.ts`). It does not read server `code` or `retryable`.
- How this is supposed to work is written in `repos/new/enterprise-web/docs/architecture/error-handling.md`.

### Proposal

1. **Read the error body in the shared HTTP helper.** If it is our error document, keep `detail`, `code`, `retryable`, `chainId`, and status. If there is no body (network drop), keep today’s behavior. Meaning for users: the app finally knows *what* failed, not only the number 404.
2. **Show the user:** the translated string for `code` if we have one; else English `detail`; else the generic “something went wrong.” Never show `type`, internal names, `traceId`, `chainId`, stacks, or class names. Meaning for users: French UI can say the French “not found”; a missing translation still shows a safe English sentence, never a Java class.
3. **Add language strings** for the aggregator types (`errors.not-found`, and so on) in the existing locale files. Missing string = show `detail`.
4. **Stop rewriting the message** in feature hooks (the expense-report open path that invents its own English). API failures should follow step 2.
5. **Put `chainId` and `code` on the existing error log**, not on the toast. Meaning for support: a user’s report plus the log line can be joined.
6. **Do not retry** when `retryable` is no. Network failures with no body may still retry once, as today.
7. **Do not add a second list of product types** in the website. Local names stay only for failures with no server body.
8. **Chat:** the bubble uses the same rule as step 2. Telemetry includes `code` and `retryable`. No extra hint field.
9. **Update the error-handling doc** so it matches this.
10. **Do not change** 401 refresh or logout.

A language key on a request stays valid for client-only failures (no server `code`). Do not use it to override a server `code`.

### Risks

- Toasts that always say “Something went wrong” will start saying the translated type (or English `detail`). That is what the ticket asks for.
- Some list screens already show an on-page error *and* a toast. Do not change that here.
- Generated API clients go through the shared HTTP helper; parse once there.
- The chat vendor’s error type may only allow extra fields in a side bag. Confirm when building; it does not change the document.
- A full “not found” through UI and chat needs the aggregator list of types to exist first.

---

## Alternatives considered

| Option | Why not |
| --- | --- |
| Aggregator translates using the browser language | Ticket says each consumer owns translations. Chat and the website would still want different sentences. |
| Website always prints English `detail` | Contradicts the ticket line that the website may translate using `code`. |
| Match the old server’s fail-inside-200 JSON | The old website is not a caller of the aggregator. |
| Extra English hint for the assistant | Duplicates `detail`. The assistant uses `code` and `retryable`. |
| Put the list of types only on the website | Ticket requires the aggregator to turn every failure into one document. The website currently throws the body away. |

## Open questions

1. **[RESOLVED] [both]** User-visible copy: website translates by `code`, falls back to English `detail`. Matches the updated ticket.
2. **[NON-BLOCKING] [aggregator]** Whether `type` should be a URN (as in the example) or a real documentation URL if API standards insist.
3. **[NON-BLOCKING] [website]** Whether the chat vendor type can hold `code` / `retryable` directly or only in extra fields.
4. **[RESOLVED] [both]** No extra assistant hint field.

## Definition of done

**Aggregator**

- One file lists all product error types; adding a type is one new entry there.
- Tests for website-call errors and login-filter errors include `type`, `code`, `retryable`, English `detail`, and `chainId` when the request had a chain id.
- Unexpected failure → 500 `unexpected`, generic English `detail`, no Java message, no stack in the body.
- Other service 500 or timeout → 502 `upstream-unavailable`, `retryable` yes.
- Other service 404 → 404 `not-found`, `retryable` no.
- Other service 409 keeps `updateDate` when present; `detail` is our English, not apollo JSON.
- No test body contains Java package names, the word `Exception`, or a stack frame.
- The aggregator does not change the sentence based on browser language.

**Website**

- Opening a missing report with `code: not-found` shows the locale string when present, otherwise English `detail`, never `Request failed: 404 Not Found`.
- A 404 is not retried.
- The error log includes `chainId` when the body had one.
- A chat action failure uses the same display rule; telemetry includes `code` when present.
- A network drop with no body still uses the existing language-file fallback.
- 401 refresh/logout is unchanged.
- Internals never appear in toast, page error, or chat bubble.

**Together**

- A missing report from the aggregator is visible in the UI using translate-or-`detail`, and chat sees the same `code`. Needs both slices.

## Suggested sequencing

1. **Aggregator first.** The list of types and the error document must exist before the website can look up `code`.
2. **Website second.** Read the body, add language strings, fall back to `detail`, log `chainId`, honor `retryable`, chat telemetry.
3. Do not change mercury or apollo.

Every slice named here has a Today section above.
