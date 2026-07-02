# 10 Meetings

## Purpose

The Meetings folder stores notes from all project meetings — standups, planning sessions, design reviews, retrospectives, and stakeholder meetings. Meeting notes create an searchable record of discussions, decisions made in meetings, and action items assigned.

## Contents

| Item | Type | Description |
|------|------|-------------|
| `MTG-YYYY-MM-DD-<Topic>.md` | Notes | Individual meeting notes |
| `MeetingIndex.md` | Index | Chronological list of all meetings |
| `ActionItems.md` | Tracker | Outstanding action items from all meetings |
| `README.md` | Guide | This file |

## Workflow

1. **Before Meeting**: Create a meeting note file with agenda items.
2. **During Meeting**: Record decisions, discussion points, and action items.
3. **After Meeting**: Finalize notes within 24 hours, update `ActionItems.md`.
4. **Action Item Tracking**: Action items are tracked until completed, with status updates in `ActionItems.md`.
5. **Indexing**: Add the meeting to `MeetingIndex.md`.
6. **Linking**: Link to related decisions in `08 Decisions/` and tasks in the project tracker.

## Conventions

- Meeting filenames: `MTG-YYYY-MM-DD-Short-Topic.md`.
- Each note includes: `Date`, `Attendees`, `Type`, `Agenda`, `Discussion`, `Decisions`, `Action Items`.
- Meeting types: `standup`, `planning`, `review`, `retrospective`, `design`, `stakeholder`, `ad-hoc`.
- Action items include: assignee, due date, and status.
- Action item status: `Open`, `In Progress`, `Done`, `Cancelled`.
- Keep notes factual — record what was discussed and decided, not opinions.

## Examples

```markdown
## MTG-2026-06-15-Sprint-Planning.md excerpt

## Type
Planning

## Attendees
@dev1, @dev2, @pm, @designer

## Agenda
1. Review Sprint-001 completion
2. Plan Sprint-002 scope
3. Assign tasks

## Decisions
- Sprint-002 will focus on authentication and user profiles
- @dev1 will lead auth implementation

## Action Items
| ID | Action | Assignee | Due | Status |
|----|--------|----------|-----|--------|
| A-014 | Create auth middleware | @dev1 | 2026-06-20 | Open |
| A-015 | Design profile page | @designer | 2026-06-18 | Open |
```
