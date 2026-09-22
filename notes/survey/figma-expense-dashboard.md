# Figma — expense dashboard (Home + unreported)

Source of truth stays in Figma. This file is a workspace snapshot so
agents and people can work without re-pulling MCP every time.

File: [T-E - Front-End Epic](https://www.figma.com/design/O2eRGOwGZkI1cJprkyShOl/T-E---Front-End-Epic?node-id=3029-581)
Section: Expense creation → Add expense - Dashboard
Pulled: 2026-08-28

| Frame | Node | Link |
|-------|------|------|
| Canvas (whole epic section) | `3029:581` | [open](https://www.figma.com/design/O2eRGOwGZkI1cJprkyShOl/T-E---Front-End-Epic?node-id=3029-581) |
| Home page | `6162:35431` | [open](https://www.figma.com/design/O2eRGOwGZkI1cJprkyShOl/T-E---Front-End-Epic?node-id=6162-35431) |
| Unreported expenses | `4909:28114` | [open](https://www.figma.com/design/O2eRGOwGZkI1cJprkyShOl/T-E---Front-End-Epic?node-id=4909-28114) |

Related: notes/survey/expense-parity.md (flow 1 and the UnreportedExpenses question).

## Home page — elements

**Top nav:** hamburger, Emburse Enterprise logo, account chip (Michael
Rubini / michaelrubini@emburse.com + chevron), app-launcher grid.

**Left nav (expanded):** Home (selected); Expenses expanded with Drafts /
Returned / Submitted (badge `1` each); Pre-Approvals, Approvals,
Invoices, Purchase orders (collapsed); Settings; Help center; New
Experience toggle (on).

**Main:** greeting "Hi, Michael"; date "Tuesday, May 12"; MOTD about
Expense Intelligence; Company information (external link); Unreported
Expenses card (count `1` + chevron); Add expense; Expense reports +
View all.

**Report cards:**
- Austin trip — New, Draft, In policy
- August expenses — Draft, Needs attention
- MSY New Orleans May 2026 — Submitted, Pending

**Emburse AI:** sparkle header; "Folder name" / "9 expenses" + history +
chevron; empty chat body; "Type or use voice for assistance..." + mic.

## Unreported expenses — elements

Collapsed icon rail (Home selected; inbox has a notification dot). Back
+ title. Upload. Tabs: Expenses / Attachments / Recycle bin. Toolbar:
"2 expenses" + Date sort. Four rows — Amazon, Starbucks, Shell
uncategorized; Enterprise / Car rental categorized. Same AI panel as
Home.

## Actions

- Collapse/expand nav; go Home, Expenses, Pre-Approvals, Approvals,
  Invoices, Purchase orders
- Open Drafts, Returned, Submitted
- Settings, Help center; toggle New Experience off
- Account menu; app launcher
- Company information; Unreported Expenses card; Add expense; View all;
  open a report card
- Type or speak to Emburse AI; open folder / history
- On Unreported: back, Upload, switch tabs, sort, select rows, use
  source/link-plus, open a row

## States

| Kind | On Home / Unreported? |
|------|------------------------|
| Empty page | No. Only the AI chat body is empty. |
| Loading / skeleton | Not on these frames. Nearby: Analyzing receipt / Analysing. |
| Error page / banner | No. Danger treatment is Needs attention on a report card. |
| Partial data | Yes. Home: 1 unreported + 3 cards. Unreported: 3× No category vs 1 categorized; toolbar says 2 expenses, 4 rows shown. |
| Report variants | Draft + In policy + New; Draft + Needs attention; Submitted + Pending. |
| Nav variants | Expanded labeled nav vs collapsed icon rail. |
| Selection | Sibling frames: Unreported expenses-selected; With category - Selected. |
| Hidden layers | Connect to Calendar; Returned Folders; collapsed "Ask me anything..." AI chip. |

Nearby flow frames in the same Dashboard section (not Home itself):
Add expense, Upload from chat, Analyzing receipt, Analysis Completed,
Add to report, Select existing report, Create draft report, Expense
Review, Expense added - Confirmation.

## Annotations

No sticky notes, redlines, or comment pins on Home or Unreported
expenses. Frame and section names are the flow map. Component docs in
the file cover expanded vs compact side nav, 32px buttons, badge
tokens, and status icons (verified_user, encrypted_minus_circle,
schedule).

## How to refresh this snapshot

1. Open a Home or Unreported node URL above.
2. Re-pull with Figma MCP (`get_design_context` / `get_screenshot` on
   that nodeId).
3. Update this file. Do not treat MCP asset URLs as permanent — they
   expire in about 7 days.
4. Optional: export PNGs from Figma into `notes/survey/figma/` if you
   want pixels in git. Keep Figma as the source of truth.
