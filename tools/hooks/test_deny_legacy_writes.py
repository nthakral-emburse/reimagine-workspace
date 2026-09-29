#!/usr/bin/env python3
"""Checks that the legacy write guard blocks writes and allows reads.

Run from the workspace root:  python3 tools/hooks/test_deny_legacy_writes.py

The legacy path is assembled at runtime so this file can be edited and run
without the guard blocking the editor's own command line.
"""

import json
import os
import subprocess
import sys

GUARD = ["python3", "tools/hooks/deny_legacy_writes.py"]

LEG = "repos/" + "legacy"

CASES = [
    # (expected, label, tool_input)
    ("deny", "Write into legacy", {"path": f"{LEG}/mercury/foo.java"}),
    ("deny", "StrReplace into legacy", {"file_path": f"{LEG}/apollo/X.java"}),
    ("deny", "absolute path into legacy",
     {"path": os.path.join(os.getcwd(), LEG, "apollo/X.java")}),
    ("deny", "sed -i on a legacy file", {"command": f"sed -i s/a/b/ {LEG}/mercury/foo.java"}),
    ("deny", "redirect into a legacy file", {"command": f"echo x > {LEG}/mercury/foo.java"}),
    ("deny", "cd into legacy then git checkout",
     {"command": f"cd {LEG}/mercury && git checkout ."}),
    ("deny", "mutate with cwd set to legacy",
     {"command": "rm -rf src", "working_directory": f"{LEG}/mercury"}),
    ("deny", "interpreter write into legacy",
     {"command": f"python3 -c \"open('{LEG}/x','w')\""}),

    ("allow", "grep legacy (read)", {"command": f"rg somepattern {LEG}/mercury"}),
    ("allow", "read a legacy file", {"command": f"cat {LEG}/mercury/foo.java"}),
    ("allow", "read legacy, write to /tmp",
     {"command": f"rg somepattern {LEG} > /tmp/out.txt"}),
    ("allow", "read-only command inside legacy",
     {"command": f"cd {LEG}/mercury && rg somepattern ."}),
    ("allow", "git log inside legacy", {"command": f"cd {LEG}/mercury && git log --oneline"}),
    ("allow", "write to notes", {"path": "notes/mer-1/proposal.md"}),
    ("allow", "edit new code", {"command": "sed -i s/a/b/ repos/new/enterprise-web/src/app.ts"}),
    ("allow", "similarly named sibling dir", {"path": "repos/legacy-notes/foo.md"}),
]

# Claude Code reports the shell's directory as a top-level "cwd", and it
# persists between commands.
LEGACY_CWD = os.path.join(os.getcwd(), LEG, "mercury")
CLAUDE_CASES = [
    # (expected, label, payload)
    ("deny", "mutate with shell cwd in legacy",
     {"cwd": LEGACY_CWD, "tool_input": {"command": "rm -rf src"}}),
    ("deny", "relative redirect with shell cwd in legacy",
     {"cwd": LEGACY_CWD, "tool_input": {"command": "echo x > foo.java"}}),
    ("allow", "read with shell cwd in legacy",
     {"cwd": LEGACY_CWD, "tool_input": {"command": "rg somepattern ."}}),
    ("allow", "relative redirect with shell cwd at root",
     {"cwd": os.getcwd(), "tool_input": {"command": "echo x > notes/out.txt"}}),
]


def decision(mode, stdin):
    """Run the guard and return "allow" or "deny" as the given tool reads it."""
    args = GUARD + (["--claude"] if mode == "claude" else [])
    out = subprocess.run(args, input=stdin, capture_output=True, text=True)
    if mode == "cursor":
        return json.loads(out.stdout)["permission"]
    # Claude Code: no output means no objection.
    if not out.stdout.strip():
        return "allow"
    return json.loads(out.stdout)["hookSpecificOutput"]["permissionDecision"]


runs = [(mode, expected, label, json.dumps({"tool_input": tool_input}))
        for mode in ("cursor", "claude")
        for expected, label, tool_input in CASES]
runs += [("claude", expected, label, json.dumps(payload))
         for expected, label, payload in CLAUDE_CASES]
# Fail closed: unreadable input and input that crashes the guard.
runs += [(mode, "deny", label, stdin)
         for mode in ("cursor", "claude")
         for label, stdin in (("unreadable input", "not json"),
                              ("input that crashes the guard", "[]"))]

failures = 0
for mode, expected, label, stdin in runs:
    got = decision(mode, stdin)
    mark = "ok  " if got == expected else "FAIL"
    if got != expected:
        failures += 1
    print(f"{mark} {mode:6} expected {expected:5} got {got:5}  {label}")

print()
print(f"{len(runs) - failures}/{len(runs)} passed")
sys.exit(1 if failures else 0)
