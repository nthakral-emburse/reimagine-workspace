---
description: "mercury, apollo, and repos/legacy are read-only in phase 1"
alwaysApply: true
---

`repos/legacy/**` is READ ONLY. This covers mercury, apollo, and all backend
services.

Never edit, create, delete, or move a file there. Never suggest a patch to
legacy code as an action to take.

When legacy behaviour is wrong or needs changing, write it down in
`notes/<feature>/findings.md` as a finding with a decision. Changing legacy is
a later phase and a different conversation.

Writes are also blocked by a hook and by disabled git push URLs. If you find
yourself working around any of those, stop and tell me.