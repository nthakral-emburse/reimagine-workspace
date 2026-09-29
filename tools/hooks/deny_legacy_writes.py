#!/usr/bin/env python3
"""Block any write under repos/legacy/. Legacy stays read-only until Phase 2.

Two things get checked:
  1. File-editing tools — the path they are about to write.
  2. Shell commands — whether a mutating command targets a legacy path.

Reads are always allowed. This is a speed bump, not a sandbox: the disabled
git push URLs (`mani run lock-readonly`) are the real backstop.

Runs for Cursor (.cursor/hooks.json) and, with --claude, for Claude Code
(.claude/settings.json). The flag picks the response format; Cursor also sets
CLAUDE_PROJECT_DIR, so the environment cannot tell the two apart.
"""

import json
import os
import re
import sys

ROOT = (os.environ.get("CURSOR_PROJECT_ROOT") or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd())
LEGACY = os.path.realpath(os.path.join(ROOT, "repos", "legacy")) + os.sep
CLAUDE = "--claude" in sys.argv[1:]

PATH_KEYS = ("path", "file_path", "target_file", "notebook_path", "destination")

# Commands that can change a file on disk.
MUTATOR = (
    r"(?:rm|mv|cp|sed|tee|truncate|chmod|chown|ln|touch|dd|patch|install|rsync"
    r"|git\s+(?:add|commit|checkout|apply|am|push|reset|clean|restore|rm|mv|stash))"
)
LEGACY_ARG = r"[^;|&\n]*repos/legacy"

# A mutating command with a legacy path among its arguments.
MUTATES_LEGACY = re.compile(rf"\b{MUTATOR}\b{LEGACY_ARG}")
# Redirecting output into a legacy path.
REDIRECT = re.compile(r">>?\s*([^\s;|&]+)")
# Moving into legacy first, then mutating.
CD_LEGACY = re.compile(rf"\bcd\s+[^\s;|&]*repos/legacy")
ANY_MUTATOR = re.compile(rf"\b{MUTATOR}\b")
# Writing via an interpreter, e.g. python3 -c "open('repos/legacy/x','w')".
INTERPRETER_WRITE = re.compile(r"open\([^)]*repos/legacy[^)]*['\"][wa]")


def respond_allow():
    # Claude Code: say nothing, so its normal permission prompts still apply.
    # Answering "allow" there would skip them.
    if not CLAUDE:
        print(json.dumps({"permission": "allow"}))
    sys.exit(0)


def respond_deny(what, why):
    user_message = f"Blocked: {what} is legacy (read-only until Phase 2)."
    agent_message = (
        "mercury, apollo, and the backend services are read-only. " + why +
        " Record what needs to change in notes/<feature>/findings.md as a "
        "finding with a decision. Do not try another route."
    )
    if CLAUDE:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"{user_message} {agent_message}",
            },
        }))
    else:
        print(json.dumps({
            "permission": "deny",
            "user_message": user_message,
            "agent_message": agent_message,
        }))
    sys.exit(0)


def is_legacy_path(candidate, base=ROOT):
    """True if candidate resolves to repos/legacy or anything inside it."""
    if not candidate:
        return False
    cleaned = candidate.strip().strip("'\"")
    full = os.path.realpath(os.path.join(base, cleaned))
    return (full + os.sep).startswith(LEGACY)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        respond_deny("this tool call", "The guard could not read the tool input.")

    tool_input = payload.get("tool_input") or {}

    # 1. File-editing tools.
    for key in PATH_KEYS:
        candidate = tool_input.get(key)
        if is_legacy_path(candidate):
            respond_deny(candidate, "Direct file write to legacy.")

    # 2. Shell commands. Claude Code's shell keeps its directory between calls
    # and reports it as the top-level "cwd".
    command = tool_input.get("command") or ""
    if command:
        working_dir = tool_input.get("working_directory") or payload.get("cwd") or ""
        shell_dir = os.path.join(ROOT, working_dir)

        for target in REDIRECT.findall(command):
            if is_legacy_path(target, shell_dir):
                respond_deny(target, "Shell output redirected into legacy.")

        if MUTATES_LEGACY.search(command):
            respond_deny("a legacy path in this command", f"Command was: {command[:160]}")

        if INTERPRETER_WRITE.search(command):
            respond_deny("a legacy path in this script", f"Command was: {command[:160]}")

        inside_legacy = is_legacy_path(working_dir) or CD_LEGACY.search(command)
        if inside_legacy and ANY_MUTATOR.search(command):
            respond_deny("the legacy directory", f"Mutating command run inside legacy: {command[:160]}")

    respond_allow()


if __name__ == "__main__":
    # Claude Code lets the tool call through if a hook crashes, so a crash
    # has to deny here. (Cursor gets the same from failClosed.)
    try:
        main()
    except Exception:
        respond_deny("this tool call", "The guard crashed while checking it.")
