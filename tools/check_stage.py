#!/usr/bin/env python3
"""Check a stage folder before it can be approved. Exits 1 on any failure."""

import re, sys, os

FILE_LINE = re.compile(r"[\w./-]+\.\w+:\d+")


def main(folder):
    problems = []

    def read(name):
        p = os.path.join(folder, name)
        return open(p).read() if os.path.exists(p) else None

    # 1. blocking questions must be answered
    q = read("questions.md")
    if q:
        for block in q.split("## ")[1:]:
            if "[BLOCKING]" in block:
                title = block.splitlines()[0].strip()
                after = block.split("ANSWER:")[-1] if "ANSWER:" in block else ""
                answer = after.split("ANSWERED BY:")[0].strip()
                if not answer:
                    problems.append(f"blocking question unanswered: {title}")

    # 2. every finding needs evidence and a consumer check
    f = read("findings.md")
    if f:
        for block in f.split("### ")[1:]:
            title = block.splitlines()[0].strip()
            if not FILE_LINE.search(block):
                problems.append(f"no file:line evidence: {title}")
            if "depends on it" not in block.lower():
                problems.append(f"no consumer check: {title}")

    # 3. every finding needs a decision
    c = read("checklist.md")
    if f and c:
        ids = re.findall(r"^### (\w+)", f, re.M)
        for i in ids:
            if not re.search(rf"\|\s*{re.escape(i)}\s*\|", c):
                problems.append(f"{i} has no decision in checklist.md")

    # 4. commit SHAs recorded
    if not read("commit-shas.md") and not os.path.exists("notes/commit-shas.md"):
        problems.append("no commit SHAs recorded")

    if problems:
        print(f"{len(problems)} problem(s):")
        for p in problems:
            print("  -", p)
        sys.exit(1)

    print("OK")


if __name__ == "__main__":
    main(sys.argv[1])