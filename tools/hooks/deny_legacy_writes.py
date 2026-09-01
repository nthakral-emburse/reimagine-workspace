#!/usr/bin/env python3
"""Block any write under repos/legacy/. Phase 1 is read-only there."""

import json, sys, os

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        # cannot parse -> fail closed, because failClosed is set
        print(json.dumps({
            "permission": "deny",
            "user_message": "Legacy write guard could not read the tool input.",
        }))
        return

    blob = json.dumps(payload)
    root = os.getcwd()

    for candidate in (
        payload.get("tool_input", {}).get("path"),
        payload.get("tool_input", {}).get("file_path"),
        payload.get("tool_input", {}).get("target_file"),
    ):
        if not candidate:
            continue
        full = os.path.realpath(os.path.join(root, candidate))
        if os.path.realpath(os.path.join(root, "repos/legacy")) in full:
            print(json.dumps({
                "permission": "deny",
                "user_message": f"Blocked: {candidate} is legacy (read-only in phase 1).",
                "agent_message": (
                    "mercury, apollo, and the backend services are read-only. "
                    "Record what needs to change in notes/ instead."
                ),
            }))
            return

    print(json.dumps({"permission": "allow"}))

if __name__ == "__main__":
    main()