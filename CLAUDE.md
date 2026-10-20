# reimagine-workspace

Coordination workspace for the enterprise-web reimagine project. It holds no
application code. See README.md for setup (mani) and the skill workflow.
Cloned repos live under `repos/` (git-ignored). If it is missing, run `mani sync`.

Project rules are in `.claude/rules/`: architecture and legacy-read-only always
load, and design-principles loads when you work on TypeScript under `repos/new/`.

## Claude Code setup

- Read legacy code through the `legacy-reader` subagent, never in the main conversation.
- Skills: `/epic-create`, `/refine`, `/contract`, `/propose`, `/triage` (bugs). `.claude/skills/` links to `.cursor/skills/`.
- `.cursor/` is the source of truth. Claude Code cannot load `.mdc` files, so these are
  copies that must be kept in sync by hand:
  - `.claude/rules/architecture.md` and `.claude/rules/legacy-read-only.md`: identical to the `.mdc`
  - `.claude/rules/design-principles.md`: same body, `paths:` instead of `globs:`
  - `.claude/agents/legacy-reader.md`: same body, `tools:` instead of `readonly:`
- `.claude/settings.json` denies edits under `repos/legacy/` and runs
  `tools/hooks/deny_legacy_writes.py --claude` before every edit and shell command.
