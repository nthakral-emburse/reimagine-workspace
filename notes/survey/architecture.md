# Architecture — expense migration

## Request path

Browser
  -> enterprise-web SPA        (served by Apollo at /ent-web/*)
  -> /dispatch/*               (prefix stripped by Apollo in prod, rsbuild locally)
  -> Dispatcher                (mints JWT from cr_s_* session cookie)
  -> enterprise-web-aggregator (EWA)  /v1/ent-web-api/*
  -> Apollo
  -> 60+ backend services

Legacy path, still live:
Browser -> mercury -> Apollo -> 60+ backend services

## What the aggregator is for

EWA exists so enterprise-web owns its own contract instead of consuming
Apollo's. Apollo shapes should not leak past EWA. EWA is transitional —
it goes away or is repurposed when Apollo is replaced.

## Auth

Session cookie (cr_s_*) -> dispatcher -> JWT -> every EWA call.
KNOWN TRAP: a JWT minted in a different environment is accepted for the
report shell but returns empty scoped fields (e.g. lineItems).

## Aggregator endpoints in production today

Expense reports: list (one status per call), create, get, submit,
  line-items list, line-item detail, receipt images
eWallet:         transactions (filter/sort), count, filters,
                 receipts (paged, bulk delete)
Forms V4:        definition, validate, field options, expense-types
Platform:        users/me, authorization/permissions, config,
                 navigation/counts, activity-log, mosaics